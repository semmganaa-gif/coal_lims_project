# app/routes/chat_events.py
# -*- coding: utf-8 -*-
"""
WebSocket чат events - Flask-SocketIO
Химич ↔ Ахлах real-time харилцаа
"""

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from markupsafe import escape as _esc
from app import socketio, db
from app.models import ChatMessage, UserOnlineStatus, User, Sample
from app.utils.datetime import now_local as now_mn
import logging
import re
from threading import Lock

logger = logging.getLogger(__name__)

# CC-5: Thread-safe online users tracking
online_users = {}  # {user_id: socket_id}
_online_lock = Lock()


def get_user_room(user_id):
    """User-ийн хувийн room нэр"""
    return f"user_{user_id}"


@socketio.on('connect')
def handle_connect():
    """WebSocket холболт үүссэн үед"""
    if not current_user.is_authenticated:
        return False

    user_id = current_user.id
    socket_id = request.sid

    join_room(get_user_room(user_id))
    join_room('broadcast')  # Broadcast room-д нэгдэх

    with _online_lock:
        online_users[user_id] = socket_id
    update_online_status(user_id, True, socket_id)

    emit('user_online', {
        'user_id': user_id,
        'username': current_user.username,
        'is_online': True
    }, broadcast=True)

    logger.info(f"User {current_user.username} connected")


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket холболт тасарсан үед"""
    if not current_user.is_authenticated:
        return

    user_id = current_user.id
    leave_room(get_user_room(user_id))
    leave_room('broadcast')

    with _online_lock:
        online_users.pop(user_id, None)
    update_online_status(user_id, False, None)

    emit('user_offline', {
        'user_id': user_id,
        'username': current_user.username,
        'is_online': False
    }, broadcast=True)

    logger.info(f"User {current_user.username} disconnected")


@socketio.on('send_message')
def handle_send_message(data):
    """Мессеж илгээх"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Login required'})
        return

    receiver_id = data.get('receiver_id')
    message_text = str(_esc(data.get('message', '').strip()))
    is_urgent = data.get('is_urgent', False)
    sample_id = data.get('sample_id')
    message_type = data.get('message_type', 'text')

    if not message_text:
        emit('error', {'message': 'Message is empty'})
        return

    # Validate receiver
    receiver = None
    if receiver_id:
        receiver = db.session.get(User, receiver_id)
        if not receiver:
            emit('error', {'message': 'Recipient not found'})
            return

    # Validate sample if provided
    sample = None
    if sample_id:
        sample = db.session.get(Sample, sample_id)
        if sample:
            message_type = 'sample'

    # Create message
    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_text,
        message_type=message_type,
        is_urgent=is_urgent,
        sample_id=sample_id if sample else None,
        sent_at=now_mn()
    )
    db.session.add(msg)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Message save error: {e}")
        emit('error', {'message': 'Message save failed'})
        return

    message_data = msg.to_dict()

    # Send to receiver
    if receiver_id:
        emit('new_message', message_data, room=get_user_room(receiver_id))

    # Confirmation to sender
    emit('message_sent', message_data)

    # Urgent notification
    if is_urgent and receiver_id:
        emit('urgent_message', message_data, room=get_user_room(receiver_id))

    logger.info(f"Message sent: {current_user.username} -> {receiver.username if receiver else 'self'}")


@socketio.on('send_file')
def handle_send_file(data):
    """Файл илгээх"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Login required'})
        return

    receiver_id = data.get('receiver_id')
    file_url = data.get('file_url', '')
    file_name = data.get('file_name', '')
    file_size = data.get('file_size', 0)

    if not file_url:
        emit('error', {'message': 'File URL required'})
        return

    # M-8: Validate file_url — only allow internal upload paths
    if not re.match(r'^/static/uploads/[\w.\-/]+$', file_url):
        emit('error', {'message': 'Invalid file URL'})
        return

    # Sanitize file_name
    file_name = str(_esc(file_name)) if file_name else ''
    message_text = str(_esc(data.get('message', file_name or 'File')))

    # Determine file type
    ext = file_name.lower().split('.')[-1] if file_name else ''
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        message_type = 'image'
    else:
        message_type = 'file'

    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_text,
        message_type=message_type,
        file_url=file_url,
        file_name=file_name,
        file_size=file_size,
        sent_at=now_mn()
    )
    db.session.add(msg)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"File message save error: {e}")
        emit('error', {'message': 'File save failed'})
        return

    message_data = msg.to_dict()

    if receiver_id:
        emit('new_message', message_data, room=get_user_room(receiver_id))
    emit('message_sent', message_data)


@socketio.on('delete_message')
def handle_delete_message(data):
    """Мессеж устгах (soft delete)"""
    if not current_user.is_authenticated:
        return

    message_id = data.get('message_id')
    msg = db.session.get(ChatMessage, message_id)

    if not msg:
        emit('error', {'message': 'Message not found'})
        return

    # Only sender can delete
    if msg.sender_id != current_user.id:
        emit('error', {'message': 'Can only delete your own messages'})
        return

    msg.is_deleted = True
    msg.deleted_at = now_mn()
    msg.message = "Мессеж устгагдсан"
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete message error: {e}")
        return

    # Notify both parties
    emit('message_deleted', {'message_id': message_id})
    if msg.receiver_id:
        emit('message_deleted', {'message_id': message_id}, room=get_user_room(msg.receiver_id))


@socketio.on('broadcast_message')
def handle_broadcast(data):
    """Бүх хэрэглэгчид зарлал илгээх (senior/admin only)"""
    if not current_user.is_authenticated:
        return

    if current_user.role not in ('senior', 'admin'):
        emit('error', {'message': 'Only senior and admin can send announcements'})
        return

    message_text = str(_esc(data.get('message', '').strip()))
    if not message_text:
        return

    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=None,
        message=message_text,
        message_type='broadcast',
        is_broadcast=True,
        sent_at=now_mn()
    )
    db.session.add(msg)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Broadcast save error: {e}")
        emit('error', {'message': 'Broadcast save failed'})
        return

    message_data = msg.to_dict()

    # Send to all connected users
    emit('broadcast_message', message_data, room='broadcast')
    emit('message_sent', message_data)

    logger.info(f"Broadcast from {current_user.username}: {message_text[:50]}")


@socketio.on('mark_read')
def handle_mark_read(data):
    """Мессежийг уншсан гэж тэмдэглэх"""
    if not current_user.is_authenticated:
        return

    message_id = data.get('message_id')
    sender_id = data.get('sender_id')

    try:
        if message_id:
            msg = db.session.get(ChatMessage, message_id)
            if msg and msg.receiver_id == current_user.id and not msg.read_at:
                msg.read_at = now_mn()
                db.session.commit()
                emit('message_read', {
                    'message_id': message_id,
                    'read_at': msg.read_at.isoformat()
                }, room=get_user_room(msg.sender_id))

        elif sender_id:
            unread = ChatMessage.query.filter(
                ChatMessage.sender_id == sender_id,
                ChatMessage.receiver_id == current_user.id,
                ChatMessage.read_at.is_(None)
            ).all()

            for msg in unread:
                msg.read_at = now_mn()
            db.session.commit()

            emit('messages_read', {
                'reader_id': current_user.id,
                'count': len(unread)
            }, room=get_user_room(sender_id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mark read error: {e}")


@socketio.on('typing')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
    receiver_id = data.get('receiver_id')
    if receiver_id:
        emit('user_typing', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=get_user_room(receiver_id))


@socketio.on('stop_typing')
def handle_stop_typing(data):
    if not current_user.is_authenticated:
        return
    receiver_id = data.get('receiver_id')
    if receiver_id:
        emit('user_stop_typing', {
            'user_id': current_user.id
        }, room=get_user_room(receiver_id))


@socketio.on('get_online_users')
def handle_get_online_users():
    if not current_user.is_authenticated:
        return

    with _online_lock:
        user_ids = list(online_users.keys())
    online_list = []
    for uid in user_ids:
        user = db.session.get(User, uid)
        if user:
            online_list.append({
                'user_id': user.id,
                'username': user.username,
                'role': user.role
            })
    emit('online_users_list', {'users': online_list})


def update_online_status(user_id, is_online, socket_id):
    """Database дээр онлайн статус шинэчлэх"""
    try:
        status = db.session.get(UserOnlineStatus, user_id)
        if not status:
            status = UserOnlineStatus(user_id=user_id)
            db.session.add(status)

        status.is_online = is_online
        status.last_seen = now_mn()
        status.socket_id = socket_id
        db.session.commit()
    except Exception as e:
        logger.error(f"Error updating online status: {e}")
        db.session.rollback()

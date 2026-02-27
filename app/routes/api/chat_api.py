# app/routes/api/chat_api.py
# -*- coding: utf-8 -*-
"""
Chat REST API endpoints
"""

import asyncio
import os
import uuid
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import ChatMessage, User, UserOnlineStatus, Sample
from sqlalchemy import or_, and_
from app.utils.security import escape_like_pattern


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ✅ ШИНЭ: MIME type validation (magic bytes)
ALLOWED_MIME_TYPES = {
    'image/png': [b'\x89PNG'],
    'image/jpeg': [b'\xff\xd8\xff'],
    'image/gif': [b'GIF87a', b'GIF89a'],
    'image/webp': [b'RIFF'],
    'application/pdf': [b'%PDF'],
    # Office 97-2003 (.doc, .xls) - OLE/Compound File format
    'application/msword': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    'application/vnd.ms-excel': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    # Office 2007+ (.docx, .xlsx) - ZIP-based OOXML format
    'application/vnd.openxmlformats-officedocument': [b'PK\x03\x04'],
}


def allowed_file(filename):
    """Extension шалгах"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_content(file, extension):
    """
    ✅ ШИНЭ: Файлын агуулгыг magic bytes-ээр шалгах
    Зураг, PDF, Office файлуудад хэрэглэнэ
    """
    file.seek(0)
    header = file.read(16)
    file.seek(0)

    # Extension → MIME type mapping
    ext_to_mime = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'pdf': 'application/pdf',
        # Office 97-2003
        'doc': 'application/msword',
        'xls': 'application/vnd.ms-excel',
        # Office 2007+ (OOXML - ZIP format)
        'docx': 'application/vnd.openxmlformats-officedocument',
        'xlsx': 'application/vnd.openxmlformats-officedocument',
    }

    mime_type = ext_to_mime.get(extension)
    if mime_type and mime_type in ALLOWED_MIME_TYPES:
        magic_bytes_list = ALLOWED_MIME_TYPES[mime_type]
        for magic in magic_bytes_list:
            if header.startswith(magic):
                return True
        return False

    return True  # Unknown type - allow (extension already validated)


def register_routes(bp):
    """Chat API routes-ийг blueprint дээр бүртгэх"""

    @bp.route("/chat/contacts", methods=["GET"])
    @login_required
    async def get_chat_contacts():
        """Чат контакт жагсаалт"""
        contacts = []

        if current_user.role in ('chemist', 'prep'):
            users = User.query.filter(
                User.role.in_(['senior', 'admin']),
                User.id != current_user.id
            ).all()
        else:
            users = User.query.filter(
                User.role.in_(['chemist', 'prep', 'senior', 'admin']),
                User.id != current_user.id
            ).all()

        for user in users:
            unread_count = ChatMessage.query.filter(
                ChatMessage.sender_id == user.id,
                ChatMessage.receiver_id == current_user.id,
                ChatMessage.read_at.is_(None),
                ChatMessage.is_deleted == False
            ).count()

            last_msg = ChatMessage.query.filter(
                or_(
                    and_(ChatMessage.sender_id == user.id, ChatMessage.receiver_id == current_user.id),
                    and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user.id)
                ),
                ChatMessage.is_deleted == False
            ).order_by(ChatMessage.sent_at.desc()).first()

            online_status = db.session.get(UserOnlineStatus, user.id)
            is_online = online_status.is_online if online_status else False

            contacts.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'is_online': is_online,
                'unread_count': unread_count,
                'last_message': last_msg.message[:50] if last_msg else None,
                'last_message_time': last_msg.sent_at.isoformat() if last_msg else None,
                'last_message_urgent': last_msg.is_urgent if last_msg else False
            })

        contacts.sort(key=lambda x: (-x['unread_count'], -x['is_online'], x['username']))
        return jsonify({'contacts': contacts})

    @bp.route("/chat/history/<int:user_id>", methods=["GET"])
    @login_required
    async def get_chat_history(user_id):
        """Хоёр хэрэглэгчийн хоорондын мессежийн түүх"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        search = request.args.get('search', '').strip()

        query = ChatMessage.query.filter(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
                and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
            ),
            ChatMessage.is_deleted == False
        )

        # Хайлт
        if search:
            safe_search = escape_like_pattern(search)
            query = query.filter(ChatMessage.message.ilike(f'%{safe_search}%'))

        messages = query.order_by(ChatMessage.sent_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Mark as read
        from app.utils.datetime import now_local as now_mn
        unread_from_user = ChatMessage.query.filter(
            ChatMessage.sender_id == user_id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.read_at.is_(None)
        ).all()

        for msg in unread_from_user:
            msg.read_at = now_mn()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Mark messages read commit error: {e}")

        return jsonify({
            'messages': [m.to_dict() for m in reversed(messages.items)],
            'page': page,
            'pages': messages.pages,
            'total': messages.total,
            'has_more': messages.has_next
        })

    @bp.route("/chat/search", methods=["GET"])
    @login_required
    async def search_messages():
        """Мессеж хайх"""
        query_text = request.args.get('q', '').strip()
        user_id = request.args.get('user_id', type=int)

        if not query_text or len(query_text) < 2:
            return jsonify({'messages': []})

        safe_query_text = escape_like_pattern(query_text)
        q = ChatMessage.query.filter(
            ChatMessage.message.ilike(f'%{safe_query_text}%'),
            ChatMessage.is_deleted == False,
            or_(
                ChatMessage.sender_id == current_user.id,
                ChatMessage.receiver_id == current_user.id
            )
        )

        if user_id:
            q = q.filter(
                or_(
                    and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id),
                    and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id)
                )
            )

        messages = q.order_by(ChatMessage.sent_at.desc()).limit(50).all()

        return jsonify({
            'messages': [m.to_dict() for m in messages],
            'query': query_text
        })

    @bp.route("/chat/unread_count", methods=["GET"])
    @login_required
    async def get_unread_count():
        """Нийт уншаагүй мессежийн тоо"""
        count = ChatMessage.query.filter(
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.read_at.is_(None),
            ChatMessage.is_deleted == False
        ).count()
        return jsonify({'unread_count': count})

    @bp.route("/chat/upload", methods=["POST"])
    @login_required
    async def upload_chat_file():
        """Файл upload хийх"""
        if 'file' not in request.files:
            return jsonify({'error': 'Файл олдсонгүй'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл сонгоогүй байна'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Энэ файлын төрөл зөвшөөрөгдөөгүй'}), 400

        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Файл хэт том байна (хамгийн ихдээ 10MB)'}), 400

        # ✅ ЗАСВАРЛАСАН: Аюулгүй файл нэр үүсгэх
        original_filename = secure_filename(file.filename)
        if not original_filename or '.' not in original_filename:
            return jsonify({'error': 'Буруу файлын нэр'}), 400

        extension = original_filename.rsplit('.', 1)[1].lower()

        # ✅ Magic bytes validation (зураг, PDF)
        if not validate_file_content(file, extension):
            return jsonify({'error': 'Файлын агуулга өргөтгөлтэй таарахгүй байна'}), 400

        # ✅ UUID ашиглах (timestamp биш - урьдчилан таах боломжгүй)
        unique_filename = f"{uuid.uuid4().hex}.{extension}"

        # Save to uploads/chat folder
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'chat')
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        file_url = f"/static/uploads/chat/{unique_filename}"

        return jsonify({
            'success': True,
            'file_url': file_url,
            'file_name': file.filename,  # Original name for display
            'file_size': file_size
        })

    @bp.route("/chat/samples/search", methods=["GET"])
    @login_required
    async def search_samples_for_chat():
        """Дээж хайх (чатад холбохын тулд)"""
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'samples': []})

        safe_query = escape_like_pattern(query)
        samples = Sample.query.filter(
            or_(
                Sample.sample_code.ilike(f'%{safe_query}%'),
                Sample.client_name.ilike(f'%{safe_query}%'),
                Sample.sample_type.ilike(f'%{safe_query}%')
            )
        ).order_by(Sample.id.desc()).limit(20).all()

        return jsonify({
            'samples': [{
                'id': s.id,
                'code': s.sample_code,
                'name': f"{s.sample_type} - {s.client_name or ''}",
                'type': s.sample_type,
                'client': s.client_name
            } for s in samples]
        })

    @bp.route("/chat/templates", methods=["GET"])
    @login_required
    async def get_message_templates():
        """Template мессежүүд"""
        templates = [
            {'id': 1, 'text': 'Дээж бэлэн боллоо', 'icon': '✅'},
            {'id': 2, 'text': 'Шинжилгээ эхэллээ', 'icon': '🔬'},
            {'id': 3, 'text': 'Шинжилгээ дууслаа', 'icon': '✔️'},
            {'id': 4, 'text': 'Үр дүн шалгана уу', 'icon': '👀'},
            {'id': 5, 'text': 'Асуулт байна', 'icon': '❓'},
            {'id': 6, 'text': 'Яаралтай шалгаарай', 'icon': '🚨'},
            {'id': 7, 'text': 'OK, ойлголоо', 'icon': '👍'},
            {'id': 8, 'text': 'Түр хүлээнэ үү', 'icon': '⏳'},
            {'id': 9, 'text': 'Баярлалаа', 'icon': '🙏'},
            {'id': 10, 'text': 'Тоног төхөөрөмж асуудалтай', 'icon': '⚠️'},
        ]
        return jsonify({'templates': templates})

    @bp.route("/chat/broadcasts", methods=["GET"])
    @login_required
    async def get_broadcasts():
        """Broadcast зарлалууд"""
        broadcasts = ChatMessage.query.filter(
            ChatMessage.is_broadcast,
            ChatMessage.is_deleted == False
        ).order_by(ChatMessage.sent_at.desc()).limit(20).all()

        return jsonify({
            'broadcasts': [b.to_dict() for b in broadcasts]
        })

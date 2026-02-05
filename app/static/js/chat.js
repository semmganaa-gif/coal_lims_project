/**
 * LIMS Chat - Real-time messaging with Flask-SocketIO
 * Full-featured: Files, Emoji, Delete, Urgent, Sample linking, Templates, Search, Broadcast
 */

(function() {
  'use strict';

  // State
  let socket = null;
  let currentChatUserId = null;
  let contacts = [];
  let isConnected = false;
  let typingTimeout = null;
  let isUrgentMode = false;
  let selectedSampleId = null;
  let templates = [];

  // Audio elements (preloaded)
  let notificationAudio = null;
  let audioUnlocked = false;

  // Common emojis
  const EMOJIS = [
    '👍', '👎', '👌', '🙏', '👋', '✅', '❌', '❓',
    '🔬', '🧪', '📊', '📈', '📉', '⚗️', '🔥', '💧',
    '⏰', '⏳', '🕐', '📅', '📝', '📋', '📁', '📎',
    '⚠️', '🚨', '🔴', '🟢', '🟡', '🔵', '⭐', '💡',
    '😀', '😊', '🤔', '😅', '😢', '😤', '🎉', '💪'
  ];

  // DOM Elements
  const widget = document.getElementById('chatWidget');
  const toggleBtn = document.getElementById('chatToggleBtn');
  const container = document.getElementById('chatContainer');
  const unreadBadge = document.getElementById('chatUnreadBadge');
  const contactsEl = document.getElementById('chatContacts');
  const contactsEmpty = document.getElementById('chatContactsEmpty');
  const listView = document.getElementById('chatListView');
  const chatView = document.getElementById('chatView');
  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  const partnerName = document.getElementById('chatPartnerName');
  const partnerAvatar = document.getElementById('chatPartnerAvatar');
  const partnerStatus = document.getElementById('chatPartnerStatus');
  const typingIndicator = document.getElementById('typingIndicator');
  const typingUser = document.getElementById('typingUser');
  const broadcastsEl = document.getElementById('chatBroadcasts');
  const broadcastView = document.getElementById('broadcastView');

  // Initialize
  function init() {
    if (!widget) return;

    // Preload audio and setup unlock
    preloadAudio();
    unlockAudio();

    // Connect to WebSocket
    connectSocket();

    // Event listeners - Main
    toggleBtn.addEventListener('click', toggleChat);
    document.getElementById('chatCloseBtn').addEventListener('click', closeChat);
    document.getElementById('chatRefreshBtn').addEventListener('click', loadContacts);
    document.getElementById('chatBackBtn').addEventListener('click', showContactList);
    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keypress', handleInputKeypress);
    inputEl.addEventListener('input', handleTyping);

    // Tab switching
    document.querySelectorAll('.chat-tab').forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Search
    const searchBtn = document.getElementById('chatSearchBtn');
    const searchBox = document.getElementById('chatSearchBox');
    const searchInput = document.getElementById('chatSearchInput');
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        searchBox.style.display = searchBox.style.display === 'none' ? 'block' : 'none';
        if (searchBox.style.display === 'block') searchInput.focus();
      });
    }
    if (searchInput) {
      searchInput.addEventListener('input', debounce(handleSearch, 300));
    }

    // Message search in chat
    const msgSearchBtn = document.getElementById('chatMsgSearchBtn');
    if (msgSearchBtn) {
      msgSearchBtn.addEventListener('click', () => {
        const query = prompt('Хайх үг:');
        if (query && query.trim()) {
          searchMessagesInChat(query.trim());
        }
      });
    }

    // Tool buttons
    document.getElementById('btnTemplate').addEventListener('click', () => togglePopup('templatePopup'));
    document.getElementById('btnEmoji').addEventListener('click', () => togglePopup('emojiPopup'));
    document.getElementById('btnFile').addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('btnSample').addEventListener('click', () => togglePopup('samplePopup'));
    document.getElementById('btnUrgent').addEventListener('click', toggleUrgentMode);

    // File input
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);

    // Sample search
    const sampleSearchInput = document.getElementById('sampleSearchInput');
    if (sampleSearchInput) {
      sampleSearchInput.addEventListener('input', debounce(searchSamples, 300));
    }

    // Broadcast
    const broadcastBtn = document.getElementById('chatBroadcastBtn');
    if (broadcastBtn) {
      broadcastBtn.addEventListener('click', showBroadcastView);
    }
    const broadcastBackBtn = document.getElementById('broadcastBackBtn');
    if (broadcastBackBtn) {
      broadcastBackBtn.addEventListener('click', hideBroadcastView);
    }
    const sendBroadcastBtn = document.getElementById('sendBroadcastBtn');
    if (sendBroadcastBtn) {
      sendBroadcastBtn.addEventListener('click', sendBroadcast);
    }

    // Load templates and emojis
    loadTemplates();
    renderEmojis();

    // Load initial data
    loadUnreadCount();
  }

  // WebSocket Connection
  function connectSocket() {
    socket = io({
      transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
      console.log('Chat connected');
      isConnected = true;
    });

    socket.on('disconnect', () => {
      console.log('Chat disconnected');
      isConnected = false;
    });

    // New message received
    socket.on('new_message', (data) => {
      // Always play sound for incoming messages
      if (data.is_urgent) {
        playUrgentSound();
      } else {
        playNotificationSound();
      }

      if (currentChatUserId === data.sender_id) {
        // Chat is open with this person
        appendMessage(data, false);
        markAsRead(data.sender_id);
      } else {
        // Chat is not open - show notification
        updateUnreadBadge();
        loadContacts();
        showNotification(data);
      }
    });

    // Message sent confirmation
    socket.on('message_sent', (data) => {
      appendMessage(data, true);
      inputEl.value = '';
      clearSelectedSample();
      scrollToBottom();
    });

    // User online/offline
    socket.on('user_online', (data) => {
      updateContactStatus(data.user_id, true);
      if (currentChatUserId === data.user_id) {
        partnerStatus.textContent = 'Онлайн';
        partnerStatus.classList.remove('offline');
      }
    });

    socket.on('user_offline', (data) => {
      updateContactStatus(data.user_id, false);
      if (currentChatUserId === data.user_id) {
        partnerStatus.textContent = 'Офлайн';
        partnerStatus.classList.add('offline');
      }
    });

    // Typing indicators
    socket.on('user_typing', (data) => {
      if (currentChatUserId === data.user_id) {
        typingUser.textContent = data.username;
        typingIndicator.classList.add('show');
      }
    });

    socket.on('user_stop_typing', (data) => {
      if (currentChatUserId === data.user_id) {
        typingIndicator.classList.remove('show');
      }
    });

    // Message deleted
    socket.on('message_deleted', (data) => {
      const msgEl = messagesEl.querySelector(`[data-message-id="${data.message_id}"]`);
      if (msgEl) {
        msgEl.classList.add('deleted');
        const textEl = msgEl.querySelector('.message-text');
        if (textEl) textEl.textContent = 'Мессеж устгагдсан';
      }
    });

    // Broadcast message
    socket.on('broadcast_message', (data) => {
      showBroadcastNotification(data);
      loadBroadcasts();
    });

    // Urgent message
    socket.on('urgent_message', (data) => {
      playUrgentSound();
      showUrgentNotification(data);
    });

    // Message read
    socket.on('message_read', (data) => {
      const msgEl = messagesEl.querySelector(`[data-message-id="${data.message_id}"]`);
      if (msgEl) {
        const readEl = msgEl.querySelector('.message-read');
        if (readEl) readEl.innerHTML = '<i class="bi bi-check2-all"></i>';
      }
    });

    socket.on('error', (data) => {
      console.error('Chat error:', data.message);
      alert(data.message);
    });
  }

  // Toggle chat window
  function toggleChat() {
    container.classList.toggle('open');
    if (container.classList.contains('open')) {
      loadContacts();
      requestNotificationPermission();
    }
  }

  function closeChat() {
    container.classList.remove('open');
  }

  // Tab switching
  function switchTab(tab) {
    document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.chat-tab[data-tab="${tab}"]`).classList.add('active');

    if (tab === 'contacts') {
      contactsEl.style.display = 'block';
      broadcastsEl.style.display = 'none';
    } else {
      contactsEl.style.display = 'none';
      broadcastsEl.style.display = 'block';
      loadBroadcasts();
    }
  }

  // Load contacts
  function loadContacts() {
    contactsEmpty.innerHTML = '<i class="bi bi-hourglass-split"></i><p>Ачаалж байна...</p>';
    contactsEmpty.style.display = 'flex';

    fetch('/api/chat/contacts')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        return r.json();
      })
      .then(data => {
        contacts = data.contacts || [];
        renderContacts();
      })
      .catch(err => {
        console.error('Error loading contacts:', err);
        // ✅ XSS сэргийлэлт: err.message escape
        contactsEmpty.innerHTML = `<i class="bi bi-exclamation-triangle"></i><p>Алдаа: ${escapeHtml(err.message || 'Unknown error')}</p>`;
      });
  }

  // Render contacts
  function renderContacts() {
    if (contacts.length === 0) {
      contactsEmpty.innerHTML = '<i class="bi bi-people"></i><p>Холбогдох хэрэглэгч байхгүй</p>';
      contactsEmpty.style.display = 'flex';
      return;
    }

    contactsEmpty.style.display = 'none';

    let html = '';
    contacts.forEach(c => {
      const initial = c.username.charAt(0).toUpperCase();
      const onlineClass = c.is_online ? '' : 'offline';
      const roleClass = c.role === 'senior' ? 'senior' : (c.role === 'admin' ? 'admin' : '');
      const roleLabel = c.role === 'senior' ? 'Ахлах' : (c.role === 'admin' ? 'Админ' : (c.role === 'chemist' ? 'Химич' : 'Бэлтгэгч'));
      const urgentIcon = c.last_message_urgent ? '<i class="bi bi-exclamation-triangle text-danger"></i> ' : '';

      html += `
        <div class="contact-item" data-user-id="${c.id}" onclick="window.LIMS_CHAT.openChat(${c.id})">
          <div class="contact-avatar">
            ${initial}
            <span class="online-dot ${onlineClass}"></span>
          </div>
          <div class="contact-info">
            <div class="contact-name">
              ${c.username}
              <span class="contact-role ${roleClass}">${roleLabel}</span>
            </div>
            <div class="contact-preview">${urgentIcon}${c.last_message || 'Шинэ харилцаа эхлүүлэх'}</div>
          </div>
          ${c.unread_count > 0 ? `<span class="contact-unread">${c.unread_count}</span>` : ''}
        </div>
      `;
    });

    const existingItems = contactsEl.querySelectorAll('.contact-item');
    existingItems.forEach(el => el.remove());
    contactsEl.insertAdjacentHTML('beforeend', html);
  }

  // Load broadcasts
  function loadBroadcasts() {
    fetch('/api/chat/broadcasts')
      .then(r => r.json())
      .then(data => {
        const broadcasts = data.broadcasts || [];
        if (broadcasts.length === 0) {
          broadcastsEl.innerHTML = '<div class="chat-empty"><i class="bi bi-megaphone"></i><p>Зарлал байхгүй</p></div>';
          return;
        }

        let html = '';
        broadcasts.forEach(b => {
          const time = formatTime(b.sent_at);
          html += `
            <div class="broadcast-message">
              <div class="sender">${b.sender_name}</div>
              <div>${b.message}</div>
              <div style="font-size:0.7rem;opacity:0.7;margin-top:0.3rem;">${time}</div>
            </div>
          `;
        });
        broadcastsEl.innerHTML = html;
      })
      .catch(err => console.error('Error loading broadcasts:', err));
  }

  // Open chat with specific user
  function openChat(userId) {
    currentChatUserId = userId;
    const contact = contacts.find(c => c.id === userId);

    if (!contact) {
      console.error('Contact not found');
      return;
    }

    partnerName.textContent = contact.username;
    partnerAvatar.textContent = contact.username.charAt(0).toUpperCase();
    partnerStatus.textContent = contact.is_online ? 'Онлайн' : 'Офлайн';
    partnerStatus.classList.toggle('offline', !contact.is_online);

    listView.style.display = 'none';
    chatView.classList.add('active');

    loadMessages(userId);
    setTimeout(() => inputEl.focus(), 100);
  }

  // Show contact list
  function showContactList() {
    currentChatUserId = null;
    chatView.classList.remove('active');
    listView.style.display = 'block';
    loadContacts();
  }

  // Load chat messages
  function loadMessages(userId) {
    messagesEl.innerHTML = '<div style="text-align:center;color:#94a3b8;padding:2rem;">Ачаалж байна...</div>';

    fetch(`/api/chat/history/${userId}`)
      .then(r => r.json())
      .then(data => {
        const messages = data.messages || [];
        renderMessages(messages);
        scrollToBottom();
        updateUnreadBadge();
      })
      .catch(err => {
        console.error('Error loading messages:', err);
        messagesEl.innerHTML = '<div style="text-align:center;color:#ef4444;padding:2rem;">Алдаа гарлаа</div>';
      });
  }

  // Render messages
  function renderMessages(messages) {
    if (messages.length === 0) {
      messagesEl.innerHTML = '<div style="text-align:center;color:#94a3b8;padding:2rem;">Мессеж байхгүй. Харилцаа эхлүүлээрэй!</div>';
      return;
    }

    let html = '';
    messages.forEach(m => {
      html += buildMessageHtml(m);
    });

    messagesEl.innerHTML = html;
  }

  // Build message HTML
  function buildMessageHtml(m) {
    const isSent = m.sender_id === window.CHAT_USER_ID;
    const time = formatTime(m.sent_at);
    const urgentClass = m.is_urgent ? 'urgent' : '';
    const deletedClass = m.is_deleted ? 'deleted' : '';

    let content = escapeHtml(m.message);

    // File/Image attachment
    if (m.message_type === 'image' && m.file_url) {
      content += `<div class="message-image-wrapper"><img src="${m.file_url}" class="message-image" onclick="window.open('${m.file_url}')" alt="Image"></div>`;
    } else if (m.message_type === 'file' && m.file_url) {
      const size = m.file_size ? formatFileSize(m.file_size) : '';
      content += `<div class="message-file"><i class="bi bi-file-earmark"></i><a href="${m.file_url}" target="_blank">${m.file_name || 'Файл'}</a> <small>(${size})</small></div>`;
    }

    // Sample link
    if (m.sample_id) {
      const sampleCode = m.sample?.code || `#${m.sample_id}`;
      content += `<div class="message-sample"><i class="bi bi-box"></i><a href="/api/sample_report/${m.sample_id}" target="_blank">${sampleCode}</a></div>`;
    }

    const deleteBtn = isSent && !m.is_deleted ? `
      <div class="message-actions">
        <button class="message-delete-btn" onclick="window.LIMS_CHAT.deleteMessage(${m.id})" title="Устгах"><i class="bi bi-trash"></i></button>
      </div>
    ` : '';

    const readStatus = isSent ? `<span class="message-read">${m.read_at ? '<i class="bi bi-check2-all"></i>' : '<i class="bi bi-check2"></i>'}</span>` : '';

    return `
      <div class="message ${isSent ? 'sent' : 'received'} ${urgentClass} ${deletedClass}" data-message-id="${m.id}">
        ${deleteBtn}
        <div class="message-text">${content}</div>
        <span class="message-time">${time} ${readStatus}</span>
      </div>
    `;
  }

  // Append new message
  function appendMessage(data, isSent) {
    // Remove "no messages" placeholder
    const placeholder = messagesEl.querySelector('[style*="text-align:center"]');
    if (placeholder) placeholder.remove();

    const html = buildMessageHtml(data);
    messagesEl.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
  }

  // Send message
  function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || !currentChatUserId) return;

    const messageData = {
      receiver_id: currentChatUserId,
      message: text,
      is_urgent: isUrgentMode
    };

    if (selectedSampleId) {
      messageData.sample_id = selectedSampleId;
    }

    socket.emit('send_message', messageData);

    // Reset urgent mode
    if (isUrgentMode) {
      toggleUrgentMode();
    }

    socket.emit('stop_typing', { receiver_id: currentChatUserId });
  }

  // Handle input keypress
  function handleInputKeypress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // Handle typing indicator
  function handleTyping() {
    if (!currentChatUserId) return;

    socket.emit('typing', { receiver_id: currentChatUserId });

    if (typingTimeout) clearTimeout(typingTimeout);

    typingTimeout = setTimeout(() => {
      socket.emit('stop_typing', { receiver_id: currentChatUserId });
    }, 2000);
  }

  // Mark messages as read
  function markAsRead(senderId) {
    socket.emit('mark_read', { sender_id: senderId });
  }

  // Delete message
  function deleteMessage(messageId) {
    if (!confirm('Мессеж устгах уу?')) return;
    socket.emit('delete_message', { message_id: messageId });
  }

  // Toggle urgent mode
  function toggleUrgentMode() {
    isUrgentMode = !isUrgentMode;
    const btn = document.getElementById('btnUrgent');
    btn.classList.toggle('urgent-active', isUrgentMode);
    inputEl.style.borderColor = isUrgentMode ? '#ef4444' : '';
  }

  // File handling
  function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Check size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Файл хэт том (max 10MB)');
      return;
    }

    // Upload file
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/chat/upload', {
      method: 'POST',
      body: formData
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }

        // Send file message
        socket.emit('send_file', {
          receiver_id: currentChatUserId,
          file_url: data.file_url,
          file_name: data.file_name,
          file_size: data.file_size,
          message: file.name
        });
      })
      .catch(err => {
        console.error('File upload error:', err);
        alert('Файл upload алдаа');
      });

    e.target.value = '';
  }

  // Templates
  function loadTemplates() {
    fetch('/api/chat/templates')
      .then(r => r.json())
      .then(data => {
        templates = data.templates || [];
        renderTemplates();
      })
      .catch(err => console.error('Error loading templates:', err));
  }

  function renderTemplates() {
    const list = document.getElementById('templateList');
    if (!list) return;

    let html = '';
    templates.forEach(t => {
      html += `<div class="template-item" onclick="window.LIMS_CHAT.selectTemplate('${t.text}')">${t.icon} ${t.text}</div>`;
    });
    list.innerHTML = html;
  }

  function selectTemplate(text) {
    inputEl.value = text;
    inputEl.focus();
    closeAllPopups();
  }

  // Emojis
  function renderEmojis() {
    const grid = document.getElementById('emojiGrid');
    if (!grid) return;

    let html = '';
    EMOJIS.forEach(e => {
      html += `<div class="emoji-item" onclick="window.LIMS_CHAT.selectEmoji('${e}')">${e}</div>`;
    });
    grid.innerHTML = html;
  }

  function selectEmoji(emoji) {
    inputEl.value += emoji;
    inputEl.focus();
    closeAllPopups();
  }

  // Sample search
  function searchSamples() {
    const input = document.getElementById('sampleSearchInput');
    const query = input.value.trim();
    if (query.length < 2) return;

    fetch(`/api/chat/samples/search?q=${encodeURIComponent(query)}`)
      .then(r => r.json())
      .then(data => {
        const list = document.getElementById('sampleList');
        const samples = data.samples || [];

        if (samples.length === 0) {
          list.innerHTML = '<div style="padding:0.5rem;color:#94a3b8;text-align:center;">Олдсонгүй</div>';
          return;
        }

        let html = '';
        samples.forEach(s => {
          html += `<div class="sample-item" onclick="window.LIMS_CHAT.selectSample(${s.id}, '${s.code}')">${s.code} - ${s.name || ''}</div>`;
        });
        list.innerHTML = html;
      })
      .catch(err => console.error('Error searching samples:', err));
  }

  function selectSample(id, code) {
    selectedSampleId = id;
    document.getElementById('selectedSample').style.display = 'block';
    document.getElementById('selectedSampleText').textContent = `Дээж: ${code}`;
    closeAllPopups();
  }

  window.clearSelectedSample = function() {
    selectedSampleId = null;
    document.getElementById('selectedSample').style.display = 'none';
  };

  // Search messages
  function handleSearch(e) {
    const query = e.target.value.trim();
    if (query.length < 2) {
      loadContacts();
      return;
    }

    fetch(`/api/chat/search?q=${encodeURIComponent(query)}`)
      .then(r => r.json())
      .then(data => {
        // Display search results
        const messages = data.messages || [];
        if (messages.length === 0) {
          contactsEmpty.innerHTML = '<i class="bi bi-search"></i><p>Олдсонгүй</p>';
          contactsEmpty.style.display = 'flex';
          return;
        }

        contactsEmpty.style.display = 'none';
        let html = '';
        messages.forEach(m => {
          const time = formatTime(m.sent_at);
          const isFromMe = m.sender_id === window.CHAT_USER_ID;
          const otherUserId = isFromMe ? m.receiver_id : m.sender_id;
          const otherName = isFromMe ? (m.receiver_name || 'Хэрэглэгч') : (m.sender_name || 'Хэрэглэгч');

          html += `
            <div class="contact-item" onclick="window.LIMS_CHAT.openChat(${otherUserId})">
              <div class="contact-avatar">${otherName.charAt(0).toUpperCase()}</div>
              <div class="contact-info">
                <div class="contact-name">${otherName}</div>
                <div class="contact-preview">${m.message.substring(0, 50)}</div>
              </div>
              <small style="color:#94a3b8;">${time}</small>
            </div>
          `;
        });

        const existingItems = contactsEl.querySelectorAll('.contact-item');
        existingItems.forEach(el => el.remove());
        contactsEl.insertAdjacentHTML('beforeend', html);
      })
      .catch(err => console.error('Search error:', err));
  }

  function searchMessagesInChat(query) {
    if (!currentChatUserId) return;

    fetch(`/api/chat/search?q=${encodeURIComponent(query)}&user_id=${currentChatUserId}`)
      .then(r => r.json())
      .then(data => {
        const messages = data.messages || [];
        if (messages.length === 0) {
          alert('Олдсонгүй');
          return;
        }
        renderMessages(messages);
      })
      .catch(err => console.error('Search error:', err));
  }

  // Broadcast
  function showBroadcastView() {
    listView.style.display = 'none';
    broadcastView.classList.add('active');
  }

  function hideBroadcastView() {
    broadcastView.classList.remove('active');
    listView.style.display = 'block';
  }

  function sendBroadcast() {
    const input = document.getElementById('broadcastInput');
    const text = input.value.trim();
    if (!text) return;

    socket.emit('broadcast_message', { message: text });
    input.value = '';
    hideBroadcastView();
    alert('Зарлал илгээгдлээ!');
  }

  // Popups
  function togglePopup(popupId) {
    const popup = document.getElementById(popupId);
    const isOpen = popup.classList.contains('open');

    closeAllPopups();

    if (!isOpen) {
      popup.classList.add('open');
    }
  }

  function closeAllPopups() {
    document.querySelectorAll('.chat-popup').forEach(p => p.classList.remove('open'));
  }

  window.closePopup = function(popupId) {
    document.getElementById(popupId).classList.remove('open');
  };

  // Update unread badge
  function updateUnreadBadge() {
    fetch('/api/chat/unread_count')
      .then(r => r.json())
      .then(data => {
        const count = data.unread_count || 0;
        if (count > 0) {
          unreadBadge.textContent = count > 99 ? '99+' : count;
          unreadBadge.style.display = 'flex';
        } else {
          unreadBadge.style.display = 'none';
        }
      })
      .catch(err => console.error('Error fetching unread count:', err));
  }

  function loadUnreadCount() {
    updateUnreadBadge();
    setInterval(updateUnreadBadge, 30000);
  }

  // Update contact online status
  function updateContactStatus(userId, isOnline) {
    const contactEl = contactsEl.querySelector(`[data-user-id="${userId}"]`);
    if (contactEl) {
      const dot = contactEl.querySelector('.online-dot');
      if (dot) dot.classList.toggle('offline', !isOnline);
    }
    const contact = contacts.find(c => c.id === userId);
    if (contact) contact.is_online = isOnline;
  }

  // Notifications
  function showNotification(data) {
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification(data.sender_name || 'Шинэ мессеж', {
          body: data.message.substring(0, 50),
          icon: '/static/favicon.ico'
        });
      } catch (e) {
        console.log('Notification error:', e);
      }
    }

    // In-app toast (browser notification зөвшөөрөл байхгүй ч харагдана)
    showInAppToast(data);
  }

  function showInAppToast(data) {
    const existing = document.getElementById('chatToast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'chatToast';
    toast.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;background:#fff;border-left:4px solid #3a8bc7;box-shadow:0 4px 12px rgba(0,0,0,0.15);border-radius:8px;padding:0.75rem 1rem;max-width:320px;cursor:pointer;animation:slideInRight 0.3s ease-out;';
    toast.innerHTML = `
      <div style="font-weight:600;font-size:0.85rem;color:#1e293b;">${escapeHtml(data.sender_name || 'Шинэ мессеж')}</div>
      <div style="font-size:0.8rem;color:#64748b;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(data.message.substring(0, 60))}</div>
    `;
    toast.addEventListener('click', () => {
      toast.remove();
      container.classList.add('open');
      openChat(data.sender_id);
    });
    document.body.appendChild(toast);

    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
  }

  function showBroadcastNotification(data) {
    if (Notification.permission === 'granted') {
      new Notification('Зарлал: ' + (data.sender_name || 'Админ'), {
        body: data.message.substring(0, 100),
        icon: '/static/favicon.ico'
      });
    }
    playNotificationSound();
  }

  function showUrgentNotification(data) {
    if (Notification.permission === 'granted') {
      new Notification('ЯАРАЛТАЙ: ' + (data.sender_name || ''), {
        body: data.message,
        icon: '/static/favicon.ico',
        requireInteraction: true
      });
    }
  }

  // Preload audio
  function preloadAudio() {
    try {
      notificationAudio = new Audio('/static/sounds/notification.mp3');
      notificationAudio.volume = 0.6;
      notificationAudio.load();
    } catch (e) {
      console.log('Audio preload failed:', e);
    }
  }

  // Unlock audio on user interaction
  function unlockAudio() {
    if (audioUnlocked) return;

    const unlock = () => {
      if (notificationAudio) {
        // Play silent to unlock
        notificationAudio.volume = 0;
        notificationAudio.play().then(() => {
          notificationAudio.pause();
          notificationAudio.currentTime = 0;
          notificationAudio.volume = 0.6;
          audioUnlocked = true;
          console.log('Audio unlocked');
        }).catch(() => {});
      }
      document.removeEventListener('click', unlock);
      document.removeEventListener('keydown', unlock);
    };

    document.addEventListener('click', unlock, { once: true });
    document.addEventListener('keydown', unlock, { once: true });
  }

  function playNotificationSound() {
    if (!notificationAudio) {
      preloadAudio();
    }

    try {
      if (notificationAudio) {
        notificationAudio.currentTime = 0;
        notificationAudio.volume = 0.6;
        const playPromise = notificationAudio.play();
        if (playPromise) {
          playPromise.catch(err => {
            console.log('Sound play blocked:', err.message);
          });
        }
      }
    } catch (e) {
      console.log('Sound error:', e);
    }
  }

  function playUrgentSound() {
    if (!notificationAudio) {
      preloadAudio();
    }

    try {
      if (notificationAudio) {
        notificationAudio.currentTime = 0;
        notificationAudio.volume = 1.0;
        notificationAudio.play().then(() => {
          // Play again after 400ms for urgent
          setTimeout(() => {
            notificationAudio.currentTime = 0;
            notificationAudio.play().catch(() => {});
          }, 400);
        }).catch(err => {
          console.log('Urgent sound blocked:', err.message);
        });
      }
    } catch (e) {
      console.log('Urgent sound error:', e);
    }
  }

  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }

  // Utilities
  function scrollToBottom() {
    setTimeout(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }, 50);
  }

  function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('mn-MN', { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString('mn-MN', { month: 'short', day: 'numeric' }) + ' ' +
             date.toLocaleTimeString('mn-MN', { hour: '2-digit', minute: '2-digit' });
    }
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function debounce(func, wait) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  // Export for external access
  window.LIMS_CHAT = {
    openChat: openChat,
    refresh: loadContacts,
    deleteMessage: deleteMessage,
    selectTemplate: selectTemplate,
    selectEmoji: selectEmoji,
    selectSample: selectSample
  };

  // Toast animation CSS
  (function() {
    const style = document.createElement('style');
    style.textContent = '@keyframes slideInRight{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}';
    document.head.appendChild(style);
  })();

  // Initialize when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      init();
      requestNotificationPermission();
    });
  } else {
    init();
    requestNotificationPermission();
  }

})();

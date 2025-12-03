document.addEventListener('DOMContentLoaded', () => {
  const chatWrapper = document.querySelector('.chat-wrapper');
  if (!chatWrapper) {
    return;
  }

  const contactsListEl = document.getElementById('lista');
  const searchResultsEl = document.getElementById('searchResults');
  const searchInput = document.getElementById('busca');
  const messagesContainer = document.getElementById('rolagem');
  const chatBody = document.getElementById('chatBody') || messagesContainer;
  const chatUserName = document.getElementById('chatUserName');
  const chatUserStatus = document.getElementById('chatUserStatus');
  const chatUserAvatar = document.getElementById('chatUserAvatar');
  const chatPartnerFallback = document.getElementById('chatPartnerFallback');
  const emojiBtn = document.querySelector('.emoji-btn');
  const emojiPicker = document.getElementById('emojiPicker');
  const imgBtn = document.getElementById('imgBtn');
  const imgInput = document.getElementById('imgInput');
  const audioBtn = document.getElementById('audioBtn');
  const recordTimer = document.getElementById('recordTimer');
  const msgInput = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const backBtn = document.querySelector('.voltarBtn');
  const sidebar = document.querySelector('.sidebar.contatos');
  const mobileQuery = window.matchMedia('(max-width: 768px)');
  const isMobile = () => mobileQuery.matches;

  const dataset = chatWrapper.dataset || {};
  const staticConfig = window.CHAT_STATIC || {};
  const defaultAvatar = staticConfig.defaultAvatar || dataset.currentAvatar || '';
  const currentUserName = dataset.currentUser || staticConfig.currentUserName || 'Você';
  const currentUserAvatar = dataset.currentAvatar || staticConfig.currentUserAvatar || defaultAvatar;

  const endpoints = {
    conversations: dataset.conversationsUrl,
    search: dataset.searchUrl,
    start: dataset.startUrl,
    messagesTemplate: dataset.messagesUrlTemplate,
    sendTemplate: dataset.sendUrlTemplate,
    deleteTemplate: dataset.deleteUrlTemplate,
  };

  const state = {
    conversations: [],
    filteredConversations: null,
    activeConversationId: null,
    messagesCache: {},
    searchTimeout: null,
    searchResults: [],
    mobileView: null,
    lastSearchTerm: '',
    hasLoadedConversations: false,
    liveInterval: null,
    isRefreshing: false,
    messageInterval: null,
    socket: null,
    socketConversationId: null,
    socketAutoReconnect: false,
    socketReconnectTimer: null,
    socketReconnectAttempts: 0,
    socketMaxRetries: 5,
  };

  const realtimeLog = (...args) => {
    if (window.COONY_DEBUG_REALTIME) {
      console.debug('[chat realtime]', ...args);
    }
  };

  const resetDesktopLayout = () => {
    chatWrapper.classList.remove('mobile-view-list', 'mobile-view-chat');
    sidebar?.classList.remove('hidden');
    state.mobileView = null;
  };

  const setMobileView = (view) => {
    if (!isMobile()) {
      resetDesktopLayout();
      return;
    }

    state.mobileView = view === 'chat' ? 'chat' : 'list';
    chatWrapper.classList.toggle('mobile-view-chat', state.mobileView === 'chat');
    chatWrapper.classList.toggle('mobile-view-list', state.mobileView === 'list');
  };

  const handleViewportChange = () => {
    if (isMobile()) {
      const nextView = state.activeConversationId ? 'chat' : 'list';
      setMobileView(nextView);
    } else {
      resetDesktopLayout();
    }
  };

  const getCsrfToken = () => {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  };

  const csrfToken = getCsrfToken();

  const notify = (text, type = 'info') => {
    if (!text) return;
    if (window.Toast && typeof window.Toast.show === 'function') {
      window.Toast.show(text, type);
    } else {
      console[type === 'error' ? 'error' : 'log'](text);
    }
  };

  const buildUrl = (template, id) => {
    if (!template || !id) return null;
    return template.replace('__ID__', String(id));
  };

  const buildDeleteUrl = (template, messageId) => {
    if (!template || !messageId) return null;
    if (template.includes('__ID__')) {
      return template.replace('__ID__', String(messageId));
    }
    return template.replace(/0(\/delete\/?)$/, `${messageId}$1`);
  };

  const apiFetch = async (url, options = {}) => {
    const config = {
      method: options.method || 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...(options.body ? { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken } : {}),
        ...options.headers,
      },
      body: options.body,
    };

    realtimeLog('apiFetch request', config.method, url);
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data?.detail || 'Não foi possível completar a ação.';
      realtimeLog('apiFetch error', response.status, url, detail);
      throw new Error(detail);
    }
    realtimeLog('apiFetch ok', url, Object.keys(data));
    return data;
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    } catch (_) {
      return '';
    }
  };

  const getPartnerInitials = (name = '') => {
    const trimmed = name.trim();
    if (!trimmed) return '?';
    const parts = trimmed.split(' ').filter(Boolean);
    if (parts.length === 1) {
      return parts[0][0]?.toUpperCase() || '?';
    }
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  };

  const updateConversationHeader = (partner) => {
    if (!partner) {
      chatUserName.textContent = 'Selecione um contato';
      chatUserStatus.textContent = 'Busque um @ para começar';
      if (chatUserAvatar) chatUserAvatar.src = defaultAvatar;
      if (chatPartnerFallback) chatPartnerFallback.src = defaultAvatar;
      return;
    }

    chatUserName.textContent = partner.name || partner.handle || 'Contato';
    chatUserStatus.textContent = partner.handle || 'Disponível';
    const avatarUrl = partner.avatar_url || defaultAvatar;
    if (chatUserAvatar) chatUserAvatar.src = avatarUrl;
    if (chatPartnerFallback) chatPartnerFallback.src = avatarUrl;
  };

  const setSendEnabled = (enabled) => {
    sendBtn.disabled = !enabled;
    sendBtn.classList.toggle('botaoDesativo', !enabled);
    sendBtn.classList.toggle('botaoEnviarAtivo', enabled);
  };

  const scrollMessagesToBottom = () => {
    const target = messagesContainer || chatBody;
    if (!target) return;
    requestAnimationFrame(() => {
      target.scrollTop = target.scrollHeight;
    });
  };

  const isNearBottom = (element) => {
    if (!element) return true;
    const threshold = 60;
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    return distance <= threshold;
  };

  const renderEmptyMessagesState = (text) => {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = `
      <div class="message-placeholder">
        <p>${text || 'Envie uma mensagem para iniciar a conversa.'}</p>
      </div>
    `;
  };

  const renderMessage = (message, partner) => {
    if (!messagesContainer) return;
    const isDeleted = Boolean(message.is_deleted_for_all);
    const canDeleteForSelf = Boolean(message.can_delete_for_self);
    const canDeleteForAll = Boolean(message.can_delete_for_all);
    const displayText = isDeleted
      ? (message.deleted_label || 'Mensagem apagada.')
      : (message.display_text || message.text || '');

    const wrapper = document.createElement('div');
    wrapper.className = `message ${message.is_self ? 'sent' : 'received'}`;
    wrapper.dataset.messageId = message.id;
    if (isDeleted) {
      wrapper.classList.add('message--deleted');
    }

    if (!message.is_self) {
      const avatar = document.createElement('img');
      avatar.className = 'avatar';
      avatar.alt = partner?.name || 'Contato';
      avatar.src = partner?.avatar_url || defaultAvatar;
      wrapper.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (!isDeleted) {
      const heading = document.createElement('h3');
      heading.textContent = message.is_self ? currentUserName : partner?.name || partner?.handle || 'Contato';
      bubble.appendChild(heading);
    }

    const paragraph = document.createElement('p');
    paragraph.textContent = displayText;
    bubble.appendChild(paragraph);

    wrapper.appendChild(bubble);

    if (message.is_self) {
      const avatar = document.createElement('img');
      avatar.className = 'avatar';
      avatar.alt = currentUserName;
      avatar.src = currentUserAvatar || defaultAvatar;
      wrapper.appendChild(avatar);
    }

    const time = document.createElement('span');
    time.className = 'time';
    time.textContent = formatTime(message.created_at) || '';
    wrapper.appendChild(time);

    if (canDeleteForSelf || canDeleteForAll) {
      const actions = document.createElement('div');
      actions.className = 'message-actions';

      if (canDeleteForSelf) {
        const deleteSelfBtn = document.createElement('button');
        deleteSelfBtn.type = 'button';
        deleteSelfBtn.className = 'message-action-btn';
        deleteSelfBtn.dataset.action = 'self';
        deleteSelfBtn.dataset.messageId = message.id;
        deleteSelfBtn.textContent = 'Apagar p/ mim';
        actions.appendChild(deleteSelfBtn);
      }

      if (canDeleteForAll) {
        const deleteAllBtn = document.createElement('button');
        deleteAllBtn.type = 'button';
        deleteAllBtn.className = 'message-action-btn';
        deleteAllBtn.dataset.action = 'all';
        deleteAllBtn.dataset.messageId = message.id;
        deleteAllBtn.textContent = 'Apagar geral';
        actions.appendChild(deleteAllBtn);
      }

      wrapper.appendChild(actions);
    }

    messagesContainer.appendChild(wrapper);
  };

  const renderMessages = (conversationId, { stickToBottom = true } = {}) => {
    if (!messagesContainer) return;
    const conversation = state.conversations.find((conv) => conv.id === conversationId);
    const partner = conversation?.partner;
    const messages = state.messagesCache[conversationId] || [];

    let previousOffsetFromBottom = 0;
    if (!stickToBottom) {
      previousOffsetFromBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop;
    }

    messagesContainer.innerHTML = '';
    if (!messages.length) {
      renderEmptyMessagesState('Ainda não há mensagens nesta conversa.');
      return;
    }

    messages.forEach((message) => renderMessage(message, partner));
    if (stickToBottom) {
      scrollMessagesToBottom();
    } else if (messagesContainer) {
      const nextTop = messagesContainer.scrollHeight - previousOffsetFromBottom;
      messagesContainer.scrollTop = nextTop > 0 ? nextTop : 0;
    }
  };

  const conversationMatchesTerm = (conversation, term) => {
    const partner = conversation.partner;
    const target = `${partner?.name || ''} ${partner?.handle || ''}`.toLowerCase();
    return target.includes(term.toLowerCase());
  };

  const applyConversationFilter = () => {
    if (!state.lastSearchTerm) {
      state.filteredConversations = null;
      return;
    }
    state.filteredConversations = state.conversations.filter((conversation) =>
      conversationMatchesTerm(conversation, state.lastSearchTerm)
    );
  };

  const renderConversations = () => {
    if (!contactsListEl) return;
    const conversations = state.filteredConversations ?? state.conversations;
    contactsListEl.innerHTML = '';

    if (!conversations.length) {
      const empty = document.createElement('li');
      empty.className = 'contact-card contact-card--empty';
      empty.innerHTML = '<p>Busque um @ e comece uma nova conversa.</p>';
      contactsListEl.appendChild(empty);
      return;
    }

    conversations.forEach((conversation) => {
      const partner = conversation.partner;
      const item = document.createElement('li');
      item.className = 'contact-card';
      item.dataset.conversationId = conversation.id;

      const avatar = document.createElement('div');
      avatar.className = 'contact-avatar';
      if (partner?.avatar_url) {
        avatar.innerHTML = `<img src="${partner.avatar_url}" alt="${partner.name || 'Contato'}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
      } else {
        avatar.textContent = getPartnerInitials(partner?.name || partner?.handle || '?');
      }

      const preview = document.createElement('div');
      preview.className = 'contact-preview';
      preview.innerHTML = `
        <div class="contact-row">
          <strong>${partner?.name || partner?.handle || 'Contato'}</strong>
          <span class="contact-time">${formatTime(conversation.last_message_at) || ''}</span>
        </div>
        <p>${conversation.last_message || 'Sem mensagens ainda'}</p>
      `;

      if (conversation.id === state.activeConversationId) {
        item.classList.add('active');
      }

      item.appendChild(avatar);
      item.appendChild(preview);
      contactsListEl.appendChild(item);
    });
  };

  const highlightConversation = (conversationId) => {
    if (!contactsListEl) return;
    contactsListEl.querySelectorAll('.contact-card').forEach((el) => {
      el.classList.toggle('active', Number(el.dataset.conversationId) === conversationId);
    });
  };

  const upsertConversation = (conversation) => {
    const idx = state.conversations.findIndex((conv) => conv.id === conversation.id);
    if (idx >= 0) {
      state.conversations[idx] = conversation;
    } else {
      state.conversations.unshift(conversation);
    }

    state.conversations.sort((a, b) => {
      const dateA = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
      const dateB = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
      return dateB - dateA;
    });

    renderConversations();
  };

  const ensureMessages = async (conversationId, { force = false } = {}) => {
    if (!force && state.messagesCache[conversationId]) {
      realtimeLog('ensureMessages using cache', conversationId, state.messagesCache[conversationId].length);
      return state.messagesCache[conversationId];
    }

    const url = buildUrl(endpoints.messagesTemplate, conversationId);
    if (!url) {
      throw new Error('Endpoint de mensagens indisponível.');
    }

    const data = await apiFetch(url);
    state.messagesCache[conversationId] = data.messages || [];
    realtimeLog('ensureMessages fetched', conversationId, state.messagesCache[conversationId].length);
    return state.messagesCache[conversationId];
  };

  const selectConversation = async (conversationId) => {
    stopMessagePolling();
    disconnectConversationSocket();
    state.activeConversationId = conversationId;
    highlightConversation(conversationId);
    const conversation = state.conversations.find((conv) => conv.id === conversationId);
    updateConversationHeader(conversation?.partner);
    renderEmptyMessagesState('Carregando mensagens...');

    try {
      await ensureMessages(conversationId);
      renderMessages(conversationId);
      if (isMobile()) {
        setMobileView('chat');
      }
      connectConversationSocket(conversationId);
      startMessagePolling();
    } catch (error) {
      notify(error.message, 'error');
      renderEmptyMessagesState('Não foi possível carregar as mensagens.');
      disconnectConversationSocket();
    }
  };

  async function loadConversations({ silent = false } = {}) {
    if (!endpoints.conversations) return;
    try {
      realtimeLog('loadConversations tick');
      const data = await apiFetch(endpoints.conversations);
      const previousActive = state.activeConversationId;
      state.conversations = data.conversations || [];
      realtimeLog('conversations count', state.conversations.length);
      applyConversationFilter();
      renderConversations();

      if (!state.hasLoadedConversations) {
        state.hasLoadedConversations = true;
        if (state.conversations.length && !previousActive && !isMobile()) {
          selectConversation(state.conversations[0].id);
        }
        startLiveUpdates();
      } else if (previousActive && !state.conversations.some((conv) => conv.id === previousActive)) {
        state.activeConversationId = null;
        renderEmptyMessagesState('Esta conversa não está mais disponível.');
        stopMessagePolling();
        disconnectConversationSocket();
      }

      if (state.activeConversationId) {
        const updated = state.conversations.find((conv) => conv.id === state.activeConversationId);
        if (updated) {
          updateConversationHeader(updated.partner);
        }
      }

      if (!state.conversations.length && isMobile()) {
        setMobileView('list');
      }
    } catch (error) {
      if (!silent) {
        notify(error.message, 'error');
      }
      realtimeLog('loadConversations error', error?.message);
    }
  }

  async function refreshActiveConversationMessages() {
    const conversationId = state.activeConversationId;
    if (!conversationId) return;
    const conversation = state.conversations.find((conv) => conv.id === conversationId);
    if (!conversation) return;

    const wasAtBottom = isNearBottom(messagesContainer);

    try {
      realtimeLog('refreshActiveConversationMessages tick', conversationId);
      await ensureMessages(conversationId, { force: true });
      renderMessages(conversationId, { stickToBottom: wasAtBottom });
      realtimeLog('refreshActiveConversationMessages rendered', conversationId);
    } catch (error) {
      // Falha silenciosa em atualizações em tempo real.
      realtimeLog('refreshActiveConversationMessages error', error?.message);
    }
  }

  const clearSocketReconnect = () => {
    if (state.socketReconnectTimer) {
      clearTimeout(state.socketReconnectTimer);
      state.socketReconnectTimer = null;
    }
  };

  const disconnectConversationSocket = () => {
    state.socketAutoReconnect = false;
    clearSocketReconnect();
    if (state.socket) {
      try {
        state.socket.close();
      } catch (_) {
        /* noop */
      }
    }
    state.socket = null;
    state.socketConversationId = null;
  };

  const scheduleSocketReconnect = (conversationId) => {
    clearSocketReconnect();
    if (!state.socketAutoReconnect) {
      return;
    }
    state.socketReconnectAttempts += 1;
    if (state.socketReconnectAttempts > state.socketMaxRetries) {
      state.socketAutoReconnect = false;
      notify('Conexão em tempo real indisponível. Mantendo atualização a cada 2s.', 'info');
      startMessagePolling();
      return;
    }

    state.socketReconnectTimer = setTimeout(() => {
      if (document.hidden) {
        return;
      }
      if (state.activeConversationId === conversationId) {
        connectConversationSocket(conversationId);
      }
    }, 5000);
  };

  const upsertMessageInCache = (message) => {
    if (!message || !message.id) {
      return;
    }
    const conversationId = message.conversation_id;
    if (!conversationId) {
      return;
    }

    if (!state.messagesCache[conversationId]) {
      state.messagesCache[conversationId] = [];
    }
    const cache = state.messagesCache[conversationId];
    const existingIndex = cache.findIndex((item) => item.id === message.id);
    if (existingIndex >= 0) {
      cache[existingIndex] = message;
    } else {
      cache.push(message);
      cache.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    }

    if (state.activeConversationId === conversationId) {
      const stickToBottom = isNearBottom(messagesContainer);
      renderMessages(conversationId, { stickToBottom });
    }
  };

  const handleRealtimePayload = (payload) => {
    if (!payload) return;
    if (payload.conversation) {
      upsertConversation(payload.conversation);
      if (payload.conversation.id === state.activeConversationId) {
        updateConversationHeader(payload.conversation.partner);
      }
    }
    if (payload.message) {
      upsertMessageInCache(payload.message);
    }
  };

  const handleSocketMessage = (rawData) => {
    if (!rawData) return;
    let payload;
    try {
      payload = JSON.parse(rawData);
    } catch (_) {
      return;
    }

    if (payload.event === 'message') {
      handleRealtimePayload(payload);
    }
  };

  const connectConversationSocket = (conversationId) => {
    if (!conversationId) {
      disconnectConversationSocket();
      return;
    }

    disconnectConversationSocket();
    state.socketAutoReconnect = true;
    state.socketReconnectAttempts = 0;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${protocol}://${window.location.host}/ws/chat/${conversationId}/`;
    let socket;
    try {
      socket = new WebSocket(url);
    } catch (e) {
      realtimeLog('socket construct failed', e);
      state.socketAutoReconnect = false;
      startMessagePolling();
      return;
    }
    state.socket = socket;
    state.socketConversationId = conversationId;

    socket.addEventListener('open', () => {
      clearSocketReconnect();
      state.socketReconnectAttempts = 0;
      realtimeLog('socket connected', conversationId);
    });

    socket.addEventListener('message', (event) => handleSocketMessage(event.data));

    socket.addEventListener('close', (event) => {
      realtimeLog('socket closed', conversationId, event.code, event.reason);
      startMessagePolling();
      if (state.socket === socket) {
        state.socket = null;
        state.socketConversationId = null;
      }
      // If abnormal close (e.g., 1006), stop reconnecting this session
      if (event && event.code === 1006) {
        state.socketAutoReconnect = false;
      }
      if (state.socketAutoReconnect && !document.hidden) {
        startMessagePolling();
        scheduleSocketReconnect(conversationId);
      }
    });

    socket.addEventListener('error', (event) => {
      realtimeLog('socket error', conversationId, event);
      // Disable auto-reconnect on persistent errors to avoid UI flicker
      state.socketAutoReconnect = false;
      try {
        socket.close();
      } catch (_) {
        /* noop */
      }
    });
  };

    const stopMessagePolling = () => {
      if (state.messageInterval) {
        clearInterval(state.messageInterval);
        state.messageInterval = null;
      }
    };

    const startMessagePolling = () => {
      stopMessagePolling();
      if (!state.activeConversationId) {
        return;
      }

      const tick = async () => {
        if (document.hidden || !state.activeConversationId) {
          return;
        }
        realtimeLog('message poll tick', state.activeConversationId);
        await refreshActiveConversationMessages();
      };

      tick();
      state.messageInterval = setInterval(tick, 2000);
    };

  function stopLiveUpdates() {
    if (state.liveInterval) {
      clearInterval(state.liveInterval);
      state.liveInterval = null;
    }
  }

  function startLiveUpdates() {
    if (state.liveInterval) {
      return;
    }
    const tick = async () => {
      if (state.isRefreshing || document.hidden) {
        return;
      }
      realtimeLog('live updates tick');
      state.isRefreshing = true;
      try {
        await loadConversations({ silent: true });
        await refreshActiveConversationMessages();
      } finally {
        state.isRefreshing = false;
      }
    };
    state.liveInterval = setInterval(tick, 3000);
  }

  const handleSendMessage = async () => {
    const text = msgInput.value.trim();
    if (!text) return;
    if (!state.activeConversationId) {
      notify('Selecione ou crie uma conversa antes de enviar mensagens.', 'error');
      return;
    }

    const url = buildUrl(endpoints.sendTemplate, state.activeConversationId);
    if (!url) {
      notify('Endpoint de envio indisponível.', 'error');
      return;
    }

    setSendEnabled(false);

    try {
      const payload = JSON.stringify({ text });
      const data = await apiFetch(url, { method: 'POST', body: payload });
      if (!state.messagesCache[state.activeConversationId]) {
        state.messagesCache[state.activeConversationId] = [];
      }
      state.messagesCache[state.activeConversationId].push(data.message);
      renderMessages(state.activeConversationId);

      const conversation = state.conversations.find((conv) => conv.id === state.activeConversationId);
      if (conversation) {
        conversation.last_message = data.message.display_text || data.message.text;
        conversation.last_message_at = data.message.created_at;
        upsertConversation(conversation);
      }

      msgInput.value = '';
      scrollMessagesToBottom();
    } catch (error) {
      notify(error.message, 'error');
    } finally {
      setSendEnabled(Boolean(msgInput.value.trim()));
    }
  };

  const deleteMessage = async (messageId, scope) => {
    if (!endpoints.deleteTemplate) {
      notify('Endpoint de exclusão indisponível.', 'error');
      return;
    }

    const url = buildDeleteUrl(endpoints.deleteTemplate, messageId);
    if (!url) {
      notify('Endpoint de exclusão indisponível.', 'error');
      return;
    }

    try {
      const payload = JSON.stringify({ scope });
      const data = await apiFetch(url, { method: 'POST', body: payload });
      const conversationId = data.conversation?.id;
      if (conversationId) {
        delete state.messagesCache[conversationId];
        await ensureMessages(conversationId, { force: true });
        if (state.activeConversationId === conversationId) {
          renderMessages(conversationId);
        }
        upsertConversation(data.conversation);
      } else {
        loadConversations();
      }

      notify(scope === 'all' ? 'Mensagem apagada para todos.' : 'Mensagem apagada para você.', 'success');
    } catch (error) {
      notify(error.message, 'error');
    }
  };

  const startConversation = async (handle) => {
    if (!endpoints.start) {
      notify('Endpoint de criação de conversa indisponível.', 'error');
      return;
    }

    const normalized = (handle || '').trim();
    if (!normalized) return;
    try {
      const payload = JSON.stringify({ username: normalized });
      const data = await apiFetch(endpoints.start, { method: 'POST', body: payload });
      const conversation = data.conversation;
      upsertConversation(conversation);
      await selectConversation(conversation.id);
    } catch (error) {
      notify(error.message, 'error');
    }
  };

  const renderSearchResults = (results, term) => {
    if (!searchResultsEl) return;

    if (!term) {
      searchResultsEl.hidden = true;
      searchResultsEl.innerHTML = '';
      return;
    }

    if (!results.length) {
      searchResultsEl.hidden = false;
      searchResultsEl.innerHTML = '<p class="search-empty">Nenhum usuário encontrado.</p>';
      return;
    }

    searchResultsEl.hidden = false;
    searchResultsEl.innerHTML = results.map((user) => {
      const avatar = user.avatar_url
        ? `<img src="${user.avatar_url}" alt="${user.name}" class="search-avatar" />`
        : `<span class="search-avatar">${getPartnerInitials(user.name || user.handle)}</span>`;
      return `
        <div class="search-result-item" tabindex="0" data-handle="${user.handle || ''}">
          ${avatar}
          <div>
            <strong>${user.name || user.handle}</strong>
            <span>${user.handle || ''}</span>
          </div>
        </div>
      `;
    }).join('');
  };

  const performRemoteSearch = async (term) => {
    const normalizedLength = term.startsWith('@') ? term.slice(1).length : term.length;
    if (!endpoints.search || normalizedLength < 1) {
      return;
    }

    try {
      const url = `${endpoints.search}?q=${encodeURIComponent(term)}`;
      const data = await apiFetch(url);
      state.searchResults = data.results || [];
      renderSearchResults(state.searchResults, term);
    } catch (error) {
      notify(error.message, 'error');
    }
  };

  const handleSearchInput = (term) => {
    const trimmed = term.trim();
    state.lastSearchTerm = trimmed;
    applyConversationFilter();
    renderConversations();

    if (!trimmed) {
      renderSearchResults([], '');
    } else if (searchResultsEl) {
      searchResultsEl.hidden = false;
      searchResultsEl.innerHTML = trimmed === '@'
        ? '<p class="search-hint">Digite o usuário após o @.</p>'
        : '<p class="search-loading">Buscando usuários...</p>';
    }

    clearTimeout(state.searchTimeout);
    if (trimmed) {
      state.searchTimeout = setTimeout(() => performRemoteSearch(trimmed), 250);
    }
  };

  const handleSearchEnter = (event) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    const value = event.target.value.trim();
    if (!value) return;
    const handle = value.startsWith('@') ? value : `@${value}`;
    startConversation(handle);
  };

  const bindEvents = () => {
    contactsListEl?.addEventListener('click', (event) => {
      const item = event.target.closest('[data-conversation-id]');
      if (!item) return;
      selectConversation(Number(item.dataset.conversationId));
    });

    searchInput?.addEventListener('input', (event) => handleSearchInput(event.target.value));
    searchInput?.addEventListener('keydown', handleSearchEnter);

    const searchResultHandler = (item) => {
      if (!item) return;
      const handle = item.dataset.handle || '';
      if (handle) {
        searchInput.value = '';
        handleSearchInput('');
        startConversation(handle);
      }
    };

    searchResultsEl?.addEventListener('click', (event) => {
      const item = event.target.closest('.search-result-item');
      searchResultHandler(item);
    });

    searchResultsEl?.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      const item = event.target.closest('.search-result-item');
      if (!item) return;
      event.preventDefault();
      searchResultHandler(item);
    });

    document.addEventListener('click', (event) => {
      if (!searchResultsEl || searchResultsEl.hidden) return;
      const isClickInside = searchResultsEl.contains(event.target) || (searchInput && searchInput.contains(event.target));
      if (!isClickInside) {
        searchResultsEl.hidden = true;
      }
    });

    emojiBtn?.addEventListener('click', () => {
      emojiPicker?.classList.toggle('hidden');
    });

    document.addEventListener('click', (event) => {
      if (!emojiPicker || emojiPicker.classList.contains('hidden')) return;
      if (event.target === emojiPicker || emojiPicker.contains(event.target) || event.target === emojiBtn) {
        return;
      }
      emojiPicker.classList.add('hidden');
    });

    emojiPicker?.addEventListener('emoji-click', (event) => {
      const emoji = event.detail?.unicode;
      if (!emoji) return;
      msgInput.value += emoji;
      setSendEnabled(Boolean(msgInput.value.trim()));
    });

    imgBtn?.addEventListener('click', () => imgInput?.click());
    imgInput?.addEventListener('change', (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        if (!state.activeConversationId) {
          notify('Selecione uma conversa antes de enviar imagens.', 'error');
          return;
        }
        const localMessage = {
          id: Date.now(),
          text: 'Imagem enviada (apenas visualização local).',
          created_at: new Date().toISOString(),
          is_self: true,
        };
        if (!state.messagesCache[state.activeConversationId]) {
          state.messagesCache[state.activeConversationId] = [];
        }
        state.messagesCache[state.activeConversationId].push(localMessage);
        renderMessages(state.activeConversationId);
        notify('Envio de imagens ainda não está disponível no servidor.', 'info');
      };
      reader.readAsDataURL(file);
      imgInput.value = '';
    });

    let recording = false;
    let recordingInterval;
    let elapsedSeconds = 0;

    const stopRecording = () => {
      recording = false;
      clearInterval(recordingInterval);
      audioBtn?.classList.remove('recording');
      recordTimer?.classList.add('hidden');
      if (elapsedSeconds > 0) {
        const localMessage = {
          id: Date.now(),
          text: `Mensagem de áudio (${elapsedSeconds}s) ainda não suportada no servidor.`,
          created_at: new Date().toISOString(),
          is_self: true,
        };
        if (state.activeConversationId) {
          if (!state.messagesCache[state.activeConversationId]) {
            state.messagesCache[state.activeConversationId] = [];
          }
          state.messagesCache[state.activeConversationId].push(localMessage);
          renderMessages(state.activeConversationId);
        }
      }
    };

    audioBtn?.addEventListener('click', () => {
      recording = !recording;
      audioBtn.classList.toggle('recording', recording);
      recordTimer?.classList.toggle('hidden', !recording);
      if (recording) {
        elapsedSeconds = 0;
        recordTimer.textContent = '00:00';
        recordingInterval = setInterval(() => {
          elapsedSeconds += 1;
          const mins = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
          const secs = String(elapsedSeconds % 60).padStart(2, '0');
          recordTimer.textContent = `${mins}:${secs}`;
        }, 1000);
      } else {
        stopRecording();
      }
    });

    messagesContainer?.addEventListener('click', (event) => {
      const actionBtn = event.target.closest('.message-action-btn');
      if (!actionBtn) return;
      const messageId = Number(actionBtn.dataset.messageId);
      const scope = actionBtn.dataset.action;
      if (!messageId || !scope) return;
      const confirmText = scope === 'all'
        ? 'Apagar esta mensagem para todos?'
        : 'Apagar esta mensagem apenas para você?';
      const confirmed = typeof window.confirm === 'function' ? window.confirm(confirmText) : true;
      if (!confirmed) return;
      deleteMessage(messageId, scope);
    });

    msgInput?.addEventListener('input', () => {
      setSendEnabled(Boolean(msgInput.value.trim()));
    });

    msgInput?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
      }
    });

    sendBtn?.addEventListener('click', handleSendMessage);

    backBtn?.addEventListener('click', () => {
      if (isMobile()) {
        setMobileView('list');
      }
    });
  };

  renderEmptyMessagesState('Selecione uma conversa ou busque alguém pelo @.');
  setSendEnabled(false);
  bindEvents();
  handleViewportChange();
  if (typeof mobileQuery.addEventListener === 'function') {
    mobileQuery.addEventListener('change', handleViewportChange);
  } else if (typeof mobileQuery.addListener === 'function') {
    mobileQuery.addListener(handleViewportChange);
  }
  loadConversations();

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopLiveUpdates();
      stopMessagePolling();
      disconnectConversationSocket();
      return;
    }
    loadConversations({ silent: true });
    startLiveUpdates();
    startMessagePolling();
    if (state.activeConversationId) {
      connectConversationSocket(state.activeConversationId);
    }
  });
  window.addEventListener('beforeunload', () => {
    stopLiveUpdates();
    stopMessagePolling();
    disconnectConversationSocket();
  });
});

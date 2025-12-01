document.addEventListener('DOMContentLoaded', () => {
  const contactsListEl = document.getElementById('lista');
  const searchInput = document.getElementById('busca');
  const chatBody = document.getElementById('rolagem');
  const chatContainer = document.querySelector('.chat-wrapper');
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

  const staticConfig = window.CHAT_STATIC || {};
  const defaultAvatar = staticConfig.defaultAvatar || '';
  const currentUserName = staticConfig.currentUserName || 'Você';
  const currentUserAvatar = staticConfig.currentUserAvatar || defaultAvatar;

  const contacts = [
    { id: 1, name: 'Ronaldo', lastMessage: 'Treino às 7h?', time: '20:30', status: 'Online agora' },
    { id: 2, name: 'Amanda', lastMessage: 'Enviei o cronograma', time: '19:10', status: 'Visto há 5 min' },
    { id: 3, name: 'Equipe Coony', lastMessage: 'Convite aprovado ✅', time: '18:45', status: 'Equipe' },
    { id: 4, name: 'Lucas Corre', lastMessage: 'Posso te ligar?', time: 'Ontem', status: 'Disponível' },
    { id: 5, name: 'Comunidade Trail', lastMessage: 'Novo tópico publicado', time: 'Ontem', status: 'Novidade' }
  ];

  function renderContacts(list) {
    if (!contactsListEl) return;
    contactsListEl.innerHTML = '';
    list.forEach((contact) => {
      const li = document.createElement('li');
      li.className = 'contact-card';
      li.dataset.contactId = contact.id;
      li.innerHTML = `
        <div class="contact-avatar" aria-hidden="true">${contact.name.charAt(0)}</div>
        <div class="contact-preview">
          <div class="contact-row">
            <strong>${contact.name}</strong>
            <span class="contact-time">${contact.time}</span>
          </div>
          <p>${contact.lastMessage}</p>
        </div>`;
      contactsListEl.appendChild(li);
    });
  }

  function filterContacts(term) {
    const normalized = term.trim().toLowerCase();
    if (!normalized) {
      renderContacts(contacts);
      return;
    }
    const filtered = contacts.filter((contact) => contact.name.toLowerCase().includes(normalized));
    renderContacts(filtered);
  }

  function updateConversationHeader(contact) {
    chatUserName.textContent = contact ? contact.name : 'Selecione um contato';
    chatUserStatus.textContent = contact ? contact.status : 'Offline';
    chatUserAvatar.src = defaultAvatar;
    chatPartnerFallback.src = defaultAvatar;
  }

  function updateSendState() {
    const hasText = msgInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
    sendBtn.classList.toggle('botaoDesativo', !hasText);
    sendBtn.classList.toggle('botaoEnviarAtivo', hasText);
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      chatBody.scrollTop = chatBody.scrollHeight;
    });
  }

  function createMessageElement({ text, type = 'sent', imageSrc }) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${type}`;

    if (type === 'received') {
      const avatar = document.createElement('img');
      avatar.src = defaultAvatar;
      avatar.alt = 'Contato';
      avatar.className = 'avatar';
      wrapper.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = imageSrc ? 'bubble image-bubble' : 'bubble';

    const heading = document.createElement('h3');
    heading.textContent = type === 'sent' ? currentUserName : chatUserName.textContent;
    bubble.appendChild(heading);

    if (imageSrc) {
      const img = document.createElement('img');
      img.src = imageSrc;
      img.alt = 'Imagem enviada';
      img.className = 'sent-image';
      bubble.appendChild(img);
    }

    if (text) {
      const paragraph = document.createElement('p');
      paragraph.textContent = text;
      bubble.appendChild(paragraph);
    }

    wrapper.appendChild(bubble);

    if (type === 'sent') {
      const avatar = document.createElement('img');
      avatar.src = currentUserAvatar;
      avatar.alt = currentUserName;
      avatar.className = 'avatar';
      wrapper.appendChild(avatar);
    }

    const time = document.createElement('span');
    time.className = 'time';
    const now = new Date();
    time.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    wrapper.appendChild(time);

    chatBody.appendChild(wrapper);
    scrollToBottom();
  }

  function handleSendMessage() {
    const text = msgInput.value.trim();
    if (!text) return;
    createMessageElement({ text, type: 'sent' });
    msgInput.value = '';
    updateSendState();
  }

  let recording = false;
  let recordingInterval;
  let elapsedSeconds = 0;

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  }

  function toggleRecording() {
    recording = !recording;
    audioBtn.classList.toggle('recording', recording);
    recordTimer.classList.toggle('hidden', !recording);
    if (recording) {
      elapsedSeconds = 0;
      recordTimer.textContent = '00:00';
      recordingInterval = setInterval(() => {
        elapsedSeconds += 1;
        recordTimer.textContent = formatTime(elapsedSeconds);
      }, 1000);
    } else {
      clearInterval(recordingInterval);
      recordTimer.classList.add('hidden');
      if (elapsedSeconds > 0) {
        createMessageElement({ text: `Mensagem de áudio (${formatTime(elapsedSeconds)})`, type: 'sent' });
      }
    }
  }

  function handleImageSelection(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      createMessageElement({ text: 'Imagem enviada', type: 'sent', imageSrc: e.target.result });
    };
    reader.readAsDataURL(file);
    imgInput.value = '';
  }

  function toggleEmojiPicker() {
    emojiPicker.classList.toggle('hidden');
  }

  function closeEmojiPicker(event) {
    if (!emojiPicker || emojiPicker.classList.contains('hidden')) return;
    if (event.target === emojiPicker || emojiPicker.contains(event.target) || event.target === emojiBtn) {
      return;
    }
    emojiPicker.classList.add('hidden');
  }

  function wireEvents() {
    if (searchInput) {
      searchInput.addEventListener('input', (e) => filterContacts(e.target.value));
    }

    if (contactsListEl) {
      contactsListEl.addEventListener('click', (event) => {
        const card = event.target.closest('li[data-contact-id]');
        if (!card) return;
        const contactId = Number(card.dataset.contactId);
        const contact = contacts.find((c) => c.id === contactId);
        if (!contact) return;
        contactsListEl.querySelectorAll('.contact-card').forEach((item) => item.classList.remove('active'));
        card.classList.add('active');
        updateConversationHeader(contact);
        if (window.matchMedia('(max-width: 768px)').matches) {
          sidebar?.classList.add('hidden');
        }
      });
    }

    emojiBtn?.addEventListener('click', toggleEmojiPicker);
    document.addEventListener('click', closeEmojiPicker);

    emojiPicker?.addEventListener('emoji-click', (event) => {
      const emoji = event.detail?.unicode;
      if (!emoji) return;
      msgInput.value += emoji;
      updateSendState();
    });

    imgBtn?.addEventListener('click', () => imgInput?.click());
    imgInput?.addEventListener('change', handleImageSelection);
    audioBtn?.addEventListener('click', toggleRecording);

    msgInput?.addEventListener('input', updateSendState);
    msgInput?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
      }
    });

    sendBtn?.addEventListener('click', handleSendMessage);

    backBtn?.addEventListener('click', () => {
      if (window.matchMedia('(max-width: 768px)').matches) {
        sidebar?.classList.toggle('hidden');
      }
    });
  }

  renderContacts(contacts);
  updateConversationHeader(null);
  updateSendState();
  wireEvents();
});

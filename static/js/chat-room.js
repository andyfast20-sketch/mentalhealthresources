(function () {
  const chatLog = document.querySelector('[data-chat-log]');
  const chatForm = document.querySelector('[data-chat-form]');
  const chatInput = document.querySelector('[data-chat-input]');
  const typingBar = document.querySelector('[data-chat-typing]');
  const typingCopy = document.querySelector('[data-chat-typing-copy]');
  const promptButtons = Array.from(document.querySelectorAll('[data-chat-prompt]'));
  const sidebarList = document.querySelector('[data-chat-sidebar]');
  const presenceCounter = document.querySelector('[data-chat-presence]');
  const chatCard = document.querySelector('[data-chat-card]');
  const chatSizeToggle = document.querySelector('[data-chat-size-toggle]');

  // Modal elements
  const chatModal = document.querySelector('[data-chat-modal]');
  const openModalButtons = Array.from(document.querySelectorAll('[data-open-chat-modal]'));
  const closeModalButton = document.querySelector('[data-close-chat-modal]');

  if (!chatLog || !chatForm || !chatInput) return;

  const participants = [
    { name: 'You', role: 'you' },
    { name: 'ModBot', role: 'mod' },
    { name: 'Rowan', role: 'peer' },
    { name: 'Sage', role: 'peer' },
    { name: 'Mia', role: 'peer' },
    { name: 'Alex', role: 'peer' },
    { name: 'Leah', role: 'peer' },
    { name: 'Priya', role: 'peer' },
  ];

  const chatHistory = [];

  function createMessageElement({ sender, role = 'peer', text }) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message chat-message--${role}`;

    const line = document.createElement('div');
    line.className = 'chat-message__line';

    const author = document.createElement('span');
    author.className = 'chat-author';
    author.textContent = `${sender}:`;

    const textContent = document.createElement('span');
    textContent.className = 'chat-message__text';
    textContent.textContent = text;

    line.appendChild(author);
    line.appendChild(textContent);

    wrapper.appendChild(line);

    return wrapper;
  }

  function addMessage(message, trackHistory = true) {
    const element = createMessageElement(message);
    chatLog.appendChild(element);
    chatLog.scrollTop = chatLog.scrollHeight;

    if (trackHistory) {
      chatHistory.push({
        sender: message.sender,
        role: message.role,
        text: message.text,
      });
    }
  }

  function showTyping(bot) {
    if (!typingBar || !typingCopy) return;
    typingCopy.textContent = `${bot} is typing…`;
    typingBar.hidden = false;
  }

  function hideTyping() {
    if (typingBar) typingBar.hidden = true;
  }

  function renderSidebar() {
    if (!sidebarList) return;

    sidebarList.innerHTML = '';

    participants.forEach((person) => {
      const item = document.createElement('li');
      item.className = 'chat-sidebar__user';

      const avatar = document.createElement('div');
      avatar.className = `chat-avatar chat-avatar--${person.role}`;
      avatar.textContent = person.name.charAt(0);

      const name = document.createElement('span');
      name.className = 'chat-sidebar__name';
      name.textContent = person.name;

      item.appendChild(avatar);
      item.appendChild(name);

      sidebarList.appendChild(item);
    });

    if (presenceCounter) {
      presenceCounter.textContent = `${participants.length} online`;
    }
  }

  function showError(message) {
    addMessage({ sender: 'System', role: 'system', text: message }, false);
  }

  async function requestReplies(userMessage, { warmup = false } = {}) {
    showTyping('Someone');

    try {
      const response = await fetch('/api/chat/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: chatHistory,
          warmup,
        }),
      });

      const result = await response.json();

      if (!response.ok || result.error) {
        throw new Error(result.error || 'Something went wrong while chatting.');
      }

      const messages = Array.isArray(result.messages) ? result.messages : [];
      messages.forEach((msg) => addMessage(msg));
    } catch (error) {
      showError(error.message || 'Unable to reach the chat service.');
    } finally {
      hideTyping();
    }
  }

  chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage({ sender: 'You', role: 'you', text });
    chatInput.value = '';
    requestReplies(text);
  });

  promptButtons.forEach((button) => {
    button.addEventListener('click', () => {
      chatInput.value = button.dataset.chatPrompt || '';
      chatInput.focus();
    });
  });

  if (chatSizeToggle && chatCard) {
    chatSizeToggle.addEventListener('click', () => {
      const expanded = chatCard.classList.toggle('is-expanded');
      chatCard.classList.toggle('is-condensed', !expanded);
      chatSizeToggle.textContent = expanded ? '⤡ Condense' : '⤢ Expand';
      chatSizeToggle.setAttribute(
        'aria-label',
        expanded ? 'Condense chat height' : 'Expand chat height'
      );
    });
  }

  // Modal functionality
  function openChatModal() {
    if (chatModal) {
      chatModal.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      // Focus the chat input when modal opens
      setTimeout(() => {
        if (chatInput) chatInput.focus();
      }, 300);
    }
  }

  function closeChatModal() {
    if (chatModal) {
      chatModal.classList.remove('is-open');
      document.body.style.overflow = '';
    }
  }

  // Open modal button handlers
  openModalButtons.forEach((button) => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      openChatModal();
    });
  });

  // Close modal button handler
  if (closeModalButton) {
    closeModalButton.addEventListener('click', closeChatModal);
  }

  // Close modal when clicking backdrop
  if (chatModal) {
    chatModal.addEventListener('click', (e) => {
      if (e.target === chatModal) {
        closeChatModal();
      }
    });
  }

  // Close modal with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatModal && chatModal.classList.contains('is-open')) {
      closeChatModal();
    }
  });

  renderSidebar();
  requestReplies('A new person quietly joined. Welcome them and show a bit of live back-and-forth.', {
    warmup: true,
  });
})();

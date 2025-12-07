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

  if (!chatLog || !chatForm || !chatInput) return;

  const participants = [
    { name: 'You', role: 'you', status: 'Active • Desktop', badge: 'You' },
    { name: 'ModBot', role: 'mod', status: 'On duty • safety monitor', badge: 'Moderator' },
    { name: 'Rowan', role: 'peer', status: 'Replying in resources', badge: 'Peer supporter' },
    { name: 'Sage', role: 'peer', status: 'Typing…', badge: 'Night owl' },
    { name: 'Mia', role: 'peer', status: 'On mobile', badge: 'She/they' },
    { name: 'Alex', role: 'peer', status: 'Away • back in 5', badge: 'They/them' },
    { name: 'Leah', role: 'peer', status: 'Listening quietly', badge: 'EU evening' },
    { name: 'Priya', role: 'peer', status: 'Reviewing grounding list', badge: 'Student counsellor' },
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

      const body = document.createElement('div');
      body.className = 'chat-sidebar__body';

      const nameRow = document.createElement('div');
      nameRow.className = 'chat-sidebar__meta';

      const name = document.createElement('div');
      name.className = 'chat-sidebar__name';
      name.textContent = person.name;

      nameRow.appendChild(name);

      if (person.badge) {
        const badge = document.createElement('span');
        badge.className = 'chat-role-badge';
        badge.textContent = person.badge;
        nameRow.appendChild(badge);
      }

      const status = document.createElement('small');
      status.textContent = person.status || 'Online';

      body.appendChild(nameRow);
      body.appendChild(status);

      item.appendChild(avatar);
      item.appendChild(body);

      sidebarList.appendChild(item);
    });

    if (presenceCounter) {
      presenceCounter.textContent = `${participants.length} online • live handles`;
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

  renderSidebar();
  requestReplies('A new person quietly joined. Welcome them and show a bit of live back-and-forth.', {
    warmup: true,
  });
})();

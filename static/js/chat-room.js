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

  // Get chat config from page (topic, etc.)
  const chatConfig = window.CHAT_CONFIG || {};
  const chatTopic = chatConfig.topic || '';

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
  let isWaitingForReply = false;
  let backgroundChatActive = true;
  let backgroundChatTimer = null;

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

  function showTyping(name) {
    if (!typingBar || !typingCopy || !isWaitingForReply) return;
    typingCopy.textContent = `${name} is typing…`;
    typingBar.hidden = false;
  }

  function hideTyping() {
    if (typingBar) typingBar.hidden = true;
    isWaitingForReply = false;
  }

  function renderSidebar() {
    if (!sidebarList) return;

    sidebarList.innerHTML = '';

    participants.forEach((person) => {
      const item = document.createElement('li');
      item.className = `chat-sidebar__user${person.role === 'you' ? ' chat-sidebar__user--you' : ''}`;

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

  // Blink the user's name in the sidebar when they send a message
  function blinkUserName() {
    if (!sidebarList) return;
    const userItem = sidebarList.querySelector('.chat-sidebar__user--you');
    if (userItem) {
      userItem.classList.add('is-active');
      setTimeout(() => {
        userItem.classList.remove('is-active');
      }, 1500);
    }
  }

  // Natural delay before someone responds (2-6 seconds)
  function getReplyDelay() {
    return 2000 + Math.random() * 4000;
  }

  async function requestReplies(userMessage, { warmup = false } = {}) {
    // Pause background chat while responding to user
    pauseBackgroundChat();
    
    // Wait a natural amount of time before showing typing
    const thinkDelay = 1000 + Math.random() * 2000;
    
    setTimeout(async () => {
      isWaitingForReply = true;
      const peers = participants.filter(p => p.role === 'peer');
      const randomPeer = peers[Math.floor(Math.random() * peers.length)];
      
      // Show typing for realistic duration
      const typingDuration = 1500 + Math.random() * 2500;
      if (typingBar && typingCopy) {
        typingCopy.textContent = `${randomPeer.name} is typing…`;
        typingBar.hidden = false;
      }

      try {
        const response = await fetch('/api/chat/reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            history: chatHistory,
            warmup,
            replyToUser: true,
          }),
        });

        const result = await response.json();

        const messages = Array.isArray(result.messages) ? result.messages : [];
        
        // If API failed or no messages, silently skip
        if (!response.ok || result.error || messages.length === 0) {
          hideTyping();
          console.log('Reply unavailable, skipping');
          resumeBackgroundChat();
          return;
        }
        
        // Show typing then message after delay
        setTimeout(() => {
          hideTyping();
          // Only show ONE message in response to user
          if (messages.length > 0) {
            addMessage(messages[0]);
          }
          // Resume background chat after responding
          resumeBackgroundChat();
        }, typingDuration);
        
      } catch (error) {
        hideTyping();
        // Silently handle - don't show error messages in chat
        console.log('Chat reply error:', error.message);
        resumeBackgroundChat();
      }
    }, thinkDelay);
  }

  // ModBot welcome message
  function showModBotWelcome() {
    let welcomeText = 'Hey! 👋 Welcome in. I\'m ModBot - here if you need anything.';
    if (chatTopic) {
      welcomeText += ` Today\'s topic: "${chatTopic}".`;
    }
    
    addMessage({ sender: 'ModBot', role: 'mod', text: welcomeText }, false);
  }

  // Get random delay between messages (8-45 seconds for realistic pacing)
  function getRandomDelay() {
    return (8000 + Math.random() * 37000); // 8-45 seconds
  }

  // Show typing indicator for background chat
  function showBackgroundTyping(name, duration) {
    if (!typingBar || !typingCopy) return;
    typingCopy.textContent = `${name} is typing…`;
    typingBar.hidden = false;
    
    setTimeout(() => {
      typingBar.hidden = true;
    }, duration);
  }

  // Request a single background message from API
  async function requestSingleBackgroundMessage() {
    if (!backgroundChatActive) return;
    
    const peers = participants.filter(p => p.role === 'peer');
    const randomPeer = peers[Math.floor(Math.random() * peers.length)];
    
    // Show typing for 1-3 seconds before message appears
    const typingDuration = 1000 + Math.random() * 2000;
    showBackgroundTyping(randomPeer.name, typingDuration);

    try {
      const response = await fetch('/api/chat/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Continue the conversation naturally with ONE short message.',
          history: chatHistory.slice(-8),
          warmup: true,
          topic: chatTopic,
          singleMessage: true,
        }),
      });

      const result = await response.json();

      if (!response.ok || result.error || !result.messages || result.messages.length === 0) {
        // Silently skip - don't show anything, just schedule next
        console.log('Background chat skipped');
        scheduleNextBackgroundMessage();
        return;
      }

      const messages = Array.isArray(result.messages) ? result.messages : [];
      
      // Show the message after typing animation
      setTimeout(() => {
        if (messages.length > 0 && backgroundChatActive) {
          // Only add ONE message
          addMessage(messages[0], true);
        }
        scheduleNextBackgroundMessage();
      }, typingDuration);
      
    } catch (error) {
      console.log('Background chat error:', error.message);
      scheduleNextBackgroundMessage();
    }
  }

  // Schedule the next background message
  function scheduleNextBackgroundMessage() {
    if (!backgroundChatActive) return;
    
    const delay = getRandomDelay();
    backgroundChatTimer = setTimeout(() => {
      requestSingleBackgroundMessage();
    }, delay);
  }

  // Start continuous background chat
  function startBackgroundChat() {
    backgroundChatActive = true;
    // Initial delay before first background message (3-8 seconds)
    const initialDelay = 3000 + Math.random() * 5000;
    backgroundChatTimer = setTimeout(() => {
      requestSingleBackgroundMessage();
    }, initialDelay);
  }

  // Stop background chat (e.g., when user is actively chatting)
  function pauseBackgroundChat() {
    if (backgroundChatTimer) {
      clearTimeout(backgroundChatTimer);
      backgroundChatTimer = null;
    }
  }

  // Resume background chat after user interaction
  function resumeBackgroundChat() {
    if (!backgroundChatActive) return;
    // Wait a bit after user message before resuming background chat
    const resumeDelay = 15000 + Math.random() * 20000; // 15-35 seconds
    backgroundChatTimer = setTimeout(() => {
      requestSingleBackgroundMessage();
    }, resumeDelay);
  }

  chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    // Blink user name and add message
    blinkUserName();
    addMessage({ sender: 'You', role: 'you', text });
    chatInput.value = '';
    
    // Request a single natural reply
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

  // Initialize chat
  renderSidebar();
  
  // Show ModBot welcome immediately
  showModBotWelcome();
  
  // Start continuous background chat
  startBackgroundChat();
})();

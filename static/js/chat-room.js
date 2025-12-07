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

  // Get chat config from page (topic, rules, etc.)
  const chatConfig = window.CHAT_CONFIG || {};
  const chatTopic = chatConfig.topic || '';
  const chatRules = chatConfig.rules || '';

  // Warning and ban system
  const WARNING_STORAGE_KEY = 'chat_warnings';
  const BAN_STORAGE_KEY = 'chat_ban_until';
  const MAX_WARNINGS = 2;
  const BAN_DURATION_MS = 10 * 60 * 1000; // 10 minutes

  // Get warning messages based on violation type
  function getViolationMessage(violation) {
    const messages = {
      'contact_info': 'Your message appears to contain contact information (phone numbers, emails, social media). For everyone\'s safety, please don\'t share personal contact details.',
      'meeting_request': 'Your message appears to be requesting to meet up in person. For safety reasons, meeting requests are not allowed in this chat.',
      'sexual_content': 'Your message contains inappropriate sexual content. This is a safe space and such content is not permitted.',
      'innuendo': 'Your message contains inappropriate innuendo. Please keep the conversation respectful and appropriate.',
      'offensive_content': 'Your message contains offensive or harmful content. Please be respectful to all members.',
      'blocked_word': 'Your message contains a word or phrase that isn\'t allowed in this chat.',
      'rule_violation': 'Your message violates our community guidelines. Please review the rules.',
    };
    return messages[violation] || messages['rule_violation'];
  }

  // Get current warning count
  function getWarningCount() {
    try {
      return parseInt(localStorage.getItem(WARNING_STORAGE_KEY) || '0', 10);
    } catch {
      return 0;
    }
  }

  // Increment warning count
  function incrementWarnings() {
    const count = getWarningCount() + 1;
    try {
      localStorage.setItem(WARNING_STORAGE_KEY, count.toString());
    } catch {}
    return count;
  }

  // Reset warnings (after ban expires)
  function resetWarnings() {
    try {
      localStorage.removeItem(WARNING_STORAGE_KEY);
    } catch {}
  }

  // Check if user is currently banned
  function isBanned() {
    try {
      const banUntil = localStorage.getItem(BAN_STORAGE_KEY);
      if (!banUntil) return false;
      const banTime = parseInt(banUntil, 10);
      if (Date.now() < banTime) {
        return true;
      } else {
        // Ban expired, clear it and reset warnings
        localStorage.removeItem(BAN_STORAGE_KEY);
        resetWarnings();
        return false;
      }
    } catch {
      return false;
    }
  }

  // Get remaining ban time in minutes
  function getBanRemainingMinutes() {
    try {
      const banUntil = localStorage.getItem(BAN_STORAGE_KEY);
      if (!banUntil) return 0;
      const remaining = parseInt(banUntil, 10) - Date.now();
      return Math.max(0, Math.ceil(remaining / 60000));
    } catch {
      return 0;
    }
  }

  // Set ban
  function setBan() {
    try {
      const banUntil = Date.now() + BAN_DURATION_MS;
      localStorage.setItem(BAN_STORAGE_KEY, banUntil.toString());
    } catch {}
  }

  // Create and show violation popup modal
  function showViolationPopup(violation, isBanNotice = false, remainingMins = 0) {
    // Remove any existing violation popup
    const existing = document.querySelector('.chat-violation-popup');
    if (existing) existing.remove();

    const warningCount = getWarningCount();
    let title, message, footerText;

    if (isBanNotice) {
      title = '🚫 Temporarily Removed';
      message = 'You have been temporarily removed from the chat due to multiple rule violations. Please take this time to review our community guidelines.';
      footerText = `You can rejoin in ${remainingMins} minute${remainingMins !== 1 ? 's' : ''}.`;
    } else {
      title = '⚠️ Message Not Sent';
      message = getViolationMessage(violation);
      const warningsLeft = MAX_WARNINGS - warningCount;
      if (warningsLeft > 0) {
        footerText = `Warning ${warningCount} of ${MAX_WARNINGS}. ${warningsLeft} more warning${warningsLeft !== 1 ? 's' : ''} will result in a 10-minute timeout.`;
      } else {
        footerText = 'This is your final warning.';
      }
    }

    const popup = document.createElement('div');
    popup.className = 'chat-violation-popup';
    popup.innerHTML = `
      <div class="chat-violation-popup__backdrop"></div>
      <div class="chat-violation-popup__content">
        <h3 class="chat-violation-popup__title">${title}</h3>
        <p class="chat-violation-popup__message">${message}</p>
        <p class="chat-violation-popup__footer">${footerText}</p>
        <button class="chat-violation-popup__close" type="button">I Understand</button>
      </div>
    `;

    document.body.appendChild(popup);

    // Close handlers
    const closeBtn = popup.querySelector('.chat-violation-popup__close');
    const backdrop = popup.querySelector('.chat-violation-popup__backdrop');

    function closePopup() {
      popup.classList.add('is-closing');
      setTimeout(() => popup.remove(), 200);
    }

    closeBtn.addEventListener('click', closePopup);
    backdrop.addEventListener('click', closePopup);

    // Animate in
    requestAnimationFrame(() => {
      popup.classList.add('is-open');
    });
  }

  // Show ban notice on page load if banned
  function checkAndShowBanNotice() {
    if (isBanned()) {
      const mins = getBanRemainingMinutes();
      showViolationPopup(null, true, mins);
      disableChatInput(mins);
      return true;
    }
    return false;
  }

  // Disable chat input during ban
  function disableChatInput(minutes) {
    if (chatInput) {
      chatInput.disabled = true;
      chatInput.placeholder = `Chat disabled for ${minutes} minute${minutes !== 1 ? 's' : ''}...`;
    }
    const submitBtn = chatForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    // Check every minute to update
    const checkInterval = setInterval(() => {
      if (!isBanned()) {
        enableChatInput();
        clearInterval(checkInterval);
      } else {
        const remaining = getBanRemainingMinutes();
        if (chatInput) {
          chatInput.placeholder = `Chat disabled for ${remaining} minute${remaining !== 1 ? 's' : ''}...`;
        }
      }
    }, 60000);
  }

  // Re-enable chat input after ban
  function enableChatInput() {
    if (chatInput) {
      chatInput.disabled = false;
      chatInput.placeholder = 'Type a message...';
    }
    const submitBtn = chatForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;

    // Show welcome back message
    addMessage({ 
      sender: 'ModBot', 
      role: 'mod', 
      text: 'Welcome back! Your timeout has ended. Please remember to follow our community guidelines. 💙' 
    }, false);
  }

  // Dynamic participants list - starts with just You and ModBot
  let participants = [
    { name: 'You', role: 'you' },
    { name: 'ModBot', role: 'mod' },
  ];

  // Store generated peer names
  let peerNames = [];
  let namesInitialized = false;

  const chatHistory = [];
  let isWaitingForReply = false;
  let backgroundChatActive = true;
  let backgroundChatTimer = null;
  let joinLeaveTimer = null;

  // Fetch random names from the API
  async function initializeRandomNames() {
    if (namesInitialized) return;
    
    try {
      const response = await fetch('/api/chat/generate-names', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 8 }),
      });
      const result = await response.json();
      
      if (result.names && result.names.length > 0) {
        peerNames = result.names;
      } else {
        // Fallback names if API fails
        peerNames = generateFallbackNames();
      }
    } catch (error) {
      console.log('Name generation failed, using fallback:', error);
      peerNames = generateFallbackNames();
    }
    
    namesInitialized = true;
    
    // Add initial random number of participants (3-5)
    const initialCount = 3 + Math.floor(Math.random() * 3);
    for (let i = 0; i < initialCount && peerNames.length > 0; i++) {
      const name = peerNames.shift();
      participants.push({ name, role: 'peer' });
    }
    
    renderSidebar();
  }

  // Generate fallback random names locally
  function generateFallbackNames() {
    const prefixes = ['Sky', 'River', 'Ash', 'Quinn', 'Jade', 'Rain', 'Storm', 'Brook', 'Wren', 'Ember', 'Luna', 'Nova', 'Kai', 'Zara', 'Finn', 'Ivy', 'Leo', 'Milo', 'Arlo', 'Eden'];
    const shuffled = prefixes.sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 10);
  }

  // Get a random peer from current participants
  function getRandomPeer() {
    const peers = participants.filter(p => p.role === 'peer');
    if (peers.length === 0) return null;
    return peers[Math.floor(Math.random() * peers.length)];
  }

  // Get all current peer names for API calls
  function getCurrentPeerNames() {
    return participants.filter(p => p.role === 'peer').map(p => p.name);
  }

  // Someone joins the chat
  function personJoins() {
    if (peerNames.length === 0) return;
    
    const name = peerNames.shift();
    participants.push({ name, role: 'peer' });
    renderSidebar();
    
    // Add join message to chat
    addSystemMessage(`${name} joined the chat`);
  }

  // Someone leaves the chat
  function personLeaves() {
    const peers = participants.filter(p => p.role === 'peer');
    if (peers.length <= 2) return; // Keep at least 2 peers
    
    const leaver = peers[Math.floor(Math.random() * peers.length)];
    participants = participants.filter(p => p.name !== leaver.name);
    
    // Add their name back to the pool for possible return
    peerNames.push(leaver.name);
    
    renderSidebar();
    
    // Add leave message
    addSystemMessage(`${leaver.name} left the chat`);
  }

  // Add a system message (join/leave notifications)
  function addSystemMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message chat-message--system';
    wrapper.innerHTML = `<div class="chat-message__system-text">— ${text} —</div>`;
    chatLog.appendChild(wrapper);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  // Schedule random join/leave events
  function scheduleJoinLeaveEvent() {
    // Random interval: 30 seconds to 2 minutes
    const delay = 30000 + Math.random() * 90000;
    
    joinLeaveTimer = setTimeout(() => {
      // 40% chance of join, 30% chance of leave, 30% nothing
      const roll = Math.random();
      const peers = participants.filter(p => p.role === 'peer');
      
      if (roll < 0.4 && peerNames.length > 0 && peers.length < 8) {
        personJoins();
      } else if (roll < 0.7 && peers.length > 2) {
        personLeaves();
      }
      
      scheduleJoinLeaveEvent();
    }, delay);
  }

  // Check message with server before sending
  async function checkMessageAllowed(message) {
    try {
      const response = await fetch('/api/chat/check-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const result = await response.json();
      return result;
    } catch (error) {
      console.log('Message check failed, allowing:', error);
      return { allowed: true };
    }
  }

  // Show a moderation warning to the user
  function showModerationWarning(warning) {
    const warningEl = document.createElement('div');
    warningEl.className = 'chat-message chat-message--warning';
    warningEl.innerHTML = `
      <div class="chat-message__line">
        <span class="chat-author">⚠️ ModBot:</span>
        <span class="chat-message__text">${warning || 'Message not sent. Please keep the conversation safe and supportive.'}</span>
      </div>
    `;
    chatLog.appendChild(warningEl);
    chatLog.scrollTop = chatLog.scrollHeight;
    
    // Remove warning after 8 seconds
    setTimeout(() => {
      if (warningEl.parentNode) {
        warningEl.remove();
      }
    }, 8000);
  }

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
      const randomPeer = getRandomPeer();
      if (!randomPeer) {
        resumeBackgroundChat();
        return;
      }
      
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
            peerNames: getCurrentPeerNames(),
            uniqueSession: Date.now(), // Force unique responses
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
            // Use one of our actual peer names
            const msg = messages[0];
            msg.sender = randomPeer.name;
            addMessage(msg);
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
    
    const randomPeer = getRandomPeer();
    if (!randomPeer) {
      scheduleNextBackgroundMessage();
      return;
    }
    
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
          peerNames: getCurrentPeerNames(),
          uniqueSession: Date.now(), // Force unique responses
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
          // Use our actual peer name
          const msg = messages[0];
          msg.sender = randomPeer.name;
          addMessage(msg, true);
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

  chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    // Check if user is banned
    if (isBanned()) {
      const mins = getBanRemainingMinutes();
      showViolationPopup(null, true, mins);
      return;
    }
    
    const text = chatInput.value.trim();
    if (!text) return;

    // Check if message is allowed before sending
    const check = await checkMessageAllowed(text);
    
    if (!check.allowed) {
      // Message was blocked - increment warning
      const warningCount = incrementWarnings();
      
      if (warningCount > MAX_WARNINGS) {
        // User has exceeded warnings, apply ban
        setBan();
        showViolationPopup(check.violation, true, 10);
        disableChatInput(10);
      } else {
        // Show warning popup
        showViolationPopup(check.violation);
      }
      
      // Clear the input but don't send the message
      chatInput.value = '';
      return;
    }

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
  
  // Check if user is banned before starting
  const wasBanned = checkAndShowBanNotice();
  
  // Initialize random names, then start chat
  initializeRandomNames().then(() => {
    // Show ModBot welcome immediately
    showModBotWelcome();
    
    // Start continuous background chat
    startBackgroundChat();
    
    // Start join/leave events
    scheduleJoinLeaveEvent();
  });
})();

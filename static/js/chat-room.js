(function () {
  const chatLog = document.querySelector('[data-chat-log]');
  const chatForm = document.querySelector('[data-chat-form]');
  const chatInput = document.querySelector('[data-chat-input]');
  const typingBar = document.querySelector('[data-chat-typing]');
  const typingCopy = document.querySelector('[data-chat-typing-copy]');
  const promptButtons = Array.from(document.querySelectorAll('[data-chat-prompt]'));
  const sidebarList = document.querySelector('[data-chat-sidebar]');
  const presenceCounter = document.querySelector('[data-chat-presence]');

  if (!chatLog || !chatForm || !chatInput) return;

  const participants = [
    { name: 'ddf', role: 'you', status: 'Active • Desktop', badge: 'You' },
    { name: 'ModBot', role: 'mod', status: 'On duty • safety monitor', badge: 'Moderator' },
    { name: 'Rowan', role: 'peer', status: 'Replying in resources', badge: 'Peer supporter' },
    { name: 'Sage', role: 'peer', status: 'Typing…', badge: 'Night owl' },
    { name: 'Mia', role: 'peer', status: 'On mobile', badge: 'She/they' },
    { name: 'Alex', role: 'peer', status: 'Away • back in 5', badge: 'They/them' },
    { name: 'Leah', role: 'peer', status: 'Listening quietly', badge: 'EU evening' },
    { name: 'Priya', role: 'peer', status: 'Reviewing grounding list', badge: 'Student counsellor' },
  ];

  const peers = participants.filter((person) => person.role === 'peer').map((person) => person.name);
  const supportReplies = [
    "You're not alone in this, even if it feels that way tonight.",
    "Breathing slow can help—shoulders down, jaw unclench, gentle breaths in and out.",
    "That sounds really heavy. Thanks for trusting us with it.",
    "Proud of you for naming this. It takes courage to say it out loud.",
    "Maybe a tiny step? Water, stretch, or a quick walk if you can.",
    "It's okay to log off and rest if you need to. We'll be here.",
    "Journaling a few lines can park the thoughts somewhere safe for the night.",
    "Weekends can be weirdly loud for the mind—totally valid to feel wobbly.",
    "Therapy talk is welcome, but this space is peer-to-peer and gentle.",
    "Small joys count: warm tea, a cozy show, a favourite playlist on low.",
  ];

  const gratitudeReplies = [
    "Glad we could sit with you for a bit 💛",
    "No worries—take what helps and leave the rest.",
    "Happy to hold space. Keep leaning on what feels steady tonight.",
  ];

  const copingReplies = [
    "Grounding ideas: five things you see, four you can touch, three you can hear.",
    "Box breathing can steady the nervous system—4 in, 4 hold, 4 out, 4 hold.",
    "Name one thing that feels safe right now. Let your body notice it.",
  ];

  let lastBotLine = '';

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

  function addMessage(message) {
    const element = createMessageElement(message);
    chatLog.appendChild(element);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function showTyping(bot) {
    if (!typingBar || !typingCopy) return;
    typingCopy.textContent = `${bot} is typing…`;
    typingBar.hidden = false;
  }

  function hideTyping() {
    if (typingBar) typingBar.hidden = true;
  }

  function randomFrom(list) {
    return list[Math.floor(Math.random() * list.length)];
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

  function craftReply(message) {
    const text = message.toLowerCase();
    const suggestions = [...supportReplies];

    if (text.includes('thank')) {
      suggestions.push(...gratitudeReplies);
    }

    if (text.includes('ground') || text.includes('anxious') || text.includes('panic')) {
      suggestions.push(...copingReplies);
    }

    let pick = randomFrom(suggestions);
    if (pick === lastBotLine) {
      pick = randomFrom(suggestions.filter((reply) => reply !== lastBotLine));
    }

    lastBotLine = pick;
    return pick;
  }

  function queueBotReply(userMessage) {
    const botName = randomFrom(peers);
    showTyping(botName);

    setTimeout(() => {
      const reply = craftReply(userMessage);
      hideTyping();
      addMessage({ sender: botName, role: 'peer', text: reply, timestamp: new Date() });
    }, 900 + Math.random() * 900);
  }

  function seedRoom() {
    const introMessages = [
      {
        sender: 'System',
        role: 'system',
        text: '* Welcome to the chat, ddf',
      },
      {
        sender: 'ModBot',
        role: 'mod',
        text: 'Friendly reminder: be kind, skip contact details, and use Crisis info for emergencies.',
      },
      {
        sender: 'Rowan',
        role: 'peer',
        text: 'Welcome in! Grab a seat—no rush to talk if you just want to listen.',
      },
      {
        sender: 'Leah',
        role: 'peer',
        text: 'I just made chamomile tea if anyone wants to settle in together.',
      },
      {
        sender: 'Priya',
        role: 'peer',
        text: 'Taking a 3-minute breathing break—join me if you want a soft start.',
      },
    ];

    introMessages.forEach((message) => addMessage(message));
  }

  chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage({ sender: 'You', role: 'you', text });
    chatInput.value = '';
    queueBotReply(text);
  });

  promptButtons.forEach((button) => {
    button.addEventListener('click', () => {
      chatInput.value = button.dataset.chatPrompt || '';
      chatInput.focus();
    });
  });

  renderSidebar();
  seedRoom();
})();

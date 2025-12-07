(function () {
  const chatLog = document.querySelector('[data-chat-log]');
  const chatForm = document.querySelector('[data-chat-form]');
  const chatInput = document.querySelector('[data-chat-input]');
  const typingBar = document.querySelector('[data-chat-typing]');
  const typingCopy = document.querySelector('[data-chat-typing-copy]');
  const promptButtons = Array.from(document.querySelectorAll('[data-chat-prompt]'));

  if (!chatLog || !chatForm || !chatInput) return;

  const peers = ['Rowan', 'Sage', 'Mia', 'Alex'];
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

  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function createMessageElement({ sender, role = 'peer', text, timestamp = new Date() }) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message chat-message--${role}`;

    const header = document.createElement('div');
    header.className = 'chat-message__meta';
    header.innerHTML = `<span class="chat-author">${sender}</span><span class="chat-time">${formatTime(timestamp)}</span>`;

    const body = document.createElement('p');
    body.className = 'chat-message__text';
    body.textContent = text;

    wrapper.appendChild(header);
    wrapper.appendChild(body);

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
        sender: 'Sage',
        role: 'peer',
        text: 'Sharing how your day went is always okay here. How are you holding up?',
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

  seedRoom();
})();

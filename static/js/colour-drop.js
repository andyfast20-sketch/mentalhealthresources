// Anxiety Colour Drop
const colourPool = document.querySelector('[data-colour-pool]');
const poolWater = colourPool?.querySelector('.pool-water');
const dropStatus = document.querySelector('[data-drop-status]');
const resetPoolBtn = document.querySelector('[data-reset-pool]');
const emotionDrops = Array.from(document.querySelectorAll('[data-emotion-drop]'));

const releaseAffirmations = [
  'Let this ripple carry the edge away.',
  'Notice the colour soften as you do.',
  'You can release without rushing.',
  'Small drops add up to lighter shoulders.',
  'Exhale and watch the feeling dissolve.',
  'Picture the colour washing into calm water.',
  'Your breath is the current—ride it out.',
  'Every release is proof you can shift the feeling.',
];

const breathCues = ['Inhale for four, exhale for six.', 'Add a shoulder roll as you drop.', 'Let your jaw loosen on the out-breath.'];
let breathCueIndex = 0;

function nextBreathCue() {
  const cue = breathCues[breathCueIndex];
  breathCueIndex = (breathCueIndex + 1) % breathCues.length;
  return cue;
}

function updateDropStatus(message) {
  if (dropStatus) {
    dropStatus.textContent = message;
  }
}

function clearPoolDrops() {
  const ripples = poolWater?.querySelectorAll('.drop');
  ripples?.forEach((drop) => drop.remove());
  updateDropStatus('Pool reset. Choose another emotion to release.');
}

function createDrop(payload) {
  if (!poolWater) return;
  const drop = document.createElement('div');
  drop.className = 'drop';
  drop.style.setProperty('--drop-colour', payload.colour || '#8ef3c5');
  drop.innerHTML = `
    <span class="drop-label">${payload.emotion || 'Release'}</span>
    <span class="drop-cue">${nextBreathCue()}</span>
  `;
  poolWater.appendChild(drop);
  updateDropStatus(releaseAffirmations[Math.floor(Math.random() * releaseAffirmations.length)]);
}

function handleDrop(event, payload) {
  if (!payload || !poolWater) return;
  const bounds = poolWater.getBoundingClientRect();
  const xPercent = ((event.clientX - bounds.left) / bounds.width) * 100;
  const yPercent = ((event.clientY - bounds.top) / bounds.height) * 100;
  createDrop(payload);
  const drop = poolWater.lastElementChild;
  if (drop) {
    drop.style.left = `${Math.min(Math.max(xPercent, 5), 95)}%`;
    drop.style.top = `${Math.min(Math.max(yPercent, 10), 90)}%`;
  }
}

emotionDrops.forEach((drop) => {
  drop.addEventListener('dragstart', (event) => {
    event.dataTransfer?.setData(
      'text/plain',
      JSON.stringify({
        emotion: drop.dataset.emotion,
        colour: drop.dataset.colour,
      }),
    );
  });

  drop.addEventListener('click', () => {
    const bounds = poolWater?.getBoundingClientRect();
    handleDrop(
      bounds
        ? { clientX: bounds.left + bounds.width / 2, clientY: bounds.top + bounds.height / 2 }
        : { clientX: 0, clientY: 0 },
      { emotion: drop.dataset.emotion, colour: drop.dataset.colour },
    );
  });
});

colourPool?.addEventListener('dragover', (event) => {
  event.preventDefault();
  colourPool.classList.add('is-ready');
});

colourPool?.addEventListener('dragleave', () => {
  colourPool.classList.remove('is-ready');
});

colourPool?.addEventListener('drop', (event) => {
  event.preventDefault();
  colourPool.classList.remove('is-ready');
  let payload = null;
  try {
    payload = JSON.parse(event.dataTransfer?.getData('text/plain') || '{}');
  } catch (error) {
    payload = null;
  }
  handleDrop(event, payload);
});

resetPoolBtn?.addEventListener('click', () => {
  clearPoolDrops();
});

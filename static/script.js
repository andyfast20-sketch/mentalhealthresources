const tags = Array.from(document.querySelectorAll('.tag'));
const cards = Array.from(document.querySelectorAll('.resource-card'));
const resetBtn = document.getElementById('filter-reset');
const sliderTrack = document.querySelector('[data-charity-track]');
const sliderProgress = document.querySelector('[data-slide-progress]');
const sliderPrev = document.querySelector('[data-slide-prev]');
const sliderNext = document.querySelector('[data-slide-next]');
const sliderWindow = document.querySelector('.slider-window');
const showCharitiesBtn = document.querySelector('[data-show-charities]');
const charityModal = document.querySelector('[data-charity-modal]');
const modalClose = document.querySelector('[data-modal-close]');
let slideIndex = 0;
let slideWidth = 0;

function applyFilter(tag) {
  cards.forEach((card) => {
    const hasTag = card.dataset.tags.split(' ').includes(tag);
    card.classList.toggle('hidden', !hasTag);
  });
}

function resetFilters() {
  cards.forEach((card) => card.classList.remove('hidden'));
  tags.forEach((tag) => tag.classList.remove('active'));
}

tags.forEach((tagBtn) => {
  tagBtn.addEventListener('click', () => {
    const isActive = tagBtn.classList.contains('active');
    resetFilters();
    if (!isActive) {
      tagBtn.classList.add('active');
      applyFilter(tagBtn.dataset.tag);
    }
  });
});

resetBtn?.addEventListener('click', resetFilters);

function setSlide(index) {
  if (!sliderTrack) return;
  const slides = Array.from(sliderTrack.children);
  if (!slides.length) return;
  slideIndex = (index + slides.length) % slides.length;
  slideWidth = sliderWindow?.getBoundingClientRect().width || slides[0].getBoundingClientRect().width;
  sliderTrack.style.transform = `translateX(-${slideIndex * slideWidth}px)`;
  const progressValue = ((slideIndex + 1) / slides.length) * 100;
  if (sliderProgress) sliderProgress.style.width = `${progressValue}%`;
  slides.forEach((slide, idx) => {
    slide.classList.toggle('is-active', idx === slideIndex);
  });
}

function initSlider() {
  if (!sliderTrack) return;
  setSlide(0);
  sliderPrev?.addEventListener('click', () => setSlide(slideIndex - 1));
  sliderNext?.addEventListener('click', () => setSlide(slideIndex + 1));
  window.addEventListener('resize', () => setSlide(slideIndex));

  let startX = 0;
  sliderTrack.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
  });
  sliderTrack.addEventListener('touchend', (e) => {
    const delta = e.changedTouches[0].clientX - startX;
    if (Math.abs(delta) > 40) {
      setSlide(slideIndex + (delta < 0 ? 1 : -1));
    }
  });
}

initSlider();

function openModal() {
  if (!charityModal) return;
  charityModal.classList.add('is-open');
  document.body.classList.add('modal-open');
}

function closeModal() {
  if (!charityModal) return;
  charityModal.classList.remove('is-open');
  document.body.classList.remove('modal-open');
}

showCharitiesBtn?.addEventListener('click', openModal);
modalClose?.addEventListener('click', closeModal);
charityModal?.addEventListener('click', (event) => {
  if (event.target === charityModal) {
    closeModal();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && charityModal?.classList.contains('is-open')) {
    closeModal();
  }
});

// Calming flow interactions
const inhaleInput = document.querySelector('[data-inhale-input]');
const holdInput = document.querySelector('[data-hold-input]');
const exhaleInput = document.querySelector('[data-exhale-input]');
const sessionInput = document.querySelector('[data-session-input]');
const sessionRemaining = document.querySelector('[data-session-remaining]');
const waveRange = document.querySelector('[data-wave-range]');
const waveValue = document.querySelector('[data-wave-value]');
const calmStart = document.querySelector('[data-calm-start]');
const calmReset = document.querySelector('[data-calm-reset]');
const phaseLabel = document.querySelector('[data-phase-label]');
const pulseRing = document.querySelector('[data-pulse-ring]');
const phaseTimeline = document.querySelector('[data-phase-timeline]');
const affirmation = document.querySelector('[data-affirmation]');

let calmTimer;
let sessionTimer;
let sessionEndTime = null;
let phaseIndex = 0;
let running = false;

const phaseConfig = [
  { label: 'Inhale', emoji: '🌅' },
  { label: 'Hold', emoji: '✨' },
  { label: 'Exhale', emoji: '🌊' },
];

const affirmations = ['You deserve this pause.', 'Every breath is progress.', 'Settle into the softness of this moment.', 'Notice how capable your body is.', 'Quiet moments count as care.'];

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function updateRangeDisplays() {
  if (waveValue && waveRange) {
    const rangeVal = Number(waveRange.value);
    const label = rangeVal < 0.95 ? 'Feather-light' : rangeVal > 1.15 ? 'Deep waves' : 'Balanced';
    waveValue.textContent = label;
  }
}

function phaseDurations() {
  const inhale = clamp(Number(inhaleInput?.value || 4), 1, 20);
  const hold = clamp(Number(holdInput?.value || 2), 0, 20);
  const exhale = clamp(Number(exhaleInput?.value || 5), 1, 20);
  return [inhale, hold, exhale];
}

function setPhase(newIndex) {
  if (!phaseTimeline || !phaseLabel || !pulseRing) return;
  const durations = phaseDurations();
  phaseIndex = (newIndex + phaseConfig.length) % phaseConfig.length;
  const { label, emoji } = phaseConfig[phaseIndex];

  phaseTimeline.querySelectorAll('.chip').forEach((chip, idx) => {
    chip.classList.toggle('active', idx === phaseIndex);
  });

  const scale = waveRange ? Number(waveRange.value) : 1;
  pulseRing.style.setProperty('--pulse-scale', scale);
  pulseRing.style.setProperty('--phase-duration', `${durations[phaseIndex]}s`);
  pulseRing.classList.add('pulsing');
  void pulseRing.offsetWidth; // restart animation
  pulseRing.classList.remove('pulsing');
  requestAnimationFrame(() => pulseRing.classList.add('pulsing'));

  phaseLabel.textContent = `${emoji} ${label}`;

  calmTimer = setTimeout(() => {
    setPhase(phaseIndex + 1);
  }, durations[phaseIndex] * 1000);
}

function startCalm() {
  if (running) {
    stopCalm();
    return;
  }
  running = true;
  const minutes = clamp(Number(sessionInput?.value || 5), 1, 30);
  sessionEndTime = Date.now() + minutes * 60 * 1000;
  startSessionTimer();
  calmStart.textContent = 'Pause flow';
  if (affirmation) {
    affirmation.textContent = affirmations[Math.floor(Math.random() * affirmations.length)];
  }
  setPhase(phaseIndex);
}

function stopCalm(reset = false) {
  running = false;
  calmStart.textContent = 'Start flow';
  clearTimeout(calmTimer);
  clearInterval(sessionTimer);
  if (reset && phaseLabel && pulseRing && phaseTimeline) {
    phaseLabel.textContent = 'Ready when you are';
    pulseRing.classList.remove('pulsing');
    phaseTimeline.querySelectorAll('.chip').forEach((chip) => chip.classList.remove('active'));
    phaseIndex = 0;
  }
}

waveRange?.addEventListener('input', updateRangeDisplays);
calmStart?.addEventListener('click', startCalm);
calmReset?.addEventListener('click', () => stopCalm(true));
sessionInput?.addEventListener('input', () => {
  if (!sessionRemaining) return;
  const minutes = clamp(Number(sessionInput.value || 0), 1, 30);
  sessionRemaining.textContent = `${minutes.toString().padStart(2, '0')}:00 remaining`;
});

updateRangeDisplays();

function startSessionTimer() {
  if (!sessionRemaining) return;
  updateSessionRemaining();
  clearInterval(sessionTimer);
  sessionTimer = setInterval(() => {
    updateSessionRemaining();
    if (!sessionEndTime || Date.now() >= sessionEndTime) {
      sessionRemaining.textContent = 'Session complete';
      stopCalm(true);
    }
  }, 250);
}

function updateSessionRemaining() {
  if (!sessionRemaining || !sessionEndTime) return;
  const remainingMs = Math.max(sessionEndTime - Date.now(), 0);
  const totalSeconds = Math.round(remainingMs / 1000);
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  sessionRemaining.textContent = `${minutes}:${seconds} remaining`;
}

// Smooth scroll for in-page anchors
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', function (e) {
    if (this.getAttribute('href') === '#') return;
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    target?.scrollIntoView({ behavior: 'smooth' });
  });
});

// micro interaction: show subtle pulse on cards
cards.forEach((card) => {
  card.addEventListener('mouseenter', () => card.classList.add('pulse'));
  card.addEventListener('mouseleave', () => card.classList.remove('pulse'));
});

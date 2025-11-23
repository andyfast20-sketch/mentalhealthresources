const tags = Array.from(document.querySelectorAll('.tag'));
const cards = Array.from(document.querySelectorAll('.resource-card'));
const resetBtn = document.getElementById('filter-reset');
const sliderTrack = document.querySelector('[data-charity-track]');
const sliderProgress = document.querySelector('[data-slide-progress]');
const sliderPrev = document.querySelector('[data-slide-prev]');
const sliderNext = document.querySelector('[data-slide-next]');
const sliderWindow = document.querySelector('.slider-window');
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

// Calming flow interactions
const breathRange = document.querySelector('[data-breath-range]');
const waveRange = document.querySelector('[data-wave-range]');
const breathValue = document.querySelector('[data-breath-value]');
const waveValue = document.querySelector('[data-wave-value]');
const calmStart = document.querySelector('[data-calm-start]');
const calmReset = document.querySelector('[data-calm-reset]');
const phaseLabel = document.querySelector('[data-phase-label]');
const pulseRing = document.querySelector('[data-pulse-ring]');
const phaseTimeline = document.querySelector('[data-phase-timeline]');
const affirmation = document.querySelector('[data-affirmation]');

let calmTimer;
let phaseIndex = 0;
let running = false;

const phaseConfig = [
  { label: 'Inhale', emoji: '🌅' },
  { label: 'Hold', emoji: '✨' },
  { label: 'Exhale', emoji: '🌊' },
  { label: 'Soften', emoji: '🍃' },
];

const affirmations = [
  'You deserve this pause.',
  'Every breath is progress.',
  'Settle into the softness of this moment.',
  'Notice how capable your body is.',
  'Quiet moments count as care.',
];

function updateRangeDisplays() {
  if (breathValue && breathRange) {
    breathValue.textContent = `${breathRange.value}s inhale`;
  }
  if (waveValue && waveRange) {
    const rangeVal = Number(waveRange.value);
    const label = rangeVal < 0.95 ? 'Feather-light' : rangeVal > 1.15 ? 'Deep waves' : 'Balanced';
    waveValue.textContent = label;
  }
}

function phaseDurations() {
  const base = Number(breathRange?.value || 5);
  return [base, Math.max(2, base - 1), base + 1, 2.5];
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
  if (reset && phaseLabel && pulseRing && phaseTimeline) {
    phaseLabel.textContent = 'Ready when you are';
    pulseRing.classList.remove('pulsing');
    phaseTimeline.querySelectorAll('.chip').forEach((chip) => chip.classList.remove('active'));
    phaseIndex = 0;
  }
}

breathRange?.addEventListener('input', updateRangeDisplays);
waveRange?.addEventListener('input', updateRangeDisplays);
calmStart?.addEventListener('click', startCalm);
calmReset?.addEventListener('click', () => stopCalm(true));

updateRangeDisplays();

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

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
const bookTrack = document.querySelector('[data-book-track]');
const bookPrev = document.querySelector('[data-book-prev]');
const bookNext = document.querySelector('[data-book-next]');
const bookProgress = document.querySelector('[data-book-progress]');
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

function updateBookProgress() {
  if (!bookTrack || !bookProgress) return;
  const maxScroll = bookTrack.scrollWidth - bookTrack.clientWidth;
  if (maxScroll <= 0) {
    bookProgress.style.width = '100%';
    return;
  }
  const visibleRatio = bookTrack.clientWidth / bookTrack.scrollWidth;
  const scrollRatio = bookTrack.scrollLeft / maxScroll;
  const widthPercent = Math.min(100, (visibleRatio + scrollRatio) * 100);
  bookProgress.style.width = `${widthPercent}%`;
}

function scrollBooks(direction = 1) {
  if (!bookTrack) return;
  const card = bookTrack.querySelector('.book-card');
  const gap = Number.parseFloat(getComputedStyle(bookTrack).columnGap || getComputedStyle(bookTrack).gap || 14);
  const cardWidth = card ? card.getBoundingClientRect().width : 280;
  const scrollAmount = (cardWidth + gap) * direction;
  bookTrack.scrollBy({ left: scrollAmount, behavior: 'smooth' });
}

bookPrev?.addEventListener('click', () => scrollBooks(-1));
bookNext?.addEventListener('click', () => scrollBooks(1));
bookTrack?.addEventListener('scroll', updateBookProgress, { passive: true });
window.addEventListener('resize', updateBookProgress);
updateBookProgress();

function initReadMore() {
  const descriptions = Array.from(document.querySelectorAll('[data-collapsible]'));

  descriptions.forEach((description) => {
    const toggle = description.nextElementSibling?.matches('[data-read-more]')
      ? description.nextElementSibling
      : null;

    if (!toggle) return;

    const needsToggle = description.scrollHeight - description.clientHeight > 6 || description.textContent.length > 140;

    if (!needsToggle) {
      toggle.style.display = 'none';
      description.classList.add('is-expanded');
      return;
    }

    const setExpandedState = (expanded) => {
      description.classList.toggle('is-expanded', expanded);
      toggle.setAttribute('aria-expanded', expanded);
      toggle.textContent = expanded ? 'Show less' : 'Read more';
    };

    setExpandedState(false);

    toggle.addEventListener('click', () => {
      const expanded = !description.classList.contains('is-expanded');
      setExpandedState(expanded);

      if (!expanded) {
        description.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReadMore);
} else {
  initReadMore();
}

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
const cyclePreview = document.querySelector('[data-cycle-preview]');
const pmrStart = document.querySelector('[data-pmr-start]');
const pmrReset = document.querySelector('[data-pmr-reset]');
const pmrStatus = document.querySelector('[data-pmr-status]');
const pmrCountdown = document.querySelector('[data-pmr-countdown]');
const pmrSteps = Array.from(document.querySelectorAll('.pmr-steps [data-step]'));
const pmrMuscles = Array.from(document.querySelectorAll('[data-muscle]'));

let calmTimer;
let sessionTimer;
let sessionEndTime = null;
let phaseIndex = 0;
let running = false;
let lastTargetScale = 1;
let pmrTimer;
let pmrTicker;
let pmrIndex = -1;
let pmrEndTime;
let pmrRunning = false;

const scaleTargets = {
  expand: 1.08,
  contract: 0.7,
};

const phaseConfig = [
  { key: 'inhale', label: 'Inhale', emoji: '🌅', duration: (durations) => durations[0], target: 'contract' },
  { key: 'hold-full', label: 'Hold full', emoji: '✨', duration: (durations) => durations[1], hold: true },
  { key: 'exhale', label: 'Exhale', emoji: '🌊', duration: (durations) => durations[2], target: 'expand' },
  { key: 'hold-open', label: 'Hold open', emoji: '✨', duration: (durations) => durations[1], hold: true },
];

const affirmations = ['You deserve this pause.', 'Every breath is progress.', 'Settle into the softness of this moment.', 'Notice how capable your body is.', 'Quiet moments count as care.'];

const pmrSequence = [
  { key: 'feet', label: 'Feet & toes', cue: 'Curl your toes for five seconds, then let them glow and soften.', duration: 6 },
  { key: 'calves', label: 'Calves', cue: 'Press your calves gently into the floor, breathe out, and release.', duration: 6 },
  { key: 'thighs', label: 'Thighs', cue: 'Engage your thighs together, notice the strength, then melt.', duration: 6 },
  { key: 'hips', label: 'Hips & glutes', cue: 'Squeeze through the hips and glutes, then imagine them floating.', duration: 6 },
  { key: 'core', label: 'Belly & lower back', cue: 'Draw your belly in as if hugging your spine, exhale and soften.', duration: 6 },
  { key: 'chest', label: 'Chest & upper back', cue: 'Lift your heart with a sip of air, breathe out and let it settle.', duration: 6 },
  { key: 'hands', label: 'Hands', cue: 'Make soft fists for five counts, then spread your fingers wide.', duration: 6 },
  { key: 'forearms', label: 'Forearms', cue: 'Tense your forearms as if holding a mug, then drop the effort.', duration: 6 },
  { key: 'upper-arms', label: 'Upper arms', cue: 'Gently hug your arms toward your ribs, then loosen completely.', duration: 6 },
  { key: 'shoulders', label: 'Shoulders', cue: 'Lift shoulders toward your ears, slide them down and breathe.', duration: 6 },
  { key: 'neck', label: 'Neck', cue: 'Press your head lightly back, feel the length, then release.', duration: 6 },
  { key: 'face', label: 'Jaw & face', cue: 'Scrunch your brow and jaw, then let your face go serene and soft.', duration: 6 },
];

const pmrTotalDuration = pmrSequence.reduce((sum, step) => sum + step.duration, 0);
const pmrStartLabel = 'Start 72-second flow';

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
  clearTimeout(calmTimer);
  const durations = phaseDurations();
  phaseIndex = (newIndex + phaseConfig.length) % phaseConfig.length;
  const currentPhase = phaseConfig[phaseIndex];
  const durationSeconds = currentPhase.duration(durations);

  if (durationSeconds <= 0) {
    setPhase(phaseIndex + 1);
    return;
  }

  phaseTimeline.querySelectorAll('.chip').forEach((chip, idx) => {
    chip.classList.toggle('active', idx === phaseIndex);
  });

  const intensity = waveRange ? Number(waveRange.value) : 1;
  const targetScale = currentPhase.target ? scaleTargets[currentPhase.target] * intensity : lastTargetScale;
  const transitionValue = currentPhase.hold ? 'none' : `transform ${durationSeconds}s ease-in-out`;
  pulseRing.style.transition = transitionValue;
  pulseRing.style.transform = `scale(${targetScale})`;
  lastTargetScale = targetScale;

  phaseLabel.textContent = `${currentPhase.emoji} ${currentPhase.label}`;

  calmTimer = setTimeout(() => {
    setPhase(phaseIndex + 1);
  }, durationSeconds * 1000);
}

function primeRing() {
  if (!pulseRing) return;
  const intensity = waveRange ? Number(waveRange.value) : 1;
  const initialScale = scaleTargets.expand * intensity;
  lastTargetScale = initialScale;
  pulseRing.style.transition = 'transform 0.4s ease-out';
  pulseRing.style.transform = `scale(${initialScale})`;
}

function updateCyclePreview() {
  if (!cyclePreview) return;
  const [inhale, hold, exhale] = phaseDurations();
  cyclePreview.textContent = `${inhale}s inhale • ${hold}s hold • ${exhale}s exhale • ${hold}s hold`;
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
  primeRing();
  setPhase(phaseIndex);
}

function stopCalm(reset = false) {
  running = false;
  calmStart.textContent = 'Start flow';
  clearTimeout(calmTimer);
  clearInterval(sessionTimer);
  if (reset && phaseLabel && pulseRing && phaseTimeline) {
    phaseLabel.textContent = 'Ready when you are';
    primeRing();
    phaseTimeline.querySelectorAll('.chip').forEach((chip) => chip.classList.remove('active'));
    phaseIndex = 0;
  }
}

waveRange?.addEventListener('input', () => {
  updateRangeDisplays();
  if (running) {
    setPhase(phaseIndex);
  } else {
    primeRing();
  }
});
calmStart?.addEventListener('click', startCalm);
calmReset?.addEventListener('click', () => stopCalm(true));
sessionInput?.addEventListener('input', () => {
  if (!sessionRemaining) return;
  const minutes = clamp(Number(sessionInput.value || 0), 1, 30);
  sessionRemaining.textContent = `${minutes.toString().padStart(2, '0')}:00 remaining`;
});
[inhaleInput, holdInput, exhaleInput].forEach((input) => {
  input?.addEventListener('input', () => {
    updateCyclePreview();
    if (running) setPhase(phaseIndex);
  });
});

updateRangeDisplays();
updateCyclePreview();
primeRing();

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

// Progressive muscle relaxation
function pmrStepIndex(key) {
  return pmrSequence.findIndex((step) => step.key === key);
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updatePMRVisual(currentKey) {
  pmrMuscles.forEach((muscle) => {
    const order = pmrStepIndex(muscle.dataset.muscle);
    muscle.classList.toggle('active', muscle.dataset.muscle === currentKey);
    muscle.classList.toggle('completed', order >= 0 && order < pmrIndex);
  });

  pmrSteps.forEach((step, idx) => {
    step.classList.toggle('active', step.dataset.step === currentKey);
    step.classList.toggle('completed', idx < pmrIndex);
  });
}

function stopPMRTimers() {
  clearTimeout(pmrTimer);
  clearInterval(pmrTicker);
}

function finishPMR() {
  pmrRunning = false;
  stopPMRTimers();
  pmrIndex = pmrSequence.length;
  updatePMRVisual(null);
  pmrMuscles.forEach((muscle) => muscle.classList.add('completed'));
  pmrSteps.forEach((step) => {
    step.classList.remove('active');
    step.classList.add('completed');
  });
  if (pmrCountdown) pmrCountdown.textContent = '00:00';
  if (pmrStatus) pmrStatus.textContent = 'Sequence complete. Breathe into the softness.';
  if (pmrStart) {
    pmrStart.textContent = pmrStartLabel;
    pmrStart.disabled = false;
  }
}

function updatePMRCountdown() {
  if (!pmrCountdown || !pmrEndTime) return;
  const remaining = Math.max(Math.round((pmrEndTime - Date.now()) / 1000), 0);
  pmrCountdown.textContent = formatTime(remaining);
  if (remaining <= 0 && pmrRunning) {
    finishPMR();
  }
}

function playNextPMRStep() {
  pmrIndex += 1;
  if (pmrIndex >= pmrSequence.length) {
    finishPMR();
    return;
  }
  const current = pmrSequence[pmrIndex];
  if (pmrStatus) {
    pmrStatus.textContent = `${current.label}: ${current.cue}`;
  }
  updatePMRVisual(current.key);
  pmrTimer = setTimeout(playNextPMRStep, current.duration * 1000);
}

function startPMR() {
  if (!pmrStart || pmrRunning || !pmrSequence.length) return;
  pmrRunning = true;
  pmrIndex = -1;
  pmrEndTime = Date.now() + pmrTotalDuration * 1000;
  pmrStart.textContent = 'Flow in motion';
  pmrStart.disabled = true;
  if (pmrStatus) {
    pmrStatus.textContent = 'Follow the glow: six seconds each—gently tense, then soften.';
  }
  updatePMRCountdown();
  clearInterval(pmrTicker);
  pmrTicker = setInterval(updatePMRCountdown, 500);
  playNextPMRStep();
}

function resetPMR() {
  pmrRunning = false;
  pmrIndex = -1;
  pmrEndTime = null;
  stopPMRTimers();
  pmrMuscles.forEach((muscle) => {
    muscle.classList.remove('active');
    muscle.classList.remove('completed');
  });
  pmrSteps.forEach((step) => {
    step.classList.remove('active');
    step.classList.remove('completed');
  });
  if (pmrCountdown) pmrCountdown.textContent = formatTime(pmrTotalDuration);
  if (pmrStatus) pmrStatus.textContent = 'Ready when you are.';
  if (pmrStart) {
    pmrStart.textContent = pmrStartLabel;
    pmrStart.disabled = false;
  }
}

pmrStart?.addEventListener('click', startPMR);
pmrReset?.addEventListener('click', resetPMR);
resetPMR();

// Floating crisis video controls
const floatingVideo = document.querySelector('[data-floating-video]');
const floatingVideoClose = document.querySelector('[data-floating-video-close]');
const floatingIframe = floatingVideo?.querySelector('iframe');
let floatingPlayer;
let floatingPlayerInitialized = false;
let youtubeApiLoading = false;
const youtubeApiCallbacks = [];

function hideFloatingVideo() {
  if (!floatingVideo) return;
  floatingVideo.classList.add('is-hidden');
  floatingVideo.classList.remove('is-playing');
  if (floatingPlayer?.pauseVideo) {
    floatingPlayer.pauseVideo();
  }
}

function loadYouTubeAPI(callback) {
  if (window.YT?.Player) {
    callback();
    return;
  }

  youtubeApiCallbacks.push(callback);

  if (youtubeApiLoading) return;
  youtubeApiLoading = true;

  const script = document.createElement('script');
  script.src = 'https://www.youtube.com/iframe_api';
  const firstScript = document.getElementsByTagName('script')[0];
  firstScript.parentNode.insertBefore(script, firstScript);

  window.onYouTubeIframeAPIReady = () => {
    youtubeApiCallbacks.splice(0).forEach((cb) => cb());
  };
}

function initFloatingPlayer() {
  if (!floatingIframe || floatingPlayerInitialized || !window.YT?.Player) return;
  floatingPlayerInitialized = true;

  floatingPlayer = new YT.Player(floatingIframe, {
    events: {
      onReady: (event) => {
        try {
          event.target.unMute();
          event.target.setVolume(100);
          event.target.playVideo();
        } catch (error) {
          console.error('Unable to start floating video audio', error);
        }
      },
      onStateChange: (event) => {
        if (!floatingVideo) return;

        if (event.data === YT.PlayerState.PLAYING) {
          floatingVideo.classList.add('is-playing');
        } else {
          floatingVideo.classList.remove('is-playing');

          if (event.data === YT.PlayerState.ENDED) {
            hideFloatingVideo();
          }
        }
      },
    },
    playerVars: {
      autoplay: 1,
      mute: 0,
      loop: 0,
      rel: 0,
      controls: 0,
      playsinline: 1,
    },
  });
}

function bootstrapFloatingVideo() {
  if (!floatingVideo || floatingPlayerInitialized) return;
  loadYouTubeAPI(initFloatingPlayer);
}

floatingVideoClose?.addEventListener('click', hideFloatingVideo);

if (floatingVideo) {
  bootstrapFloatingVideo();
  window.addEventListener('load', bootstrapFloatingVideo);
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

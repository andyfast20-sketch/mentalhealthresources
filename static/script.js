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
const bookModal = document.querySelector('[data-book-modal]');
const bookModalTitle = document.querySelector('[data-book-modal-title]');
const bookModalAuthor = document.querySelector('[data-book-modal-author]');
const bookModalDescription = document.querySelector('[data-book-modal-description]');
const bookModalCover = document.querySelector('[data-book-modal-cover]');
const bookModalCoverWrapper = document.querySelector('[data-book-modal-cover-wrapper]');
const bookModalCoverFallback = document.querySelector('[data-book-modal-cover-fallback]');
const bookModalLink = document.querySelector('[data-book-modal-link]');
const bookTriggerButtons = Array.from(document.querySelectorAll('[data-book-trigger]'));
const bookCards = Array.from(document.querySelectorAll('.book-card[data-book-index]'));
const bookModalCloseButtons = Array.from(document.querySelectorAll('[data-book-modal-close]'));
const adminBookModal = document.querySelector('[data-admin-book-modal]');
const adminBookForm = document.querySelector('[data-admin-book-form]');
const adminBookCloseButtons = Array.from(document.querySelectorAll('[data-admin-book-modal-close]'));
const adminBookEditTriggers = Array.from(document.querySelectorAll('[data-admin-book-edit-trigger]'));
const crisisVolume = document.querySelector('[data-crisis-volume]');
const crisisVolumeValue = document.querySelector('[data-crisis-volume-value]');
const calmingCompleteButtons = Array.from(document.querySelectorAll('[data-calming-complete]'));
let slideIndex = 0;
let slideWidth = 0;
let crisisPlayer;
let activeBookTrigger = null;
let activeAdminTrigger = null;
const trackedScrollBooks = new Set();

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

function updateCrisisVolumeDisplay(volume) {
  if (crisisVolumeValue) {
    crisisVolumeValue.textContent = `${Math.round(volume)}%`;
  }
}

function bindCrisisVolumeControl(player) {
  if (!crisisVolume) return;

  const startingVolume = Number.parseFloat(crisisVolume.value || '60');
  player.setVolume(startingVolume);
  updateCrisisVolumeDisplay(startingVolume);

  crisisVolume.addEventListener('input', (event) => {
    const value = Number.parseFloat(event.target.value || '0');
    player.unMute();
    player.setVolume(value);
    updateCrisisVolumeDisplay(value);
  });
}

function initCrisisPlayer() {
  const crisisIframe = document.getElementById('crisis-video-player');
  if (!crisisIframe || !window.YT || typeof window.YT.Player !== 'function') return;

  crisisPlayer = new window.YT.Player(crisisIframe, {
    events: {
      onReady: ({ target }) => {
        bindCrisisVolumeControl(target);
      },
    },
  });
}

window.onYouTubeIframeAPIReady = () => {
  initCrisisPlayer();
};

if (window.YT && typeof window.YT.Player === 'function') {
  initCrisisPlayer();
}

function updateBodyModalLock() {
  const hasOpenModal =
    charityModal?.classList.contains('is-open') ||
    bookModal?.classList.contains('is-open') ||
    adminBookModal?.classList.contains('is-open');
  document.body.classList.toggle('modal-open', Boolean(hasOpenModal));
}

function trackBookView(card) {
  const index = card?.dataset.bookIndex;
  if (index === undefined) return;

  fetch(`/books/${index}/view`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }).catch(() => {});
}

function trackBookScroll(card) {
  const index = card?.dataset.bookIndex;
  if (index === undefined || trackedScrollBooks.has(index)) return;

  trackedScrollBooks.add(index);

  fetch(`/books/${index}/scroll`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }).catch(() => {});
}

function populateBookModal(data) {
  if (!bookModal) return;

  if (bookModalTitle) {
    bookModalTitle.textContent = data.title || 'Book details';
  }

  if (bookModalAuthor) {
    bookModalAuthor.textContent = data.author || 'Featured read';
  }

  if (bookModalDescription) {
    bookModalDescription.textContent = data.description || 'Description coming soon.';
  }

  if (bookModalLink) {
    bookModalLink.href = data.link || '#';
  }

  if (bookModalCover) {
    if (data.cover) {
      bookModalCover.src = data.cover;
      bookModalCover.alt = `${data.title || 'Book'} cover`;
      bookModalCover.style.display = 'block';
      bookModalCoverWrapper?.classList.remove('is-empty');
      bookModalCoverFallback?.classList.add('hidden');
    } else {
      bookModalCover.removeAttribute('src');
      bookModalCover.alt = '';
      bookModalCover.style.display = 'none';
      bookModalCoverWrapper?.classList.add('is-empty');
      bookModalCoverFallback?.classList.remove('hidden');
    }
  }

  bookModal.classList.add('is-open');
  updateBodyModalLock();
}

function openBookModalFromCard(card, trigger) {
  if (!card) return;

  trackBookView(card);

  const data = {
    title: card.dataset.bookTitle || card.querySelector('h3')?.textContent || '',
    author: card.dataset.bookAuthor || '',
    description: card.dataset.bookDescription || card.querySelector('.book-description')?.textContent || '',
    cover: card.dataset.bookCover || card.querySelector('.book-cover img')?.src || '',
    link: card.dataset.bookLink || card.querySelector('.book-actions a')?.href || '',
  };

  activeBookTrigger = trigger || null;
  activeBookTrigger?.setAttribute('aria-expanded', 'true');

  populateBookModal(data);
}

function closeBookModal() {
  if (!bookModal) return;
  bookModal.classList.remove('is-open');
  activeBookTrigger?.setAttribute('aria-expanded', 'false');
  activeBookTrigger = null;
  updateBodyModalLock();
}

function initBookScrollTracking() {
  if (!bookCards.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          trackBookScroll(entry.target);
        }
      });
    },
    {
      root: bookTrack || null,
      threshold: 0.6,
    }
  );

  bookCards.forEach((card) => observer.observe(card));
}

bookTriggerButtons.forEach((button) => {
  button.addEventListener('click', () => {
    openBookModalFromCard(button.closest('.book-card'), button);
  });
});

initBookScrollTracking();

bookModalCloseButtons.forEach((button) => button.addEventListener('click', closeBookModal));

bookModal?.addEventListener('click', (event) => {
  if (event.target === bookModal) {
    closeBookModal();
  }
});

function populateAdminBookForm(trigger) {
  if (!adminBookForm || !trigger) return;
  adminBookForm.action = trigger.dataset.action || adminBookForm.action;
  const titleInput = adminBookForm.querySelector('input[name="title"]');
  const authorInput = adminBookForm.querySelector('input[name="author"]');
  const descriptionInput = adminBookForm.querySelector('textarea[name="description"]');
  const affiliateInput = adminBookForm.querySelector('input[name="affiliate_url"]');
  const coverInput = adminBookForm.querySelector('input[name="cover_url"]');

  if (titleInput) titleInput.value = trigger.dataset.title || '';
  if (authorInput) authorInput.value = trigger.dataset.author || '';
  if (descriptionInput) descriptionInput.value = trigger.dataset.description || '';
  if (affiliateInput) affiliateInput.value = trigger.dataset.affiliateUrl || '';
  if (coverInput) coverInput.value = trigger.dataset.coverUrl || '';
}

function openAdminBookModal(trigger) {
  if (!adminBookModal) return;
  activeAdminTrigger = trigger;
  populateAdminBookForm(trigger);
  adminBookModal.classList.add('is-open');
  updateBodyModalLock();
  adminBookForm?.querySelector('input[name="title"]')?.focus();
}

function closeAdminBookModal() {
  if (!adminBookModal) return;
  adminBookModal.classList.remove('is-open');
  activeAdminTrigger = null;
  updateBodyModalLock();
}

adminBookEditTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => openAdminBookModal(trigger));
});

adminBookCloseButtons.forEach((button) => button.addEventListener('click', closeAdminBookModal));

adminBookModal?.addEventListener('click', (event) => {
  if (event.target === adminBookModal) {
    closeAdminBookModal();
  }
});

function openModal() {
  if (!charityModal) return;
  charityModal.classList.add('is-open');
  updateBodyModalLock();
}

function closeModal() {
  if (!charityModal) return;
  charityModal.classList.remove('is-open');
  updateBodyModalLock();
}

showCharitiesBtn?.addEventListener('click', openModal);
modalClose?.addEventListener('click', closeModal);
charityModal?.addEventListener('click', (event) => {
  if (event.target === charityModal) {
    closeModal();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    if (charityModal?.classList.contains('is-open')) closeModal();
    if (bookModal?.classList.contains('is-open')) closeBookModal();
    if (adminBookModal?.classList.contains('is-open')) closeAdminBookModal();
  }
});

function updateCalmingCounts(slug, newCount) {
  document.querySelectorAll(`[data-calming-count="${slug}"]`).forEach((node) => {
    node.textContent = newCount;
  });
}

function handleCalmingComplete(button) {
  if (!button) return;

  const slug = button.dataset.calmingSlug;
  if (!slug) return;

  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = 'Logged';

  fetch(`/calming-tools/${slug}/complete`, { method: 'POST' })
    .then((response) => response.json())
    .then((data) => {
      if (!data?.success) return;
      updateCalmingCounts(slug, data.completed_count);
    })
    .catch(() => {})
    .finally(() => {
      button.textContent = originalText;
      button.disabled = false;
    });
}

calmingCompleteButtons.forEach((button) => {
  button.addEventListener('click', () => handleCalmingComplete(button));
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
const colourPool = document.querySelector('[data-colour-pool]');
const poolWater = colourPool?.querySelector('.pool-water');
const dropStatus = document.querySelector('[data-drop-status]');
const resetPoolBtn = document.querySelector('[data-reset-pool]');
const emotionDrops = Array.from(document.querySelectorAll('[data-emotion-drop]'));

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

// Anxiety Colour Drop
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
  if (dropStatus) dropStatus.textContent = message;
}

function createPoolDrop(emotion, colour, clientX = null) {
  if (!poolWater || !colourPool) return;
  const rect = poolWater.getBoundingClientRect();
  const leftPercent = clientX ? clamp(((clientX - rect.left) / rect.width) * 100, 6, 94) : 50;
  const topPercent = clamp(36 + Math.random() * 28, 28, 78);
  const size = clamp(48 + Math.random() * 36, 48, 96);

  const ripple = document.createElement('span');
  ripple.className = 'pool-ripple';
  ripple.style.left = `${leftPercent}%`;
  ripple.style.top = `${topPercent}%`;
  ripple.style.setProperty('--drop-size', `${size * 2.2}px`);
  ripple.style.setProperty('--ripple-colour', colour);
  poolWater.appendChild(ripple);
  ripple.addEventListener('animationend', () => ripple.remove());

  const drop = document.createElement('span');
  drop.className = 'pool-drop';
  drop.dataset.emotion = emotion;
  drop.style.setProperty('--drop-colour', colour);
  drop.style.left = `${leftPercent}%`;
  drop.style.top = `${topPercent}%`;
  drop.style.setProperty('--drop-size', `${size}px`);

  poolWater.appendChild(drop);
  drop.addEventListener('animationend', () => drop.remove());

  Array.from({ length: 6 }).forEach((_, index) => {
    const sparkle = document.createElement('span');
    sparkle.className = 'pool-spark';
    sparkle.style.left = `${clamp(leftPercent + (Math.random() - 0.5) * 22, 8, 92)}%`;
    sparkle.style.top = `${clamp(topPercent + (Math.random() - 0.5) * 20, 22, 86)}%`;
    sparkle.style.setProperty('--spark-colour', colour);
    sparkle.style.setProperty('--spark-delay', `${index * 90}ms`);
    poolWater.appendChild(sparkle);
    sparkle.addEventListener('animationend', () => sparkle.remove());
  });

  const affirmation = releaseAffirmations[Math.floor(Math.random() * releaseAffirmations.length)];
  const cue = nextBreathCue();
  updateDropStatus(`${emotion} released. ${affirmation} ${cue}`);
}

function clearPoolDrops() {
  poolWater?.querySelectorAll('.pool-drop').forEach((drop) => drop.remove());
  updateDropStatus('Pool cleared. Invite a new feeling to soften and breathe out as it lands.');
}

function handleDrop(event, payload) {
  if (!payload?.emotion || !payload?.colour) return;
  createPoolDrop(payload.emotion, payload.colour, event.clientX);
}

emotionDrops.forEach((drop) => {
  const emotion = drop.dataset.emotion || 'Feeling';
  const colour = drop.dataset.colour || '#6aa9f7';

  drop.addEventListener('dragstart', (event) => {
    drop.classList.add('is-dragging');
    updateDropStatus(`Carrying ${emotion.toLowerCase()} to the water...`);
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'copy';
      event.dataTransfer.setData('text/plain', JSON.stringify({ emotion, colour }));
    }
  });

  drop.addEventListener('dragend', () => {
    drop.classList.remove('is-dragging');
  });

  drop.addEventListener('click', () => {
    createPoolDrop(emotion, colour);
  });
});

colourPool?.addEventListener('dragover', (event) => {
  event.preventDefault();
  colourPool.classList.add('is-ready');
  updateDropStatus('Pool open—carry the colour in and let it ripple.');
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy';
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
      autoplay: 0,
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

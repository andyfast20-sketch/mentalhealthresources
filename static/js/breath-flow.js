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
const calmingSlug = calmStart?.dataset.calmingSlug;
const viewCounters = calmingSlug
  ? Array.from(document.querySelectorAll(`[data-calming-view="${calmingSlug}"]`))
  : [];
const completionCounters = calmingSlug
  ? Array.from(document.querySelectorAll(`[data-calming-count="${calmingSlug}"]`))
  : [];

let calmTimer;
let sessionTimer;
let sessionEndTime = null;
let phaseIndex = 0;
let running = false;
let lastTargetScale = 1;

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

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function updateRangeDisplays() {
  if (waveValue && waveRange) {
    const rangeVal = Number(waveRange.value);
    const ranges = { 0.8: 'Gentle', 0.9: 'Softer', 1: 'Balanced', 1.1: 'Focused', 1.2: 'Energized', 1.3: 'Uplifted', 1.4: 'Bright' };
    waveValue.textContent = ranges[rangeVal] || 'Balanced';
  }
}

function phaseDurations() {
  const inhale = clamp(Number(inhaleInput?.value || 4), 1, 20);
  const hold = clamp(Number(holdInput?.value || 2), 0, 20);
  const exhale = clamp(Number(exhaleInput?.value || 5), 1, 20);
  return [inhale, hold, exhale];
}

function setPhase(index = 0) {
  if (!pulseRing || !phaseLabel || !phaseTimeline) return;
  const durations = phaseDurations();
  const currentPhase = phaseConfig[index % phaseConfig.length];
  phaseIndex = index % phaseConfig.length;
  const durationSeconds = clamp(currentPhase.duration(durations), 0.5, 20);
  const chips = phaseTimeline.querySelectorAll('.chip');
  chips.forEach((chip) => chip.classList.remove('active'));
  chips[phaseIndex]?.classList.add('active');

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
  logFlowStart();
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

function updateViewCounts(newCount) {
  viewCounters.forEach((node) => {
    node.textContent = newCount;
  });
}

function updateCompletionCounts(newCount) {
  completionCounters.forEach((node) => {
    node.textContent = newCount;
  });
}

function logFlowStart() {
  if (!calmingSlug) return;

  fetch(`/calming-tools/${calmingSlug}/view`, { method: 'POST' })
    .then((response) => response.json())
    .then((data) => {
      if (!data?.success) return;
      if (typeof data.view_count === 'number') {
        updateViewCounts(data.view_count);
      }
      if (typeof data.completed_count === 'number') {
        updateCompletionCounts(data.completed_count);
      }
    })
    .catch(() => {});
}

// Progressive muscle relaxation
const pmrStart = document.querySelector('[data-pmr-start]');
const pmrReset = document.querySelector('[data-pmr-reset]');
const pmrStatus = document.querySelector('[data-pmr-status]');
const pmrCountdown = document.querySelector('[data-pmr-countdown]');
const pmrSteps = Array.from(document.querySelectorAll('.pmr-steps [data-step]'));
const pmrMuscles = Array.from(document.querySelectorAll('[data-muscle]'));

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
let pmrTimer;
let pmrTicker;
let pmrIndex = -1;
let pmrEndTime;
let pmrRunning = false;

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

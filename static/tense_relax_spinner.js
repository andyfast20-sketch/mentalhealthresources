(function () {
  const canvas = document.getElementById("spinnerCanvas");
  if (!canvas) return;

  const statusEl = document.querySelector("[data-spinner-status]");
  const ctx = canvas.getContext("2d");
  const AREAS = [
    "Neck",
    "Shoulders",
    "Face",
    "Arms",
    "Hands",
    "Calves",
    "Feet",
    "Chest",
  ];
  const COLORS = [
    [255, 182, 185],
    [255, 223, 186],
    [255, 255, 186],
    [186, 255, 201],
    [186, 225, 255],
    [210, 200, 255],
    [255, 200, 240],
    [255, 210, 200],
  ];

  const RADIUS = 208;
  const TEXT_RADIUS = 120;
  const FLASH_TOTAL = 14;
  const FLASH_SPEED = 0.12;

  let width = 576;
  let height = 576;
  let angle = 0;
  let highlight = null;
  let spinsLeft = 20;
  let spinning = false;
  let speed = 0;
  let nextSpin = performance.now();
  let flashCounter = 0;
  let flashing = false;

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    width = rect.width || 576;
    height = rect.height || 576;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function drawBackground() {
    const gradient = ctx.createRadialGradient(
      width * 0.35,
      height * 0.35,
      width * 0.1,
      width * 0.5,
      height * 0.5,
      width * 0.7
    );
    gradient.addColorStop(0, "#fff7fb");
    gradient.addColorStop(1, "#f2f6ff");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
  }

  function drawSpinner(currentAngle, flashFrame) {
    const num = AREAS.length;
    const sliceAngle = (2 * Math.PI) / num;
    let base = currentAngle - Math.PI / 2;
    for (let i = 0; i < num; i++) {
      const start = base + i * sliceAngle;
      const end = start + sliceAngle;
      let [r, g, b] = COLORS[i];
      if (highlight === i) {
        if (flashFrame) {
          r = g = b = 255;
        } else {
          r = Math.min(r + 70, 255);
          g = Math.min(g + 70, 255);
          b = Math.min(b + 70, 255);
        }
      }
      ctx.beginPath();
      ctx.moveTo(width / 2, height / 2);
      ctx.arc(width / 2, height / 2, RADIUS, start, end);
      ctx.closePath();
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fill();

      const mid = start + sliceAngle / 2;
      const tx = width / 2 + Math.cos(mid) * TEXT_RADIUS;
      const ty = height / 2 + Math.sin(mid) * TEXT_RADIUS;
      ctx.fillStyle = "#282828";
      ctx.font = "bold 15px Arial";
      ctx.textAlign = "center";
      ctx.fillText("Tense / Relax", tx, ty - 8);
      ctx.font = "bold 17px Arial";
      ctx.fillText(AREAS[i], tx, ty + 12);
    }
  }

  function drawPointer() {
    ctx.fillStyle = "#2e2e2e";
    ctx.beginPath();
    ctx.moveTo(width / 2, height / 2 - RADIUS - 8);
    ctx.lineTo(width / 2 - 16, height / 2 - RADIUS - 40);
    ctx.lineTo(width / 2 + 16, height / 2 - RADIUS - 40);
    ctx.closePath();
    ctx.fill();
  }

  function getWinningSlice(currentAngle) {
    const num = AREAS.length;
    const sliceAngle = (2 * Math.PI) / num;
    const corrected = (-currentAngle + Math.PI / 2) % (2 * Math.PI);
    return Math.floor(corrected / sliceAngle);
  }

  function startSpin() {
    spinning = true;
    highlight = null;
    speed = Math.random() * (0.4 - 0.23) + 0.23;
    spinsLeft -= 1;
    if (statusEl) {
      statusEl.textContent = `Spin ${20 - spinsLeft} of 20 in progress…`;
    }
  }

  function update(now) {
    if (spinsLeft > 0 && !spinning && !flashing && now >= nextSpin) {
      startSpin();
    }

    if (spinning) {
      angle += speed;
      speed *= 0.992;
      if (speed < 0.002) {
        spinning = false;
        highlight = getWinningSlice(angle);
        flashing = true;
        flashCounter = FLASH_TOTAL;
        nextSpin = now + 4500;
        if (statusEl) {
          statusEl.textContent = AREAS[highlight] + " — squeeze, then soften.";
        }
      }
    }

    let flashFrame = false;
    if (flashing) {
      flashFrame = flashCounter % 2 === 0;
      flashCounter -= FLASH_SPEED;
      if (flashCounter <= 0) {
        flashing = false;
        if (spinsLeft === 0 && statusEl) {
          statusEl.textContent = "All 20 spins complete. Breathe out and rest.";
        }
      }
    }

    drawBackground();
    drawSpinner(angle, flashFrame);
    drawPointer();
  }

  function loop(now) {
    update(now || performance.now());
    requestAnimationFrame(loop);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(loop);
})();

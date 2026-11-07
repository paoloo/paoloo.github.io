/* Small, local embellishments; the page's content and navigation work without JS. */
(() => {
  'use strict';

  const clock = document.getElementById('utc-clock');
  function updateClock() {
    const utc = new Date().toISOString().slice(11, 19);
    clock.textContent = `${utc} UTC / SOL III`;
    clock.dateTime = new Date().toISOString();
  }
  updateClock();
  setInterval(updateClock, 1000);

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const buttonImages = [...document.querySelectorAll('.button-wall img')];
  const stillFrames = new Map();
  let motionPaused = reducedMotion.matches;

  // Capture each GIF's first decoded frame to respect reduced-motion settings.
  // Original animated files remain untouched.
  function captureStill(img) {
    if (stillFrames.has(img)) return;
    try {
      const frame = document.createElement('canvas');
      frame.width = img.naturalWidth;
      frame.height = img.naturalHeight;
      const context = frame.getContext('2d');
      if (!context || !frame.width || !frame.height) return;
      context.drawImage(img, 0, 0);
      stillFrames.set(img, { animated: img.src, still: frame.toDataURL('image/png') });
      if (motionPaused) img.src = stillFrames.get(img).still;
    } catch {
      // Navigation and content remain available if image decoding is blocked.
    }
  }
  buttonImages.forEach(img => {
    if (img.complete && img.naturalWidth) captureStill(img);
    else img.addEventListener('load', () => captureStill(img), { once: true });
  });

  function updateMotion() {
    document.body.classList.toggle('motion-paused', motionPaused);
    stillFrames.forEach((frames, img) => { img.src = motionPaused ? frames.still : frames.animated; });
  }
  reducedMotion.addEventListener('change', event => {
    motionPaused = event.matches;
    updateMotion();
  });
  updateMotion();

  // An explicitly synthetic waterfall: deterministic noise and a drifting tone.
  const canvas = document.getElementById('waterfall');
  const context = canvas.getContext('2d');
  const retune = document.getElementById('retune');
  if (!context) return;
  const frequencies = ['1420.405 MHz', '1665.402 MHz', '1667.359 MHz'];
  let band = 0;
  function drawWaterfall() {
    const { width, height } = canvas;
    const pixels = context.createImageData(width, height);
    let seed = 1999 + band * 7919;
    const random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let y = 0; y < height; y++) {
      const signalX = width * (.34 + band * .12) + y * (.12 - band * .09);
      for (let x = 0; x < width; x++) {
        const offset = (y * width + x) * 4;
        const distance = Math.abs(x - signalX);
        let energy = random() * .27;
        if (distance < 2.5) energy += .6 + random() * .25;
        else if (distance < 6) energy += .16;
        if (y % 37 < 2) energy += random() * .1;
        if (y % 4 === 0) energy *= .7;
        pixels.data[offset] = 8 + energy * 153;
        pixels.data[offset + 1] = 14 + energy * 188;
        pixels.data[offset + 2] = 7 + energy * 89;
        pixels.data[offset + 3] = 255;
      }
    }
    context.putImageData(pixels, 0, 0);
    document.getElementById('receiver-frequency').textContent = frequencies[band];
    canvas.setAttribute('aria-label', `Synthetic radio waterfall illustration at ${frequencies[band]}. Not live telescope data.`);
  }
  drawWaterfall();
  retune.hidden = false;
  retune.addEventListener('click', () => {
    band = (band + 1) % frequencies.length;
    drawWaterfall();
  });
})();

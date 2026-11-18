/**
 * Bezier Transit Simulator — improved engine.
 *
 * Physical model
 * --------------
 * The occulter is a Bezier-bounded silhouette rasterized on a MASK grid with
 * anti-aliased (fractional) coverage. The star is a quadratic limb-darkened
 * disk I(mu) = 1 - u1 (1 - mu) - u2 (1 - mu)^2, analytic surface integral
 * S(r) = pi [1 - u1 (1 - m) - u2 (1 - m)^2] with m = sqrt(1 - r^2).
 * Flux is the exact occulted integral over opaque cells; edge cells get a
 * partial-interruption correction. The trajectory is a straight chord with
 * impact parameter b: x(t) = x0 + v t, y = -b.
 *
 * Observability model
 * -------------------
 * Optional finite-exposure time sampling (supersampled boxcar integration)
 * plus photon noise at a selectable ppm level, from a seeded PRNG, so the
 * exported light curve is reproducible.
 *
 * Export
 * ------
 * time (days, BJD-like, cadence), normalized flux, flux_err in ppm, and the
 * injected model signal, in a header-documented CSV designed to load directly
 * with lightkurve.LightCurve.read(..., time_column="time", ...).
 */
(function () {
  const root = document.querySelector("[data-bezier-simulator]");
  if (!root) return;

  const TAU = Math.PI * 2;
  const MASK_SIZE = 192;          // fractional-coverage raster of the occulter
  const CURVE_SAMPLES = 560;      // model resolution along the chord
  const SUPER_FACTOR = 6;         // sub-exposure oversampling for finite exposure
  const CIRCLE_SAMPLES = 560;     // sampling grid for the fitted reference circle
  const BJD_OFFSET = 2459500.0;   // arbitrary but documented epoch for exported times

  const stageCanvas = root.querySelector("[data-bezier-stage]");
  const curveCanvas = root.querySelector("[data-bezier-curve]");
  const modelLabel = root.querySelector("[data-bezier-model]");
  const statsLabel = root.querySelector("[data-bezier-stats]");
  const anchorLabel = root.querySelector("[data-bezier-anchor-count]");
  const depthLabel = root.querySelector("[data-bezier-depth]");
  const stageTitle = root.querySelector("[data-bezier-stage-title]");
  const customGuide = root.querySelector("[data-custom-guide]");
  const customGuideCount = root.querySelector("[data-custom-guide-count]");
  const modelButtons = [...root.querySelectorAll("[data-shape-model]")];
  const randomButton = root.querySelector("[data-bezier-random]");
  const clearButton = root.querySelector("[data-bezier-clear]");
  const playButton = root.querySelector("[data-bezier-play]");
  const scaleInput = root.querySelector("[data-bezier-scale]");
  const u1Input = root.querySelector("[data-bezier-u1]");
  const u2Input = root.querySelector("[data-bezier-u2]");
  const bInput = root.querySelector("[data-bezier-b]");
  const speedInput = root.querySelector("[data-bezier-speed]");
  const noiseInput = root.querySelector("[data-bezier-noise]");
  const cadenceInput = root.querySelector("[data-bezier-cadence]");
  const seedInput = root.querySelector("[data-bezier-seed]");
  const exposureInput = root.querySelector("[data-bezier-exposure]");
  const repeatInput = root.querySelector("[data-bezier-repeat]");
  const periodInput = root.querySelector("[data-bezier-period]");
  const epochInput = root.querySelector("[data-bezier-epoch]");
  const spanSelect = root.querySelector("[data-bezier-span]");
  const gapSelect = root.querySelector("[data-bezier-gap]");
  const compareInput = root.querySelector("[data-bezier-compare]");
  const downloadButton = root.querySelector("[data-bezier-download]");
  const downloadJsonButton = root.querySelector("[data-bezier-download-json]");
  const importButton = root.querySelector("[data-bezier-import]");
  const importFileInput = root.querySelector("[data-bezier-import-file]");
  const sumNodes = {
    duration: root.querySelector("[data-sum-duration]"),
    cadence: root.querySelector("[data-sum-cadence]"),
    points: root.querySelector("[data-sum-points]"),
    depth: root.querySelector("[data-sum-depth]"),
    rp: root.querySelector("[data-sum-rp]"),
    fitRp: root.querySelector("[data-sum-fit-rp]"),
    fitB: root.querySelector("[data-sum-fit-b]"),
    rms: root.querySelector("[data-sum-rms]")
  };

  const state = {
    model: "random",
    modelName: "Random Bezier",
    anchors: [],
    customAnchors: [],
    boundaries: [],
    mask: new Float32Array(MASK_SIZE * MASK_SIZE),
    maskPixels: [],               // {x, y, area} fractional opaque area per cell
    maskArea: 0,
    scale: Number(scaleInput.value),
    u1: Number(u1Input.value),
    u2: Number(u2Input.value),
    b: Number(bInput.value),
    speed: Number(speedInput.value),
    noisePpm: Number(noiseInput.value),
    cadenceSec: Number(cadenceInput.value),
    seed: Number(seedInput.value),
    finiteExposure: exposureInput.checked,
    repeat: false,
    periodDays: 3.5225,
    epochOffset: 0,
    repeatSpan: 5,
    gapStyle: "continuous",
    compareCircle: compareInput.checked,
    equivalentRadius: 0,
    curve: [],
    observedCurve: [],
    circleCurve: [],
    residuals: [],
    depthPpt: 0,
    rmsPpt: 0,
    fit: null,
    phase: 0,
    playing: true,
    dirty: true
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  /* Deterministic PRNG (mulberry32) so a seed reproduces a shape and its noise. */
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Quadratic limb darkening: intensity and closed-form disk integral. */
  function limbIntensity(mu) {
    return Math.max(0, 1 - state.u1 * (1 - mu) - state.u2 * (1 - mu) * (1 - mu));
  }

  function stellarTotalFlux() {
    return Math.PI * (1 - state.u1 / 3 - state.u2 / 6);
  }

  function cubicPoint(p0, p1, p2, p3, t) {
    const mt = 1 - t;
    const mt2 = mt * mt;
    const t2 = t * t;
    return {
      x: mt2 * mt * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t2 * t * p3.x,
      y: mt2 * mt * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t2 * t * p3.y
    };
  }

  function orderByAngle(points) {
    if (points.length < 3) return points.slice();
    const center = points.reduce(
      (sum, point) => ({ x: sum.x + point.x / points.length, y: sum.y + point.y / points.length }),
      { x: 0, y: 0 }
    );
    return points
      .slice()
      .sort((a, b) => Math.atan2(a.y - center.y, a.x - center.x) - Math.atan2(b.y - center.y, b.x - center.x));
  }

  function buildBezierBoundary(anchors, handleStrength = 0.3) {
    const ordered = orderByAngle(anchors);
    const boundary = [];
    const count = ordered.length;
    if (count < 3) return boundary;

    for (let index = 0; index < count; index += 1) {
      const p0 = ordered[index];
      const p3 = ordered[(index + 1) % count];
      const previous = ordered[(index - 1 + count) % count];
      const next = ordered[(index + 2) % count];
      const p1 = {
        x: p0.x + handleStrength * (p3.x - previous.x),
        y: p0.y + handleStrength * (p3.y - previous.y)
      };
      const p2 = {
        x: p3.x - handleStrength * (next.x - p0.x),
        y: p3.y - handleStrength * (next.y - p0.y)
      };

      for (let step = 0; step < 24; step += 1) {
        boundary.push(cubicPoint(p0, p1, p2, p3, step / 24));
      }
    }
    return boundary;
  }

  function randomBezierAnchors(count, rand = Math.random) {
    const anchors = [];
    const elongation = 0.72 + rand() * 0.46;
    const rotation = rand() * TAU;
    for (let index = 0; index < count; index += 1) {
      const angle = (index / count) * TAU + (rand() - 0.5) * 0.24;
      const radialTexture = 0.16 * Math.sin(index * 1.7) + 0.12 * Math.sin(index * 3.1);
      const radius = clamp(0.2 + rand() * 0.4 + radialTexture, 0.14, 0.62);
      const rawX = Math.cos(angle) * radius;
      const rawY = Math.sin(angle) * radius * elongation;
      anchors.push({
        x: rawX * Math.cos(rotation) - rawY * Math.sin(rotation),
        y: rawX * Math.sin(rotation) + rawY * Math.cos(rotation)
      });
    }
    return anchors;
  }

  function presetAnchors(name) {
    if (name === "screen") {
      return [
        { x: -0.98, y: -0.5 },
        { x: -0.66, y: -0.44 },
        { x: -0.2, y: -0.28 },
        { x: 0.24, y: -0.1 },
        { x: 0.94, y: 0.28 },
        { x: 0.88, y: 0.46 },
        { x: 0.22, y: 0.16 },
        { x: -0.34, y: -0.02 },
        { x: -0.9, y: -0.25 }
      ];
    }

    return randomBezierAnchors(15);
  }

  function fragmentedBoundaries() {
    const fragments = [
      { x: -0.78, y: 0.3, rx: 0.2, ry: 0.28, n: 8, twist: 0.1 },
      { x: -0.34, y: -0.28, rx: 0.16, ry: 0.42, n: 9, twist: -0.22 },
      { x: 0.18, y: 0.16, rx: 0.22, ry: 0.3, n: 7, twist: 0.34 },
      { x: 0.72, y: -0.18, rx: 0.16, ry: 0.26, n: 7, twist: -0.1 }
    ];

    return fragments.map(fragment => {
      const anchors = [];
      for (let index = 0; index < fragment.n; index += 1) {
        const angle = (index / fragment.n) * TAU + fragment.twist;
        const radius = 0.82 + 0.18 * Math.sin(index * 1.7);
        anchors.push({
          x: fragment.x + Math.cos(angle) * fragment.rx * radius,
          y: fragment.y + Math.sin(angle) * fragment.ry * radius
        });
      }
      return buildBezierBoundary(anchors, 0.22);
    });
  }

  function pointInPolygon(x, y, polygon) {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
      const pi = polygon[i];
      const pj = polygon[j];
      const intersects = (pi.y > y) !== (pj.y > y)
        && x < ((pj.x - pi.x) * (y - pi.y)) / ((pj.y - pi.y) || 1e-7) + pi.x;
      if (intersects) inside = !inside;
    }
    return inside;
  }

  function insideBoundaries(x, y) {
    return state.boundaries.some(boundary => boundary.length >= 3 && pointInPolygon(x, y, boundary));
  }

  /*
   * Fractional coverage: opaque area of grid cell (col,row) estimated by
   * supersampling its corners; cell size 2/MASK in normalized occulter units.
   */
  function rebuildMask() {
    state.mask.fill(0);
    state.maskPixels = [];
    const cell = 2 / MASK_SIZE;
    let filled = 0;
    for (let row = 0; row < MASK_SIZE; row += 1) {
      for (let col = 0; col < MASK_SIZE; col += 1) {
        const x0 = -1 + col * cell;
        const y0 = -1 + row * cell;
        /* 5-point coverage rule: center + 4 corners at half weight. Handles
         * corner nicks (small coverage) far better than raw corner counting. */
        let cov;
        if (insideBoundaries(x0 + cell / 2, y0 + cell / 2)) {
          const cornersHit =
            (insideBoundaries(x0, y0) ? 1 : 0) +
            (insideBoundaries(x0 + cell, y0) ? 1 : 0) +
            (insideBoundaries(x0, y0 + cell) ? 1 : 0) +
            (insideBoundaries(x0 + cell, y0 + cell) ? 1 : 0);
          cov = 0.5 + cornersHit * 0.125;   // center in: >= 0.5, at most 1
        } else {
          const cornersHit =
            (insideBoundaries(x0, y0) ? 1 : 0) +
            (insideBoundaries(x0 + cell, y0) ? 1 : 0) +
            (insideBoundaries(x0, y0 + cell) ? 1 : 0) +
            (insideBoundaries(x0 + cell, y0 + cell) ? 1 : 0);
          if (cornersHit === 0) continue;
          cov = cornersHit * 0.125;         // center out: small sliver estimate
        }
        const x = x0 + cell / 2;
        const y = y0 + cell / 2;
        state.mask[row * MASK_SIZE + col] = cov;
        state.maskPixels.push({ x, y, area: cov * cell * cell });
        filled += cov;
      }
    }
    state.maskArea = filled * cell * cell;
    state.equivalentRadius = Math.sqrt(Math.max(0, state.maskArea) / Math.PI) * state.scale;
  }

  /* Trajectory: straight chord at impact parameter b (y = -b, in stellar radii). */
  function trajectoryY() {
    return -state.b;
  }

  function trajectoryX(phase) {
    const edge = 1.34 + state.scale * 1.35;
    return lerp(-edge, edge, phase);
  }

  /* Time axis: phase 0..1 maps to one full chord crossing. Nominal T14
   * (speed 1) is 6 h, comparable to an Earth-like transit; speed rescales it. */
  function transitDurationDays() {
    return 0.25 / state.speed;
  }

  function phaseToTime(phase) {
    return (phase - 0.5) * transitDurationDays();
  }

  /*
   * Flux at occulter center x (stellar radii). Midpoint-rule integral of the
   * local limb-darkened intensity over the occulter's fractional-coverage
   * cells (pixel.area already includes cell area * scale^2 * coverage). The
   * 192-grid resolves the boundary smoothly; cells past the limb contribute
   * zero.
   */
  function fluxAt(centerX) {
    if (state.maskArea <= 0) return 1;
    const y0 = trajectoryY();
    let blocked = 0;
    for (const pixel of state.maskPixels) {
      const x = centerX + pixel.x * state.scale;
      const y = y0 + pixel.y * state.scale;
      const r = Math.hypot(x, y);
      if (r >= 1) continue;
      blocked += limbIntensity(Math.sqrt(Math.max(0, 1 - r * r))) * pixel.area;
    }
    return clamp(1 - blocked / stellarTotalFlux(), 0, 1);
  }

  /*
   * Exact circular-occulter flux via the annulus method: for each stellar
   * radius r, the arc of the annulus lying inside the planet spans angle
   * 2*acos((r^2 + z^2 - p^2)/(2 r z)) around the star-planet axis (full
   * circle when the annulus is entirely inside the planet). Radial
   * integration with 256 steps is accurate to <<1 ppt for p < 0.5.
   */
  function circleOccultedFlux(p, z) {
    if (p <= 0 || z >= 1 + p) return 0;
    const steps = 256;
    const dr = 1 / steps;
    let acc = 0;
    for (let i = 0; i < steps; i += 1) {
      const r = (i + 0.5) * dr;
      const mu = Math.sqrt(Math.max(0, 1 - r * r));
      const intensity = limbIntensity(mu);
      let arc;
      if (z <= p - r) {
        arc = TAU;                       // annulus fully inside the planet
      } else if (z >= p + r) {
        arc = 0;                         // annulus entirely outside
      } else {
        const cosT = (r * r + z * z - p * p) / (2 * r * z);
        arc = 2 * Math.acos(clamp(cosT, -1, 1));
      }
      acc += intensity * arc * r * dr;
    }
    return acc / stellarTotalFlux();
  }

  /* Reference circle: same Rp/R* on the same chord. */
  function circleFluxAt(centerX) {
    const radius = state.equivalentRadius;
    if (radius <= 0) return 1;
    return clamp(1 - circleOccultedFlux(radius, Math.hypot(centerX, trajectoryY())), 0, 1);
  }

  function recomputeCircleCurve() {
    state.circleCurve = [];
    for (let index = 0; index < CURVE_SAMPLES; index += 1) {
      const phase = index / (CURVE_SAMPLES - 1);
      state.circleCurve.push({ phase, flux: circleFluxAt(trajectoryX(phase)) });
    }
  }

  /*
   * Least-squares fit of a limb-darkened circular transit (p, b) to the
   * model curve, using the exact annulus-method flux. The grid+descent
   * search keeps the residual meaningful even for structures not centered
   * on the star or only partially occulting.
   */
  function fitCircleModel(curve) {
    const samples = 520;
    let best = null;
    const pGrid = [];
    for (let pi = 0; pi <= 24; pi += 1) pGrid.push(0.02 + (0.42 - 0.02) * pi / 24);
    const bGrid = [];
    for (let bi = 0; bi <= 20; bi += 1) bGrid.push(0.95 * bi / 20);

    function sseFor(p, b) {
      let sse = 0;
      const stride = Math.max(1, Math.floor(curve.length / samples));
      for (let i = 0; i < curve.length; i += stride) {
        const point = curve[i];
        const model = circleFluxForFit(trajectoryX(point.phase), b, p);
        sse += (point.flux - model) ** 2;
      }
      return sse;
    }

    for (const p of pGrid) {
      for (const b of bGrid) {
        const sse = sseFor(p, b);
        if (!best || sse < best.sse) best = { p, b, sse };
      }
    }

    /* coordinate descent refinement */
    const dp = 0.02 / 24;
    const db = 0.95 / 20;
    for (let pass = 0; pass < 2; pass += 1) {
      const stepP = dp / (pass + 1);
      const stepB = db / (pass + 1);
      let improved = true;
      while (improved) {
        improved = false;
        for (const [dP, dB] of [[stepP, 0], [-stepP, 0], [0, stepB], [0, -stepB]]) {
          const np = clamp(best.p + dP, 0.005, 0.6);
          const nb = clamp(best.b + dB, 0, 0.98);
          const sse = sseFor(np, nb);
          if (sse < best.sse - 1e-12) {
            best = { p: np, b: nb, sse };
            improved = true;
          }
        }
      }
    }
    return best;
  }

  /* Same as circleFluxAt but for an arbitrary (p, b) during the fit. */
  function circleFluxForFit(centerX, b, p) {
    return clamp(1 - circleOccultedFlux(p, Math.hypot(centerX, b)), 0, 1);
  }

  /* Gaussian via Box-Muller from the seeded PRNG. */
  function makeGaussian(rand) {
    return function () {
      let u = 0;
      let v = 0;
      while (u === 0) u = rand();
      while (v === 0) v = rand();
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v);
    };
  }

  /*
   * Observed light curve: optional finite exposures (supersampled boxcar
   * averaging of the continuous model) plus Gaussian photon noise in ppm.
   * Repeat mode tiles the single-transit curve at the given period with
   * optional data gaps, drawing one fresh noise realization per epoch.
   */
  function buildObservedCurve() {
    const rand = mulberry32(state.seed);
    const gauss = makeGaussian(rand);
    const sigmaRel = state.noisePpm / 1e6;
    state.observedCurve = [];
    if (!state.finiteExposure && state.noisePpm === 0) {
      for (const point of state.curve) {
        state.observedCurve.push({ phase: point.phase, flux: point.flux });
      }
      return;
    }
    const exposurePhase = state.cadenceSec / 86400 / (2 * (1.34 + state.scale * 1.35) / state.speed / 1.0);
    const nSub = SUPER_FACTOR;
    for (const point of state.curve) {
      let mean;
      if (state.finiteExposure && exposurePhase > 0) {
        let sum = 0;
        for (let sub = 0; sub < nSub; sub += 1) {
          const t = point.phase + ((sub + 0.5) / nSub - 0.5) * exposurePhase;
          const idx = (t * (state.curve.length - 1));
          const i0 = clamp(Math.floor(idx), 0, state.curve.length - 1);
          const i1 = clamp(i0 + 1, 0, state.curve.length - 1);
          const frac = idx - Math.floor(idx);
          sum += lerp(state.curve[i0].flux, state.curve[i1].flux, frac);
        }
        mean = sum / nSub;
      } else {
        mean = point.flux;
      }
      state.observedCurve.push({ phase: point.phase, flux: mean * (1 + gauss() * sigmaRel) });
    }
  }

  /* Epoch timing: transit n is centered at epochOffset + n * periodDays. */
  function repeatEpochs(spanDays) {
    const first = Math.floor(-state.epochOffset / state.periodDays);
    const last = Math.ceil((spanDays - state.epochOffset) / state.periodDays);
    const epochs = [];
    for (let n = first; n <= last; n += 1) {
      const center = state.epochOffset + n * state.periodDays;
      if (center < -transitDurationDays() / 2 || center > spanDays + transitDurationDays()) continue;
      epochs.push(center);
    }
    return epochs;
  }

  /* Data-gap windows [start, end) per gap style, in days from t0. */
  function dataGaps(spanDays) {
    const gaps = [];
    if (state.gapStyle === "tess") {
      for (let orbit = 1; orbit * 13.7 < spanDays; orbit += 1) {
        gaps.push([orbit * 13.7, orbit * 13.7 + 1.0]);
      }
    } else if (state.gapStyle === "kepler") {
      for (let month = 1; month * 30 < spanDays; month += 1) {
        gaps.push([month * 30, month * 30 + 3.0]);
      }
    }
    return gaps;
  }

  function recomputeCurve() {
    rebuildMask();
    state.curve = [];
    let minFlux = 1;
    for (let index = 0; index < CURVE_SAMPLES; index += 1) {
      const phase = index / (CURVE_SAMPLES - 1);
      const centerX = trajectoryX(phase);
      const flux = fluxAt(centerX);
      state.curve.push({ phase, flux });
      minFlux = Math.min(minFlux, flux);
    }

    state.depthPpt = Math.max(0, (1 - minFlux) * 1000);
    state.fit = fitCircleModel(state.curve);
    recomputeCircleCurve();
    state.residuals = state.circleCurve.map((point, index) => ({
      phase: point.phase,
      value: point.flux - (state.curve[index]?.flux ?? point.flux)
    }));
    state.rmsPpt = Math.sqrt(
      state.residuals.reduce((sum, point) => sum + point.value * point.value, 0)
      / Math.max(1, state.residuals.length)
    ) * 1000;

    buildObservedCurve();
    state.dirty = false;
    updateReadouts();
  }

  function canvasSize(canvas) {
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(320, rect.width);
    const height = Math.max(260, rect.height);
    const pixelWidth = Math.floor(width * dpr);
    const pixelHeight = Math.floor(height * dpr);
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }

  function stageGeometry(width, height) {
    const starRadius = Math.min(width * 0.24, height * 0.31);
    return {
      starX: width * 0.5,
      starY: height * 0.45,
      starRadius,
      curveY: height * 0.84
    };
  }

  function customEditorRadius(geom) {
    return geom.starRadius * 0.86;
  }

  function shapePath(ctx) {
    for (const boundary of state.boundaries) {
      if (boundary.length < 3) continue;
      ctx.moveTo(boundary[0].x, boundary[0].y);
      for (let index = 1; index < boundary.length; index += 1) {
        ctx.lineTo(boundary[index].x, boundary[index].y);
      }
      ctx.closePath();
    }
  }

  function drawStar(ctx, x, y, radius) {
    const glow = ctx.createRadialGradient(x - radius * 0.28, y - radius * 0.28, 0, x, y, radius * 1.24);
    glow.addColorStop(0, "#fff7b5");
    glow.addColorStop(0.34, "#f3cc55");
    glow.addColorStop(0.72, "#9b563b");
    glow.addColorStop(1, "rgba(155,86,59,0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(x, y, radius * 1.12, 0, TAU);
    ctx.fill();

    const disk = ctx.createRadialGradient(x - radius * 0.32, y - radius * 0.32, 0, x, y, radius);
    disk.addColorStop(0, "#fff9c6");
    disk.addColorStop(0.45, "#e9c85c");
    disk.addColorStop(1, "#7c3d2e");
    ctx.fillStyle = disk;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, TAU);
    ctx.fill();

    ctx.strokeStyle = "rgba(244,240,230,0.2)";
    ctx.lineWidth = 1;
    for (let index = 1; index <= 5; index += 1) {
      const yy = y - radius * 0.74 + index * radius * 0.28;
      ctx.beginPath();
      ctx.ellipse(x, yy, radius * 0.9, radius * 0.08, 0, 0, TAU);
      ctx.stroke();
    }

    if (state.b > 0.02) {
      ctx.setLineDash([6, 6]);
      ctx.strokeStyle = "rgba(97,216,228,0.5)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x - radius * 1.5, y + state.b * radius);
      ctx.lineTo(x + radius * 1.5, y + state.b * radius);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  function drawShape(ctx, centerX, centerY, radius, alpha = 1) {
    if (state.boundaries.length === 0) return;
    ctx.save();
    ctx.translate(centerX, centerY - state.b * radius);
    ctx.scale(radius * state.scale, -radius * state.scale);
    ctx.beginPath();
    shapePath(ctx);
    ctx.fillStyle = `rgba(4, 7, 6, ${0.86 * alpha})`;
    ctx.strokeStyle = `rgba(96, 211, 159, ${0.92 * alpha})`;
    ctx.lineWidth = 0.018 / state.scale;
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawCustomAnchors(ctx, geom) {
    if (state.model !== "custom") return;
    const radius = customEditorRadius(geom);
    ctx.save();
    ctx.fillStyle = "rgba(96,211,159,0.08)";
    ctx.beginPath();
    ctx.arc(geom.starX, geom.starY, radius, 0, TAU);
    ctx.fill();

    ctx.strokeStyle = "rgba(96,211,159,0.38)";
    ctx.setLineDash([5, 7]);
    ctx.beginPath();
    ctx.arc(geom.starX, geom.starY, radius, 0, TAU);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "rgba(233,200,92,0.78)";
    ctx.font = "800 11px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("anchor editor", geom.starX, geom.starY - radius - 14);

    state.customAnchors.forEach((anchor, index) => {
      const x = geom.starX + anchor.x * radius;
      const y = geom.starY - anchor.y * radius;
      ctx.fillStyle = "#e9c85c";
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, TAU);
      ctx.fill();
      ctx.fillStyle = "#0d0f0d";
      ctx.font = "800 9px Inter, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(index + 1), x, y + 0.4);
    });
    ctx.restore();
  }

  function drawStage() {
    if (state.dirty) recomputeCurve();
    const { ctx, width, height } = canvasSize(stageCanvas);
    const geom = stageGeometry(width, height);
    const centerX = geom.starX + trajectoryX(state.phase) * geom.starRadius;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#080908";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "rgba(244,240,230,0.055)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x += 64) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y += 64) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    ctx.strokeStyle = "rgba(244,240,230,0.18)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(geom.starX - geom.starRadius * 1.65, geom.starY);
    ctx.lineTo(geom.starX + geom.starRadius * 1.65, geom.starY);
    ctx.stroke();

    drawStar(ctx, geom.starX, geom.starY, geom.starRadius);
    drawShape(ctx, centerX, geom.starY, geom.starRadius);
    drawCustomAnchors(ctx, geom);

    const currentFlux = observedFluxAtPhase(state.phase);
    ctx.fillStyle = "rgba(244,240,230,0.64)";
    ctx.font = "800 12px Inter, system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("stellar disk", 26, 32);
    ctx.fillText(`flux ${currentFlux.toFixed(5)}`, 26, height - 28);
    ctx.textAlign = "right";
    ctx.fillText("rasterized Bezier occulter", width - 26, 32);

    if (state.model === "custom") {
      ctx.fillStyle = state.customAnchors.length >= 3 ? "#60d39f" : "#e9c85c";
      ctx.font = "900 13px Inter, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        state.customAnchors.length >= 3
          ? "Custom Bezier shape active"
          : "Click here to place at least 3 anchors",
        geom.starX,
        geom.starY + geom.starRadius * 1.34
      );
    }
  }

  function observedFluxAtPhase(phase) {
    if (state.observedCurve.length === 0) return 1;
    const idx = clamp(phase * (state.observedCurve.length - 1), 0, state.observedCurve.length - 1);
    const i0 = Math.floor(idx);
    const i1 = Math.min(state.observedCurve.length - 1, i0 + 1);
    const frac = idx - i0;
    return lerp(state.observedCurve[i0].flux, state.observedCurve[i1].flux, frac);
  }

  function drawCurve() {
    if (state.dirty) recomputeCurve();
    const { ctx, width, height } = canvasSize(curveCanvas);
    const left = 48;
    const right = width - 24;
    const top = 30;
    const mainBottom = height * 0.62;
    const residualTop = height * 0.7;
    const residualBottom = height - 42;
    const fluxMin = Math.max(0.08, 1 - Math.max(0.08, state.depthPpt / 1000 * 1.28));
    const residualMax = Math.max(
      0.002,
      ...state.residuals.map(point => Math.abs(point.value))
    );

    function xFor(phase) {
      return left + phase * (right - left);
    }

    function yFor(flux) {
      return mainBottom - ((flux - fluxMin) / (1 - fluxMin)) * (mainBottom - top);
    }

    function residualYFor(value) {
      const middle = (residualTop + residualBottom) / 2;
      const halfHeight = (residualBottom - residualTop) / 2;
      return middle - (value / residualMax) * halfHeight * 0.86;
    }

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#080908";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "rgba(244,240,230,0.08)";
    ctx.lineWidth = 1;
    for (let index = 0; index <= 5; index += 1) {
      const y = lerp(top, mainBottom, index / 5);
      ctx.beginPath();
      ctx.moveTo(left, y);
      ctx.lineTo(right, y);
      ctx.stroke();
    }
    for (let index = 0; index <= 8; index += 1) {
      const x = lerp(left, right, index / 8);
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, mainBottom);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, residualTop);
      ctx.lineTo(x, residualBottom);
      ctx.stroke();
    }

    ctx.strokeStyle = "rgba(244,240,230,0.32)";
    ctx.beginPath();
    ctx.moveTo(left, yFor(1));
    ctx.lineTo(right, yFor(1));
    ctx.stroke();

    ctx.strokeStyle = "rgba(244,240,230,0.16)";
    ctx.beginPath();
    ctx.moveTo(left, residualTop);
    ctx.lineTo(right, residualTop);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(left, residualBottom);
    ctx.lineTo(right, residualBottom);
    ctx.stroke();

    ctx.strokeStyle = "rgba(233,200,92,0.42)";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(left, residualYFor(0));
    ctx.lineTo(right, residualYFor(0));
    ctx.stroke();

    if (state.compareCircle) {
      ctx.strokeStyle = "rgba(242,116,95,0.72)";
      ctx.setLineDash([7, 6]);
      ctx.lineWidth = 2;
      ctx.beginPath();
      state.circleCurve.forEach((point, index) => {
        const x = xFor(point.phase);
        const y = yFor(point.flux);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.strokeStyle = "#60d39f";
    ctx.lineWidth = 3;
    ctx.beginPath();
    state.curve.forEach((point, index) => {
      const x = xFor(point.phase);
      const y = yFor(point.flux);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    if (state.noisePpm > 0 || state.finiteExposure) {
      ctx.fillStyle = "rgba(244,240,230,0.5)";
      const radius = Math.max(1.2, Math.min(2.6, (right - left) / state.observedCurve.length));
      for (let index = 0; index < state.observedCurve.length; index += Math.max(1, Math.floor(state.observedCurve.length / 140))) {
        const point = state.observedCurve[index];
        ctx.beginPath();
        ctx.arc(xFor(point.phase), yFor(point.flux), radius, 0, TAU);
        ctx.fill();
      }
    }

    const activeIndex = Math.min(state.curve.length - 1, Math.max(0, Math.round(state.phase * (state.curve.length - 1))));
    const active = state.curve[activeIndex] || { phase: 0, flux: 1 };
    ctx.fillStyle = "#f2745f";
    ctx.beginPath();
    ctx.arc(xFor(active.phase), yFor(active.flux), 5, 0, TAU);
    ctx.fill();

    ctx.strokeStyle = "#e9c85c";
    ctx.lineWidth = 2;
    ctx.beginPath();
    state.residuals.forEach((point, index) => {
      const x = xFor(point.phase);
      const y = residualYFor(point.value);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const activeResidual = state.residuals[activeIndex] || { phase: 0, value: 0 };
    ctx.fillStyle = "#e9c85c";
    ctx.beginPath();
    ctx.arc(xFor(activeResidual.phase), residualYFor(activeResidual.value), 4, 0, TAU);
    ctx.fill();

    ctx.fillStyle = "rgba(244,240,230,0.62)";
    ctx.font = "800 12px Inter, system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("relative flux", left, 18);
    ctx.textAlign = "right";
    ctx.fillText("time", right, height - 12);
    ctx.textAlign = "left";
    ctx.fillText("residual: circle - Bezier", left, residualTop - 12);
    ctx.textAlign = "right";
    ctx.fillText(`${(residualMax * 1000).toFixed(1)} ppt`, right, residualTop - 12);
    ctx.fillStyle = "rgba(96,211,159,0.9)";
    ctx.textAlign = "left";
    ctx.fillText("Bezier raster", left, height - 12);
    if (state.compareCircle) {
      ctx.fillStyle = "rgba(242,116,95,0.85)";
      ctx.fillText("fitted circle", left + 112, height - 12);
    }
    ctx.fillStyle = "rgba(233,200,92,0.9)";
    ctx.fillText("residual", left + 250, height - 12);
  }

  function setBoundaries(boundaries) {
    state.boundaries = boundaries.filter(boundary => boundary.length >= 3);
    state.dirty = true;
  }

  function setModel(model, options = {}) {
    state.model = model;
    state.playing = model !== "custom";
    if (model === "random") {
      state.modelName = "Random Bezier";
      const rand = mulberry32(state.seed);
      state.anchors = randomBezierAnchors(12 + Math.floor(rand() * 7), rand);
      setBoundaries([buildBezierBoundary(state.anchors)]);
    } else if (model === "screen") {
      state.modelName = "Thin Bezier Screen";
      state.anchors = presetAnchors("screen");
      setBoundaries([buildBezierBoundary(state.anchors, 0.2)]);
    } else if (model === "fragmented") {
      state.modelName = "Fragmented Mask";
      state.anchors = [];
      setBoundaries(fragmentedBoundaries());
    } else {
      state.modelName = "Custom Anchors";
      state.phase = 0.5;
      setBoundaries(state.customAnchors.length >= 3 ? [buildBezierBoundary(state.customAnchors, 0.24)] : []);
    }
    updateButtons();
    updateReadouts();
    updatePlayButton();
  }

  function updateButtons() {
    root.classList.toggle("custom-mode", state.model === "custom");
    stageCanvas.classList.toggle("is-editable", state.model === "custom");
    if (customGuide) customGuide.hidden = state.model !== "custom";
    modelButtons.forEach(button => {
      const active = button.dataset.shapeModel === state.model;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
    });
  }

  function updatePlayButton() {
    const path = state.playing
      ? "M8 5h3v14H8zM13 5h3v14h-3z"
      : "M8 5v14l11-7z";
    playButton.setAttribute("aria-label", state.playing ? "Pause animation" : "Play animation");
    playButton.setAttribute("title", state.playing ? "Pause animation" : "Play animation");
    playButton.querySelector("path").setAttribute("d", path);
  }

  function updateReadouts() {
    const anchorCount = state.model === "custom" ? state.customAnchors.length : state.anchors.length;
    modelLabel.textContent = state.modelName;
    statsLabel.textContent = `Equivalent Rp/R* ${state.equivalentRadius.toFixed(3)} · u1 ${state.u1.toFixed(2)} · u2 ${state.u2.toFixed(2)} · b ${state.b.toFixed(2)}`;
    anchorLabel.textContent = `Anchors ${anchorCount}`;
    if (customGuideCount) {
      customGuideCount.textContent = state.model !== "custom"
        ? ""
        : anchorCount >= 3
          ? `${anchorCount} anchors ready`
          : `${anchorCount} / 3 anchors`;
    }
    depthLabel.textContent = `Depth ${state.depthPpt.toFixed(1)} ppt`;
    stageTitle.textContent = state.model === "custom"
      ? "Custom anchor shadow across stellar disk"
      : "Raster shadow across stellar disk";

    if (state.dirty || !state.fit) return;
    const durationDays = transitDurationDays();
    const cadenceDays = state.cadenceSec / 86400;
    const nPoints = Math.max(2, Math.round(durationDays / cadenceDays) + 1);
    sumNodes.duration.textContent = `${(durationDays * 24).toFixed(2)} h`;
    sumNodes.cadence.textContent = `${state.cadenceSec / 60} min`;
    sumNodes.points.textContent = String(nPoints);
    sumNodes.depth.textContent = `${state.depthPpt.toFixed(1)} ppt`;
    sumNodes.rp.textContent = state.equivalentRadius.toFixed(4);
    sumNodes.fitRp.textContent = state.fit ? state.fit.p.toFixed(4) : "—";
    sumNodes.fitB.textContent = state.fit ? state.fit.b.toFixed(3) : "—";
    sumNodes.rms.textContent = `${state.rmsPpt.toFixed(2)} ppt`;
  }

  function addCustomAnchor(event) {
    if (state.model !== "custom") return;
    const rect = stageCanvas.getBoundingClientRect();
    const { width, height } = rect;
    const geom = stageGeometry(width, height);
    const radius = customEditorRadius(geom);
    let x = ((event.clientX - rect.left) - geom.starX) / radius;
    let y = -((event.clientY - rect.top) - geom.starY) / radius;
    const distance = Math.hypot(x, y);
    if (distance > 1) {
      x /= distance;
      y /= distance;
    }

    const existingIndex = state.customAnchors.findIndex(anchor => Math.hypot(anchor.x - x, anchor.y - y) < 0.12);
    if (existingIndex >= 0) {
      state.customAnchors.splice(existingIndex, 1);
    } else if (state.customAnchors.length < 32) {
      state.customAnchors.push({ x: clamp(x, -1, 1), y: clamp(y, -1, 1) });
    }

    state.phase = 0.5;
    state.playing = false;
    setBoundaries(state.customAnchors.length >= 3 ? [buildBezierBoundary(state.customAnchors, 0.24)] : []);
    updatePlayButton();
    updateReadouts();
  }

  function serializeProject() {
    return {
      version: 2,
      mission: "tarang",
      quarter: 666,
      model: state.model,
      anchors: state.model === "custom" ? state.customAnchors : state.anchors,
      boundaries: state.boundaries,
      params: {
        scale: state.scale,
        u1: state.u1,
        u2: state.u2,
        b: state.b,
        speed: state.speed,
        noisePpm: state.noisePpm,
        cadenceSec: state.cadenceSec,
        seed: state.seed,
        finiteExposure: state.finiteExposure,
        repeat: state.repeat,
        periodDays: state.periodDays,
        epochOffset: state.epochOffset,
        gapStyle: state.gapStyle
      }
    };
  }

  function downloadText(filename, text, mime = "text/csv") {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 400);
  }

  /* Observed samples on the cadence grid (nearest engine sample, so noise is
   * preserved, not interpolated away). Used for export. In repeat mode, tiles
   * the transit at the period with optional gaps and per-epoch noise. */
  function exportRows() {
    const rows = [];
    const n = state.observedCurve.length;
    const sigma = state.noisePpm / 1e6;

    if (!state.repeat) {
      const durationDays = transitDurationDays();
      const cadenceDays = state.cadenceSec / 86400;
      const nPoints = Math.max(2, Math.min(n, Math.round(durationDays / cadenceDays) + 1));
      for (let index = 0; index < nPoints; index += 1) {
        const phase = nPoints === 1 ? 0.5 : index / (nPoints - 1);
        const nearest = Math.round(phase * (n - 1));
        const observed = state.observedCurve[nearest];
        rows.push({
          time: BJD_OFFSET + phaseToTime(phase),
          flux: observed.flux,
          fluxErr: observed.flux * sigma,
          model: state.curve[nearest].flux,
          epoch: 0
        });
      }
      return rows;
    }

    const rand = mulberry32(state.seed + 1);
    const gauss = makeGaussian(rand);
    const cadenceDays = state.cadenceSec / 86400;
    const T14 = transitDurationDays();
    const spanDays = Number(spanSelect.value);
    const gaps = dataGaps(spanDays);
    const inGap = t => gaps.some(([start, end]) => t >= start && t < end);

    /* Time axis: absolute days; transit k is centered at epochOffset + k*period.
     * Cover from before the first transit to after the last one. */
    const epochs = repeatEpochs(spanDays);
    const t0 = epochs[0] - T14 / 2;
    const tEnd = epochs[epochs.length - 1] + T14 / 2;
    for (let t = t0; t <= tEnd; t += cadenceDays) {
      if (inGap(t)) continue;
      /* Nearest epoch whose transit window contains t; else flux = 1 (OOT). */
      let phase = null;
      let epoch = 0;
      for (let k = 0; k < epochs.length; k += 1) {
        const dt = t - epochs[k];
        if (Math.abs(dt) <= T14 / 2) {
          epoch = k + 1;
          phase = 0.5 + dt / T14;
          break;
        }
      }
      let model = 1;
      if (phase !== null) {
        const nearest = clamp(Math.round(phase * (n - 1)), 0, n - 1);
        model = state.curve[nearest].flux;
      }
      const flux = model * (1 + gauss() * sigma);
      rows.push({
        time: BJD_OFFSET + t,
        flux,
        fluxErr: flux * sigma,
        model,
        epoch
      });
    }
    return rows;
  }

  function buildCsv(rows) {
    const headerLines = [
      "# Bezier Transit Simulator light curve (Project Tarang)",
      `# generated: ${new Date().toISOString()}`,
      `# mission: tarang`,
      `# quarter: 666`,
      `# model: ${state.modelName}`,
      `# structure_scale: ${state.scale.toFixed(4)}`,
      `# rp_over_rstar_geometric: ${state.equivalentRadius.toFixed(6)}`,
      `# rp_over_rstar_fitted_circle: ${state.fit ? state.fit.p.toFixed(6) : "n/a"}`,
      `# impact_parameter_fitted: ${state.fit ? state.fit.b.toFixed(4) : "n/a"}`,
      `# limb_darkening: quadratic u1=${state.u1.toFixed(4)} u2=${state.u2.toFixed(4)}`,
      `# impact_parameter_b: ${state.b.toFixed(4)}`,
      `# data_span_days: ${transitDurationDays().toFixed(6)}  (full chord crossing; photometric T14 is shorter)`,
      `# cadence_sec: ${state.cadenceSec}`,
      `# noise_ppm: ${state.noisePpm}`,
      `# finite_exposure: ${state.finiteExposure ? "true" : "false"}`,
      `# seed: ${state.seed}`,
      `# repeat_transits: ${state.repeat ? "true" : "false"}`,
      state.repeat ? `# period_days: ${state.periodDays}` : null,
      state.repeat ? `# epoch_offset_days: ${state.epochOffset}` : null,
      state.repeat ? `# gap_style: ${state.gapStyle}` : null,
      "# time = absolute BJD (TDB), days; flux normalized to 1.0 out of transit;",
      "# flux_err = 1-sigma relative error; model = noiseless simulated flux.",
      "# epoch = transit number (0 = out of transit); meaningful in repeat mode.",
      "time,flux,flux_err,model,epoch"
    ];
    const lines = rows.map(row =>
      `${row.time.toFixed(7)},${row.flux.toFixed(7)},${row.fluxErr.toFixed(7)},${row.model.toFixed(7)},${row.epoch}`
    );
    const header = headerLines.filter(line => line !== null);
    return `${header.join("\n")}\n${lines.join("\n")}\n`;
  }

  function onDownload() {
    recomputeCurve();
    const rows = exportRows();
    downloadText("bezier_lightcurve.csv", buildCsv(rows));
  }

  function onDownloadJson() {
    downloadText("bezier_project.json", JSON.stringify(serializeProject(), null, 2), "application/json");
  }

  function onImportFile(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(String(reader.result));
        const params = data.params || {};
        if (typeof params.scale === "number") {
          state.scale = clamp(params.scale, 0.45, 1.15);
          scaleInput.value = String(state.scale);
        }
        if (typeof params.u1 === "number") {
          state.u1 = clamp(params.u1, 0, 0.9);
          u1Input.value = String(state.u1);
        }
        if (typeof params.u2 === "number") {
          state.u2 = clamp(params.u2, -0.3, 0.45);
          u2Input.value = String(state.u2);
        }
        if (typeof params.b === "number") {
          state.b = clamp(params.b, 0, 0.95);
          bInput.value = String(state.b);
        }
        if (typeof params.speed === "number") {
          state.speed = clamp(params.speed, 0.35, 1.8);
          speedInput.value = String(state.speed);
        }
        if (typeof params.noisePpm === "number") {
          state.noisePpm = clamp(params.noisePpm, 0, 2000);
          noiseInput.value = String(state.noisePpm);
        }
        if (typeof params.cadenceSec === "number") {
          state.cadenceSec = clamp(params.cadenceSec, 60, 1800);
          cadenceInput.value = String(state.cadenceSec);
        }
        if (typeof params.seed === "number") {
          state.seed = params.seed;
          seedInput.value = String(params.seed);
        }
        if (typeof params.finiteExposure === "boolean") {
          state.finiteExposure = params.finiteExposure;
          exposureInput.checked = params.finiteExposure;
        }
        if (typeof params.repeat === "boolean") {
          state.repeat = params.repeat;
          repeatInput.checked = params.repeat;
        }
        if (typeof params.periodDays === "number" && params.periodDays >= 0.05) {
          state.periodDays = params.periodDays;
          periodInput.value = String(params.periodDays);
        }
        if (typeof params.epochOffset === "number") {
          state.epochOffset = params.epochOffset;
          epochInput.value = String(params.epochOffset);
        }
        if (typeof params.gapStyle === "string") {
          state.gapStyle = params.gapStyle;
          gapSelect.value = params.gapStyle;
        }
        if (data.model === "custom" && Array.isArray(data.anchors)) {
          state.customAnchors = data.anchors
            .filter(a => typeof a.x === "number" && typeof a.y === "number")
            .slice(0, 32);
          setModel("custom");
        } else if (data.model === "random" && Array.isArray(data.anchors) && data.anchors.length >= 3) {
          state.anchors = data.anchors;
          state.modelName = "Random Bezier (imported)";
          setBoundaries([buildBezierBoundary(state.anchors)]);
          updateButtons();
          updateReadouts();
        } else {
          setModel(data.model in { random: 1, screen: 1, fragmented: 1 } ? data.model : "random");
        }
        state.dirty = true;
      } catch (error) {
        console.error("Invalid project file", error);
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  }

  modelButtons.forEach(button => {
    button.addEventListener("click", () => setModel(button.dataset.shapeModel));
  });

  randomButton.addEventListener("click", () => {
    state.seed = Math.floor(Math.random() * 1e9);
    seedInput.value = String(state.seed);
    setModel("random");
    state.playing = true;
    updatePlayButton();
  });

  clearButton.addEventListener("click", () => {
    state.customAnchors = [];
    setModel("custom");
  });

  playButton.addEventListener("click", () => {
    state.playing = !state.playing;
    updatePlayButton();
  });

  scaleInput.addEventListener("input", () => {
    state.scale = Number(scaleInput.value);
    state.dirty = true;
  });

  u1Input.addEventListener("input", () => {
    state.u1 = Number(u1Input.value);
    state.dirty = true;
  });

  u2Input.addEventListener("input", () => {
    state.u2 = Number(u2Input.value);
    state.dirty = true;
  });

  bInput.addEventListener("input", () => {
    state.b = Number(bInput.value);
    state.dirty = true;
  });

  speedInput.addEventListener("input", () => {
    state.speed = Number(speedInput.value);
    state.dirty = true;
  });

  noiseInput.addEventListener("input", () => {
    state.noisePpm = Number(noiseInput.value);
    state.dirty = true;
  });

  cadenceInput.addEventListener("change", () => {
    state.cadenceSec = Number(cadenceInput.value);
    state.dirty = true;
  });

  seedInput.addEventListener("change", () => {
    state.seed = Math.max(0, Math.floor(Number(seedInput.value) || 0));
    if (state.model === "random") setModel("random");
    state.dirty = true;
  });

  exposureInput.addEventListener("change", () => {
    state.finiteExposure = exposureInput.checked;
    state.dirty = true;
  });

  repeatInput.addEventListener("change", () => {
    state.repeat = repeatInput.checked;
    state.dirty = true;
  });

  periodInput.addEventListener("input", () => {
    const value = Number(periodInput.value);
    if (Number.isFinite(value) && value >= 0.05) {
      state.periodDays = value;
      state.dirty = true;
    }
  });

  epochInput.addEventListener("input", () => {
    const value = Number(epochInput.value);
    if (Number.isFinite(value)) {
      state.epochOffset = value;
      state.dirty = true;
    }
  });

  spanSelect.addEventListener("change", () => {
    state.dirty = true;
  });

  gapSelect.addEventListener("change", () => {
    state.gapStyle = gapSelect.value;
    state.dirty = true;
  });

  compareInput.addEventListener("change", () => {
    state.compareCircle = compareInput.checked;
  });

  stageCanvas.addEventListener("pointerdown", addCustomAnchor);

  downloadButton.addEventListener("click", onDownload);
  downloadJsonButton.addEventListener("click", onDownloadJson);
  importButton.addEventListener("click", () => importFileInput.click());
  importFileInput.addEventListener("change", onImportFile);

  let lastTime = performance.now();
  function frame(now) {
    const delta = Math.min(80, now - lastTime);
    lastTime = now;
    if (state.playing) {
      state.phase = (state.phase + (delta / 9500) * state.speed) % 1;
    }
    drawStage();
    drawCurve();
    requestAnimationFrame(frame);
  }

  setModel("random");
  recomputeCurve();
  requestAnimationFrame(frame);
  window.addEventListener("resize", () => {
    drawStage();
    drawCurve();
  });
})();

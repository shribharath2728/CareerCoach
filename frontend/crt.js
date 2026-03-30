/**
 * crt.js — CRT Effect Engine
 * Adds animated film-grain noise canvas and helper methods.
 *
 * Usage:
 *   <script src="crt.js"></script>
 *   const crt = new CRTEffect(document.querySelector('.crt-screen'));
 *   crt.powerOn();
 */

class CRTEffect {
  /**
   * @param {HTMLElement} screenEl  - The element with class `crt-screen`
   * @param {Object}      options
   * @param {number}      options.grainFrameRate  - FPS for noise canvas (default 12 — classic CRT)
   * @param {number}      options.grainIntensity  - 0–255 pixel brightness variance (default 30)
   */
  constructor(screenEl, options = {}) {
    this.screen = screenEl;
    this.grainFrameRate = options.grainFrameRate ?? 12;
    this.grainIntensity = options.grainIntensity ?? 30;

    this._canvas = null;
    this._ctx = null;
    this._rafId = null;
    this._lastTime = 0;

    this._initNoise();
  }

  // ── Private: build the noise canvas ────────────────────────
  _initNoise() {
    this._canvas = document.createElement("canvas");
    this._canvas.classList.add("crt-noise-canvas");
    this.screen.appendChild(this._canvas);

    this._ctx = this._canvas.getContext("2d");
    this._resizeCanvas();

    // Keep canvas size in sync with the element
    this._ro = new ResizeObserver(() => this._resizeCanvas());
    this._ro.observe(this.screen);

    this._startNoise();
  }

  _resizeCanvas() {
    this._canvas.width  = this.screen.offsetWidth;
    this._canvas.height = this.screen.offsetHeight;
  }

  _startNoise() {
    const interval = 1000 / this.grainFrameRate;

    const draw = (timestamp) => {
      this._rafId = requestAnimationFrame(draw);
      if (timestamp - this._lastTime < interval) return;
      this._lastTime = timestamp;
      this._renderGrain();
    };

    this._rafId = requestAnimationFrame(draw);
  }

  _renderGrain() {
    const { width, height } = this._canvas;
    const imageData = this._ctx.createImageData(width, height);
    const data = imageData.data;
    const intensity = this.grainIntensity;

    for (let i = 0; i < data.length; i += 4) {
      const v = (Math.random() * intensity) | 0;
      data[i]     = v;   // R
      data[i + 1] = v;   // G
      data[i + 2] = v;   // B
      data[i + 3] = 255; // A  (opacity controlled by CSS)
    }

    this._ctx.putImageData(imageData, 0, 0);
  }

  // ── Public API ─────────────────────────────────────────────

  /** Trigger the power-on animation */
  powerOn() {
    this.screen.classList.remove("crt-power-off");
    this.screen.classList.add("crt-power-on");
    this.screen.addEventListener(
      "animationend",
      () => this.screen.classList.remove("crt-power-on"),
      { once: true }
    );
  }

  /** Trigger the power-off animation */
  powerOff() {
    this.screen.classList.remove("crt-power-on");
    this.screen.classList.add("crt-power-off");
  }

  /** Stop the noise grain animation and clean up */
  destroy() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._ro) this._ro.disconnect();
    this._canvas?.remove();
  }

  /**
   * Static helper: automatically wire CRT to all elements with [data-crt]
   * Call once after DOM is ready.
   */
  static autoInit() {
    document.querySelectorAll("[data-crt]").forEach((el) => {
      el._crtInstance = new CRTEffect(el);
      if (el.dataset.crtPowerOn !== undefined) {
        el._crtInstance.powerOn();
      }
    });
  }
}

// Auto-initialise on DOM ready if any [data-crt] elements exist
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => CRTEffect.autoInit());
} else {
  CRTEffect.autoInit();
}

// Expose globally
window.CRTEffect = CRTEffect;

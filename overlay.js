(function () {
  'use strict';

  // Avoid duplicate initialization if the script runs multiple times
  if (window.__AUTH_OVERLAY_INITIALIZED__) return;
  window.__AUTH_OVERLAY_INITIALIZED__ = true;

  const DEFAULT_CONFIG = {
    WS_URL: 'wss://your-backend-url/ws',
    RECONNECT_INTERVAL_MS: 5000,
    DEBUG: true, // if true and WS fails, simulate data
    THEME: 'auto', // 'auto' | 'light' | 'dark'
  };

  function getConfig() {
    const userCfg = (window.AUTH_OVERLAY_CONFIG || {});
    return {
      ...DEFAULT_CONFIG,
      ...userCfg,
    };
  }

  const state = {
    ws: null,
    reconnectTimer: null,
    simTimer: null,
    currentPercent: 0,
    targetPercent: 0,
    animRAF: null,
    isConnected: false,
    container: null,
    statusDot: null,
    percentEl: null,
    scoreEl: null,
    emojiEl: null,
    connTextEl: null,
    ringFG: null,
    ringCircumference: 100,
    lastUpdateTs: 0,
  };

  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

  function mountOverlayIfNeeded() {
    const existing = document.getElementById('gh-auth-overlay');
    if (existing) {
      // Update references if needed
      cacheRefs(existing);
      return existing;
    }

    const overlay = createOverlayDOM();
    document.body.appendChild(overlay);
    cacheRefs(overlay);
    applyTheme();
    return overlay;
  }

  function cacheRefs(container) {
    state.container = container;
    state.statusDot = container.querySelector('.gh-status-dot');
    state.percentEl = container.querySelector('.gh-percent');
    state.scoreEl = container.querySelector('.gh-score');
    state.emojiEl = container.querySelector('.gh-emoji');
    state.connTextEl = container.querySelector('.gh-conn');
    state.ringFG = container.querySelector('.gh-ring circle.fg');

    // Calculate proper circumference for smooth animation
    const r = parseFloat(state.ringFG.getAttribute('r')) || 16;
    const C = 2 * Math.PI * r;
    state.ringCircumference = C;
    state.ringFG.setAttribute('stroke-dasharray', String(C));
    state.ringFG.setAttribute('stroke-dashoffset', String(C));
  }

  function createOverlayDOM() {
    const wrap = document.createElement('div');
    wrap.id = 'gh-auth-overlay';
    wrap.className = 'gh-auth-overlay';
    wrap.setAttribute('role', 'status');
    wrap.setAttribute('aria-live', 'polite');
    wrap.style.pointerEvents = 'none';

    wrap.innerHTML = `
      <span class="gh-status-dot disconnected" aria-label="WebSocket disconnected"></span>
      <div class="gh-row">
        <div class="gh-meter">
          <svg class="gh-ring" viewBox="0 0 36 36" aria-hidden="true">
            <circle class="bg" cx="18" cy="18" r="16" fill="none" stroke-width="4"></circle>
            <circle class="fg" cx="18" cy="18" r="16" fill="none" stroke-width="4" stroke-dasharray="100" stroke-dashoffset="100" stroke-linecap="round"></circle>
          </svg>
          <div class="gh-percent">0%</div>
        </div>
        <div class="gh-text">
          <div class="gh-label">Authenticity</div>
          <div class="gh-value"><span class="gh-score">0</span>% <span class="gh-emoji">❌</span></div>
          <div class="gh-conn">Disconnected</div>
        </div>
      </div>
    `;

    return wrap;
  }

  function applyTheme() {
    const cfg = getConfig();
    const root = state.container;
    if (!root) return;

    if (cfg.THEME === 'light') {
      root.style.colorScheme = 'light';
    } else if (cfg.THEME === 'dark') {
      root.style.colorScheme = 'dark';
    } else {
      root.style.colorScheme = 'normal'; // follow system (prefers-color-scheme)
    }
  }

  function setRingColorByScore(score) {
    let color = '#ef4444'; // red
    if (score >= 80) color = '#22c55e'; // green
    else if (score >= 50) color = '#f59e0b'; // amber
    state.container && state.container.style.setProperty('--ring-color', color);
  }

  function emojiForConfidence(conf) {
    if (!conf) return '❌';
    const c = String(conf).toLowerCase();
    if (c === 'high') return '✅';
    if (c === 'medium') return '⚠️';
    return '❌';
  }

  function updateScore(data) {
    const score = clamp(Number(data && data.authenticity), 0, 100) || 0;
    const conf = data && data.confidence;

    state.targetPercent = score;
    setRingColorByScore(score);

    if (state.scoreEl) state.scoreEl.textContent = String(Math.round(score));
    if (state.percentEl) state.percentEl.textContent = `${Math.round(score)}%`;
    if (state.emojiEl) state.emojiEl.textContent = emojiForConfidence(conf) || (score >= 80 ? '✅' : score >= 50 ? '⚠️' : '❌');

    animateRingTo(score);
  }

  function animateRingTo(targetPercent) {
    const fg = state.ringFG;
    if (!fg) return;

    const C = state.ringCircumference;
    const start = state.currentPercent;
    const end = clamp(targetPercent, 0, 100);
    const duration = 300; // ms
    const startTs = performance.now();

    cancelAnimationFrame(state.animRAF);

    function easeInOutQuad(t) {
      return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    function step(now) {
      const t = clamp((now - startTs) / duration, 0, 1);
      const eased = easeInOutQuad(t);
      const val = start + (end - start) * eased;
      const offset = C * (1 - val / 100);
      fg.setAttribute('stroke-dashoffset', String(offset));
      state.currentPercent = val;
      if (t < 1) {
        state.animRAF = requestAnimationFrame(step);
      }
    }

    state.animRAF = requestAnimationFrame(step);
  }

  function updateStatus(connected, reason) {
    state.isConnected = !!connected;
    if (!state.container) return;

    const dot = state.statusDot;
    const connText = state.connTextEl;

    state.container.classList.toggle('reconnecting', !connected && !!reason && reason === 'reconnecting');

    if (connected) {
      dot && dot.classList.remove('disconnected');
      dot && dot.classList.add('connected');
      connText && (connText.textContent = 'Connected');
      if (dot) dot.setAttribute('aria-label', 'WebSocket connected');
    } else {
      dot && dot.classList.remove('connected');
      dot && dot.classList.add('disconnected');
      if (reason === 'reconnecting') {
        connText && (connText.textContent = 'Reconnecting…');
        if (dot) dot.setAttribute('aria-label', 'WebSocket reconnecting');
      } else {
        connText && (connText.textContent = 'Disconnected');
        if (dot) dot.setAttribute('aria-label', 'WebSocket disconnected');
      }
    }
  }

  function connectWebSocket() {
    const cfg = getConfig();

    if (state.ws) {
      try { state.ws.close(); } catch (e) {}
      state.ws = null;
    }

    clearTimeout(state.reconnectTimer);

    let ws;
    try {
      ws = new WebSocket(cfg.WS_URL);
    } catch (e) {
      console.warn('[Overlay] Invalid WebSocket URL or construction failed:', e);
      maybeStartSimulation();
      scheduleReconnect();
      return;
    }

    state.ws = ws;

    ws.onopen = function () {
      debugLog('WebSocket connected');
      updateStatus(true);
      stopSimulation();
    };

    ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        if (typeof data === 'object' && data) {
          updateScore(data);
        }
      } catch (e) {
        debugLog('Invalid JSON message:', event.data);
      }
    };

    ws.onclose = function () {
      debugLog('WebSocket closed');
      updateStatus(false, 'reconnecting');
      maybeStartSimulation();
      scheduleReconnect();
    };

    ws.onerror = function (err) {
      debugLog('WebSocket error', err);
      // Let onclose handle reconnection
    };
  }

  function scheduleReconnect() {
    const cfg = getConfig();
    clearTimeout(state.reconnectTimer);
    state.reconnectTimer = setTimeout(() => {
      connectWebSocket();
    }, cfg.RECONNECT_INTERVAL_MS);
  }

  function debugLog(...args) {
    const cfg = getConfig();
    if (cfg.DEBUG) {
      console.log('[AuthOverlay]', ...args);
    }
  }

  // Simulation in DEBUG mode to aid development/testing
  function maybeStartSimulation() {
    const cfg = getConfig();
    if (!cfg.DEBUG || state.simTimer) return;

    debugLog('Starting simulated data updates');
    let val = Math.floor(Math.random() * 41) + 30; // 30-70
    let dir = 1;

    state.simTimer = setInterval(() => {
      val += dir * (Math.random() * 8);
      if (val >= 98) dir = -1;
      if (val <= 5) dir = 1;
      val = clamp(val, 0, 100);

      const confidence = val >= 80 ? 'high' : val >= 50 ? 'medium' : 'low';
      updateScore({ authenticity: Math.round(val), confidence });
    }, 1200);
  }

  function stopSimulation() {
    if (state.simTimer) {
      clearInterval(state.simTimer);
      state.simTimer = null;
      debugLog('Stopped simulation');
    }
  }

  // Keep the overlay present even if Meet re-renders parts of the DOM
  function installPersistenceObserver() {
    const obs = new MutationObserver(() => {
      // If overlay was removed, re-inject
      if (!document.getElementById('gh-auth-overlay')) {
        mountOverlayIfNeeded();
      }
    });
    obs.observe(document.documentElement || document.body, {
      childList: true,
      subtree: true,
    });
  }

  function init() {
    mountOverlayIfNeeded();
    installPersistenceObserver();
    connectWebSocket();
  }

  function waitForReadyAndInit() {
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      // Give Meet a moment to finish major layout passes
      setTimeout(init, 300);
    } else {
      window.addEventListener('load', () => setTimeout(init, 300), { once: true });
    }
  }

  try {
    waitForReadyAndInit();
  } catch (e) {
    console.error('[AuthOverlay] Failed to initialize:', e);
  }
})();

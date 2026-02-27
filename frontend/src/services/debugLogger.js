/**
 * MEDISYNC DEBUG LOGGER
 * =====================
 * Captures all pipelineStore dispatches, API calls, camera events,
 * and errors into a downloadable log file.
 * 
 * Usage: Import once in main.jsx. View logs via the floating [📋 LOGS] button.
 */

const MAX_ENTRIES = 500;
const logs = [];

const timestamp = () => new Date().toISOString();

const addEntry = (category, action, data = {}) => {
  const entry = {
    ts: timestamp(),
    cat: category,
    action,
    data: typeof data === 'object' ? JSON.stringify(data) : String(data)
  };
  logs.push(entry);
  if (logs.length > MAX_ENTRIES) logs.shift();

  // Also print to console with a prefix for easy filtering
  console.log(`[MLOG][${category}] ${action}`, data);
};

// ── PUBLIC API ──────────────────────────────────────────────────

export const mlog = {
  /** Log a pipelineStore dispatch */
  dispatch: (event, payload) => addEntry('STORE', event, payload),

  /** Log an API call start */
  apiStart: (endpoint, body) => addEntry('API', `→ ${endpoint}`, body),

  /** Log an API response */
  apiEnd: (endpoint, status, body) => addEntry('API', `← ${endpoint} [${status}]`, body),

  /** Log a camera lifecycle event */
  camera: (action, detail) => addEntry('CAMERA', action, detail),

  /** Log a WhatsApp notification event */
  whatsapp: (action, detail) => addEntry('WHATSAPP', action, detail),

  /** Log an error */
  error: (source, err) => addEntry('ERROR', source, { message: err?.message || String(err), stack: err?.stack?.split('\n').slice(0, 3).join(' | ') }),

  /** Log a generic info event */
  info: (action, detail) => addEntry('INFO', action, detail),

  /** Get all logs as a formatted string for download */
  dump: () => {
    const header = `MEDISYNC DEBUG LOG — Exported ${timestamp()}\n${'='.repeat(60)}\n\n`;
    const body = logs.map(e => `[${e.ts}] [${e.cat}] ${e.action}  ${e.data !== '{}' ? e.data : ''}`).join('\n');
    return header + body;
  },

  /** Get raw log array */
  raw: () => [...logs],

  /** Download logs as a .txt file */
  download: () => {
    const blob = new Blob([mlog.dump()], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medisync_debug_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  },

  /** Clear all logs */
  clear: () => { logs.length = 0; addEntry('SYSTEM', 'Logs cleared'); }
};

// ── AUTO-PATCH: Intercept pipelineStore.dispatch ────────────────

export const patchPipelineStore = (store) => {
  const originalDispatch = store.dispatch;
  store.dispatch = (event, payload) => {
    mlog.dispatch(event, payload);
    return originalDispatch(event, payload);
  };
  mlog.info('Logger attached to pipelineStore');
};

// ── AUTO-PATCH: Intercept fetch for API logging ────────────────

export const patchFetch = () => {
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || 'unknown';
    const method = args[1]?.method || 'GET';
    const isLocalAPI = url.includes('localhost:8000');

    if (isLocalAPI) {
      // Log body for JSON requests only
      let bodyPreview = '';
      if (args[1]?.body && typeof args[1].body === 'string') {
        try { bodyPreview = JSON.parse(args[1].body); } catch { bodyPreview = args[1].body.slice(0, 200); }
      } else if (args[1]?.body instanceof FormData) {
        bodyPreview = '[FormData]';
      }
      mlog.apiStart(`${method} ${url}`, bodyPreview);
    }

    try {
      const res = await originalFetch(...args);
      if (isLocalAPI) {
        // Clone response to read body without consuming it
        const cloned = res.clone();
        try {
          const json = await cloned.json();
          mlog.apiEnd(`${method} ${url}`, res.status, json);
        } catch {
          mlog.apiEnd(`${method} ${url}`, res.status, '[non-JSON response]');
        }
      }
      return res;
    } catch (err) {
      if (isLocalAPI) {
        mlog.error(`FETCH ${method} ${url}`, err);
      }
      throw err;
    }
  };
  mlog.info('Fetch interceptor installed');
};

// ── FLOATING LOG VIEWER UI ─────────────────────────────────────

export const mountLogViewer = () => {
  // Create floating button
  const btn = document.createElement('button');
  btn.id = 'mlog-toggle';
  btn.textContent = '📋 LOGS';
  btn.style.cssText = `
    position: fixed; bottom: 12px; right: 12px; z-index: 99999;
    background: #1a1a2e; color: #e0e0e0; border: 1px solid #444;
    padding: 6px 14px; font-family: monospace; font-size: 12px;
    cursor: pointer; border-radius: 4px; opacity: 0.8;
  `;
  btn.onmouseenter = () => btn.style.opacity = '1';
  btn.onmouseleave = () => btn.style.opacity = '0.8';

  // Create log panel
  const panel = document.createElement('div');
  panel.id = 'mlog-panel';
  panel.style.cssText = `
    position: fixed; bottom: 48px; right: 12px; z-index: 99998;
    width: 520px; max-height: 400px; background: #0d0d1a; color: #b0b0b0;
    border: 1px solid #333; border-radius: 6px; display: none;
    font-family: 'Courier New', monospace; font-size: 11px;
    flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  `;

  // Panel header
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 10px; background: #161625; border-bottom: 1px solid #333;
    color: #e0e0e0; font-weight: bold; font-size: 11px;
  `;
  header.innerHTML = '<span>MEDISYNC DEBUG LOG</span>';

  const dlBtn = document.createElement('button');
  dlBtn.textContent = '⬇ DOWNLOAD';
  dlBtn.style.cssText = 'background: #2a2a4a; color: #8f8; border: none; padding: 3px 8px; cursor: pointer; font-family: monospace; font-size: 10px; border-radius: 3px;';
  dlBtn.onclick = () => mlog.download();
  header.appendChild(dlBtn);

  // Log content area
  const content = document.createElement('div');
  content.id = 'mlog-content';
  content.style.cssText = 'flex: 1; overflow-y: auto; padding: 6px 10px; white-space: pre-wrap; word-break: break-all;';

  panel.appendChild(header);
  panel.appendChild(content);

  let isOpen = false;
  let refreshInterval = null;

  const colorMap = {
    STORE: '#7eb8da',
    API: '#c792ea',
    CAMERA: '#f78c6c',
    WHATSAPP: '#82aaff',
    ERROR: '#ff5572',
    INFO: '#c3e88d',
    SYSTEM: '#666'
  };

  const renderLogs = () => {
    const entries = logs.slice(-100); // Show last 100
    content.innerHTML = entries.map(e => {
      const color = colorMap[e.cat] || '#999';
      const dataStr = e.data !== '{}' ? ` ${e.data}` : '';
      const truncData = dataStr.length > 300 ? dataStr.slice(0, 300) + '…' : dataStr;
      return `<span style="color:#555">${e.ts.slice(11, 23)}</span> <span style="color:${color};font-weight:bold">[${e.cat}]</span> ${e.action}<span style="color:#666">${truncData}</span>`;
    }).join('\n');
    content.scrollTop = content.scrollHeight;
  };

  btn.onclick = () => {
    isOpen = !isOpen;
    panel.style.display = isOpen ? 'flex' : 'none';
    if (isOpen) {
      renderLogs();
      refreshInterval = setInterval(renderLogs, 1000);
    } else {
      clearInterval(refreshInterval);
    }
  };

  document.body.appendChild(panel);
  document.body.appendChild(btn);
  mlog.info('Log viewer UI mounted');
};

// ── DEFAULT INIT (call from main.jsx) ──────────────────────────

export const initDebugLogger = (pipelineStore) => {
  patchPipelineStore(pipelineStore);
  patchFetch();
  mountLogViewer();
  mlog.info('MediSync Debug Logger v1.0 initialized');
};

export default mlog;

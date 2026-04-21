/* Bridge to Python backend via pywebview */

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
  }
}

interface PyWebViewAPI {
  get_config(): Promise<Record<string, unknown>>;
  save_config(config: Record<string, unknown>): Promise<void>;
  get_models(): Promise<{ label: string; value: string }[]>;
  get_input_devices(): Promise<string[]>;
  get_metrics(): Promise<Metrics>;
  get_history(query?: string, app_filter?: string): Promise<HistoryEntry[]>;
  get_unique_apps(): Promise<string[]>;
  get_status(): Promise<AppStatus>;
  toggle_pause(): Promise<void>;
  get_personality(): Promise<{ greeting: string }>;
  get_version(): Promise<string>;
  download_model(model_id: string): Promise<{ status: string }>;
  is_onboarding_done(): Promise<boolean>;
  complete_onboarding(config: Record<string, unknown>): Promise<void>;
  reinitialize(): Promise<{ status: string }>;
}

export interface HistoryEntry {
  text: string;
  timestamp: string;
  window: string;
  duration: number;
  words: number;
  audio_file?: string;
}

export interface Metrics {
  total_sessions: number;
  total_words: number;
  total_time_saved_s: number;
  avg_words_per_session: number;
  avg_processing_s: number;
  sessions_today: number;
  words_today: number;
  time_saved_today_s: number;
  streak_days: number;
  words_by_day: Record<string, number>;
}

export interface AppStatus {
  status: string;
  is_recording: boolean;
  is_processing: boolean;
  pending_text: string | null;
  model: string;
  backend: string;
  hotkey: string;
}

/**
 * Wait for pywebview API to be ready.
 * Resolves immediately if already available, otherwise waits for the
 * 'pywebviewready' event (fired by pywebview once the JS bridge is set up).
 */
let _apiReady: Promise<PyWebViewAPI | null> | null = null;
function waitForApi(): Promise<PyWebViewAPI | null> {
  if (!_apiReady) {
    _apiReady = new Promise((resolve) => {
      // Already available
      if (window.pywebview?.api) {
        resolve(window.pywebview.api);
        return;
      }
      // Not in pywebview at all (dev mode)
      if (!window.pywebview) {
        resolve(null);
        return;
      }
      // pywebview exists but api not ready yet — wait for the ready event
      const handler = () => {
        window.removeEventListener("pywebviewready", handler);
        resolve(window.pywebview?.api ?? null);
      };
      window.addEventListener("pywebviewready", handler);
      // Safety timeout: don't wait forever
      setTimeout(() => {
        window.removeEventListener("pywebviewready", handler);
        resolve(window.pywebview?.api ?? null);
      }, 5000);
    });
  }
  return _apiReady;
}

function getApi(): PyWebViewAPI | null {
  return window.pywebview?.api ?? null;
}

/** Generic API call — for methods not individually wrapped */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function callApi(method: string, ...args: unknown[]): Promise<any> {
  const api = getApi() as any;
  if (api && typeof api[method] === "function") {
    return api[method](...args);
  }
  return null;
}

// Async wrappers with fallbacks for development
export async function getConfig(): Promise<Record<string, unknown>> {
  const api = getApi();
  if (api) return api.get_config();
  return { theme: "dark", hotkey: "<f9>", model: null };
}

export async function saveConfig(config: Record<string, unknown>): Promise<void> {
  const api = getApi();
  if (api) await api.save_config(config);
}

export async function getModels(): Promise<{ label: string; value: string }[]> {
  const api = getApi();
  if (api) return api.get_models();
  return [
    { label: "⚡ Parakeet v3 (recomendado)", value: "nemo-parakeet-tdt-0.6b-v3" },
  ];
}

export async function getInputDevices(): Promise<string[]> {
  const api = getApi();
  if (api) return api.get_input_devices();
  return ["(System Default)"];
}

export async function getMetrics(): Promise<Metrics> {
  const api = getApi();
  if (api) return api.get_metrics();
  return {
    total_sessions: 142, total_words: 5929, total_time_saved_s: 7800,
    avg_words_per_session: 42, avg_processing_s: 3.2,
    sessions_today: 12, words_today: 640, time_saved_today_s: 822,
    streak_days: 3, words_by_day: { "2026-03-21": 180, "2026-03-22": 340, "2026-03-23": 640 },
  };
}

export async function getHistory(query = "", appFilter = ""): Promise<HistoryEntry[]> {
  const api = getApi();
  if (api) return api.get_history(query, appFilter);
  // Dev mock data
  const mock: HistoryEntry[] = [
    { text: "Teste de transcrição longa para verificar que o card tem altura suficiente e não fica comprimido em 1 pixel. Esta mensagem deve ser completamente legível.", timestamp: "2026-03-23T08:30:00", window: "VS Code", duration: 5.2, words: 24 },
    { text: "Outro teste mais curto.", timestamp: "2026-03-23T08:25:00", window: "Chrome - Google", duration: 2.1, words: 4 },
    { text: "Configurações do sistema precisam ser verificadas antes do deploy final.", timestamp: "2026-03-23T08:20:00", window: "Discord", duration: 4.8, words: 9 },
    { text: "Não se esqueça das animações que falamos do 21 First Dev que eu te enviei.", timestamp: "2026-03-23T00:47:00", window: "Claude Code", duration: 3.5, words: 15 },
    { text: "Ok, vamos começar essa migração, então, refaça todo o app nessa stack que você está me sugerindo agora.", timestamp: "2026-03-23T00:10:00", window: "Claude Code", duration: 6.1, words: 18 },
  ];
  const q = query.toLowerCase();
  return mock.filter(e =>
    (!q || e.text.toLowerCase().includes(q)) &&
    (!appFilter || e.window.includes(appFilter))
  );
}

export async function getUniqueApps(): Promise<string[]> {
  const api = getApi();
  if (api) return api.get_unique_apps();
  return ["VS Code", "Chrome - Google", "Discord", "Claude Code"];
}

export async function getStatus(): Promise<AppStatus> {
  const api = getApi();
  if (api) return api.get_status();
  return { status: "Ready", is_recording: false, is_processing: false, pending_text: null, model: "none", backend: "detecting...", hotkey: "<f9>" };
}

export async function togglePause(): Promise<void> {
  const api = getApi();
  if (api) await api.toggle_pause();
}

export async function getPersonality(): Promise<{ greeting: string }> {
  const api = getApi();
  if (api) return api.get_personality();
  return { greeting: "Welcome to LeroLero!" };
}

export async function getVersion(): Promise<string> {
  const api = getApi();
  if (api) return api.get_version();
  return "1.0.0";
}

export async function downloadModel(modelId: string): Promise<{ status: string }> {
  const api = getApi();
  if (api) return api.download_model(modelId);
  return { status: "mock" };
}

/**
 * Check if onboarding is done. WAITS for pywebview API to be ready
 * before checking, to avoid race conditions where the API isn't
 * available yet and the fallback incorrectly skips onboarding.
 */
export async function isOnboardingDone(): Promise<boolean> {
  const api = await waitForApi();
  if (api) return api.is_onboarding_done();
  return false; // No API = show onboarding (safe default)
}

export async function completeOnboarding(config: Record<string, unknown>): Promise<void> {
  const api = getApi();
  if (api) await api.complete_onboarding(config);
}

export async function reinitialize(): Promise<{ status: string }> {
  const api = getApi();
  if (api) return api.reinitialize();
  return { status: "mock" };
}

// Event listener system — Python pushes events via evaluate_js
type EventCallback = (data: unknown) => void;
const listeners: Record<string, EventCallback[]> = {};

export function on(event: string, cb: EventCallback): () => void {
  if (!listeners[event]) listeners[event] = [];
  listeners[event].push(cb);
  return () => {
    listeners[event] = listeners[event].filter(f => f !== cb);
  };
}

// Called from Python via evaluate_js("window.__lerolero_event('name', data)")
(window as any).__lerolero_event = (event: string, data: unknown) => {
  (listeners[event] || []).forEach(cb => cb(data));
};

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

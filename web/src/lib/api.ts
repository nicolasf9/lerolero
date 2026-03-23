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
}

export interface HistoryEntry {
  text: string;
  timestamp: string;
  window: string;
  duration: number;
  words: number;
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

function getApi(): PyWebViewAPI | null {
  return window.pywebview?.api ?? null;
}

// Async wrappers with fallbacks for development
export async function getConfig(): Promise<Record<string, unknown>> {
  const api = getApi();
  if (api) return api.get_config();
  return { theme: "dark", hotkey: "<f9>", model: "openai/whisper-small" };
}

export async function saveConfig(config: Record<string, unknown>): Promise<void> {
  const api = getApi();
  if (api) await api.save_config(config);
}

export async function getModels(): Promise<{ label: string; value: string }[]> {
  const api = getApi();
  if (api) return api.get_models();
  return [{ label: "whisper-base", value: "openai/whisper-base" }];
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
    total_sessions: 0, total_words: 0, total_time_saved_s: 0,
    avg_words_per_session: 0, avg_processing_s: 0,
    sessions_today: 0, words_today: 0, time_saved_today_s: 0,
    streak_days: 0, words_by_day: {},
  };
}

export async function getHistory(query = "", appFilter = ""): Promise<HistoryEntry[]> {
  const api = getApi();
  if (api) return api.get_history(query, appFilter);
  return [];
}

export async function getUniqueApps(): Promise<string[]> {
  const api = getApi();
  if (api) return api.get_unique_apps();
  return [];
}

export async function getStatus(): Promise<AppStatus> {
  const api = getApi();
  if (api) return api.get_status();
  return { status: "Ready", is_recording: false, is_processing: false, pending_text: null, model: "whisper-base", backend: "openvino", hotkey: "<f9>" };
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

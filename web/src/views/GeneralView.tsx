import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Filter } from "lucide-react";
import { ChatBubble } from "@/components/ChatBubble";
import { VoiceOrb } from "@/components/ui/siri-voice-orb";
import { getHistory, getMetrics, getUniqueApps, formatDuration, on, type HistoryEntry, type AppStatus, type Metrics } from "@/lib/api";

interface GeneralViewProps {
  status: AppStatus;
}

export function GeneralView({ status }: GeneralViewProps) {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [apps, setApps] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [appFilter, setAppFilter] = useState("");
  const [liveText, setLiveText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadData = useCallback(async () => {
    const [h, m, a] = await Promise.all([
      getHistory(query, appFilter),
      getMetrics(),
      getUniqueApps(),
    ]);
    setEntries(h);
    setMetrics(m);
    setApps(a);
  }, [query, appFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  // Listen for live preview updates
  useEffect(() => {
    const unsub1 = on("preview_update", (data) => {
      setLiveText((data as any)?.text || "");
    });
    const unsub2 = on("recording_done", () => {
      setLiveText("");
      loadData();
    });
    return () => { unsub1(); unsub2(); };
  }, [loadData]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries, liveText]);

  return (
    <div className="h-full flex flex-col">
      {/* Metrics strip + search */}
      <div className="flex items-center gap-3 px-4 py-2 bg-[var(--surface2)] border-b border-[var(--border)]">
        {metrics && (
          <>
            <span className="text-xs font-bold text-[var(--accent)]">
              💬 {metrics.words_today.toLocaleString()} words
            </span>
            <span className="text-xs font-bold text-[var(--green)]">
              ⏱ {formatDuration(metrics.time_saved_today_s)} saved
            </span>
            {metrics.streak_days > 1 && (
              <span className="text-xs font-bold text-[var(--gold)]">
                🔥 {metrics.streak_days}-day streak
              </span>
            )}
          </>
        )}
        <div className="flex-1" />

        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
          <input
            type="text"
            placeholder="Buscar..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-44 h-8 pl-8 pr-3 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] placeholder:text-[var(--muted-dim)] focus:border-[var(--accent)] focus:outline-none transition-colors"
          />
        </div>

        {/* App filter */}
        <div className="relative">
          <Filter size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
          <select
            value={appFilter}
            onChange={(e) => setAppFilter(e.target.value)}
            className="h-8 pl-8 pr-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:border-[var(--accent)] focus:outline-none appearance-none cursor-pointer"
          >
            <option value="">Todos os apps</option>
            {apps.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {/* Voice orb when recording/processing */}
        {(status.is_recording || status.is_processing) && (
          <VoiceOrb
            isRecording={status.is_recording}
            isProcessing={status.is_processing}
          />
        )}

        {entries.length === 0 && !liveText && !status.is_recording && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <span className="text-5xl mb-4">🎙️</span>
            <h2 className="text-xl font-bold text-[var(--text)]">Tudo pronto.</h2>
            <p className="text-sm text-[var(--muted)] mt-2">
              Pressione <kbd className="px-2 py-0.5 rounded bg-[var(--surface2)] text-[var(--accent)] font-mono text-xs">{status.hotkey?.replace(/[<>]/g, "").toUpperCase()}</kbd> e comece a ditar.
            </p>
            <p className="text-xs text-[var(--muted-dim)] mt-3">
              100% offline · sua voz nunca sai do seu computador
            </p>
          </div>
        )}

        {entries.map((entry, i) => (
          <ChatBubble
            key={`${entry.timestamp}-${i}`}
            text={entry.text}
            timestamp={entry.timestamp}
            duration={entry.duration}
            words={entry.words}
            windowTitle={entry.window}
          />
        ))}

        {/* Live bubble during recording */}
        {liveText && (
          <ChatBubble
            text={liveText}
            timestamp=""
            duration={0}
            words={0}
            windowTitle=""
            isLive
          />
        )}
      </div>
    </div>
  );
}

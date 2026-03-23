import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Mic } from "lucide-react";
import { ChatBubble } from "@/components/ChatBubble";
import { VoiceOrb } from "@/components/ui/siri-voice-orb";
import { getHistory, getMetrics, getUniqueApps, formatDuration, on, type HistoryEntry, type AppStatus, type Metrics } from "@/lib/api";

export function GeneralView({ status }: { status: AppStatus }) {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [apps, setApps] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [appFilter, setAppFilter] = useState("");
  const [liveText, setLiveText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadData = useCallback(async () => {
    const [h, m, a] = await Promise.all([getHistory(query, appFilter), getMetrics(), getUniqueApps()]);
    setEntries(h);
    setMetrics(m);
    setApps(a);
  }, [query, appFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    const unsub1 = on("preview_update", (d) => setLiveText((d as any)?.text || ""));
    const unsub2 = on("recording_done", () => { setLiveText(""); loadData(); });
    return () => { unsub1(); unsub2(); };
  }, [loadData]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [entries, liveText]);

  return (
    <div className="h-full flex flex-col">
      {/* Stats + search bar */}
      <div className="flex items-center gap-[var(--sp-4)] px-[var(--sp-5)] py-[var(--sp-3)] border-b"
           style={{ background: "var(--surface2)", borderColor: "var(--border-subtle)" }}>
        {metrics && (
          <div className="flex items-center gap-[var(--sp-4)]">
            <span className="text-[12px] font-semibold" style={{ color: "var(--accent)" }}>
              {metrics.words_today.toLocaleString()} palavras
            </span>
            <span className="text-[12px] font-semibold" style={{ color: "var(--success)" }}>
              {formatDuration(metrics.time_saved_today_s)} salvos
            </span>
            {metrics.streak_days > 1 && (
              <span className="text-[12px] font-semibold" style={{ color: "var(--warning)" }}>
                {metrics.streak_days} dias seguidos
              </span>
            )}
          </div>
        )}

        <div className="flex-1" />

        {/* Glowing search bar — animated-glowing-search inspired */}
        <div className="glow-border rounded-[var(--radius-md)] p-[1px]">
          <div className="relative flex items-center rounded-[calc(var(--radius-md)-1px)]"
               style={{ background: "var(--surface)" }}>
            <Search size={14} className="absolute left-[var(--sp-3)]" style={{ color: "var(--text-tertiary)" }} />
            <input
              type="text" placeholder="Buscar transcrições..."
              value={query} onChange={(e) => setQuery(e.target.value)}
              className="w-[200px] h-[34px] pl-[var(--sp-8)] pr-[var(--sp-3)] text-[12px] bg-transparent outline-none"
              style={{ color: "var(--text)" }}
            />
          </div>
        </div>

        {/* App filter */}
        <select
          value={appFilter} onChange={(e) => setAppFilter(e.target.value)}
          className="h-[34px] pl-[var(--sp-3)] pr-[var(--sp-6)] text-[12px] rounded-[var(--radius-md)] outline-none cursor-pointer appearance-none"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text)" }}
        >
          <option value="">Todos os apps</option>
          {apps.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-[var(--sp-5)] py-[var(--sp-4)] space-y-[var(--sp-2)]">
        {/* Voice orb */}
        {(status.is_recording || status.is_processing) && (
          <VoiceOrb isRecording={status.is_recording} isProcessing={status.is_processing} />
        )}

        {/* Empty state */}
        {entries.length === 0 && !liveText && !status.is_recording && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mb-[var(--sp-4)]"
                 style={{ background: "var(--accent-subtle)" }}>
              <Mic size={28} style={{ color: "var(--accent)" }} />
            </div>
            <h2 className="text-lg font-semibold" style={{ color: "var(--text)" }}>Tudo pronto.</h2>
            <p className="text-[13px] mt-[var(--sp-2)] max-w-[280px]" style={{ color: "var(--text-secondary)" }}>
              Pressione <kbd className="px-1.5 py-0.5 rounded-[var(--radius-sm)] text-[11px] font-mono"
                             style={{ background: "var(--surface2)", color: "var(--accent)" }}>
                {status.hotkey?.replace(/[<>]/g, "").toUpperCase()}
              </kbd> e comece a ditar.
            </p>
            <p className="text-[11px] mt-[var(--sp-4)]" style={{ color: "var(--text-tertiary)" }}>
              100% offline · sua voz nunca sai do seu computador
            </p>
          </div>
        )}

        {/* History entries */}
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

        {/* Live bubble */}
        {liveText && (
          <ChatBubble text={liveText} timestamp="" duration={0} words={0} windowTitle="" isLive />
        )}
      </div>
    </div>
  );
}

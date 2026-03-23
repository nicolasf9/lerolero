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
    setEntries(h); setMetrics(m); setApps(a);
  }, [query, appFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    const u1 = on("preview_update", (d) => setLiveText((d as any)?.text || ""));
    const u2 = on("recording_done", () => { setLiveText(""); loadData(); });
    return () => { u1(); u2(); };
  }, [loadData]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [entries, liveText]);

  return (
    <div className="h-full flex flex-col">
      {/* Stats + Search bar */}
      <div
        className="flex items-center"
        style={{
          padding: "8px 20px",
          gap: 16,
          background: "var(--surface2)",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        {metrics && (
          <div className="flex items-center" style={{ gap: 20 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--accent)" }}>
              💬 {metrics.words_today.toLocaleString()} palavras
            </span>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--success)" }}>
              ⏱ {formatDuration(metrics.time_saved_today_s)} salvos
            </span>
            {metrics.streak_days > 1 && (
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--warning)" }}>
                🔥 {metrics.streak_days} dias seguidos
              </span>
            )}
          </div>
        )}

        <div style={{ flex: 1 }} />

        {/* Glowing search bar */}
        <div className="glow-border" style={{ borderRadius: 10, padding: 1 }}>
          <div
            className="flex items-center"
            style={{ background: "var(--surface)", borderRadius: 9, position: "relative" }}
          >
            <Search size={14} style={{ position: "absolute", left: 10, color: "var(--text-tertiary)" }} />
            <input
              type="text"
              placeholder="Buscar transcrições..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: 220,
                height: 34,
                paddingLeft: 32,
                paddingRight: 12,
                fontSize: 12,
                background: "transparent",
                color: "var(--text)",
                border: "none",
                outline: "none",
              }}
            />
          </div>
        </div>

        {/* App filter */}
        <select
          value={appFilter}
          onChange={(e) => setAppFilter(e.target.value)}
          style={{
            height: 34,
            padding: "0 12px",
            fontSize: 12,
            borderRadius: 10,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            outline: "none",
            cursor: "pointer",
            minWidth: 120,
          }}
        >
          <option value="">Todos os apps</option>
          {apps.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Chat area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 8 }}
      >
        {(status.is_recording || status.is_processing) && (
          <VoiceOrb isRecording={status.is_recording} isProcessing={status.is_processing} />
        )}

        {entries.length === 0 && !liveText && !status.is_recording && (
          <div className="flex-1 flex flex-col items-center justify-center" style={{ textAlign: "center" }}>
            <div
              style={{
                width: 72, height: 72, borderRadius: "50%",
                background: "var(--accent-subtle)",
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 16,
              }}
            >
              <Mic size={32} style={{ color: "var(--accent)" }} />
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "var(--text)" }}>Tudo pronto.</h2>
            <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 8, maxWidth: 300 }}>
              Pressione{" "}
              <kbd style={{
                padding: "2px 8px", borderRadius: 6, fontSize: 12, fontFamily: "monospace",
                background: "var(--surface2)", color: "var(--accent)",
              }}>
                {status.hotkey?.replace(/[<>]/g, "").toUpperCase()}
              </kbd>{" "}
              e comece a ditar.
            </p>
            <p style={{ fontSize: 11, color: "var(--text-tertiary)", marginTop: 16 }}>
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

        {liveText && (
          <ChatBubble text={liveText} timestamp="" duration={0} words={0} windowTitle="" isLive />
        )}
      </div>
    </div>
  );
}

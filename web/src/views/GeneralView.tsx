import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Mic } from "lucide-react";
import { ChatBubble } from "@/components/ChatBubble";
import { VoiceOrb } from "@/components/ui/siri-voice-orb";
import { getHistory, getMetrics, getUniqueApps, formatDuration, on, type HistoryEntry, type AppStatus, type Metrics } from "@/lib/api";
import { motion } from "framer-motion";

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
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [entries, liveText]);

  const reversed = [...entries].reverse();

  return (
    <div className="h-full flex flex-col">
      {/* Stats + Search */}
      <div
        className="flex items-center"
        style={{
          padding: "10px 20px",
          gap: 14,
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        {metrics && (
          <div className="flex items-center" style={{ gap: 16 }}>
            <Stat label="palavras" value={metrics.words_today.toLocaleString()} color="var(--accent)" />
            <Stat label="salvos" value={formatDuration(metrics.time_saved_today_s)} color="var(--success)" />
            {metrics.streak_days > 1 && (
              <Stat label="dias" value={String(metrics.streak_days)} color="var(--warning)" />
            )}
          </div>
        )}

        <div style={{ flex: 1 }} />

        {/* Search */}
        <div className="glow-border" style={{ borderRadius: "var(--radius-md)", padding: 1 }}>
          <div className="flex items-center" style={{ background: "var(--surface)", borderRadius: 7, position: "relative" }}>
            <Search size={13} style={{ position: "absolute", left: 10, color: "var(--text-disabled)" }} />
            <input
              type="text"
              placeholder="Buscar..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: 180,
                height: 32,
                paddingLeft: 30,
                paddingRight: 10,
                fontSize: 12,
                fontFamily: "var(--font-body)",
                background: "transparent",
                color: "var(--text)",
                border: "none",
                outline: "none",
              }}
            />
          </div>
        </div>

        <select
          value={appFilter}
          onChange={(e) => setAppFilter(e.target.value)}
          style={{
            height: 32,
            padding: "0 10px",
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            borderRadius: "var(--radius-md)",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
            outline: "none",
            cursor: "pointer",
          }}
        >
          <option value="">Todos</option>
          {apps.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Chat area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        style={{ padding: "12px 0", display: "flex", flexDirection: "column" }}
      >
        {(status.is_recording || status.is_processing) && (
          <div style={{ padding: "8px 20px" }}>
            <VoiceOrb isRecording={status.is_recording} isProcessing={status.is_processing} />
          </div>
        )}

        {reversed.length === 0 && !liveText && !status.is_recording && (
          <EmptyState hotkey={status.hotkey} />
        )}

        {reversed.map((entry, i) => (
          <motion.div
            key={`${entry.timestamp}-${i}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15, delay: Math.min(i * 0.03, 0.3) }}
          >
            <ChatBubble
              text={entry.text}
              timestamp={entry.timestamp}
              duration={entry.duration}
              words={entry.words}
              windowTitle={entry.window}
              searchQuery={query}
              audioFile={entry.audio_file}
            />
          </motion.div>
        ))}

        {liveText && (
          <ChatBubble text={liveText} timestamp="" duration={0} words={0} windowTitle="" isLive />
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
      <span style={{
        fontFamily: "var(--font-mono)",
        fontSize: 13,
        fontWeight: 700,
        color,
        letterSpacing: "-0.02em",
      }}>
        {value}
      </span>
      <span style={{
        fontSize: 10,
        color: "var(--text-tertiary)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}>
        {label}
      </span>
    </div>
  );
}

function EmptyState({ hotkey }: { hotkey?: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center" style={{ textAlign: "center", padding: 40 }}>
      <div style={{
        width: 64, height: 64,
        borderRadius: "var(--radius-lg)",
        background: "var(--accent-subtle)",
        display: "flex", alignItems: "center", justifyContent: "center",
        marginBottom: 20,
        border: "1px solid var(--accent-glow)",
      }}>
        <Mic size={28} style={{ color: "var(--accent)" }} />
      </div>
      <h2 style={{
        fontFamily: "var(--font-display)",
        fontSize: 24,
        fontWeight: 400,
        color: "var(--text)",
        letterSpacing: "-0.02em",
      }}>
        Tudo pronto.
      </h2>
      <p style={{
        fontFamily: "var(--font-body)",
        fontSize: 14,
        color: "var(--text-secondary)",
        marginTop: 8,
        maxWidth: 280,
        lineHeight: 1.6,
      }}>
        Pressione{" "}
        <kbd style={{
          padding: "2px 8px",
          borderRadius: "var(--radius-sm)",
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          fontWeight: 600,
          background: "var(--surface2)",
          border: "1px solid var(--border)",
          color: "var(--accent)",
        }}>
          {hotkey?.replace(/[<>]/g, "").toUpperCase() || "F9"}
        </kbd>{" "}
        e comece a ditar.
      </p>
      <p style={{
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        color: "var(--text-disabled)",
        marginTop: 24,
        letterSpacing: "0.05em",
        textTransform: "uppercase",
      }}>
        100% offline · sua voz nunca sai do computador
      </p>
    </div>
  );
}

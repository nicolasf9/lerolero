import { useState, useEffect, useRef } from "react";
import { getMetrics, formatDuration, type Metrics } from "@/lib/api";
import { motion } from "framer-motion";

function HoloCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [hovering, setHovering] = useState(false);

  return (
    <motion.div
      ref={ref}
      onMouseMove={(e) => {
        if (!ref.current) return;
        const r = ref.current.getBoundingClientRect();
        setPos({ x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 });
      }}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => { setHovering(false); setPos({ x: 50, y: 50 }); }}
      style={{
        position: "relative",
        borderRadius: 16,
        overflow: "hidden",
        padding: 24,
        cursor: "default",
        background: hovering
          ? `radial-gradient(circle at ${pos.x}% ${pos.y}%, ${accent}18 0%, var(--surface) 60%)`
          : "var(--surface)",
        border: `1px solid ${hovering ? accent + "40" : "var(--border)"}`,
        boxShadow: hovering ? `0 8px 30px ${accent}15` : "var(--shadow-sm)",
        transition: "border-color 0.3s, box-shadow 0.3s, background 0.3s",
      }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {/* Shine line */}
      {hovering && (
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          background: `linear-gradient(${pos.x * 3.6}deg, transparent 40%, ${accent}15 50%, transparent 60%)`,
        }} />
      )}
      <p style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700, color: "var(--text-tertiary)", position: "relative", zIndex: 1 }}>
        {label}
      </p>
      <p style={{ fontSize: 28, fontWeight: 700, marginTop: 4, letterSpacing: "-0.02em", color: accent, position: "relative", zIndex: 1 }}>
        {value}
      </p>
    </motion.div>
  );
}

export function MetricsView() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  useEffect(() => { getMetrics().then(setMetrics); }, []);

  if (!metrics) return (
    <div className="h-full flex items-center justify-center" style={{ color: "var(--text-tertiary)" }}>
      Carregando métricas...
    </div>
  );

  const days = Object.entries(metrics.words_by_day).sort(([a], [b]) => a.localeCompare(b));
  const maxW = Math.max(...days.map(([, w]) => w as number), 1);

  return (
    <div className="h-full overflow-y-auto" style={{ padding: 24 }}>
      {/* Holographic cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <HoloCard label="Tempo Salvo" value={formatDuration(metrics.total_time_saved_s)} accent="var(--success)" />
        <HoloCard label="Total Palavras" value={metrics.total_words.toLocaleString()} accent="var(--accent)" />
        <HoloCard label="Sessões" value={String(metrics.total_sessions)} accent="var(--text-secondary)" />
        <HoloCard label="Vel. Média" value={`${metrics.avg_words_per_session.toFixed(0)} p/sessão`} accent="var(--warning)" />
      </div>

      {/* 7-day chart */}
      <h3 style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700, color: "var(--accent)", marginTop: 24, marginBottom: 12 }}>
        Últimos 7 dias
      </h3>
      <div style={{ borderRadius: 14, padding: 16, background: "var(--surface)", border: "1px solid var(--border)" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {days.map(([day, words]) => (
            <div key={day} style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-tertiary)", width: 44, flexShrink: 0 }}>
                {day.slice(5)}
              </span>
              <div style={{ flex: 1, height: 10, borderRadius: 5, background: "var(--border)", overflow: "hidden" }}>
                <motion.div
                  style={{ height: "100%", borderRadius: 5, background: "var(--accent)" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${((words as number) / maxW) * 100}%` }}
                  transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
                />
              </div>
              <span style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, color: "var(--text)", width: 36, textAlign: "right" }}>
                {words as number}
              </span>
            </div>
          ))}
          {days.length === 0 && (
            <p style={{ fontSize: 13, textAlign: "center", padding: "24px 0", color: "var(--text-tertiary)" }}>
              Nenhum dado ainda.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

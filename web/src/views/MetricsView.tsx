import { useState, useEffect, useRef } from "react";
import { getMetrics, formatDuration, type Metrics } from "@/lib/api";
import { motion } from "framer-motion";

function HoloCard({ label, value, accent, delay = 0 }: { label: string; value: string; accent: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [hovering, setHovering] = useState(false);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      onMouseMove={(e) => {
        if (!ref.current) return;
        const r = ref.current.getBoundingClientRect();
        setPos({ x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 });
      }}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => { setHovering(false); setPos({ x: 50, y: 50 }); }}
      style={{
        position: "relative",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        padding: "20px 22px",
        cursor: "default",
        background: hovering
          ? `radial-gradient(circle at ${pos.x}% ${pos.y}%, ${accent}18 0%, var(--surface) 60%)`
          : "var(--surface)",
        border: `1px solid ${hovering ? accent + "40" : "var(--border)"}`,
        boxShadow: hovering ? `0 6px 24px ${accent}12` : "var(--shadow-sm)",
        transition: "border-color 0.25s, box-shadow 0.25s, background 0.25s",
      }}
      whileHover={{ scale: 1.015 }}
    >
      {hovering && (
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          background: `linear-gradient(${pos.x * 3.6}deg, transparent 42%, ${accent}10 50%, transparent 58%)`,
        }} />
      )}
      <p style={{
        fontFamily: "var(--font-mono)",
        fontSize: 9,
        textTransform: "uppercase",
        letterSpacing: "0.12em",
        fontWeight: 600,
        color: "var(--text-tertiary)",
        position: "relative", zIndex: 1,
      }}>
        {label}
      </p>
      <p style={{
        fontFamily: "var(--font-display)",
        fontSize: 32,
        fontWeight: 400,
        marginTop: 4,
        letterSpacing: "-0.03em",
        color: accent,
        position: "relative", zIndex: 1,
        lineHeight: 1.1,
      }}>
        {value}
      </p>
    </motion.div>
  );
}

export function MetricsView() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  useEffect(() => { getMetrics().then(setMetrics); }, []);

  if (!metrics) return (
    <div className="h-full flex items-center justify-center" style={{
      color: "var(--text-disabled)",
      fontFamily: "var(--font-mono)",
      fontSize: 12,
    }}>
      Carregando...
    </div>
  );

  const days = Object.entries(metrics.words_by_day).sort(([a], [b]) => a.localeCompare(b));
  const maxW = Math.max(...days.map(([, w]) => w as number), 1);

  return (
    <div className="h-full overflow-y-auto" style={{ padding: "20px 24px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <HoloCard label="Tempo Salvo" value={formatDuration(metrics.total_time_saved_s)} accent="var(--success)" delay={0} />
        <HoloCard label="Total Palavras" value={metrics.total_words.toLocaleString()} accent="var(--accent)" delay={0.06} />
        <HoloCard label="Sessões" value={String(metrics.total_sessions)} accent="var(--text-secondary)" delay={0.12} />
        <HoloCard label="Média" value={`${metrics.avg_words_per_session.toFixed(0)} p/s`} accent="var(--warning)" delay={0.18} />
      </div>

      {/* Weekly chart */}
      <h3 style={{
        fontFamily: "var(--font-mono)",
        fontSize: 9,
        textTransform: "uppercase",
        letterSpacing: "0.12em",
        fontWeight: 600,
        color: "var(--text-tertiary)",
        marginTop: 28,
        marginBottom: 12,
      }}>
        Últimos 7 dias
      </h3>

      <div style={{
        borderRadius: "var(--radius-lg)",
        padding: "16px 18px",
        background: "var(--surface)",
        border: "1px solid var(--border)",
      }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {days.map(([day, words], i) => (
            <div key={day} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                color: "var(--text-disabled)",
                width: 40,
                flexShrink: 0,
              }}>
                {day.slice(5)}
              </span>
              <div style={{
                flex: 1, height: 6, borderRadius: 3,
                background: "var(--border-subtle)", overflow: "hidden",
              }}>
                <motion.div
                  style={{ height: "100%", borderRadius: 3, background: "var(--accent)" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${((words as number) / maxW) * 100}%` }}
                  transition={{ duration: 0.5, ease: "easeOut", delay: i * 0.06 }}
                />
              </div>
              <span style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                fontWeight: 600,
                color: "var(--text)",
                width: 32,
                textAlign: "right",
              }}>
                {words as number}
              </span>
            </div>
          ))}
          {days.length === 0 && (
            <p style={{
              fontFamily: "var(--font-body)",
              fontSize: 13,
              textAlign: "center",
              padding: "20px 0",
              color: "var(--text-disabled)",
            }}>
              Nenhum dado ainda.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

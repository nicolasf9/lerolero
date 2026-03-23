import { useState, useEffect, useRef } from "react";
import { getMetrics, formatDuration, type Metrics } from "@/lib/api";
import { motion } from "framer-motion";

/* Holographic Card — mouse-tracking gradient + shine line */
function HoloCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [hovering, setHovering] = useState(false);

  const onMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    setPos({ x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 });
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => { setHovering(false); setPos({ x: 50, y: 50 }); }}
      className="relative rounded-[var(--radius-xl)] overflow-hidden cursor-default"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        boxShadow: hovering ? "var(--shadow-lg)" : "var(--shadow-sm)",
        transition: "box-shadow 0.3s ease",
      }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {/* Holographic gradient overlay */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-300"
        style={{
          background: `radial-gradient(circle at ${pos.x}% ${pos.y}%, ${accent}15 0%, transparent 60%)`,
          opacity: hovering ? 1 : 0,
        }}
      />
      {/* Shine line */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-300"
        style={{
          background: `linear-gradient(${pos.x * 3.6}deg, transparent 40%, ${accent}20 50%, transparent 60%)`,
          opacity: hovering ? 1 : 0,
        }}
      />

      <div className="relative z-10 p-[var(--sp-5)]">
        <p className="text-[10px] uppercase tracking-[0.1em] font-bold" style={{ color: "var(--text-tertiary)" }}>
          {label}
        </p>
        <p className="text-[28px] font-bold mt-[var(--sp-1)] tracking-tight" style={{ color: accent }}>
          {value}
        </p>
      </div>
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
    <div className="h-full overflow-y-auto p-[var(--sp-6)] space-y-[var(--sp-6)]">
      {/* Holographic cards grid */}
      <div className="grid grid-cols-2 gap-[var(--sp-4)]">
        <HoloCard label="Tempo Salvo" value={formatDuration(metrics.total_time_saved_s)} accent="var(--success)" />
        <HoloCard label="Total Palavras" value={metrics.total_words.toLocaleString()} accent="var(--accent)" />
        <HoloCard label="Sessões" value={String(metrics.total_sessions)} accent="var(--text-secondary)" />
        <HoloCard label="Vel. Média" value={`${metrics.avg_words_per_session.toFixed(0)} p/sessão`} accent="var(--warning)" />
      </div>

      {/* 7-day chart */}
      <div>
        <h3 className="text-[11px] uppercase tracking-[0.1em] font-bold mb-[var(--sp-3)]"
            style={{ color: "var(--accent)" }}>
          Últimos 7 dias
        </h3>
        <div className="rounded-[var(--radius-lg)] p-[var(--sp-4)] space-y-[var(--sp-3)]"
             style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
          {days.map(([day, words]) => (
            <div key={day} className="flex items-center gap-[var(--sp-3)]">
              <span className="text-[11px] font-mono w-[44px] shrink-0" style={{ color: "var(--text-tertiary)" }}>
                {day.slice(5)}
              </span>
              <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: "var(--accent)" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${((words as number) / maxW) * 100}%` }}
                  transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
                />
              </div>
              <span className="text-[11px] font-mono font-semibold w-[36px] text-right" style={{ color: "var(--text)" }}>
                {words as number}
              </span>
            </div>
          ))}
          {days.length === 0 && (
            <p className="text-[13px] text-center py-[var(--sp-6)]" style={{ color: "var(--text-tertiary)" }}>
              Nenhum dado ainda.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

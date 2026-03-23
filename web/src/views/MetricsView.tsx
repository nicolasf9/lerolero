import { useState, useEffect, useRef } from "react";
import { getMetrics, formatDuration, type Metrics } from "@/lib/api";

function HoloCard({ label, value, color }: { label: string; value: string; color: string }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setMousePos({ x: 50, y: 50 })}
      className="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 overflow-hidden cursor-default transition-all hover:border-[var(--accent-dim)]/50"
      style={{
        background: `radial-gradient(circle at ${mousePos.x}% ${mousePos.y}%, var(--accent-dim) 0%, transparent 60%), var(--surface)`,
        backgroundBlendMode: "soft-light",
      }}
    >
      {/* Shine line */}
      <div
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          background: `linear-gradient(${mousePos.x * 3.6}deg, transparent 40%, var(--accent) 50%, transparent 60%)`,
        }}
      />
      <p className="text-[10px] uppercase tracking-wider font-bold text-[var(--muted)] relative z-10">
        {label}
      </p>
      <p className="text-2xl font-bold mt-1 relative z-10" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

export function MetricsView() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    getMetrics().then(setMetrics);
  }, []);

  if (!metrics) return null;

  const days = Object.entries(metrics.words_by_day).sort(([a], [b]) => a.localeCompare(b));
  const maxWords = Math.max(...days.map(([, w]) => w), 1);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <HoloCard label="⏱ Tempo Salvo" value={formatDuration(metrics.total_time_saved_s)} color="var(--green)" />
        <HoloCard label="💬 Total Palavras" value={metrics.total_words.toLocaleString()} color="var(--accent)" />
        <HoloCard label="🎯 Sessões" value={String(metrics.total_sessions)} color="var(--muted)" />
        <HoloCard label="⚡ Velocidade Média" value={`${metrics.avg_words_per_session.toFixed(0)} w/sessão`} color="var(--gold)" />
      </div>

      {/* Bar chart */}
      <div>
        <h3 className="text-xs uppercase tracking-wider font-bold text-[var(--accent)] mb-3">
          Últimos 7 dias
        </h3>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
          {days.map(([day, words]) => (
            <div key={day} className="flex items-center gap-3">
              <span className="text-xs font-mono text-[var(--muted)] w-12 shrink-0">
                {day.slice(5)}
              </span>
              <div className="flex-1 h-3 bg-[var(--border)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--accent-dim)] rounded-full transition-all duration-500"
                  style={{ width: `${(words / maxWords) * 100}%` }}
                />
              </div>
              <span className="text-xs font-mono font-bold text-[var(--text)] w-10 text-right">
                {words}
              </span>
            </div>
          ))}
          {days.length === 0 && (
            <p className="text-sm text-[var(--muted)] text-center py-4">
              Nenhum dado ainda. Comece a ditar!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

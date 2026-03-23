import { useState, useRef } from "react";
import { Monitor, Copy, Check } from "lucide-react";

interface ChatBubbleProps {
  text: string;
  timestamp: string;
  duration: number;
  words: number;
  windowTitle: string;
  isLive?: boolean;
}

export function ChatBubble({ text, timestamp, duration, words, windowTitle, isLive }: ChatBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const tsShort = timestamp?.slice(11, 16) || "";
  const dateShort = timestamp?.slice(0, 10) || "";
  const shortWin = windowTitle?.includes(" - ") ? windowTitle.split(" - ")[0].trim() : (windowTitle || "");

  return (
    <div
      ref={ref}
      className="group relative rounded-[var(--radius-lg)] overflow-hidden transition-all duration-200"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border-subtle)",
        boxShadow: isHovered ? "var(--shadow-md)" : "var(--shadow-sm)",
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Spotlight glow — follows cursor */}
      {isHovered && (
        <div
          className="spotlight-glow"
          style={{ left: mousePos.x, top: mousePos.y, opacity: 1 }}
        />
      )}

      {/* Content */}
      <div className="relative z-10 px-[var(--sp-4)] py-[var(--sp-3)]">
        <p className={`text-[13px] leading-[1.6] ${isLive ? "opacity-70" : ""}`}
           style={{ color: "var(--text)" }}>
          {text || "..."}
        </p>

        {/* Metadata row */}
        <div className="flex items-center gap-[var(--sp-2)] mt-[var(--sp-2)] flex-wrap">
          {tsShort && (
            <span className="text-[11px] font-mono" style={{ color: "var(--text-tertiary)" }}>
              {dateShort !== new Date().toISOString().slice(0, 10) ? `${dateShort} ` : ""}{tsShort}
            </span>
          )}
          {duration > 0 && (
            <span className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
              · {duration.toFixed(1)}s
            </span>
          )}
          {words > 0 && (
            <span className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
              · {words} palavras
            </span>
          )}
          {shortWin && (
            <span className="inline-flex items-center gap-1 text-[11px]" style={{ color: "var(--text-tertiary)" }}>
              · <Monitor size={10} strokeWidth={1.5} /> {shortWin}
            </span>
          )}
          <div className="flex-1" />
          <button
            onClick={handleCopy}
            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-[var(--radius-sm)] cursor-pointer"
            style={{ color: "var(--text-tertiary)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface2)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            {copied ? <Check size={13} style={{ color: "var(--success)" }} /> : <Copy size={13} />}
          </button>
        </div>
      </div>
    </div>
  );
}

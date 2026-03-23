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
  const dateStr = timestamp?.slice(0, 10) || "";
  const today = new Date().toISOString().slice(0, 10);
  const shortWin = windowTitle?.includes(" - ") ? windowTitle.split(" - ")[0].trim() : (windowTitle || "");

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        position: "relative",
        borderRadius: 12,
        overflow: "hidden",
        background: isHovered ? "var(--surface2)" : "var(--surface)",
        border: `1px solid ${isHovered ? "var(--accent)" : "var(--border)"}`,
        boxShadow: isHovered
          ? "0 4px 24px rgba(167,139,250,0.12), 0 0 0 1px var(--accent)"
          : "var(--shadow-sm)",
        transition: "all 0.2s ease",
        flexShrink: 0,
      }}
    >
      {/* Spotlight glow — follows cursor */}
      {isHovered && (
        <div
          style={{
            position: "absolute",
            left: mousePos.x,
            top: mousePos.y,
            width: 320,
            height: 320,
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
            background: "radial-gradient(circle, var(--accent-glow) 0%, transparent 65%)",
            pointerEvents: "none",
            zIndex: 0,
            opacity: 0.8,
          }}
        />
      )}

      {/* Content */}
      <div style={{ position: "relative", zIndex: 1, padding: "16px 20px" }}>
        <p style={{
          fontSize: 14,
          lineHeight: 1.7,
          color: "var(--text)",
          opacity: isLive ? 0.6 : 1,
          letterSpacing: "-0.01em",
        }}>
          {text || "..."}
        </p>

        {/* Metadata */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginTop: 10,
          fontSize: 12,
          color: "var(--text-tertiary)",
          flexWrap: "wrap",
        }}>
          {tsShort && (
            <span style={{ fontFamily: "monospace", fontSize: 11 }}>
              {dateStr !== today ? `${dateStr} ` : ""}{tsShort}
            </span>
          )}
          {duration > 0 && (
            <span style={{ color: "var(--accent)", fontWeight: 500 }}>
              {duration.toFixed(1)}s
            </span>
          )}
          {words > 0 && <span>{words} palavras</span>}
          {shortWin && (
            <span style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              padding: "2px 8px",
              borderRadius: 6,
              background: "var(--surface3)",
              fontSize: 11,
            }}>
              <Monitor size={11} strokeWidth={1.5} /> {shortWin}
            </span>
          )}
          <span style={{ flex: 1 }} />
          <button
            onClick={handleCopy}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              border: "none",
              background: isHovered ? "var(--surface3)" : "transparent",
              cursor: "pointer",
              color: "var(--text-tertiary)",
              opacity: isHovered ? 1 : 0,
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
            }}
          >
            {copied ? (
              <><Check size={12} style={{ color: "var(--success)" }} /> Copiado</>
            ) : (
              <><Copy size={12} /> Copiar</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

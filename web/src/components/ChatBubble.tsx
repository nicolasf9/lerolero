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
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--surface)",
        border: `1px solid ${isHovered ? "var(--accent)" : "var(--border-subtle)"}`,
        boxShadow: isHovered ? "0 4px 20px rgba(167,139,250,0.08)" : "var(--shadow-sm)",
        transition: "border-color 0.2s, box-shadow 0.2s",
      }}
    >
      {/* Spotlight glow — follows cursor */}
      {isHovered && (
        <div
          style={{
            position: "absolute",
            left: mousePos.x,
            top: mousePos.y,
            width: 280,
            height: 280,
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
            background: "radial-gradient(circle, var(--accent-glow) 0%, transparent 70%)",
            pointerEvents: "none",
            zIndex: 0,
          }}
        />
      )}

      {/* Content */}
      <div style={{ position: "relative", zIndex: 1, padding: "14px 18px" }}>
        <p style={{
          fontSize: 13,
          lineHeight: 1.65,
          color: "var(--text)",
          opacity: isLive ? 0.65 : 1,
        }}>
          {text || "..."}
        </p>

        {/* Metadata */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginTop: 8,
          fontSize: 11,
          color: "var(--text-tertiary)",
          flexWrap: "wrap",
        }}>
          {tsShort && <span style={{ fontFamily: "monospace" }}>{dateStr !== today ? `${dateStr} ` : ""}{tsShort}</span>}
          {duration > 0 && <span>· {duration.toFixed(1)}s</span>}
          {words > 0 && <span>· {words} palavras</span>}
          {shortWin && (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
              · <Monitor size={10} strokeWidth={1.5} /> {shortWin}
            </span>
          )}
          <span style={{ flex: 1 }} />
          <button
            onClick={handleCopy}
            style={{
              padding: 4,
              borderRadius: 6,
              border: "none",
              background: "transparent",
              cursor: "pointer",
              color: "var(--text-tertiary)",
              opacity: isHovered ? 1 : 0,
              transition: "opacity 0.2s",
            }}
          >
            {copied ? <Check size={13} style={{ color: "var(--success)" }} /> : <Copy size={13} />}
          </button>
        </div>
      </div>
    </div>
  );
}

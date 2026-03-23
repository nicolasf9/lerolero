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
  const [hovering, setHovering] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const tsShort = timestamp?.slice(0, 16).replace("T", " ") || "";
  const shortWin = windowTitle?.includes(" - ") ? windowTitle.split(" - ")[0].trim() : (windowTitle || "");

  return (
    <div
      ref={cardRef}
      className="group relative rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden transition-colors hover:border-[var(--accent-dim)]/40"
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      {/* Spotlight glow */}
      {hovering && (
        <div
          className="absolute pointer-events-none rounded-full w-[200px] h-[200px] -translate-x-1/2 -translate-y-1/2 opacity-10"
          style={{
            left: mousePos.x,
            top: mousePos.y,
            background: `radial-gradient(circle, var(--accent-dim), transparent 70%)`,
          }}
        />
      )}

      <div className="relative z-10 px-4 py-3">
        {/* Text */}
        <p className={`text-sm leading-relaxed text-[var(--text)] ${isLive ? "animate-pulse" : ""}`}>
          {text || "..."}
        </p>

        {/* Meta row */}
        <div className="flex items-center gap-2 mt-2 text-[11px] text-[var(--muted-dim)]">
          {tsShort && <span>{tsShort}</span>}
          {duration > 0 && <><span>·</span><span>{duration.toFixed(1)}s</span></>}
          {words > 0 && <><span>·</span><span>{words} words</span></>}
          {shortWin && (
            <>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Monitor size={11} /> {shortWin}
              </span>
            </>
          )}
          <div className="flex-1" />
          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-[var(--surface2)]"
          >
            {copied ? <Check size={13} className="text-[var(--green)]" /> : <Copy size={13} />}
          </button>
        </div>
      </div>
    </div>
  );
}

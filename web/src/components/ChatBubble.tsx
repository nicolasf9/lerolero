import { useState, useRef, useCallback } from "react";
import { Monitor, Copy, Check, Play, Pause, Volume2 } from "lucide-react";
import { callApi } from "@/lib/api";

interface ChatBubbleProps {
  text: string;
  timestamp: string;
  duration: number;
  words: number;
  windowTitle: string;
  isLive?: boolean;
  searchQuery?: string;
  audioFile?: string;
}

/** Highlight matching text segments */
function HighlightText({ text, query }: { text: string; query: string }) {
  if (!query || query.length < 2) return <>{text}</>;

  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, i) =>
        regex.test(part) ? (
          <mark
            key={i}
            style={{
              background: "var(--accent)",
              color: "#fff",
              borderRadius: 3,
              padding: "1px 3px",
              fontWeight: 600,
            }}
          >
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

/** Mini audio player for recorded audio */
function AudioPlayer({ audioFile }: { audioFile: string }) {
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlay = useCallback(async () => {
    if (playing && audioRef.current) {
      audioRef.current.pause();
      setPlaying(false);
      return;
    }

    if (!audioRef.current) {
      setLoading(true);
      try {
        const dataUri = await callApi("get_audio_base64", audioFile) as string;
        if (!dataUri) {
          setLoading(false);
          return;
        }
        const audio = new Audio(dataUri);
        audio.ontimeupdate = () => {
          if (audio.duration > 0) {
            setProgress((audio.currentTime / audio.duration) * 100);
          }
        };
        audio.onended = () => {
          setPlaying(false);
          setProgress(0);
        };
        audioRef.current = audio;
      } catch {
        setLoading(false);
        return;
      }
      setLoading(false);
    }

    audioRef.current.currentTime = 0;
    audioRef.current.play();
    setPlaying(true);
  }, [audioFile, playing]);

  return (
    <button
      onClick={handlePlay}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "3px 10px",
        borderRadius: 8,
        border: "1px solid var(--border)",
        background: playing ? "var(--accent)" : "var(--surface3)",
        cursor: "pointer",
        color: playing ? "#fff" : "var(--text-tertiary)",
        fontSize: 11,
        transition: "all 0.2s",
        position: "relative",
        overflow: "hidden",
        minWidth: 70,
      }}
    >
      {/* Progress bar background */}
      {playing && (
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: `${progress}%`,
            background: "rgba(255,255,255,0.15)",
            transition: "width 0.1s linear",
          }}
        />
      )}
      <span style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", gap: 4 }}>
        {loading ? (
          <Volume2 size={12} style={{ animation: "pulse 1s infinite" }} />
        ) : playing ? (
          <Pause size={12} />
        ) : (
          <Play size={12} />
        )}
        {playing ? "Pausar" : "Ouvir"}
      </span>
    </button>
  );
}

export function ChatBubble({ text, timestamp, duration, words, windowTitle, isLive, searchQuery, audioFile }: ChatBubbleProps) {
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
          {searchQuery ? <HighlightText text={text || "..."} query={searchQuery} /> : (text || "...")}
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

          {/* Audio player */}
          {audioFile && <AudioPlayer audioFile={audioFile} />}

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

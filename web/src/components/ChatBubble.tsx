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

function HighlightText({ text, query }: { text: string; query: string }) {
  if (!query || query.length < 2) return <>{text}</>;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        regex.test(part) ? (
          <mark key={i} style={{
            background: "var(--accent)",
            color: "var(--bg)",
            borderRadius: 2,
            padding: "1px 4px",
            fontWeight: 600,
          }}>
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

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
        if (!dataUri) { setLoading(false); return; }
        const audio = new Audio(dataUri);
        audio.ontimeupdate = () => {
          if (audio.duration > 0) setProgress((audio.currentTime / audio.duration) * 100);
        };
        audio.onended = () => { setPlaying(false); setProgress(0); };
        audioRef.current = audio;
      } catch { setLoading(false); return; }
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
        borderRadius: "var(--radius-sm)",
        border: "1px solid var(--border)",
        background: playing ? "var(--accent)" : "var(--surface3)",
        cursor: "pointer",
        color: playing ? "var(--bg)" : "var(--text-tertiary)",
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        fontWeight: 500,
        transition: "all 0.15s",
        position: "relative",
        overflow: "hidden",
        minWidth: 64,
      }}
    >
      {playing && (
        <div style={{
          position: "absolute", left: 0, top: 0, bottom: 0,
          width: `${progress}%`,
          background: "rgba(255,255,255,0.15)",
          transition: "width 0.1s linear",
        }} />
      )}
      <span style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", gap: 3 }}>
        {loading ? <Volume2 size={11} /> : playing ? <Pause size={11} /> : <Play size={11} />}
        {playing ? "Parar" : "Ouvir"}
      </span>
    </button>
  );
}

export function ChatBubble({ text, timestamp, duration, words, windowTitle, isLive, searchQuery, audioFile }: ChatBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const tsShort = timestamp?.slice(11, 16) || "";
  const dateStr = timestamp?.slice(0, 10) || "";
  const today = new Date().toISOString().slice(0, 10);
  const shortWin = windowTitle?.includes(" - ") ? windowTitle.split(" - ")[0].trim() : (windowTitle || "");

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        position: "relative",
        padding: "14px 18px",
        background: isHovered ? "var(--surface2)" : "transparent",
        borderLeft: `2px solid ${isLive ? "var(--warning)" : isHovered ? "var(--accent)" : "var(--border-subtle)"}`,
        transition: "all 0.15s ease",
        flexShrink: 0,
      }}
    >
      {/* Text */}
      <p style={{
        fontFamily: "var(--font-body)",
        fontSize: 14,
        lineHeight: 1.7,
        color: "var(--text)",
        opacity: isLive ? 0.5 : 1,
        letterSpacing: "-0.01em",
      }}>
        {searchQuery ? <HighlightText text={text || "..."} query={searchQuery} /> : (text || "...")}
      </p>

      {/* Metadata row */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginTop: 8,
        fontSize: 11,
        color: "var(--text-tertiary)",
        flexWrap: "wrap",
        fontFamily: "var(--font-mono)",
      }}>
        {tsShort && (
          <span>{dateStr !== today ? `${dateStr} ` : ""}{tsShort}</span>
        )}
        {duration > 0 && (
          <span style={{ color: "var(--accent)", fontWeight: 600 }}>
            {duration.toFixed(1)}s
          </span>
        )}
        {words > 0 && <span>{words} pal.</span>}
        {shortWin && (
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 3,
            padding: "1px 6px",
            background: "var(--surface3)",
            borderRadius: "var(--radius-sm)",
            fontSize: 10,
          }}>
            <Monitor size={10} strokeWidth={1.5} /> {shortWin}
          </span>
        )}

        {audioFile && <AudioPlayer audioFile={audioFile} />}

        <span style={{ flex: 1 }} />
        <button
          onClick={handleCopy}
          aria-label="Copiar texto"
          style={{
            padding: "3px 8px",
            borderRadius: "var(--radius-sm)",
            border: "none",
            background: isHovered ? "var(--surface3)" : "transparent",
            cursor: "pointer",
            color: "var(--text-tertiary)",
            opacity: isHovered ? 1 : 0,
            transition: "all 0.15s",
            display: "flex",
            alignItems: "center",
            gap: 3,
            fontFamily: "var(--font-mono)",
            fontSize: 10,
          }}
        >
          {copied ? <><Check size={11} style={{ color: "var(--success)" }} /> ok</> : <><Copy size={11} /> copiar</>}
        </button>
      </div>
    </div>
  );
}

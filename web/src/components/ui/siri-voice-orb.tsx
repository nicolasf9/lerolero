import { motion, AnimatePresence } from "framer-motion";
import { Mic, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

interface VoiceOrbProps {
  isRecording: boolean;
  isProcessing: boolean;
}

export function VoiceOrb({ isRecording, isProcessing }: VoiceOrbProps) {
  const [waveform, setWaveform] = useState<number[]>(Array(24).fill(4));

  // Simulate waveform during recording
  useEffect(() => {
    if (!isRecording) { setWaveform(Array(24).fill(4)); return; }
    const interval = setInterval(() => {
      setWaveform(Array(24).fill(0).map(() => Math.random() * 40 + 4));
    }, 80);
    return () => clearInterval(interval);
  }, [isRecording]);

  if (!isRecording && !isProcessing) return null;

  return (
    <div className="flex flex-col items-center py-[var(--sp-8)]">
      {/* Orb container */}
      <div className="relative w-28 h-28 flex items-center justify-center">
        {/* Background glow */}
        <motion.div
          className="absolute inset-[-20px] rounded-full"
          style={{
            background: isRecording
              ? "radial-gradient(circle, rgba(239,68,68,0.15) 0%, transparent 70%)"
              : "radial-gradient(circle, rgba(245,158,11,0.15) 0%, transparent 70%)",
          }}
          animate={{ scale: isRecording ? [1, 1.15, 1] : [1, 1.08, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Pulse rings — siri-voice-chat inspired */}
        <AnimatePresence>
          {isRecording && (
            <>
              <motion.div
                className="absolute inset-0 rounded-full"
                style={{ border: "2px solid rgba(239,68,68,0.3)" }}
                initial={{ scale: 1, opacity: 0.6 }}
                animate={{ scale: 1.8, opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
              />
              <motion.div
                className="absolute inset-0 rounded-full"
                style={{ border: "2px solid rgba(239,68,68,0.2)" }}
                initial={{ scale: 1, opacity: 0.4 }}
                animate={{ scale: 2.2, opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
              />
            </>
          )}
        </AnimatePresence>

        {/* Main orb */}
        <motion.div
          className="w-24 h-24 rounded-full flex items-center justify-center relative z-10"
          style={{
            background: isRecording
              ? "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"
              : "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
            boxShadow: isRecording
              ? "0 0 30px rgba(239,68,68,0.3)"
              : "0 0 30px rgba(245,158,11,0.3)",
          }}
          animate={{
            scale: isRecording ? [1, 1.04, 1] : [1, 1.06, 1],
          }}
          transition={{ duration: isRecording ? 0.8 : 1.5, repeat: Infinity, ease: "easeInOut" }}
        >
          {isRecording ? (
            <Mic size={32} color="white" strokeWidth={1.5} />
          ) : (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Loader2 size={32} color="white" strokeWidth={1.5} />
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Waveform bars */}
      <div className="flex items-center justify-center gap-[2px] h-12 mt-[var(--sp-4)]">
        {waveform.map((h, i) => (
          <motion.div
            key={i}
            className="w-[3px] rounded-full"
            style={{
              background: isRecording ? "#ef4444" : "#f59e0b",
            }}
            animate={{ height: h, opacity: isRecording ? 0.8 : 0.3 }}
            transition={{ duration: 0.08, ease: "easeOut" }}
          />
        ))}
      </div>

      {/* Status label */}
      <motion.p
        className="mt-[var(--sp-2)] text-[13px] font-medium"
        style={{ color: isRecording ? "#ef4444" : "#f59e0b" }}
        animate={{ opacity: [1, 0.6, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {isRecording ? "Gravando..." : "Processando..."}
      </motion.p>
    </div>
  );
}

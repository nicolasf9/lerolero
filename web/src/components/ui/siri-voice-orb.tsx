import { motion } from "framer-motion";

interface VoiceOrbProps {
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel?: number;
}

export function VoiceOrb({ isRecording, isProcessing, audioLevel = 0 }: VoiceOrbProps) {
  const scale = 1 + audioLevel * 0.3;

  if (!isRecording && !isProcessing) return null;

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="relative">
        {/* Pulse rings */}
        {isRecording && (
          <>
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-red-500/30"
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 2, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-red-500/20"
              initial={{ scale: 1, opacity: 0.4 }}
              animate={{ scale: 2.5, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
            />
          </>
        )}

        {/* Main orb */}
        <motion.div
          className={`w-24 h-24 rounded-full flex items-center justify-center ${
            isRecording
              ? "bg-gradient-to-br from-red-500 to-red-700 shadow-lg shadow-red-500/30"
              : "bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/30"
          }`}
          animate={{
            scale: isRecording ? [scale, scale * 1.05, scale] : [1, 1.1, 1],
          }}
          transition={{ duration: isRecording ? 0.3 : 1.5, repeat: Infinity, ease: "easeInOut" }}
        >
          {isRecording ? (
            <span className="text-3xl">🎙️</span>
          ) : (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="text-2xl"
            >
              ⏳
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Status text */}
      <motion.p
        className={`mt-4 text-sm font-medium ${isRecording ? "text-red-400" : "text-amber-400"}`}
        animate={{ opacity: [1, 0.6, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {isRecording ? "Gravando..." : "Processando..."}
      </motion.p>
    </div>
  );
}

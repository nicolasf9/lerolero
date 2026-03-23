import { motion } from "framer-motion";

export function Preloader({ model }: { model?: string }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-[var(--bg)]">
      {/* Spinner */}
      <motion.div
        className="w-16 h-16 rounded-full border-4 border-[var(--border)] border-t-[var(--accent)]"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      />
      <p className="mt-6 text-base font-semibold text-[var(--text)]">
        Carregando motores de IA...
      </p>
      <p className="mt-2 text-sm font-mono text-[var(--muted)]">
        {model?.split("/").pop() || "whisper"} · detecting GPU...
      </p>
    </div>
  );
}

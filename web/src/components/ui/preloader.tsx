import { motion } from "framer-motion";

export function Preloader({ model }: { model?: string }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center"
         style={{ background: "var(--bg)" }}>
      {/* Animated spinner */}
      <div className="relative w-16 h-16">
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ border: "3px solid var(--border)", borderTopColor: "var(--accent)" }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute inset-2 rounded-full"
          style={{ border: "2px solid transparent", borderTopColor: "var(--accent)", opacity: 0.4 }}
          animate={{ rotate: -360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
        />
      </div>

      <p className="mt-[var(--sp-6)] text-[15px] font-semibold" style={{ color: "var(--text)" }}>
        Carregando motores de IA...
      </p>
      <p className="mt-[var(--sp-2)] text-[12px] font-mono" style={{ color: "var(--text-tertiary)" }}>
        {model?.split("/").pop() || "whisper"} · detectando GPU
      </p>
    </div>
  );
}

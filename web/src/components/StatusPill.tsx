import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  Loading: { bg: "bg-[var(--muted)]", text: "text-[var(--bg)]", label: "Carregando..." },
  Recording: { bg: "bg-red-500", text: "text-white", label: "Gravando..." },
  Processing: { bg: "bg-amber-400", text: "text-amber-950", label: "Pensando..." },
  Ready: { bg: "bg-emerald-400", text: "text-emerald-950", label: "Pronto!" },
  Error: { bg: "bg-red-800", text: "text-white", label: "Erro" },
};

export function StatusPill({ status, isRecording }: { status: string; isRecording: boolean }) {
  const cfg = statusConfig[status] || statusConfig["Ready"];
  return (
    <motion.div
      className={cn("px-4 py-1.5 rounded-full text-xs font-bold", cfg.bg, cfg.text)}
      animate={isRecording ? { scale: [1, 1.05, 1] } : {}}
      transition={isRecording ? { duration: 1, repeat: Infinity } : {}}
    >
      {cfg.label}
    </motion.div>
  );
}

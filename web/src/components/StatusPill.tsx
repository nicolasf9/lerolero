import { motion } from "framer-motion";

const configs: Record<string, { bg: string; text: string; label: string }> = {
  Loading:    { bg: "var(--text-tertiary)", text: "var(--bg)",   label: "Carregando..." },
  Recording:  { bg: "#ef4444",             text: "#fff",         label: "● Gravando" },
  Processing: { bg: "#f59e0b",             text: "#78350f",      label: "Pensando..." },
  Ready:      { bg: "var(--success)",      text: "#042f2e",      label: "Pronto" },
  Error:      { bg: "var(--danger)",       text: "#fff",         label: "Erro" },
};

export function StatusPill({ status, isRecording }: { status: string; isRecording: boolean }) {
  const c = configs[status] || configs.Ready;
  return (
    <motion.span
      className="inline-flex items-center justify-center rounded-full font-semibold tracking-wide whitespace-nowrap"
      style={{
        background: c.bg,
        color: c.text,
        padding: "6px 16px",
        fontSize: 13,
        lineHeight: 1,
        minWidth: 90,
        textAlign: "center",
      }}
      animate={isRecording ? { scale: [1, 1.06, 1] } : {}}
      transition={isRecording ? { duration: 1.2, repeat: Infinity, ease: "easeInOut" } : {}}
    >
      {c.label}
    </motion.span>
  );
}

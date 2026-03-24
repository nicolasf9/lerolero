import { motion } from "framer-motion";

const configs: Record<string, { bg: string; text: string; label: string }> = {
  Loading:    { bg: "var(--text-disabled)", text: "var(--bg)",      label: "..." },
  Recording:  { bg: "var(--danger)",        text: "var(--bg)",      label: "● REC" },
  Processing: { bg: "var(--warning)",       text: "var(--bg)",      label: "Processando" },
  Ready:      { bg: "var(--success)",       text: "var(--bg)",      label: "Pronto" },
  Error:      { bg: "var(--danger)",        text: "var(--bg)",      label: "Erro" },
};

export function StatusPill({ status, isRecording }: { status: string; isRecording: boolean }) {
  const c = configs[status] || configs.Ready;
  return (
    <motion.span
      className="inline-flex items-center justify-center font-semibold whitespace-nowrap"
      style={{
        background: c.bg,
        color: c.text,
        padding: "5px 14px",
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        fontWeight: 600,
        lineHeight: 1,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        borderRadius: "var(--radius-sm)",
      }}
      animate={isRecording ? { scale: [1, 1.05, 1] } : {}}
      transition={isRecording ? { duration: 1, repeat: Infinity, ease: "easeInOut" } : {}}
    >
      {c.label}
    </motion.span>
  );
}

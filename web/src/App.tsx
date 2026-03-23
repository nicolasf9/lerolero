import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./components/Sidebar";
import { GeneralView } from "./views/GeneralView";
import { MetricsView } from "./views/MetricsView";
import { SettingsView } from "./views/SettingsView";
import { AboutView } from "./views/AboutView";
import { Preloader } from "./components/ui/preloader";
import { StatusPill } from "./components/StatusPill";
import { Moon, Sun } from "lucide-react";
import { on, getStatus, type AppStatus } from "./lib/api";

type Tab = "general" | "metrics" | "settings" | "about";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("general");
  // Skip preloader in dev (no pywebview)
  const [loading, setLoading] = useState(!!window.pywebview);
  const [status, setStatus] = useState<AppStatus>({
    status: "Loading", is_recording: false, is_processing: false,
    pending_text: null, model: "...", backend: "detecting...", hotkey: "...",
  });
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  useEffect(() => {
    const u1 = on("status_change", (s) => {
      setStatus(prev => ({ ...prev, ...(s as Partial<AppStatus>) }));
      if ((s as any).status === "Ready" || (s as any).status === "Error") setLoading(false);
    });
    const u2 = on("loading_done", () => setLoading(false));
    getStatus().then(s => {
      setStatus(s);
      if (s.status !== "Loading") setLoading(false);
    });
    const t = setTimeout(() => setLoading(false), 30000);
    return () => { u1(); u2(); clearTimeout(t); };
  }, []);

  return (
    <div className="flex h-full w-full overflow-hidden" style={{ background: "var(--bg)" }}>
      {/* Dotted surface */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          zIndex: -1,
          backgroundImage: "radial-gradient(circle, var(--accent) 0.8px, transparent 0.8px)",
          backgroundSize: "24px 24px",
          opacity: 0.12,
        }}
      />

      <Sidebar activeTab={activeTab} onTabChange={(t) => setActiveTab(t as Tab)} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header
          className="flex items-center shrink-0"
          style={{
            padding: "8px 20px",
            gap: 12,
            background: "var(--surface)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          <StatusPill status={status.status} isRecording={status.is_recording} />
          <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-tertiary)" }}>
            {status.model?.split("/").pop()} · {status.backend} · {status.hotkey}
          </span>
          <div style={{ flex: 1 }} />
          <button
            onClick={useCallback(() => setIsDark(d => !d), [])}
            style={{
              width: 32, height: 32, borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "var(--text-tertiary)", background: "transparent",
              border: "none", cursor: "pointer",
            }}
          >
            {isDark ? <Moon size={15} /> : <Sun size={15} />}
          </button>
        </header>

        {/* Tab content */}
        <main className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.12, ease: "easeOut" }}
              className="absolute inset-0"
            >
              {activeTab === "general" && <GeneralView status={status} />}
              {activeTab === "metrics" && <MetricsView />}
              {activeTab === "settings" && <SettingsView />}
              {activeTab === "about" && <AboutView />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Preloader */}
      <AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
                      className="fixed inset-0 z-50">
            <Preloader model={status.model} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

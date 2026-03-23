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
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<AppStatus>({
    status: "Loading", is_recording: false, is_processing: false,
    pending_text: null, model: "...", backend: "detecting...", hotkey: "...",
  });
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  useEffect(() => {
    const unsub1 = on("status_change", (s) => {
      setStatus(prev => ({ ...prev, ...(s as Partial<AppStatus>) }));
      if ((s as any).status === "Ready" || (s as any).status === "Error") setLoading(false);
    });
    const unsub2 = on("loading_done", () => setLoading(false));
    getStatus().then(s => {
      setStatus(s);
      if (s.status !== "Loading") setLoading(false);
    });
    const timer = setTimeout(() => setLoading(false), 30000);
    return () => { unsub1(); unsub2(); clearTimeout(timer); };
  }, []);

  const toggleTheme = useCallback(() => setIsDark(d => !d), []);

  return (
    <div className="flex h-full overflow-hidden" style={{ background: "var(--bg)" }}>
      {/* Dotted surface background */}
      <div className="dotted-surface fixed inset-0 -z-10 pointer-events-none opacity-40" />

      <Sidebar activeTab={activeTab} onTabChange={(t) => setActiveTab(t as Tab)} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-[var(--sp-3)] px-[var(--sp-4)] py-[var(--sp-2)] border-b"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <StatusPill status={status.status} isRecording={status.is_recording} />
          <span className="text-[11px] font-mono" style={{ color: "var(--text-tertiary)" }}>
            {status.model?.split("/").pop()} · {status.backend} · {status.hotkey}
          </span>
          <div className="flex-1" />
          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-[var(--radius-sm)] flex items-center justify-center transition-colors cursor-pointer"
            style={{ color: "var(--text-tertiary)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface2)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            {isDark ? <Moon size={15} /> : <Sun size={15} />}
          </button>
        </header>

        {/* Tab content with animation */}
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

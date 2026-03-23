import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./components/Sidebar";
import { GeneralView } from "./views/GeneralView";
import { MetricsView } from "./views/MetricsView";
import { SettingsView } from "./views/SettingsView";
import { AboutView } from "./views/AboutView";
import { Preloader } from "./components/ui/preloader";
import { StatusPill } from "./components/StatusPill";
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
      if ((s as any).status === "Ready" || (s as any).status === "Error") {
        setLoading(false);
      }
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
    <div className="flex h-screen overflow-hidden">
      <div className="dotted-bg fixed inset-0 -z-10 pointer-events-none" />

      <Sidebar activeTab={activeTab} onTabChange={(t) => setActiveTab(t as Tab)} />

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] bg-[var(--surface)]">
          <StatusPill status={status.status} isRecording={status.is_recording} />
          <span className="text-xs font-mono text-[var(--muted)]">
            {status.model?.split("/").pop()} · {status.backend} · {status.hotkey}
          </span>
          <div className="flex-1" />
          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--muted)] hover:bg-[var(--surface2)] transition-colors"
          >
            {isDark ? "☽" : "☀"}
          </button>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute inset-0"
            >
              {activeTab === "general" && <GeneralView status={status} />}
              {activeTab === "metrics" && <MetricsView />}
              {activeTab === "settings" && <SettingsView />}
              {activeTab === "about" && <AboutView />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-50"
          >
            <Preloader model={status.model} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

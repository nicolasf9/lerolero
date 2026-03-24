import { motion, AnimatePresence } from "framer-motion";
import { Mic, BarChart3, Settings, Info, Download, ExternalLink } from "lucide-react";
import { useState, useEffect } from "react";
import { callApi } from "@/lib/api";

const tabs = [
  { key: "general", icon: Mic, label: "Geral" },
  { key: "metrics", icon: BarChart3, label: "Métricas" },
  { key: "settings", icon: Settings, label: "Configurações" },
  { key: "about", icon: Info, label: "Sobre" },
];

interface UpdateInfo {
  version?: string;
  current_version?: string;
  up_to_date?: boolean;
  release_url?: string;
  download_url?: string;
  download_size_mb?: number;
}

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const [update, setUpdate] = useState<UpdateInfo | null>(null);
  const [currentVersion, setCurrentVersion] = useState("1.0");
  const [updating, setUpdating] = useState(false);

  // Check for updates on mount (silent, no error if offline)
  useEffect(() => {
    const checkUpdate = async () => {
      try {
        const ver = await callApi("get_version") as string;
        if (ver) setCurrentVersion(ver);
        const result = await callApi("check_update") as UpdateInfo;
        if (result && result.version && !result.up_to_date) {
          setUpdate(result);
        }
      } catch {
        // Offline or no bridge — ignore
      }
    };
    // Delay check by 3s to not slow startup
    const timer = setTimeout(checkUpdate, 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleUpdate = async () => {
    if (!update?.download_url) {
      // Open release page if no download URL
      if (update?.release_url) {
        window.open(update.release_url, "_blank");
      }
      return;
    }
    setUpdating(true);
    try {
      const result = await callApi("apply_update", update.download_url) as { status: string; message?: string };
      if (result?.status === "restarting") {
        // App will restart via batch script
      } else if (result?.status === "manual") {
        window.open(update.release_url || `https://github.com/nicolasf9/lerolero/releases`, "_blank");
      }
    } catch {
      window.open(update.release_url || `https://github.com/nicolasf9/lerolero/releases`, "_blank");
    }
    setUpdating(false);
  };

  return (
    <div
      className="w-[220px] flex flex-col select-none shrink-0"
      style={{ background: "var(--surface)", borderRight: "1px solid var(--border)" }}
    >
      <nav className="flex-1 flex flex-col gap-1 p-3 pt-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          const isHovered = hoveredTab === tab.key;

          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              onMouseEnter={() => setHoveredTab(tab.key)}
              onMouseLeave={() => setHoveredTab(null)}
              className="relative flex items-center gap-3 cursor-pointer"
              style={{
                padding: "10px 14px",
                borderRadius: 0,
                fontSize: "13px",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#fff" : "var(--text-secondary)",
                transition: "color 0.15s",
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active-bg"
                  className="absolute inset-0 overflow-hidden"
                  style={{ borderRadius: 0 }}
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                >
                  <div className="absolute inset-0" style={{ background: "var(--accent)", borderRadius: 0 }} />
                  <motion.div
                    className="absolute"
                    style={{
                      inset: -6,
                      borderRadius: 0,
                      background: "var(--accent)",
                      filter: "blur(14px)",
                    }}
                    animate={{ opacity: [0.15, 0.35, 0.15], scale: [1, 1.03, 1] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                  />
                </motion.div>
              )}

              <AnimatePresence>
                {isHovered && !isActive && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute inset-0"
                    style={{ background: "var(--surface2)", borderRadius: 0 }}
                  />
                )}
              </AnimatePresence>

              <Icon size={17} strokeWidth={2} style={{ position: "relative", zIndex: 10, flexShrink: 0 }} />
              <span style={{ position: "relative", zIndex: 10 }}>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Update banner */}
      <AnimatePresence>
        {update && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            style={{
              margin: "0 12px 8px",
              padding: "10px 12px",
              borderRadius: 8,
              background: "linear-gradient(135deg, var(--accent), #2563eb)",
              cursor: "pointer",
            }}
            onClick={handleUpdate}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
              <Download size={14} color="#fff" />
              <span style={{ fontSize: 12, fontWeight: 600, color: "#fff" }}>
                {updating ? "Atualizando..." : `v${update.version} disponível`}
              </span>
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.7)", display: "flex", alignItems: "center", gap: 4 }}>
              {update.download_size_mb ? (
                <span>{update.download_size_mb} MB</span>
              ) : (
                <span>Clique para atualizar</span>
              )}
              <ExternalLink size={10} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Brand footer */}
      <div
        className="flex items-center gap-2"
        style={{ padding: "12px 16px", borderTop: "1px solid var(--border)" }}
      >
        <img src="/icon.png" alt="" style={{ width: 22, height: 22, borderRadius: 4, flexShrink: 0 }} />
        <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-secondary)" }}>
          LeroLero
        </span>
        <span style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-tertiary)" }}>
          v{currentVersion}
        </span>
      </div>
    </div>
  );
}

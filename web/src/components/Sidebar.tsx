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
        // Offline — ignore
      }
    };
    const timer = setTimeout(checkUpdate, 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleUpdate = async () => {
    if (!update?.download_url) {
      if (update?.release_url) window.open(update.release_url, "_blank");
      return;
    }
    setUpdating(true);
    try {
      const result = await callApi("apply_update", update.download_url) as { status: string };
      if (result?.status !== "restarting") {
        window.open(update.release_url || "https://github.com/nicolasf9/lerolero/releases", "_blank");
      }
    } catch {
      window.open(update.release_url || "https://github.com/nicolasf9/lerolero/releases", "_blank");
    }
    setUpdating(false);
  };

  return (
    <div
      className="flex flex-col select-none shrink-0"
      style={{
        width: 200,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
      }}
    >
      {/* Tabs */}
      <nav className="flex-1 flex flex-col pt-3 pb-2" style={{ gap: 2 }}>
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
              aria-current={isActive ? "page" : undefined}
              className="relative flex items-center cursor-pointer"
              style={{
                padding: "11px 16px",
                gap: 10,
                fontSize: 13,
                fontFamily: "var(--font-body)",
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "var(--accent)" : isHovered ? "var(--text)" : "var(--text-secondary)",
                background: "transparent",
                border: "none",
                transition: "color 0.15s",
                letterSpacing: "-0.01em",
              }}
            >
              {/* Left accent bar */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-indicator"
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 6,
                    bottom: 6,
                    width: 3,
                    background: "var(--accent)",
                    borderRadius: "0 2px 2px 0",
                  }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}

              {/* Hover bg */}
              <AnimatePresence>
                {isHovered && !isActive && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.12 }}
                    className="absolute inset-0"
                    style={{ background: "var(--surface2)" }}
                  />
                )}
              </AnimatePresence>

              <Icon
                size={16}
                strokeWidth={isActive ? 2.2 : 1.8}
                style={{ position: "relative", zIndex: 1, flexShrink: 0 }}
              />
              <span style={{ position: "relative", zIndex: 1 }}>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Update banner */}
      <AnimatePresence>
        {update && (
          <motion.button
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            onClick={handleUpdate}
            style={{
              margin: "0 10px 8px",
              padding: "10px 12px",
              borderRadius: "var(--radius-md)",
              background: "var(--accent)",
              border: "none",
              cursor: "pointer",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
              <Download size={13} color="var(--bg)" />
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--bg)" }}>
                {updating ? "Atualizando..." : `v${update.version}`}
              </span>
            </div>
            <div style={{ fontSize: 10, color: "var(--bg)", opacity: 0.7, display: "flex", alignItems: "center", gap: 3 }}>
              {update.download_size_mb ? `${update.download_size_mb} MB` : "Clique para atualizar"}
              <ExternalLink size={9} />
            </div>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Brand footer */}
      <div
        className="flex items-center gap-2"
        style={{
          padding: "14px 16px",
          borderTop: "1px solid var(--border)",
        }}
      >
        <img src="/icon.png" alt="" style={{ width: 20, height: 20, borderRadius: 3, flexShrink: 0 }} />
        <span style={{
          fontFamily: "var(--font-display)",
          fontSize: 16,
          fontWeight: 400,
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}>
          LeroLero
        </span>
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: 9,
          color: "var(--text-disabled)",
          marginLeft: "auto",
        }}>
          v{currentVersion}
        </span>
      </div>
    </div>
  );
}

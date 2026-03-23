import { motion, AnimatePresence } from "framer-motion";
import { Mic, BarChart3, Settings, Info } from "lucide-react";
import { useState } from "react";

const tabs = [
  { key: "general", icon: Mic, label: "Geral" },
  { key: "metrics", icon: BarChart3, label: "Métricas" },
  { key: "settings", icon: Settings, label: "Configurações" },
  { key: "about", icon: Info, label: "Sobre" },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);

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
                borderRadius: "10px",
                fontSize: "13px",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#fff" : "var(--text-secondary)",
                transition: "color 0.15s",
              }}
            >
              {/* Active indicator with glow — anime-navbar layoutId */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active-bg"
                  className="absolute inset-0 overflow-hidden"
                  style={{ borderRadius: 10 }}
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                >
                  <div className="absolute inset-0" style={{ background: "var(--accent)", borderRadius: 10 }} />
                  <motion.div
                    className="absolute"
                    style={{
                      inset: -6,
                      borderRadius: 16,
                      background: "var(--accent)",
                      filter: "blur(14px)",
                    }}
                    animate={{ opacity: [0.15, 0.35, 0.15], scale: [1, 1.03, 1] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                  />
                </motion.div>
              )}

              {/* Hover background */}
              <AnimatePresence>
                {isHovered && !isActive && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute inset-0"
                    style={{ background: "var(--surface2)", borderRadius: 10 }}
                  />
                )}
              </AnimatePresence>

              <Icon size={17} strokeWidth={2} style={{ position: "relative", zIndex: 10, flexShrink: 0 }} />
              <span style={{ position: "relative", zIndex: 10 }}>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Brand footer */}
      <div
        className="flex items-center gap-2"
        style={{ padding: "12px 16px", borderTop: "1px solid var(--border)" }}
      >
        <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-secondary)" }}>
          LeroLero
        </span>
        <span style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-tertiary)" }}>v1.0</span>
      </div>
    </div>
  );
}

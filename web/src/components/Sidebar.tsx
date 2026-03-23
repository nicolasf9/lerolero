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
    <div className="w-[200px] flex flex-col border-r select-none"
         style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
      {/* Nav items */}
      <nav className="flex-1 p-3 space-y-1">
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
              className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-[13px] font-medium transition-colors cursor-pointer"
              style={{ color: isActive ? "#fff" : "var(--text-secondary)" }}
            >
              {/* Active indicator — anime-navbar layoutId */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-indicator"
                  className="absolute inset-0 rounded-[var(--radius-md)] -z-10 overflow-hidden"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                >
                  <div className="absolute inset-0 rounded-[var(--radius-md)]" style={{ background: "var(--accent)" }} />
                  {/* Pulsing glow like anime-navbar */}
                  <motion.div
                    className="absolute inset-[-4px] rounded-[var(--radius-lg)]"
                    style={{ background: "var(--accent)", filter: "blur(12px)" }}
                    animate={{ opacity: [0.15, 0.3, 0.15], scale: [1, 1.02, 1] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                  />
                </motion.div>
              )}

              {/* Hover bg */}
              <AnimatePresence>
                {isHovered && !isActive && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute inset-0 rounded-[var(--radius-md)] -z-10"
                    style={{ background: "var(--surface2)" }}
                  />
                )}
              </AnimatePresence>

              <Icon size={16} strokeWidth={2} className="relative z-10 shrink-0" />
              <span className="relative z-10">{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Brand */}
      <div className="px-4 py-3 border-t flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
        <img src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'><text y='16' font-size='16'>🎙</text></svg>"
             alt="" width={20} height={20} />
        <span className="text-sm font-bold" style={{ color: "var(--text-secondary)" }}>
          LeroLero
        </span>
        <span className="text-[10px] font-mono" style={{ color: "var(--text-tertiary)" }}>v1.0</span>
      </div>
    </div>
  );
}

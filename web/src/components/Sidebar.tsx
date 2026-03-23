import { motion } from "framer-motion";
import { Mic, BarChart3, Settings, Info } from "lucide-react";
import { cn } from "@/lib/utils";

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
  return (
    <div className="w-[220px] flex flex-col bg-[var(--surface)] border-r border-[var(--border)] select-none">
      <div className="flex-1 py-4 px-2 space-y-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={cn(
                "relative w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors cursor-pointer",
                isActive ? "text-white" : "text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface2)]",
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-xl -z-10 overflow-hidden"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                >
                  <div className="absolute inset-0 bg-[var(--accent-dim)] rounded-xl" />
                  <motion.div
                    className="absolute inset-0 bg-[var(--accent)]/20 rounded-xl"
                    animate={{ opacity: [0.3, 0.6, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  />
                </motion.div>
              )}
              <Icon size={18} strokeWidth={2} className="relative z-10 shrink-0" />
              <span className="relative z-10">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Brand */}
      <div className="px-4 py-4 border-t border-[var(--border)] flex items-center gap-2">
        <span className="text-lg font-bold text-[var(--muted)]" style={{ fontFamily: "'Modak', cursive" }}>
          LeroLero
        </span>
        <span className="text-[10px] font-mono text-[var(--muted-dim)]">v1.0</span>
      </div>
    </div>
  );
}

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Cpu, Mic, Download, Check, ChevronRight, Loader2 } from "lucide-react";
import {
  getModels, getInputDevices, downloadModel, completeOnboarding,
  reinitialize, on,
} from "@/lib/api";

interface OnboardingProps {
  onComplete: () => void;
}

/* ── Step indicators ─────────────────────────────────────── */
function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div style={{ display: "flex", gap: 6, justifyContent: "center", marginTop: 24 }}>
      {Array.from({ length: total }, (_, i) => (
        <div key={i} style={{
          width: i === current ? 20 : 6, height: 6,
          borderRadius: 3,
          background: i === current ? "var(--accent)" : "var(--border)",
          transition: "all 0.2s",
        }} />
      ))}
    </div>
  );
}

/* ── Step 1: Welcome ─────────────────────────────────────── */
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div style={{ textAlign: "center", padding: "40px 32px" }}>
      <h1 style={{ fontSize: 36, fontWeight: 700, color: "var(--text)", letterSpacing: "-0.02em" }}>
        LeroLero
      </h1>
      <p style={{ fontSize: 15, color: "var(--text-secondary)", marginTop: 8 }}>
        Fale e o texto aparece. Simples assim.
      </p>

      <div style={{ display: "flex", justifyContent: "center", gap: 32, marginTop: 40 }}>
        {[
          { icon: Shield, label: "100% Offline", desc: "Nada sai do seu PC", color: "var(--success)" },
          { icon: Cpu, label: "Multi-GPU", desc: "Intel · NVIDIA · AMD", color: "var(--accent)" },
          { icon: Mic, label: "Whisper IA", desc: "Transcrição precisa", color: "var(--warning)" },
        ].map(({ icon: Icon, label, desc, color }) => (
          <div key={label} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: `color-mix(in srgb, ${color} 10%, transparent)`,
            }}>
              <Icon size={22} style={{ color }} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>{label}</span>
            <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>{desc}</span>
          </div>
        ))}
      </div>

      <p style={{ fontSize: 13, color: "var(--accent)", fontStyle: "italic", marginTop: 32 }}>
        Sua voz nunca sai do seu computador.
      </p>

      <button onClick={onNext} style={{
        marginTop: 32, padding: "12px 32px", borderRadius: 8,
        background: "var(--accent)", color: "white", border: "none",
        fontSize: 14, fontWeight: 600, cursor: "pointer",
        display: "inline-flex", alignItems: "center", gap: 6,
      }}>
        Começar <ChevronRight size={16} />
      </button>
    </div>
  );
}

/* ── Step 2: Preferences ─────────────────────────────────── */
function PreferencesStep({ config, setConfig, devices, onNext }: {
  config: Record<string, unknown>;
  setConfig: (c: Record<string, unknown>) => void;
  devices: string[];
  onNext: () => void;
}) {
  const set = (key: string, value: unknown) => setConfig({ ...config, [key]: value });

  return (
    <div style={{ padding: "32px 32px" }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text)", textAlign: "center" }}>
        Personalize
      </h2>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", textAlign: "center", marginTop: 4 }}>
        Ajuste como o LeroLero funciona pra você
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 28 }}>
        <SettingRow label="Microfone">
          <select value={(config.microphone_name as string) || ""} onChange={(e) => set("microphone_name", e.target.value || null)}
            style={selectStyle}>
            {devices.map(d => <option key={d} value={d === "(System Default)" ? "" : d}>{d}</option>)}
          </select>
        </SettingRow>

        <SettingRow label="Modo de gravação">
          <select value={(config.recording_mode as string) || "hold"} onChange={(e) => set("recording_mode", e.target.value)}
            style={selectStyle}>
            <option value="hold">Segurar tecla</option>
            <option value="toggle">Pressionar para alternar</option>
          </select>
        </SettingRow>

        <SettingRow label="Tecla de atalho">
          <input type="text" value={(config.hotkey as string) || "<f8>"}
            onChange={(e) => set("hotkey", e.target.value)}
            style={{ ...selectStyle, width: 100 }} />
        </SettingRow>

        <ToggleRow label="Digitar ao vivo enquanto grava" checked={config.live_typing !== false}
          onChange={(v) => set("live_typing", v)} />

        <ToggleRow label="Salvar gravações de áudio (.wav)" checked={!!config.save_audio}
          onChange={(v) => set("save_audio", v)} />

        <ToggleRow label="Salvar histórico de transcrições" checked={config.save_history !== false}
          onChange={(v) => set("save_history", v)} />
      </div>

      <div style={{ textAlign: "center", marginTop: 28 }}>
        <button onClick={onNext} style={{
          padding: "12px 32px", borderRadius: 8,
          background: "var(--accent)", color: "white", border: "none",
          fontSize: 14, fontWeight: 600, cursor: "pointer",
          display: "inline-flex", alignItems: "center", gap: 6,
        }}>
          Próximo <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

/* ── Step 3: Model Download ──────────────────────────────── */
function ModelStep({ config, setConfig, models, onNext }: {
  config: Record<string, unknown>;
  setConfig: (c: Record<string, unknown>) => void;
  models: { label: string; value: string }[];
  onNext: () => void;
}) {
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState({ message: "", percent: 0 });
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const selectedModel = (config.model as string) || "nemo-parakeet-tdt-0.6b-v3";

  // Show all available models (backend returns Parakeet only now)
  const recommended = models;

  useEffect(() => {
    const u1 = on("model_download_progress", (d: any) => {
      setProgress({ message: d.message, percent: Math.max(0, d.percent) });
    });
    const u2 = on("model_download_done", (d: any) => {
      setDownloading(false);
      if (d.success) {
        setDone(true);
      } else {
        setError(d.error || "Download falhou");
      }
    });
    return () => { u1(); u2(); };
  }, []);

  const handleDownload = async () => {
    setDownloading(true);
    setError("");
    setProgress({ message: "Iniciando download...", percent: 0 });
    await downloadModel(selectedModel);
  };

  return (
    <div style={{ padding: "32px 32px" }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text)", textAlign: "center" }}>
        <Download size={20} style={{ display: "inline", verticalAlign: "middle", marginRight: 8 }} />
        Baixar Modelo de IA
      </h2>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", textAlign: "center", marginTop: 4 }}>
        Escolha um modelo. Modelos maiores são mais precisos, mas mais lentos.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 24 }}>
        {recommended.map(m => (
          <button key={m.value} onClick={() => !downloading && setConfig({ ...config, model: m.value })}
            style={{
              padding: "12px 16px", borderRadius: 8, border: "1.5px solid",
              borderColor: selectedModel === m.value ? "var(--accent)" : "var(--border)",
              background: selectedModel === m.value ? "var(--accent-subtle)" : "var(--surface)",
              color: "var(--text)", fontSize: 13, cursor: downloading ? "default" : "pointer",
              textAlign: "left", display: "flex", alignItems: "center", gap: 10,
            }}>
            <div style={{
              width: 18, height: 18, borderRadius: 9,
              border: `2px solid ${selectedModel === m.value ? "var(--accent)" : "var(--border)"}`,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {selectedModel === m.value && <div style={{ width: 10, height: 10, borderRadius: 5, background: "var(--accent)" }} />}
            </div>
            <span style={{ fontWeight: 500 }}>{m.label}</span>
          </button>
        ))}
      </div>

      {/* Download progress */}
      {downloading && (
        <div style={{ marginTop: 20 }}>
          <div style={{
            height: 6, borderRadius: 3, background: "var(--border)", overflow: "hidden",
          }}>
            <motion.div
              style={{ height: "100%", borderRadius: 3, background: "var(--accent)" }}
              animate={{ width: `${progress.percent}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <p style={{ fontSize: 12, color: "var(--text-tertiary)", marginTop: 6, textAlign: "center" }}>
            {progress.message}
          </p>
        </div>
      )}

      {error && (
        <p style={{ fontSize: 12, color: "var(--error, #ef4444)", marginTop: 12, textAlign: "center" }}>
          {error}
        </p>
      )}

      <div style={{ textAlign: "center", marginTop: 24 }}>
        {!done ? (
          <button onClick={handleDownload} disabled={downloading} style={{
            padding: "12px 32px", borderRadius: 8,
            background: downloading ? "var(--border)" : "var(--accent)",
            color: "white", border: "none",
            fontSize: 14, fontWeight: 600,
            cursor: downloading ? "default" : "pointer",
            display: "inline-flex", alignItems: "center", gap: 6,
          }}>
            {downloading
              ? <><Loader2 size={16} className="animate-spin" /> Baixando...</>
              : <><Download size={16} /> Baixar Modelo</>
            }
          </button>
        ) : (
          <button onClick={onNext} style={{
            padding: "12px 32px", borderRadius: 8,
            background: "var(--success, #22c55e)", color: "white", border: "none",
            fontSize: 14, fontWeight: 600, cursor: "pointer",
            display: "inline-flex", alignItems: "center", gap: 6,
          }}>
            <Check size={16} /> Pronto! Começar a usar
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Helpers ──────────────────────────────────────────────── */
function SettingRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{label}</span>
      {children}
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!checked)}
      style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
               background: "transparent", border: "none", cursor: "pointer", padding: "2px 0" }}>
      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{label}</span>
      <div style={{
        width: 34, height: 18, borderRadius: 9, position: "relative",
        background: checked ? "var(--accent)" : "var(--border)", transition: "background 0.15s",
      }}>
        <div style={{
          position: "absolute", top: 2, width: 14, height: 14, borderRadius: 7,
          background: "white", boxShadow: "0 1px 2px rgba(0,0,0,0.15)",
          transition: "transform 0.15s",
          transform: checked ? "translateX(18px)" : "translateX(2px)",
        }} />
      </div>
    </button>
  );
}

const selectStyle: React.CSSProperties = {
  height: 34, padding: "0 10px", fontSize: 13, borderRadius: 6,
  background: "var(--surface2)", border: "1px solid var(--border)",
  color: "var(--text)", outline: "none",
};

/* ── Main Onboarding Component ───────────────────────────── */
export function OnboardingView({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0);
  const [config, setConfig] = useState<Record<string, unknown>>({
    recording_mode: "hold",
    hotkey: "<f8>",
    live_typing: true,
    save_audio: false,
    save_history: true,
    model: "nemo-parakeet-tdt-0.6b-v3",
  });
  const [models, setModels] = useState<{ label: string; value: string }[]>([]);
  const [devices, setDevices] = useState<string[]>(["(System Default)"]);

  useEffect(() => {
    getModels().then(setModels);
    getInputDevices().then(setDevices);
  }, []);

  const handleComplete = async () => {
    await completeOnboarding(config);
    await reinitialize();
    onComplete();
  };

  const steps = [
    <WelcomeStep key="welcome" onNext={() => setStep(1)} />,
    <PreferencesStep key="prefs" config={config} setConfig={setConfig} devices={devices} onNext={() => setStep(2)} />,
    <ModelStep key="model" config={config} setConfig={setConfig} models={models} onNext={handleComplete} />,
  ];

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      background: "var(--bg)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{ width: "100%", maxWidth: 480 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.2 }}
          >
            {steps[step]}
          </motion.div>
        </AnimatePresence>
        <StepDots current={step} total={3} />
      </div>
    </div>
  );
}

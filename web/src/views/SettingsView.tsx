import { useState, useEffect } from "react";
import { getConfig, saveConfig, getModels, getInputDevices } from "@/lib/api";
import { Check } from "lucide-react";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <h3 style={{
        fontFamily: "var(--font-mono)",
        fontSize: 9,
        textTransform: "uppercase",
        letterSpacing: "0.12em",
        fontWeight: 600,
        color: "var(--accent)",
      }}>
        {title}
      </h3>
      <div style={{
        borderRadius: "var(--radius-lg)",
        padding: "18px 20px",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <label style={{
        fontFamily: "var(--font-body)",
        fontSize: 13,
        width: 130,
        flexShrink: 0,
        color: "var(--text-secondary)",
      }}>
        {label}
      </label>
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  );
}

function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="text" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      style={{
        width: "100%",
        height: 36,
        padding: "0 12px",
        fontSize: 13,
        fontFamily: "var(--font-body)",
        borderRadius: "var(--radius-md)",
        background: "var(--surface2)",
        border: "1px solid var(--border)",
        color: "var(--text)",
        outline: "none",
        transition: "border-color 0.15s",
      }}
      onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
      onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
    />
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { label: string; value: string }[] }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      style={{
        width: "100%",
        height: 36,
        padding: "0 12px",
        fontSize: 13,
        fontFamily: "var(--font-body)",
        borderRadius: "var(--radius-md)",
        background: "var(--surface2)",
        border: "1px solid var(--border)",
        color: "var(--text)",
        outline: "none",
        cursor: "pointer",
      }}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="flex items-center cursor-pointer"
      style={{ gap: 10, padding: "2px 0", background: "transparent", border: "none" }}
    >
      <div style={{
        width: 34, height: 18, borderRadius: 9,
        background: checked ? "var(--accent)" : "var(--border)",
        position: "relative",
        flexShrink: 0,
        transition: "background 0.15s",
      }}>
        <div style={{
          position: "absolute", top: 2, width: 14, height: 14,
          borderRadius: 7, background: "white",
          boxShadow: "0 1px 2px rgba(0,0,0,0.15)",
          transition: "transform 0.15s",
          transform: checked ? "translateX(18px)" : "translateX(2px)",
        }} />
      </div>
      <span style={{
        fontFamily: "var(--font-body)",
        fontSize: 13,
        color: "var(--text-secondary)",
      }}>
        {label}
      </span>
    </button>
  );
}

const ACCENT_PRESETS = [
  { label: "Terracotta", value: "#e8653a" },
  { label: "Oceano", value: "#2e86ab" },
  { label: "Floresta", value: "#3a9d6e" },
  { label: "Lavanda", value: "#8b6cc1" },
  { label: "Rosa", value: "#d4587a" },
  { label: "Dourado", value: "#c49520" },
  { label: "Carvão", value: "#6b7280" },
  { label: "Cereja", value: "#c93b3b" },
];

function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r}, ${g}, ${b}`;
}

export function applyAccentColor(hex: string) {
  const root = document.documentElement;
  const rgb = hexToRgb(hex);
  root.style.setProperty("--accent", hex);
  root.style.setProperty("--accent-rgb", rgb);
  root.style.setProperty("--accent-hover", hex);
  root.style.setProperty("--accent-subtle", `rgba(${rgb}, 0.07)`);
  root.style.setProperty("--accent-glow", `rgba(${rgb}, 0.14)`);
}

function ColorPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {ACCENT_PRESETS.map((preset) => (
        <button
          key={preset.value}
          onClick={() => onChange(preset.value)}
          title={preset.label}
          style={{
            width: 28,
            height: 28,
            borderRadius: "var(--radius-sm)",
            background: preset.value,
            border: value === preset.value ? "2px solid var(--text)" : "1.5px solid var(--border)",
            cursor: "pointer",
            transition: "transform 0.12s, border-color 0.12s",
            transform: value === preset.value ? "scale(1.12)" : "scale(1)",
          }}
        />
      ))}
    </div>
  );
}

export function SettingsView() {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [models, setModels] = useState<{ label: string; value: string }[]>([]);
  const [devices, setDevices] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([getConfig(), getModels(), getInputDevices()]).then(([c, m, d]) => {
      setConfig(c); setModels(m); setDevices(d);
    });
  }, []);

  const set = (key: string, value: unknown) => setConfig(prev => ({ ...prev, [key]: value }));

  const setAccentColor = (color: string) => {
    set("accent_color", color);
    applyAccentColor(color);
  };

  const handleSave = async () => {
    await saveConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 24 }}>
        <Section title="Áudio">
          <Field label="Microfone">
            <Select value={config.microphone_name || ""} onChange={(v) => set("microphone_name", v || null)}
              options={devices.map(d => ({ label: d, value: d === "(System Default)" ? "" : d }))} />
          </Field>
          <Field label="Modo">
            <Select value={config.recording_mode || "hold"} onChange={(v) => set("recording_mode", v)}
              options={[{ label: "Segurar", value: "hold" }, { label: "Alternar", value: "toggle" }]} />
          </Field>
          <Toggle checked={config.auto_stop ?? true} onChange={(v) => set("auto_stop", v)} label="Parar no silêncio" />
        </Section>

        <Section title="Modelo">
          <Field label="Whisper">
            <Select value={config.model || ""} onChange={(v) => set("model", v)}
              options={models.map(m => ({ label: m.label, value: m.value }))} />
          </Field>
          <Field label="Idioma">
            <Select value={config.language || "auto"} onChange={(v) => set("language", v === "auto" ? null : v)}
              options={[
                { label: "Auto-detectar", value: "auto" }, { label: "Português", value: "pt" },
                { label: "English", value: "en" }, { label: "Español", value: "es" },
              ]} />
          </Field>
          <Field label="Dispositivo">
            <Select value={config.device || "auto"} onChange={(v) => set("device", v)}
              options={[
                { label: "Auto", value: "auto" }, { label: "CPU", value: "cpu" },
                { label: "CUDA", value: "cuda" }, { label: "DirectML", value: "directml" },
              ]} />
          </Field>
        </Section>

        <Section title="Atalhos">
          <Field label="Gravar"><Input value={config.hotkey || "<f9>"} onChange={(v) => set("hotkey", v)} /></Field>
          <Field label="Traduzir"><Input value={config.translate_hotkey || ""} onChange={(v) => set("translate_hotkey", v)} placeholder="ex: <f10>" /></Field>
        </Section>

        <Section title="Digitação">
          <Toggle checked={config.live_typing ?? true} onChange={(v) => set("live_typing", v)} label="Digitar ao vivo enquanto grava" />
          <Toggle checked={config.auto_paste ?? true} onChange={(v) => set("auto_paste", v)} label="Colar automaticamente" />
        </Section>

        <Section title="Armazenamento">
          <Field label="Diretório"><Input value={config.data_dir || ""} onChange={(v) => set("data_dir", v)} placeholder="AppData/LeroLero" /></Field>
          <Toggle checked={config.save_audio ?? false} onChange={(v) => set("save_audio", v)} label="Gravar áudio (.wav)" />
          <Toggle checked={config.save_history ?? true} onChange={(v) => set("save_history", v)} label="Salvar histórico" />
        </Section>

        <Section title="Geral">
          <Toggle checked={config.show_overlay ?? true} onChange={(v) => set("show_overlay", v)} label="Mostrar overlay" />
          <Toggle checked={config.refocus_window ?? true} onChange={(v) => set("refocus_window", v)} label="Voltar para janela ao colar" />
          <Toggle checked={config.run_at_startup ?? false} onChange={(v) => set("run_at_startup", v)} label="Iniciar com o sistema" />
        </Section>

        <Section title="Aparência">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
              Cor de destaque
            </span>
            <ColorPicker value={config.accent_color || "#e8653a"} onChange={setAccentColor} />
          </div>
        </Section>
      </div>

      {/* Sticky save */}
      <div style={{
        padding: "12px 24px",
        borderTop: "1px solid var(--border)",
        background: "var(--surface)",
        display: "flex",
        justifyContent: "flex-end",
      }}>
        <button
          onClick={handleSave}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "10px 28px",
            borderRadius: "var(--radius-md)",
            border: "none",
            fontFamily: "var(--font-body)",
            fontSize: 13,
            fontWeight: 600,
            color: "var(--bg)",
            background: saved ? "var(--success)" : "var(--accent)",
            cursor: "pointer",
            transition: "background 0.15s",
          }}
        >
          {saved ? <><Check size={14} /> Salvo</> : "Salvar"}
        </button>
      </div>
    </div>
  );
}

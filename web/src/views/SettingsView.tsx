import { useState, useEffect } from "react";
import { getConfig, saveConfig, getModels, getInputDevices } from "@/lib/api";
import { Check } from "lucide-react";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-[var(--sp-3)]">
      <h3 className="text-[10px] uppercase tracking-[0.1em] font-bold" style={{ color: "var(--accent)" }}>
        {title}
      </h3>
      <div className="rounded-[var(--radius-lg)] p-[var(--sp-5)] space-y-[var(--sp-5)]"
           style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-[var(--sp-4)]">
      <label className="text-[13px] w-[140px] shrink-0" style={{ color: "var(--text-secondary)" }}>{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="text" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className="w-full h-[36px] px-[var(--sp-3)] text-[13px] rounded-[var(--radius-md)] outline-none transition-colors"
      style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text)" }}
      onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
      onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
    />
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { label: string; value: string }[] }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className="w-full h-[36px] px-[var(--sp-3)] text-[13px] rounded-[var(--radius-md)] outline-none cursor-pointer"
      style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text)" }}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button onClick={() => onChange(!checked)} className="flex items-center gap-[var(--sp-3)] cursor-pointer group w-full"
            style={{ padding: "4px 0" }}>
      <div className="w-9 h-5 rounded-full transition-colors relative shrink-0"
           style={{ background: checked ? "var(--accent)" : "var(--border)" }}>
        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform"
             style={{ transform: checked ? "translateX(18px)" : "translateX(2px)" }} />
      </div>
      <span className="text-[13px] transition-colors" style={{ color: "var(--text-secondary)" }}>{label}</span>
    </button>
  );
}

const ACCENT_PRESETS = [
  { label: "Roxo", value: "#a78bfa" },
  { label: "Azul", value: "#60a5fa" },
  { label: "Verde", value: "#34d399" },
  { label: "Teal", value: "#2dd4bf" },
  { label: "Laranja", value: "#fb923c" },
  { label: "Rosa", value: "#f472b6" },
  { label: "Vermelho", value: "#f87171" },
  { label: "Amarelo", value: "#fbbf24" },
];

function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r}, ${g}, ${b}`;
}

/** Apply accent color CSS variables to :root */
export function applyAccentColor(hex: string) {
  const root = document.documentElement;
  const rgb = hexToRgb(hex);
  root.style.setProperty("--accent", hex);
  root.style.setProperty("--accent-rgb", rgb);
  root.style.setProperty("--accent-hover", hex);
  root.style.setProperty("--accent-subtle", `rgba(${rgb}, 0.08)`);
  root.style.setProperty("--accent-glow", `rgba(${rgb}, 0.12)`);
}

function ColorPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
      {ACCENT_PRESETS.map((preset) => (
        <button
          key={preset.value}
          onClick={() => onChange(preset.value)}
          title={preset.label}
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: preset.value,
            border: value === preset.value ? "3px solid var(--text)" : "2px solid var(--border)",
            cursor: "pointer",
            transition: "border-color 0.15s, transform 0.15s",
            transform: value === preset.value ? "scale(1.1)" : "scale(1)",
            boxShadow: value === preset.value ? `0 0 12px ${preset.value}60` : "none",
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

  // Live-preview accent color when changed in settings
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
      <div className="flex-1 overflow-y-auto p-[var(--sp-6)] space-y-[var(--sp-8)]">
        <Section title="Áudio">
          <Field label="Microfone">
            <Select value={config.microphone_name || ""} onChange={(v) => set("microphone_name", v || null)}
              options={devices.map(d => ({ label: d, value: d === "(System Default)" ? "" : d }))} />
          </Field>
          <Field label="Modo Gravação">
            <Select value={config.recording_mode || "hold"} onChange={(v) => set("recording_mode", v)}
              options={[{ label: "Segurar", value: "hold" }, { label: "Alternar", value: "toggle" }]} />
          </Field>
          <Toggle checked={config.auto_stop ?? true} onChange={(v) => set("auto_stop", v)} label="Parar no silêncio" />
        </Section>

        <Section title="Modelo">
          <Field label="Modelo Whisper">
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
                { label: "Auto-detectar", value: "auto" }, { label: "CPU", value: "cpu" },
                { label: "CUDA (NVIDIA)", value: "cuda" }, { label: "OpenVINO (Intel)", value: "openvino" },
                { label: "DirectML (AMD)", value: "directml" },
              ]} />
          </Field>
        </Section>

        <Section title="Atalhos">
          <Field label="Gravar"><Input value={config.hotkey || "<f9>"} onChange={(v) => set("hotkey", v)} /></Field>
          <Field label="Traduzir"><Input value={config.translate_hotkey || ""} onChange={(v) => set("translate_hotkey", v)} placeholder="ex: <f10>" /></Field>
        </Section>

        <Section title="Digitação">
          <Toggle checked={config.live_typing ?? true} onChange={(v) => set("live_typing", v)} label="Digitar ao vivo enquanto grava" />
          <Toggle checked={config.auto_paste ?? true} onChange={(v) => set("auto_paste", v)} label="Colar automaticamente ao terminar" />
        </Section>

        <Section title="Armazenamento">
          <Field label="Diretório"><Input value={config.data_dir || ""} onChange={(v) => set("data_dir", v)} placeholder="Padrão: AppData/LeroLero" /></Field>
          <Toggle checked={config.save_audio ?? false} onChange={(v) => set("save_audio", v)} label="Salvar gravações de áudio (.wav)" />
          <Toggle checked={config.save_history ?? true} onChange={(v) => set("save_history", v)} label="Salvar histórico de transcrições" />
        </Section>

        <Section title="Geral">
          <Toggle checked={config.show_overlay ?? true} onChange={(v) => set("show_overlay", v)} label="Mostrar overlay flutuante" />
          <Toggle checked={config.refocus_window ?? true} onChange={(v) => set("refocus_window", v)} label="Voltar para janela anterior ao colar" />
          <Toggle checked={config.run_at_startup ?? false} onChange={(v) => set("run_at_startup", v)} label="Iniciar com o Windows" />
        </Section>

        <Section title="Aparência">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <span className="text-[13px]" style={{ color: "var(--text-secondary)" }}>Cor de destaque</span>
            <ColorPicker value={config.accent_color || "#a78bfa"} onChange={setAccentColor} />
          </div>
        </Section>
      </div>

      {/* Sticky save button */}
      <div className="px-[var(--sp-6)] py-[var(--sp-4)] border-t flex justify-end"
           style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <button onClick={handleSave}
          className="flex items-center gap-[var(--sp-2)] rounded-[var(--radius-md)] text-[13px] font-semibold text-white transition-colors cursor-pointer"
          style={{ background: saved ? "var(--success)" : "var(--accent)", padding: "10px 32px" }}>
          {saved ? <><Check size={14} /> Salvo!</> : "Salvar Configurações"}
        </button>
      </div>
    </div>
  );
}

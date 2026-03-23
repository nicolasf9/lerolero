import { useState, useEffect } from "react";
import { getConfig, saveConfig, getModels, getInputDevices } from "@/lib/api";
import { Check } from "lucide-react";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[10px] uppercase tracking-wider font-bold text-[var(--accent)] mb-3">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <label className="text-sm text-[var(--muted)] shrink-0">{label}</label>
      <div className="flex-1 max-w-xs">{children}</div>
    </div>
  );
}

function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="text" value={value} onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full h-9 px-3 text-sm rounded-lg bg-[var(--surface2)] border border-[var(--border)] text-[var(--text)] placeholder:text-[var(--muted-dim)] focus:border-[var(--accent)] focus:outline-none"
    />
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { label: string; value: string }[] }) {
  return (
    <select
      value={value} onChange={(e) => onChange(e.target.value)}
      className="w-full h-9 px-3 text-sm rounded-lg bg-[var(--surface2)] border border-[var(--border)] text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="flex items-center gap-3 cursor-pointer group"
    >
      <div className={`w-10 h-5 rounded-full transition-colors ${checked ? "bg-[var(--accent-dim)]" : "bg-[var(--border)]"}`}>
        <div className={`w-5 h-5 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-5" : "translate-x-0"}`} />
      </div>
      <span className="text-sm text-[var(--muted)] group-hover:text-[var(--text)] transition-colors">{label}</span>
    </button>
  );
}

export function SettingsView() {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [models, setModels] = useState<{ label: string; value: string }[]>([]);
  const [devices, setDevices] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([getConfig(), getModels(), getInputDevices()]).then(([c, m, d]) => {
      setConfig(c);
      setModels(m);
      setDevices(d);
    });
  }, []);

  const set = (key: string, value: unknown) => setConfig(prev => ({ ...prev, [key]: value }));

  const handleSave = async () => {
    await saveConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        <Section title="🎤 Áudio">
          <Field label="Microfone">
            <Select
              value={config.microphone_name || ""}
              onChange={(v) => set("microphone_name", v || null)}
              options={devices.map(d => ({ label: d, value: d === "(System Default)" ? "" : d }))}
            />
          </Field>
          <Field label="Modo de Gravação">
            <Select value={config.recording_mode || "hold"} onChange={(v) => set("recording_mode", v)} options={[
              { label: "Segurar (Hold)", value: "hold" },
              { label: "Alternar (Toggle)", value: "toggle" },
            ]} />
          </Field>
          <Toggle checked={config.auto_stop ?? true} onChange={(v) => set("auto_stop", v)} label="Parar no silêncio" />
        </Section>

        <Section title="🧠 Modelo">
          <Field label="Modelo Whisper">
            <Select value={config.model || ""} onChange={(v) => set("model", v)} options={models.map(m => ({ label: m.label, value: m.value }))} />
          </Field>
          <Field label="Idioma">
            <Select value={config.language || "auto"} onChange={(v) => set("language", v === "auto" ? null : v)} options={[
              { label: "Auto-detectar", value: "auto" },
              { label: "Português", value: "pt" },
              { label: "English", value: "en" },
              { label: "Español", value: "es" },
              { label: "Français", value: "fr" },
              { label: "Deutsch", value: "de" },
            ]} />
          </Field>
          <Field label="Dispositivo">
            <Select value={config.device || "auto"} onChange={(v) => set("device", v)} options={[
              { label: "Auto-detectar", value: "auto" },
              { label: "CPU", value: "cpu" },
              { label: "CUDA (NVIDIA)", value: "cuda" },
              { label: "OpenVINO (Intel)", value: "openvino" },
              { label: "DirectML (AMD)", value: "directml" },
            ]} />
          </Field>
        </Section>

        <Section title="⌨ Atalhos">
          <Field label="Hotkey Gravar">
            <Input value={config.hotkey || "<f9>"} onChange={(v) => set("hotkey", v)} />
          </Field>
          <Field label="Hotkey Traduzir">
            <Input value={config.translate_hotkey || ""} onChange={(v) => set("translate_hotkey", v)} placeholder="ex: <f10>" />
          </Field>
        </Section>

        <Section title="✍ Digitação">
          <Toggle checked={config.live_typing ?? true} onChange={(v) => set("live_typing", v)} label="Digitar ao vivo (enquanto grava)" />
          <Toggle checked={config.auto_paste ?? true} onChange={(v) => set("auto_paste", v)} label="Colar automaticamente ao terminar" />
        </Section>

        <Section title="💾 Armazenamento">
          <Field label="Diretório de dados">
            <Input value={config.data_dir || ""} onChange={(v) => set("data_dir", v)} placeholder="%APPDATA%/LeroLero" />
          </Field>
          <Toggle checked={config.save_audio ?? false} onChange={(v) => set("save_audio", v)} label="Salvar áudio das gravações (.wav)" />
          <Toggle checked={config.save_history ?? true} onChange={(v) => set("save_history", v)} label="Salvar histórico de transcrições" />
        </Section>

        <Section title="⚙ Geral">
          <Toggle checked={config.show_overlay ?? true} onChange={(v) => set("show_overlay", v)} label="Mostrar overlay flutuante" />
          <Toggle checked={config.refocus_window ?? true} onChange={(v) => set("refocus_window", v)} label="Voltar para janela anterior ao colar" />
          <Toggle checked={config.run_at_startup ?? false} onChange={(v) => set("run_at_startup", v)} label="Iniciar com o Windows" />
        </Section>
      </div>

      {/* Sticky save bar */}
      <div className="px-6 py-3 border-t border-[var(--border)] bg-[var(--surface)] flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[var(--accent-dim)] hover:bg-[var(--accent-hover)] text-white font-bold text-sm transition-colors"
        >
          {saved ? <><Check size={16} /> Salvo!</> : "✔ Salvar Configurações"}
        </button>
      </div>
    </div>
  );
}

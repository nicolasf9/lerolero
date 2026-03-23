import { useState, useEffect } from "react";
import { getConfig, saveConfig, getModels, getInputDevices } from "@/lib/api";
import { Check } from "lucide-react";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-[var(--sp-3)]">
      <h3 className="text-[10px] uppercase tracking-[0.1em] font-bold" style={{ color: "var(--accent)" }}>
        {title}
      </h3>
      <div className="rounded-[var(--radius-lg)] p-[var(--sp-4)] space-y-[var(--sp-4)]"
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
    <button onClick={() => onChange(!checked)} className="flex items-center gap-[var(--sp-3)] cursor-pointer group w-full">
      <div className="w-9 h-5 rounded-full transition-colors relative shrink-0"
           style={{ background: checked ? "var(--accent)" : "var(--border)" }}>
        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform"
             style={{ transform: checked ? "translateX(18px)" : "translateX(2px)" }} />
      </div>
      <span className="text-[13px] transition-colors" style={{ color: "var(--text-secondary)" }}>{label}</span>
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
      setConfig(c); setModels(m); setDevices(d);
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
      <div className="flex-1 overflow-y-auto p-[var(--sp-6)] space-y-[var(--sp-6)]">
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
      </div>

      {/* Sticky save button */}
      <div className="px-[var(--sp-6)] py-[var(--sp-3)] border-t flex justify-end"
           style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <button onClick={handleSave}
          className="flex items-center gap-[var(--sp-2)] px-[var(--sp-5)] py-[var(--sp-2)] rounded-[var(--radius-md)] text-[13px] font-semibold text-white transition-colors cursor-pointer"
          style={{ background: saved ? "var(--success)" : "var(--accent)" }}>
          {saved ? <><Check size={14} /> Salvo!</> : "Salvar Configurações"}
        </button>
      </div>
    </div>
  );
}

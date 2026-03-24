import { useState, useEffect } from "react";
import { Shield, Cpu, Globe } from "lucide-react";
import { getVersion } from "@/lib/api";

export function AboutView() {
  const [version, setVersion] = useState("...");

  useEffect(() => {
    getVersion().then(setVersion);
  }, []);

  return (
    <div className="h-full overflow-y-auto flex flex-col items-center justify-center text-center px-[var(--sp-8)]">
      <div className="max-w-[360px]">
        <h1 className="text-[32px] font-bold tracking-tight" style={{ color: "var(--text)" }}>
          LeroLero
        </h1>
        <p className="text-[12px] font-mono mt-[var(--sp-1)]" style={{ color: "var(--text-tertiary)" }}>
          v{version}
        </p>

        <p className="text-[14px] mt-[var(--sp-6)]" style={{ color: "var(--text-secondary)" }}>
          Fale e o texto aparece. Simples assim.
        </p>

        <div className="flex justify-center gap-[var(--sp-6)] mt-[var(--sp-8)]">
          <div className="flex flex-col items-center gap-[var(--sp-2)]">
            <div className="w-10 h-10 rounded-[var(--radius-md)] flex items-center justify-center"
                 style={{ background: "var(--success-subtle)" }}>
              <Shield size={18} style={{ color: "var(--success)" }} />
            </div>
            <span className="text-[11px] font-medium" style={{ color: "var(--text-tertiary)" }}>100% Offline</span>
          </div>
          <div className="flex flex-col items-center gap-[var(--sp-2)]">
            <div className="w-10 h-10 rounded-[var(--radius-md)] flex items-center justify-center"
                 style={{ background: "var(--accent-subtle)" }}>
              <Cpu size={18} style={{ color: "var(--accent)" }} />
            </div>
            <span className="text-[11px] font-medium" style={{ color: "var(--text-tertiary)" }}>Multi-GPU</span>
          </div>
          <div className="flex flex-col items-center gap-[var(--sp-2)]">
            <div className="w-10 h-10 rounded-[var(--radius-md)] flex items-center justify-center"
                 style={{ background: "var(--warning-subtle)" }}>
              <Globe size={18} style={{ color: "var(--warning)" }} />
            </div>
            <span className="text-[11px] font-medium" style={{ color: "var(--text-tertiary)" }}>Multilingual</span>
          </div>
        </div>

        <p className="text-[12px] italic mt-[var(--sp-8)]" style={{ color: "var(--accent)" }}>
          Sua voz nunca sai do seu computador.
        </p>

        <p className="text-[11px] mt-[var(--sp-6)]" style={{ color: "var(--text-disabled)" }}>
          OpenVINO · CUDA · DirectML · Whisper
        </p>
        <p className="text-[10px] mt-[var(--sp-2)]" style={{ color: "var(--text-disabled)" }}>
          Based on whisper-typing by Roger Filomeno (MIT)
        </p>
      </div>
    </div>
  );
}

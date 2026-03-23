export function AboutView() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-8">
      <h1 className="text-4xl font-bold text-[var(--text)]" style={{ fontFamily: "'Modak', cursive" }}>
        LeroLero
      </h1>
      <p className="text-sm font-mono text-[var(--muted)] mt-1">v1.0.0</p>
      <p className="text-base text-[var(--muted)] mt-4 max-w-md">
        100% offline speech-to-text para Windows.
      </p>
      <p className="text-sm text-[var(--muted-dim)] mt-2">
        Powered by OpenVINO / CUDA / DirectML + Whisper
      </p>
      <p className="text-sm italic text-[var(--accent)] mt-6">
        Sua voz nunca sai do seu computador.
      </p>
      <p className="text-xs text-[var(--muted-dim)] mt-8">
        Based on whisper-typing by Roger Filomeno (MIT License)
      </p>
    </div>
  );
}

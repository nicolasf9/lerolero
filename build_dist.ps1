# Build LeroLero executable
$projectName = "LeroLero"
$distPath = "dist/$projectName"

if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path $distPath) { Remove-Item -Path $distPath -Recurse -Force }

Write-Host "Building $projectName..." -ForegroundColor Green
Write-Host "This may take several minutes (bundling OpenVINO + Transformers)..." -ForegroundColor Yellow

uv run pyinstaller "whisper-typing.spec" --noconfirm

if ($LASTEXITCODE -ne 0) { Write-Host "Build failed!" -ForegroundColor Red; exit $LASTEXITCODE }

# Copy default config (without user-specific settings)
$defaultConfig = @{
    hotkey = "<f9>"
    model = "openai/whisper-small"
    language = $null
    device = "auto"
    compute_type = "auto"
    debug = $false
    typing_wpm = 40
    refocus_window = $true
    auto_stop = $false
    auto_paste = $true
    auto_stop_delay = 1.5
    save_history = $true
    run_at_startup = $false
    recording_mode = "hold"
    show_overlay = $true
    live_typing = $false
    theme = "dark"
} | ConvertTo-Json
$defaultConfig | Out-File -FilePath "$distPath/config.json" -Encoding utf8

New-Item -ItemType Directory -Force -Path "$distPath/history" | Out-Null
New-Item -ItemType Directory -Force -Path "$distPath/models" | Out-Null

Write-Host "`nBuild Complete!" -ForegroundColor Green
Write-Host "Output: $((Get-Item $distPath).FullName)" -ForegroundColor Cyan
Write-Host "Run: $distPath\$projectName.exe" -ForegroundColor Yellow

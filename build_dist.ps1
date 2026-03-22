# Build script for LeroLero distribution
$projectName = "lerolero"
$distPath = "dist/$projectName"

if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path $distPath) { Remove-Item -Path $distPath -Recurse -Force }

Write-Host "Building $projectName..." -ForegroundColor Green

uv run pyinstaller `
    --noconfirm --onedir --noconsole `
    --name "$projectName" `
    --collect-all "whisper_typing" `
    --collect-all "customtkinter" `
    --hidden-import "pynput.keyboard._win32" `
    --hidden-import "pynput.mouse._win32" `
    --paths "src" `
    --icon "src/whisper_typing/assets/icon.png" `
    "src/whisper_typing/__main__.py"

if ($LASTEXITCODE -ne 0) { Write-Host "Build failed!" -ForegroundColor Red; exit $LASTEXITCODE }

if (Test-Path "config.json") { Copy-Item "config.json" "$distPath/config.json" }
New-Item -ItemType Directory -Force -Path "$distPath/history" | Out-Null

Write-Host "`nBuild Complete! -> $distPath/$projectName.exe" -ForegroundColor Green

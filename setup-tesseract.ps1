# LMA Synapse - Tesseract OCR Setup for Windows
# MUST be run as Administrator

Write-Host "=== Installing Tesseract OCR for Windows ===" -ForegroundColor Cyan

# -----------------------------
# Require Administrator
# -----------------------------
$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)

if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] Please run this script as Administrator." -ForegroundColor Red
    exit 1
}

# -----------------------------
# Ensure TLS 1.2 for download
# -----------------------------
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$tesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = Join-Path $env:TEMP "tesseract-installer.exe"

# -----------------------------
# Download installer
# -----------------------------
Write-Host "Downloading Tesseract OCR..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath -UseBasicParsing

if (-not (Test-Path $installerPath)) {
    Write-Host "[ERROR] Failed to download Tesseract installer." -ForegroundColor Red
    exit 1
}

# -----------------------------
# Run installer
# -----------------------------
Write-Host "Launching Tesseract installer (follow installer prompts)..." -ForegroundColor Yellow
Start-Process -FilePath $installerPath -Wait

# -----------------------------
# Add Tesseract to PATH (Machine)
# -----------------------------
$tesseractPath = "C:\Program Files\Tesseract-OCR"

if (-not (Test-Path $tesseractPath)) {
    Write-Host "[ERROR] Tesseract installation directory not found." -ForegroundColor Red
    exit 1
}

$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($currentPath -notmatch [Regex]::Escape($tesseractPath)) {
    [Environment]::SetEnvironmentVariable(
        "Path",
        "$currentPath;$tesseractPath",
        "Machine"
    )
    Write-Host "[OK] Added Tesseract to system PATH." -ForegroundColor Green
}
else {
    Write-Host "[OK] Tesseract already present in PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "[OK] Tesseract OCR installation complete." -ForegroundColor Green
Write-Host "Restart PowerShell to use the 'tesseract' command." -ForegroundColor Cyan

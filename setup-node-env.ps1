# LMA Synapse - Node.js Environment Setup for Windows

Write-Host "=== LMA Synapse Node.js Environment Setup ===" -ForegroundColor Cyan

# -----------------------------
# Check Node.js version
# -----------------------------
$nodeVersion = (node --version 2>&1).Trim()

if ($nodeVersion -notmatch "^v(20|21|22|23|24)\.") {
    Write-Host "[ERROR] Node.js 20+ required. Current: $nodeVersion" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Node.js $nodeVersion detected" -ForegroundColor Green

# -----------------------------
# Ensure pnpm is available
# -----------------------------
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "pnpm not found. Installing pnpm..." -ForegroundColor Yellow
    npm install -g pnpm
    Write-Host "pnpm installed. Please re-run the script." -ForegroundColor Yellow
    exit 0
}

$pnpmVersion = pnpm --version
Write-Host "[OK] pnpm $pnpmVersion detected" -ForegroundColor Green

# -----------------------------
# Validate all package.json files
# -----------------------------
Write-Host ""
Write-Host "Validating workspace package.json files..." -ForegroundColor Yellow

$invalidFound = $false

Get-ChildItem -Recurse -Filter package.json | ForEach-Object {
    try {
        $content = Get-Content $_.FullName -Raw
        if ([string]::IsNullOrWhiteSpace($content)) {
            throw "Empty"
        }
        $null = $content | ConvertFrom-Json
    }
    catch {
        Write-Host "[INVALID] $($_.FullName)" -ForegroundColor Red
        $invalidFound = $true
    }
}

if ($invalidFound) {
    Write-Host ""
    Write-Host "[ERROR] One or more package.json files are empty or invalid." -ForegroundColor Red
    Write-Host "Run the repair step and re-run this script." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] All package.json files are valid" -ForegroundColor Green

# -----------------------------
# Install dependencies
# -----------------------------
Write-Host ""
Write-Host "Installing workspace dependencies..." -ForegroundColor Yellow

pnpm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pnpm install failed." -ForegroundColor Red
    exit 1
}

# -----------------------------
# Ensure Turbo exists
# -----------------------------
if (-not (Test-Path "node_modules\.bin\turbo.cmd")) {
    Write-Host "[ERROR] turbo not found in node_modules." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] turbo detected" -ForegroundColor Green

# -----------------------------
# Build shared packages (optional)
# -----------------------------
Write-Host ""
Write-Host "Building shared packages..." -ForegroundColor Yellow

pnpm run build --filter=@nexus/shared --if-present
pnpm run build --filter=@nexus/lma-ontology --if-present

Write-Host ""
Write-Host "[OK] Node.js environment setup complete!" -ForegroundColor Green

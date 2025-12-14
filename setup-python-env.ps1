# LMA Synapse - Python Environment Setup for Windows
# Python 3.11 ONLY

Write-Host "=== LMA Synapse Python Environment Setup (Python 3.11) ===" -ForegroundColor Cyan

# Verify Python 3.11 is installed
$py311 = py -3.11 --version 2>$null
if (-not $py311) {
    Write-Host "[ERROR] Python 3.11 is not installed or not available via py launcher." -ForegroundColor Red
    Write-Host "Install Python 3.11 from https://www.python.org/downloads/release/python-3119/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] $py311 detected" -ForegroundColor Green

# Remove old virtual environment if it exists
if (Test-Path ".venv") {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    deactivate 2>$null
    Remove-Item -Recurse -Force ".venv"
}

# Create virtual environment using Python 3.11 explicitly
Write-Host "Creating virtual environment with Python 3.11..." -ForegroundColor Yellow
py -3.11 -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

# Confirm Python version inside venv
$venvPython = python --version
if ($venvPython -notlike "Python 3.11*") {
    Write-Host "[ERROR] Virtual environment is NOT using Python 3.11." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Virtual environment using $venvPython" -ForegroundColor Green

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install PyTorch (CPU-only, Windows)
Write-Host "`nInstalling PyTorch (CPU-only for Windows)..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Core dependencies
Write-Host "`nInstalling core dependencies..." -ForegroundColor Yellow
pip install fastapi==0.109.0
pip install "uvicorn[standard]==0.27.0"
pip install python-multipart==0.0.9
pip install pydantic==2.6.0
pip install pydantic-settings==2.1.0

# Gemini SDK
Write-Host "`nInstalling Google Gemini SDK..." -ForegroundColor Yellow
pip install google-generativeai==0.3.2

# LangChain ecosystem
Write-Host "`nInstalling LangChain ecosystem..." -ForegroundColor Yellow
pip install langchain==0.1.16
pip install langchain-google-genai==1.0.1
pip install langgraph==0.0.26
pip install langchain-community==0.0.29

# Document processing
Write-Host "`nInstalling document processing libraries..." -ForegroundColor Yellow
pip install transformers==4.36.0
pip install pdf2image==1.16.3
pip install pypdf2==3.0.1
pip install python-docx==1.1.0
pip install pillow==10.2.0
pip install pytesseract==0.3.10

# LayoutLMv3 dependencies
Write-Host "`nInstalling LayoutLMv3 dependencies..." -ForegroundColor Yellow
pip install sentencepiece==0.1.99
pip install protobuf==4.25.2

# Vector database
Write-Host "`nInstalling ChromaDB..." -ForegroundColor Yellow
pip install chromadb==0.4.22

# Utilities
Write-Host "`nInstalling utilities..." -ForegroundColor Yellow
pip install python-dotenv==1.0.1
pip install aiofiles==23.2.1
pip install httpx==0.26.0
pip install tenacity==8.2.3

# Save requirements
Write-Host "`nSaving requirements.txt..." -ForegroundColor Yellow
pip freeze > requirements.txt

Write-Host "`n[OK] Python 3.11 environment setup complete!" -ForegroundColor Green
Write-Host "Activate later with: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan

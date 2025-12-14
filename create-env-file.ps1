# Create .env file with required API keys

Write-Host "=== Creating .env configuration ===" -ForegroundColor Cyan

$envContent = @"
# LMA Synapse Configuration

# Gemini API Key (Get from: https://ai.google.dev/gemini-api/docs/api-key)
GEMINI_API_KEY=AIzaSyA-CoSz2FcKfBDzPXt4gShER6QJMOUY7V0

# Model Selection
GEMINI_FLASH_MODEL=gemini-2.0-flash-exp
GEMINI_PRO_MODEL=gemini-1.5-pro

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Database (SQLite for MVP)
DATABASE_URL=sqlite:///./lma_synapse.db

# Upload Configuration
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=.pdf,.docx

# Processing
ENABLE_LAYOUTLMV3=false
BATCH_SIZE=1
MAX_CONCURRENT_JOBS=3

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# Logging
LOG_LEVEL=INFO
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "✓ Created .env file" -ForegroundColor Green
Write-Host "`n⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY" -ForegroundColor Yellow
Write-Host "Get your key from: https://ai.google.dev/gemini-api/docs/api-key" -ForegroundColor Cyan

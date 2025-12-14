# Test all installations

Write-Host "=== Testing LMA Synapse Setup ===" -ForegroundColor Cyan

# Test Python
Write-Host "`n[1/6] Testing Python..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1
python -c "import torch; import transformers; import google.generativeai; print('✓ Python imports OK')"

# Test Gemini connection
Write-Host "`n[2/6] Testing Gemini API..." -ForegroundColor Yellow
python -c @"
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if api_key and api_key != 'your_gemini_api_key_here':
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content('Say: Gemini connected!')
    print(f'✓ {response.text}')
else:
    print('⚠️  Set GEMINI_API_KEY in .env file')
"@

# Test Node.js
Write-Host "`n[3/6] Testing Node.js..." -ForegroundColor Yellow
node -e "console.log('✓ Node.js OK')"

# Test pnpm
Write-Host "`n[4/6] Testing pnpm..." -ForegroundColor Yellow
pnpm --version

# Test Tesseract
Write-Host "`n[5/6] Testing Tesseract..." -ForegroundColor Yellow
tesseract --version

# Test directory structure
Write-Host "`n[6/6] Checking directory structure..." -ForegroundColor Yellow
if (Test-Path "services/document-service") { Write-Host "✓ services/document-service exists" -ForegroundColor Green }
if (Test-Path "apps/desktop") { Write-Host "✓ apps/desktop exists" -ForegroundColor Green }
if (Test-Path "packages/@nexus") { Write-Host "✓ packages/@nexus exists" -ForegroundColor Green }

Write-Host "`n✓ Setup verification complete!" -ForegroundColor Green

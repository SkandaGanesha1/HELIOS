# LMA Synapse - Quick Start Guide

## Step 1: Run Setup Scripts

Open PowerShell in the HELIOS directory and run:

```powershell
# 1. Setup Python environment (takes 5-10 minutes)
powershell -ExecutionPolicy Bypass -File setup-python-env.ps1

# 2. Setup Node.js environment
powershell -ExecutionPolicy Bypass -File setup-node-env.ps1

# 3. Create .env file
powershell -ExecutionPolicy Bypass -File create-env-file.ps1
```

## Step 2: Get Gemini API Key

1. Go to: https://ai.google.dev/gemini-api/docs/api-key
2. Click "Get API Key"
3. Copy your API key

## Step 3: Configure .env

Open `.env` file and replace `your_gemini_api_key_here` with your actual API key:

```bash
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

## Step 4: Install aiosqlite

The database module needs aiosqlite:

```powershell
.\.venv\Scripts\Activate.ps1
pip install aiosqlite
```

## Step 5: Start the FastAPI Backend

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Navigate to document service
cd services\document-service

# Run the server
python -m uvicorn src.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 6: Test the API

Open a new PowerShell window:

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","gemini_configured":true}

# Open API docs in browser
start http://localhost:8000/docs
```

## Step 7: Upload a Test Document

### Option A: Using Swagger UI (Easiest)

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/documents/upload`
3. Click "Try it out"
4. Click "Choose File" and select a PDF or DOCX
5. Click "Execute"
6. Copy the `job_id` from the response
7. Use `GET /api/v1/documents/{job_id}/status` to check progress

### Option B: Using PowerShell

```powershell
# Upload a document
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/upload" `
    -Method Post `
    -Form @{file = Get-Item "path\to\your\document.pdf"}

$jobId = $response.job_id
Write-Host "Job ID: $jobId"

# Check status (wait 30-60 seconds for processing)
Start-Sleep -Seconds 45
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/$jobId/status"
```

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"
- Make sure you edited `.env` file with your actual API key
- Restart the FastAPI server after editing `.env`

### Issue: "Module not found"
```powershell
.\.venv\Scripts\Activate.ps1
pip install aiosqlite python-docx PyPDF2
```

### Issue: "Port 8000 already in use"
```powershell
# Use a different port
python -m uvicorn src.main:app --reload --port 8001
```

### Issue: "Can't read PDF"
- Make sure the PDF is not encrypted or password-protected
- Try a simple text-based PDF first

## Next Steps

Once the backend is working:

1. **Create a sample test document** (or use an existing loan agreement PDF)
2. **Test full extraction workflow**
3. **Build the Electron UI** (optional for MVP)
4. **Prepare demo presentation**

## Useful Commands

```powershell
# Activate Python environment
.\.venv\Scripts\Activate.ps1

# Run FastAPI with auto-reload
cd services\document-service
python -m uvicorn src.main:app --reload --port 8000

# View logs in real-time
# (logs appear in the terminal where uvicorn is running)

# List all jobs
curl http://localhost:8000/api/v1/documents/

# View API documentation
start http://localhost:8000/docs
```

## Success Criteria

✅ FastAPI server starts without errors
✅ Health check returns `gemini_configured: true`
✅ Can upload a PDF document
✅ Job status changes from "processing" to "completed"
✅ Extraction results contain borrower/facility data

---

**You're ready to develop LMA Synapse! 🚀**

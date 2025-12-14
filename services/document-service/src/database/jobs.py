"""SQLite-based job tracking for document extraction"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import aiosqlite

# Database file path
DB_PATH = Path("lma_synapse.db")

async def init_db():
    """Initialize SQLite database with jobs table"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS extraction_jobs (
                job_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result TEXT,
                error TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def create_job(
    job_id: str,
    filename: str,
    file_path: str,
    file_size: int,
    status: str = "pending"
) -> Dict[str, Any]:
    """Create a new extraction job"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO extraction_jobs (job_id, filename, file_path, file_size, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, filename, file_path, file_size, status)
        )
        await db.commit()

    return {
        "job_id": job_id,
        "filename": filename,
        "status": status,
        "created_at": datetime.now().isoformat()
    }

async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM extraction_jobs WHERE job_id = ?",
            (job_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return None

            job = dict(row)
            # Parse JSON result if present
            if job.get("result"):
                job["result"] = json.loads(job["result"])

            return job

async def update_job_status(
    job_id: str,
    status: str,
    progress: int = None,
    result: Dict[str, Any] = None,
    error: str = None,
    confidence: float = None
):
    """Update job status and results"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Build update query dynamically
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]

        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)

        if result is not None:
            updates.append("result = ?")
            params.append(json.dumps(result))

        if error is not None:
            updates.append("error = ?")
            params.append(error)

        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)

        params.append(job_id)

        query = f"UPDATE extraction_jobs SET {', '.join(updates)} WHERE job_id = ?"
        await db.execute(query, params)
        await db.commit()

async def list_jobs(limit: int = 100, offset: int = 0) -> list:
    """List all jobs with pagination"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT job_id, filename, status, progress, confidence, created_at, updated_at
            FROM extraction_jobs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

"""Dashboard router — stats and control."""
from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats():
    conn = get_connection()
    try:
        # Simplified stats
        cursor = conn.cursor()
        stats = {}
        for table in ["businesses", "analyses", "outreach", "sites"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"total_{table}"] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()

@router.post("/run-now")
async def run_cycle_now():
    from scheduler import AutonomousScheduler
    s = AutonomousScheduler()
    s.run_cycle()
    return {"status": "cycle_started"}
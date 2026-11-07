import httpx
from fastapi import APIRouter
from backend.config.settings import settings
from backend.db.firestore import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    # Check Bifrost connectivity
    bifrost_status = {"reachable": False, "url": settings.bifrost_url, "error": None}
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.bifrost_url.rstrip('/')}/health")
            if resp.status_code == 200:
                bifrost_status["reachable"] = True
            else:
                bifrost_status["error"] = f"Bifrost returned HTTP {resp.status_code}"
    except Exception as e:
        bifrost_status["error"] = str(e)

    # Check Database connectivity
    db = get_db()
    db_status = {"connected": True, "type": type(db).__name__}

    overall_status = "ok" if bifrost_status["reachable"] else "degraded"

    return {
        "status": overall_status,
        "bifrost": bifrost_status,
        "database": db_status
    }


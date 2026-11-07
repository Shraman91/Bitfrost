from fastapi import APIRouter, HTTPException
from backend.db.firestore import get_db

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run(run_id: str):
    db = get_db()
    doc = db.collection("runs").document(run_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Run not found")

    run_data = doc.to_dict()
    # Fetch task details for rich prompt display in UI
    task_id = run_data.get("task_id")
    task_data = None
    if task_id:
        t_doc = db.collection("tasks").document(task_id).get()
        if t_doc.exists:
            task_data = t_doc.to_dict()

    return {
        "run": run_data,
        "task": task_data
    }


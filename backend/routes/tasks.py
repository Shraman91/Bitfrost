import json
import os
import glob
from typing import List
from fastapi import APIRouter, HTTPException
from backend.models.task import Task
from backend.db.firestore import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[Task])
def list_tasks():
    db = get_db()
    docs = db.collection("tasks").stream()
    tasks = [Task(**doc.to_dict()) for doc in docs]
    
    # If DB not yet seeded, dynamically load from disk
    if not tasks:
        task_dir = os.path.join(os.path.dirname(__file__), "..", "tasks")
        for path in glob.glob(os.path.join(task_dir, "*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tasks.append(Task(**data))
            except Exception:
                pass
    return tasks


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    db = get_db()
    doc = db.collection("tasks").document(task_id).get()
    if doc.exists:
        return Task(**doc.to_dict())

    # Check disk fallback
    task_dir = os.path.join(os.path.dirname(__file__), "..", "tasks")
    for path in glob.glob(os.path.join(task_dir, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("id") == task_id:
                    return Task(**data)
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Task not found")


import os
import sys
import glob
import json
import time

# Robust path setup so this script runs from any working directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from backend.db.firestore import get_db
except ImportError:
    from db.firestore import get_db

BUILTIN_AGENTS = [
    {
        "id": "naive",
        "name": "Naive Single-Prompt",
        "type": "builtin",
        "model": "openai/gpt-4o-mini",
        "description": "Single-turn prompt asking LLM to generate the complete solution in one shot.",
        "created_at": time.time()
    },
    {
        "id": "react-lite",
        "name": "ReAct-Lite (Plan-Write-Check)",
        "type": "builtin",
        "model": "openai/gpt-4o-mini",
        "description": "Multi-turn iterative agent: plans, drafts code, then self-checks for edge cases and bugs.",
        "created_at": time.time()
    },
    {
        "id": "token-saver",
        "name": "Token-Saver",
        "type": "builtin",
        "model": "openai/gpt-4o-mini",
        "description": "Prunes context to function signatures and uses terse instructions to minimize token usage.",
        "created_at": time.time()
    }
]


def seed_database():
    db = get_db()
    print("=" * 60)
    print("AgentArena: Seeding Firestore Database")
    print("=" * 60)

    # 1. Seed Builtin Agents
    print(f"\n[+] Seeding {len(BUILTIN_AGENTS)} Builtin Agents...")
    for agent in BUILTIN_AGENTS:
        db.collection("agents").document(agent["id"]).set(agent)
        print(f"  -> Agent '{agent['id']}' ({agent['name']}) seeded.")

    # 2. Seed Tasks from tasks/*.json
    task_dir = os.path.join(CURRENT_DIR, "tasks")
    task_files = glob.glob(os.path.join(task_dir, "*.json"))
    print(f"\n[+] Found {len(task_files)} task definitions in {task_dir}...")

    seeded_tasks_count = 0
    for task_path in task_files:
        try:
            with open(task_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                task_id = task_data.get("id")
                if task_id:
                    db.collection("tasks").document(task_id).set(task_data)
                    print(f"  -> Task '{task_id}': {task_data.get('title')} [{task_data.get('difficulty')}]")
                    seeded_tasks_count += 1
        except Exception as e:
            print(f"  [!] Failed to load {task_path}: {e}")

    print("=" * 60)
    print(f"Seeding completed successfully: {len(BUILTIN_AGENTS)} agents and {seeded_tasks_count} tasks loaded.")
    print("=" * 60)


if __name__ == "__main__":
    seed_database()

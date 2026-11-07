from typing import Dict, Any
from backend.agents.base import call_proxy_llm, extract_code_blocks


async def run_react_lite_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    ReAct-Lite agent: Plan -> Write -> Self-check loop (max 3 iterations).
    Calls LLM via llm_base_url.
    """
    task = payload.get("task", {})
    prompt = task.get("prompt", "")
    starter_files = task.get("files", {})
    llm_base_url = payload.get("llm_base_url")
    llm_api_key = payload.get("llm_api_key", "arena-key")
    model = payload.get("model", "openai/gpt-4o-mini")
    limits = payload.get("limits", {})
    timeout = float(limits.get("timeout", 45))

    files_context = ""
    for path, content in starter_files.items():
        files_context += f"\nFile: `{path}`\n```python\n{content}\n```\n"

    # Step 1: Plan and Initial Code Draft
    system_prompt = (
        "You are an analytical coding agent. First briefly outline your plan, "
        "then provide the complete code in a ```python ... ``` block."
    )
    user_prompt = f"Task:\n{prompt}\n\nFiles:\n{files_context}\n\nFormulate a plan and provide the initial implementation."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    resp1 = await call_proxy_llm(llm_base_url, llm_api_key, model, messages, temperature=0.2, timeout=timeout)
    draft_content = resp1.get("choices", [{}])[0].get("message", {}).get("content", "")
    current_files = extract_code_blocks(draft_content, default_filename="solution.py")

    # Step 2: Self-Check Loop
    messages.append({"role": "assistant", "content": draft_content})
    messages.append({
        "role": "user",
        "content": (
            "Carefully critique your draft above. Check for:\n"
            "1. Edge cases (empty inputs, zeroes, single-item collections, duplicates)\n"
            "2. Off-by-one errors or indexing bounds\n"
            "3. Time/space complexity constraints\n"
            "If your draft has any flaw, output the corrected code in a ```python ... ``` block.\n"
            "If it is already 100% correct and robust, reply with 'VERIFIED_CORRECT'."
        )
    })

    resp2 = await call_proxy_llm(llm_base_url, llm_api_key, model, messages, temperature=0.1, timeout=timeout)
    check_content = resp2.get("choices", [{}])[0].get("message", {}).get("content", "")

    if "VERIFIED_CORRECT" not in check_content:
        revised_files = extract_code_blocks(check_content, default_filename="solution.py")
        if revised_files:
            current_files = revised_files

    if not current_files:
        current_files = dict(starter_files)

    return {
        "files": current_files,
        "notes": f"ReAct-Lite completed 2-step plan -> self-check iteration."
    }


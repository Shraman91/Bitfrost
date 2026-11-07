from typing import Dict, Any
from backend.agents.base import call_proxy_llm, extract_code_blocks


async def run_naive_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive agent: single prompt, returns code.
    Calls LLM exactly once via llm_base_url.
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

    system_message = (
        "You are an expert software engineer. Solve the user's coding task.\n"
        "Output ONLY the complete solution code inside a markdown code block ```python ... ```.\n"
        "Do not include conversational chit-chat."
    )

    user_message = f"Task Description:\n{prompt}\n\nStarter Files:\n{files_context}\n\nPlease output the complete solution."

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    response = await call_proxy_llm(
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        model=model,
        messages=messages,
        temperature=0.2,
        timeout=timeout
    )

    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    files = extract_code_blocks(content, default_filename="solution.py")
    
    # If no files parsed, retain starter files
    if not files:
        files = dict(starter_files)

    return {
        "files": files,
        "notes": "Naive agent generated code in 1 step."
    }


from typing import Dict, Any
from backend.agents.base import call_proxy_llm, extract_code_blocks


async def run_token_saver_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Token-saver agent: sends only relevant snippets, terse prompts.
    Calls LLM via llm_base_url with pruned tokens.
    """
    task = payload.get("task", {})
    prompt = task.get("prompt", "")
    starter_files = task.get("files", {})
    llm_base_url = payload.get("llm_base_url")
    llm_api_key = payload.get("llm_api_key", "arena-key")
    model = payload.get("model", "openai/gpt-4o-mini")
    limits = payload.get("limits", {})
    timeout = float(limits.get("timeout", 45))

    # Prune starter files: keep only lines with def, class, or imports to save tokens
    pruned_files = ""
    for path, content in starter_files.items():
        lines = content.splitlines()
        sig_lines = [
            l for l in lines 
            if l.strip().startswith(("def ", "class ", "import ", "from ", "@")) or not l.strip()
        ]
        pruned_content = "\n".join(sig_lines[:20]) # Limit signature preview
        pruned_files += f"\n#{path}\n{pruned_content}\n"

    # Extremely terse system prompt to save prompt tokens
    system_prompt = "Code only. Format: ```python\n# solution.py\n<code>\n```"
    user_prompt = f"{prompt.strip()}\nSignatures:\n{pruned_files.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = await call_proxy_llm(
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        timeout=timeout
    )

    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    files = extract_code_blocks(content, default_filename="solution.py")
    
    if not files:
        files = dict(starter_files)

    return {
        "files": files,
        "notes": "Token-Saver completed with pruned context."
    }


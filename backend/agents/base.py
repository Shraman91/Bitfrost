import re
import httpx
from typing import Dict, List, Any


def extract_code_blocks(text: str, default_filename: str = "solution.py") -> Dict[str, str]:
    """
    Extracts code blocks from LLM markdown response.
    Supports:
    ```filename.py
    code
    ```
    or
    ```python
    # filename.py
    code
    ```
    """
    files: Dict[str, str] = {}
    
    # Pattern to match ```lang:filename or ```python\n# filename.py
    pattern = r"```(?:python|py)?[:\s]*([\w\.\-]+)?\n(.*?)```"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    if not matches:
        stripped = text.strip()
        if "def " in stripped or "class " in stripped or "import " in stripped:
            files[default_filename] = stripped
        return files

    for match in matches:
        filename_hint = match.group(1)
        code = match.group(2)

        # Check if first line inside code block specifies filename (e.g. # solution.py)
        first_line = code.strip().split("\n")[0] if code.strip() else ""
        if first_line.startswith("#") and any(ext in first_line for ext in [".py", ".txt", ".json"]):
            target_name = first_line.lstrip("#").strip()
            code = "\n".join(code.strip().split("\n")[1:])
        elif filename_hint and "." in filename_hint:
            target_name = filename_hint.strip()
        else:
            target_name = default_filename

        files[target_name] = code.strip() + "\n"

    if not files and matches:
        files[default_filename] = matches[0].group(2).strip() + "\n"

    return files


async def call_proxy_llm(
    llm_base_url: str,
    llm_api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 2048,
    timeout: float = 45.0
) -> Dict[str, Any]:
    """
    Calls the metering proxy at {llm_base_url}/chat/completions.
    Falls back to in-process proxy call if running standalone without HTTP daemon.
    """
    url = f"{llm_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {llm_api_key}"
    }

    try:
        timeout_cfg = httpx.Timeout(timeout=timeout, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException):
        # In-process direct proxy fallback
        match = re.search(r"/llm/([^/]+)/v1", llm_base_url)
        if match:
            run_id = match.group(1)
            from backend.routes.proxy import chat_completions_proxy
            from unittest.mock import AsyncMock, MagicMock
            mock_req = MagicMock()
            mock_req.json = AsyncMock(return_value=payload)
            mock_req.headers = headers
            return await chat_completions_proxy(run_id, mock_req)
        raise

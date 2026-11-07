import logging
import httpx
from typing import Dict, Any

from backend.agents.naive import run_naive_agent
from backend.agents.react_lite import run_react_lite_agent
from backend.agents.token_saver import run_token_saver_agent

logger = logging.getLogger("agentarena.dispatcher")


async def execute_agent(agent_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes an agent (builtin reference agent or external HTTP agent)
    adhering to the AgentArena contract:
    POST {agent_endpoint}/run
    body: { run_id, task: {prompt, files}, llm_base_url, llm_api_key, model, limits }
    response: { files: {path: content}, notes }
    """
    agent_type = agent_data.get("type", "builtin")
    agent_id = agent_data.get("id", "")

    if agent_type == "builtin":
        if "react" in agent_id.lower():
            return await run_react_lite_agent(payload)
        elif "token" in agent_id.lower():
            return await run_token_saver_agent(payload)
        else:
            return await run_naive_agent(payload)

    elif agent_type == "external_http":
        endpoint = agent_data.get("endpoint")
        if not endpoint:
            raise ValueError(f"External agent '{agent_id}' has no endpoint configured.")

        timeout_sec = float(payload.get("limits", {}).get("timeout", 60))
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.post(endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict) or "files" not in data:
                raise ValueError("External agent response missing required 'files' dict")
            return {
                "files": data.get("files", {}),
                "notes": data.get("notes", "Executed external agent")
            }

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


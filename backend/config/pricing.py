"""
Model token pricing dictionary (rates in USD per 1 Million tokens).
Rate format: (input_price_per_1m, output_price_per_1m)
"""
from typing import Dict, Tuple

MODEL_PRICING_PER_1M: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4-turbo": (10.00, 30.00),
    "openai/o1-mini": (3.00, 12.00),
    "openai/o1-preview": (15.00, 60.00),
    
    # Anthropic models
    "anthropic/claude-3-5-sonnet": (3.00, 15.00),
    "anthropic/claude-3-5-haiku": (0.80, 4.00),
    "anthropic/claude-3-opus": (15.00, 75.00),
    
    # Google Gemini models
    "gemini/gemini-1.5-flash": (0.075, 0.30),
    "gemini/gemini-1.5-pro": (1.25, 5.00),
    "gemini/gemini-2.0-flash": (0.10, 0.40),

    # Groq / Open source models
    "groq/llama-3.1-70b-versatile": (0.59, 0.79),
    "groq/llama-3.1-8b-instant": (0.05, 0.08),

    # Default fallback
    "default": (1.00, 3.00),
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the cost in USD for the given token usage."""
    # Match exact or normalized model string
    pricing = MODEL_PRICING_PER_1M.get(model)
    if not pricing:
        # Try stripping provider prefix if present or matching partial
        for key, p in MODEL_PRICING_PER_1M.items():
            if key in model or model in key:
                pricing = p
                break
    if not pricing:
        pricing = MODEL_PRICING_PER_1M["default"]

    in_price, out_price = pricing
    cost = (prompt_tokens * (in_price / 1_000_000.0)) + (completion_tokens * (out_price / 1_000_000.0))
    return round(cost, 8)


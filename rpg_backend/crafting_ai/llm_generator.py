from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from .crafting_text import sanitize_item_name

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


@dataclass
class LLMTextResult:
    name: str
    description: str
    source: str
    debug: dict[str, Any]


def _load_env() -> None:
    if load_dotenv is not None:
        # rpg_backend/.env or current working directory .env
        load_dotenv()


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty LLM response")
    # Responses API text may already be raw JSON, but be tolerant of fenced output.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start:end + 1]
    return json.loads(text)


def generate_item_text_openai(
    *,
    ingredient1_name: str,
    ingredient2_name: str,
    method: str,
    type_effect: str,
    effects: dict[str, Any],
    attributes: dict[str, Any],
    fallback_name: str,
    fallback_description: str,
) -> LLMTextResult:
    """Generate RPG item name/description with OpenAI when configured.

    If OPENAI_API_KEY is missing, the SDK is not installed, or the request fails,
    return the fallback text and include the reason in debug. This keeps the game
    playable during local development and demonstrations without an API key.
    """
    _load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_CRAFTING_MODEL", "gpt-4o-mini")

    base_debug: dict[str, Any] = {
        "provider": "openai",
        "model": model,
        "used": False,
        "fallback_used": True,
        "error": None,
    }

    if not api_key:
        base_debug["error"] = "OPENAI_API_KEY is not set. Used rule-based fallback text."
        return LLMTextResult(fallback_name, fallback_description, "rule_fallback_no_key", base_debug)
    if OpenAI is None:
        base_debug["error"] = "openai package is not installed. Used rule-based fallback text."
        return LLMTextResult(fallback_name, fallback_description, "rule_fallback_no_sdk", base_debug)

    prompt_payload = {
        "ingredient1": ingredient1_name,
        "ingredient2": ingredient2_name,
        "method": method,
        "type_effect": type_effect,
        "effects": effects,
        "attributes": attributes,
    }

    system = (
        "You create concise Korean RPG item names and descriptions for a crafting system. "
        "Return only valid JSON with keys item_name and item_note. "
        "The item_name must be short, natural, and suitable for an RPG inventory. "
        "Rules for item_name: Korean preferred, 4-16 characters recommended, 24 characters maximum, "
        "do not repeat words, do not simply concatenate both ingredient names, and do not include markdown. "
        "Examples of good names: 정화 회복약, 맹독 추출액, 수호 보호제, 불꽃 촉매, 서리 결정. "
        "The item_note must be 1-2 Korean sentences explaining ingredients, method, and main effect. "
        "Do not include markdown."
    )
    user = (
        "다음 제작 결과에 어울리는 한국어 아이템 이름과 설명을 JSON으로 만들어줘.\n"
        + json.dumps(prompt_payload, ensure_ascii=False)
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
            max_output_tokens=220,
        )
        raw_text = getattr(response, "output_text", "") or ""
        data = _extract_json(raw_text)
        raw_name = str(data.get("item_name") or "").strip()
        name, invalid_reason = sanitize_item_name(raw_name, fallback_name, max_len=24)
        desc = str(data.get("item_note") or fallback_description).strip()[:500]
        if not desc:
            desc = fallback_description
        used_fallback_name = invalid_reason is not None
        base_debug.update({
            "used": True,
            "fallback_used": used_fallback_name,
            "name_validation": invalid_reason or "ok",
            "raw_item_name": raw_name[:200],
            "raw_output": raw_text[:1000],
        })
        return LLMTextResult(name, desc, "openai" if not used_fallback_name else "openai_name_sanitized", base_debug)
    except Exception as exc:  # pragma: no cover - network/API dependent
        base_debug["error"] = str(exc)
        return LLMTextResult(fallback_name, fallback_description, "rule_fallback_openai_error", base_debug)

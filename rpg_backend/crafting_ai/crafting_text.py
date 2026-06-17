from __future__ import annotations

import re
from .constants import METHOD_KR

TYPE_SUFFIX = {
    "회복형": "회복약",
    "독성형": "독액",
    "공격형": "전투약",
    "방어형": "보호제",
    "폭발형": "폭탄",
    "속성형": "결정",
}

TYPE_NOTE = {
    "회복형": "체력 회복이나 저항 보조에 사용되는 제작 아이템입니다.",
    "독성형": "독성 성분을 응축한 위험한 제작 아이템입니다.",
    "공격형": "공격력을 높이거나 속성 피해를 일으키는 제작 아이템입니다.",
    "방어형": "방어력과 저항력을 높이는 제작 아이템입니다.",
    "폭발형": "불안정한 에너지를 담은 폭발성 제작 아이템입니다.",
    "속성형": "재료의 속성을 응축한 특수 제작 아이템입니다.",
}

ATTRIBUTE_NAME = {
    "healing": "치유",
    "toxic": "맹독",
    "poison": "맹독",
    "attack": "격전",
    "defense": "수호",
    "defensive": "수호",
    "hot": "불꽃",
    "burn": "불꽃",
    "cold": "서리",
    "freeze": "서리",
    "electric": "전류",
    "shock": "전류",
    "explosive": "폭발",
    "magical": "마력",
    "metallic": "강철",
    "plant": "초목",
    "organic": "생명",
    "holy": "성광",
    "dark": "암흑",
    "sharp": "예리",
    "stable": "안정",
    "unstable": "불안정",
    "pure": "정화",
}

TYPE_PREFIX = {
    "회복형": "정화",
    "독성형": "맹독",
    "공격형": "격전",
    "방어형": "수호",
    "폭발형": "폭발",
    "속성형": "마력",
}


def _dominant_attribute_word(effects: dict[str, int | float], type_effect: str) -> str:
    candidates = {
        "hp": float(effects.get("hp", 0) or 0),
        "poison": float(effects.get("poison", 0) or 0),
        "attack": float(effects.get("attack", 0) or 0),
        "defense": float(effects.get("defense", 0) or 0),
        "burn": float(effects.get("burn", 0) or 0),
        "freeze": float(effects.get("freeze", 0) or 0),
        "shock": float(effects.get("shock", 0) or 0),
        "explosion_damage": float(effects.get("explosion_damage", 0) or 0),
    }
    best_key = max(candidates, key=candidates.get)
    if candidates[best_key] > 0:
        return ATTRIBUTE_NAME.get(best_key, TYPE_PREFIX.get(type_effect, "제작"))
    return TYPE_PREFIX.get(type_effect, "제작")


def _dedupe_words(text: str) -> str:
    words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
    result: list[str] = []
    for word in words:
        if result and result[-1] == word:
            continue
        if result.count(word) >= 1 and len(word) >= 2:
            # Avoid names such as "구운 구운 낡은 뼈다귀 낡은 뼈다귀 ...".
            continue
        result.append(word)
    return " ".join(result).strip()


def validate_item_name(name: str, max_len: int = 24) -> tuple[bool, str]:
    cleaned = _dedupe_words(str(name or "").replace("\n", " "))
    if not cleaned:
        return False, "empty"
    if len(cleaned) > max_len:
        return False, f"too_long:{len(cleaned)}"
    words = cleaned.split()
    if len(words) >= 7:
        return False, "too_many_words"
    if any(len(w) > 18 for w in words):
        return False, "word_too_long"
    return True, "ok"


def sanitize_item_name(name: str, fallback: str, max_len: int = 24) -> tuple[str, str | None]:
    cleaned = _dedupe_words(str(name or "").replace("\n", " "))
    ok, reason = validate_item_name(cleaned, max_len=max_len)
    if ok:
        return cleaned, None
    fallback_cleaned = _dedupe_words(fallback)[:max_len].strip()
    return fallback_cleaned or "AI 제작품", reason


def build_item_name_note(
    ingredient1_name: str,
    ingredient2_name: str,
    method: str,
    type_effect: str,
    effects: dict[str, int | float],
) -> tuple[str, str]:
    """Build a short rule-based fallback name and description.

    The fallback intentionally avoids concatenating both ingredient names into
    the item name. Ingredient names are kept in the description instead, because
    repeated crafting of generated items can otherwise create very long names.
    """
    method_kr = METHOD_KR.get(method.upper(), method.upper())
    suffix = TYPE_SUFFIX.get(type_effect, "제작품")
    prefix = _dominant_attribute_word(effects, type_effect)

    # Keep fallback names compact for inventory UI and DB reuse.
    name = f"{prefix} {suffix}"
    name, _ = sanitize_item_name(name, fallback=f"{prefix} {suffix}")

    major_effects = []
    for key, label in [
        ("hp", "체력 회복"), ("poison", "독 피해"), ("attack", "공격력 증가"),
        ("defense", "방어력 증가"), ("resistance", "저항 증가"),
        ("burn", "화상"), ("freeze", "빙결"), ("shock", "감전"),
        ("explosion_damage", "폭발 피해"),
    ]:
        value = int(round(float(effects.get(key, 0) or 0)))
        if value > 0:
            major_effects.append(f"{label} {value}")
    effect_text = ", ".join(major_effects[:3]) if major_effects else "약한 보조 효과"
    note = (
        f"{ingredient1_name}와 {ingredient2_name}을(를) {method_kr} 방식으로 조합해 만든 {type_effect} 아이템입니다. "
        f"주요 효과: {effect_text}. {TYPE_NOTE.get(type_effect, '')}"
    ).strip()
    return name, note

from __future__ import annotations

ATTRIBUTES = [
    "toxic", "healing", "viscous", "stable", "organic", "plant", "unstable", "burnt",
    "neutral", "pure", "metallic", "magical", "cold", "hot", "electric", "explosive",
    "fragile", "dense", "dark", "holy", "sharp", "defensive",
]

EFFECT_COLUMNS = [
    "hp", "poison", "duration", "attack", "defense", "speed", "resistance",
    "burn", "freeze", "shock", "explosion_damage",
]

METHODS = ["MIX", "BOIL", "BAKE", "DISTILL", "COMPRESS", "INFUSE"]

METHOD_ALIASES = {
    "mix": "MIX", "MIX": "MIX", "혼합": "MIX",
    "boil": "BOIL", "BOIL": "BOIL", "끓이기": "BOIL", "끓임": "BOIL",
    "bake": "BAKE", "BAKE": "BAKE", "굽기": "BAKE",
    "distill": "DISTILL", "DISTILL": "DISTILL", "증류": "DISTILL",
    "compress": "COMPRESS", "COMPRESS": "COMPRESS", "압축": "COMPRESS",
    "infuse": "INFUSE", "INFUSE": "INFUSE", "주입": "INFUSE",
}

METHOD_KR = {
    "MIX": "혼합", "BOIL": "끓인", "BAKE": "구운", "DISTILL": "증류한",
    "COMPRESS": "압축한", "INFUSE": "주입한",
}

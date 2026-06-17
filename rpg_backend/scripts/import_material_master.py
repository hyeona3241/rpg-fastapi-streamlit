"""Import material_master_dataset_120.xlsx into MyRPG Item / ItemAttribute.

Usage:
    python scripts/import_material_master.py ../../material_master_dataset_120.xlsx

This is optional but recommended before AI crafting tests so DB item attributes
match the crafting dataset. It expects the xlsx to contain a `materials` sheet
with columns like name_kr, category, rarity, toxic, healing, ... defensive.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://rpg:rpg@localhost:3306/MyRPG"
ATTRIBUTES = [
    "toxic", "healing", "viscous", "stable", "organic", "plant", "unstable", "burnt",
    "neutral", "pure", "metallic", "magical", "cold", "hot", "electric", "explosive",
    "fragile", "dense", "dark", "holy", "sharp", "defensive",
]


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/import_material_master.py <material_master_dataset_120.xlsx>")
    xlsx_path = Path(sys.argv[1])
    if not xlsx_path.exists():
        raise SystemExit(f"File not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name="materials")
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            name = str(row.get("name_kr", "")).strip()
            if not name:
                continue
            category = str(row.get("category", "material") or "material").strip().lower()
            rarity = str(row.get("rarity", "common") or "common").strip().upper()
            note = f"AI 크래프팅 재료 데이터셋에서 가져온 {category} 재료입니다."

            item_id = conn.execute(text("SELECT id FROM Item WHERE name = :name"), {"name": name}).scalar()
            if item_id is None:
                result = conn.execute(
                    text(
                        """
                        INSERT INTO Item (name, description, type, sub_type, capacity, rarity, is_generated)
                        VALUES (:name, :description, 'material', :sub_type, -1, :rarity, FALSE)
                        """
                    ),
                    {"name": name, "description": note, "sub_type": category, "rarity": rarity},
                )
                item_id = result.lastrowid
            else:
                conn.execute(
                    text("UPDATE Item SET type='material', sub_type=:sub_type, rarity=:rarity WHERE id=:id"),
                    {"sub_type": category, "rarity": rarity, "id": item_id},
                )

            attrs = {attr: float(row.get(attr, 0) or 0) for attr in ATTRIBUTES}
            placeholders = ", ".join([f":{attr}" for attr in ATTRIBUTES])
            updates = ", ".join([f"{attr}=VALUES({attr})" for attr in ATTRIBUTES])
            conn.execute(
                text(
                    f"""
                    INSERT INTO ItemAttribute (item_id, {', '.join(ATTRIBUTES)})
                    VALUES (:item_id, {placeholders})
                    ON DUPLICATE KEY UPDATE {updates}
                    """
                ),
                {"item_id": item_id, **attrs},
            )

    print(f"Imported {len(df)} material rows from {xlsx_path}")


if __name__ == "__main__":
    main()

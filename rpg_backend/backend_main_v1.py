import random
import uuid
from typing import List, Optional

import uvicorn
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://rpg:rpg@localhost:3306/MyRPG"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session_store: dict[str, dict] = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# SQLAlchemy Models
# =========================
class UserModel(Base):
    __tablename__ = "User"
    id = Column(String(20), primary_key=True)
    user_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="USER")
    active = Column(Boolean, nullable=False, default=True)


class ActorModel(Base):
    __tablename__ = "Actor"
    id = Column(Integer, primary_key=True, autoincrement=True)


class CharacterModel(Base):
    __tablename__ = "Character"
    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    user_id = Column(String(20), ForeignKey("User.id"), nullable=False)
    character_name = Column(String(255), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class StatModel(Base):
    __tablename__ = "Stat"
    type = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)


class ActorStatModel(Base):
    __tablename__ = "ActorStat"
    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    stat_type = Column(String(50), ForeignKey("Stat.type"), primary_key=True)
    value = Column(Integer, nullable=False)


class LevelBaseStatModel(Base):
    __tablename__ = "LevelBaseStat"
    char_level = Column(Integer, primary_key=True)
    stat_type = Column(String(50), ForeignKey("Stat.type"), primary_key=True)
    value = Column(Integer, nullable=False)


class SpecimenModel(Base):
    __tablename__ = "Specimen"
    type = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)


class SpecimenBaseStatModel(Base):
    __tablename__ = "SpecimenBaseStat"
    specimen_type = Column(String(50), ForeignKey("Specimen.type"), primary_key=True)
    stat_type = Column(String(50), ForeignKey("Stat.type"), primary_key=True)
    value = Column(Integer, nullable=False)


class CharacterSpecimenModel(Base):
    __tablename__ = "CharacterSpecimen"
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    type = Column(String(50), ForeignKey("Specimen.type"), primary_key=True)
    fraction = Column(Float, nullable=False)


class JobModel(Base):
    __tablename__ = "Job"
    type = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    reference_image = Column(String(255))
    unlock_condition_id = Column(Integer)


class CharacterJobModel(Base):
    __tablename__ = "CharacterJob"
    type = Column(String(50), ForeignKey("Job.type"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    obtain_date = Column(DateTime, server_default=func.now())
    active = Column(Boolean, nullable=False, default=False)


class SkillModel(Base):
    __tablename__ = "Skill"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mp_cost = Column(Integer, nullable=False, default=0)
    cooldown_sec = Column(Integer, nullable=False, default=0)
    unlock_condition_id = Column(Integer)


class CharacterSkillModel(Base):
    __tablename__ = "CharacterSkill"
    skill_id = Column(Integer, ForeignKey("Skill.id"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    skill_level = Column(Float, nullable=False, default=0.0)


class InventoryModel(Base):
    __tablename__ = "Inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("Character.actor_id"), nullable=False)
    type = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)


class ItemModel(Base):
    __tablename__ = "Item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    sub_type = Column(String(50))
    capacity = Column(Integer, default=-1)
    icon_url = Column(Text)
    equipment_part = Column(String(50))
    required_level = Column(Integer, nullable=False, default=1)
    rarity = Column(String(50), nullable=False, default="COMMON")
    is_generated = Column(Boolean, nullable=False, default=False)


class InventoryItemModel(Base):
    __tablename__ = "InventoryItem"
    inventory_id = Column(Integer, ForeignKey("Inventory.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)


class EquippedSkillModel(Base):
    __tablename__ = "EquippedSkill"
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    slot_no = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("Skill.id"), nullable=False)
    equipped_at = Column(DateTime, server_default=func.now())


class MonsterModel(Base):
    __tablename__ = "Monster"
    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    hp = Column(Integer, nullable=False)
    atk = Column(Integer, nullable=False)
    def_ = Column("def", Integer, nullable=False)
    drop_reward_id = Column(Integer)
    # Demo/UI columns added by patch_battle_monster_display.sql
    name = Column(String(100))
    description = Column(Text)
    level = Column(Integer, nullable=False, default=1)


class RewardItemModel(Base):
    __tablename__ = "RewardItem"
    reward_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    drop_probability = Column(Float)


class RewardExpModel(Base):
    __tablename__ = "RewardExp"
    reward_id = Column(Integer, primary_key=True)
    amount = Column(Integer, nullable=False, default=0)


class EquipmentPartModel(Base):
    __tablename__ = "EquipmentPart"
    type = Column(String(50), primary_key=True)


class ItemBonusStatModel(Base):
    __tablename__ = "ItemBonusStat"
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    stat_type = Column(String(50), ForeignKey("Stat.type"), primary_key=True)
    value = Column(Integer, nullable=False, default=0)


class CharacterEquipmentModel(Base):
    __tablename__ = "CharacterEquipment"
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    equipment_part = Column(String(50), ForeignKey("EquipmentPart.type"), primary_key=True)
    inventory_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, primary_key=True)


class QuestModel(Base):
    __tablename__ = "Quest"
    id = Column(Integer, primary_key=True, autoincrement=True)
    unlock_condition_id = Column(Integer)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    max_steps = Column(Integer, nullable=False, default=1)
    type = Column(String(50), nullable=False, default="side")
    is_repeatable = Column(Boolean, nullable=False, default=False)
    prerequisite_quest_id = Column(Integer, nullable=True)
    next_quest_id = Column(Integer, nullable=True)
    reward_id = Column(Integer, nullable=True)


class CharacterQuestModel(Base):
    __tablename__ = "CharacterQuest"
    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    start_time = Column(DateTime, server_default=func.now())
    status = Column(String(50), nullable=False, default="active")
    current_step = Column(Integer, nullable=False, default=0)


class QuestObjectiveModel(Base):
    __tablename__ = "QuestObjective"
    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    objective_type = Column(String(50), primary_key=True)
    target_id = Column(Integer, primary_key=True)
    required_count = Column(Integer, nullable=False, default=1)


class CharacterQuestProgressModel(Base):
    __tablename__ = "CharacterQuestProgress"
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    objective_type = Column(String(50), primary_key=True)
    target_id = Column(Integer, primary_key=True)
    current_count = Column(Integer, nullable=False, default=0)


class ItemEffectModel(Base):
    __tablename__ = "ItemEffect"
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    type_effect = Column(String(50))
    hp = Column(Integer, nullable=False, default=0)
    poison = Column(Integer, nullable=False, default=0)
    duration = Column(Integer, nullable=False, default=0)
    attack = Column(Integer, nullable=False, default=0)
    defense = Column(Integer, nullable=False, default=0)
    speed = Column(Integer, nullable=False, default=0)
    resistance = Column(Integer, nullable=False, default=0)
    burn = Column(Integer, nullable=False, default=0)
    freeze = Column(Integer, nullable=False, default=0)
    shock = Column(Integer, nullable=False, default=0)
    explosion_damage = Column(Integer, nullable=False, default=0)




class ItemAttributeModel(Base):
    __tablename__ = "ItemAttribute"
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    toxic = Column(Float, nullable=False, default=0)
    healing = Column(Float, nullable=False, default=0)
    viscous = Column(Float, nullable=False, default=0)
    stable = Column(Float, nullable=False, default=0)
    organic = Column(Float, nullable=False, default=0)
    plant = Column(Float, nullable=False, default=0)
    unstable = Column(Float, nullable=False, default=0)
    burnt = Column(Float, nullable=False, default=0)
    neutral = Column(Float, nullable=False, default=0)
    pure = Column(Float, nullable=False, default=0)
    metallic = Column(Float, nullable=False, default=0)
    magical = Column(Float, nullable=False, default=0)
    cold = Column(Float, nullable=False, default=0)
    hot = Column(Float, nullable=False, default=0)
    electric = Column(Float, nullable=False, default=0)
    explosive = Column(Float, nullable=False, default=0)
    fragile = Column(Float, nullable=False, default=0)
    dense = Column(Float, nullable=False, default=0)
    dark = Column(Float, nullable=False, default=0)
    holy = Column(Float, nullable=False, default=0)
    sharp = Column(Float, nullable=False, default=0)
    defensive = Column(Float, nullable=False, default=0)


class CraftingMethodModel(Base):
    __tablename__ = "CraftingMethod"
    method = Column(String(50), primary_key=True)
    description = Column(Text)


class CraftingRecipeModel(Base):
    __tablename__ = "CraftingRecipe"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient1_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    ingredient2_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    method = Column(String(50), ForeignKey("CraftingMethod.method"), nullable=False)
    result_item_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    created_by_ai = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())


class CraftingLogModel(Base):
    __tablename__ = "CraftingLog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("CraftingRecipe.id"), nullable=False)
    ingredient1_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    ingredient2_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    method = Column(String(50), ForeignKey("CraftingMethod.method"), nullable=False)
    result_item_id = Column(Integer, ForeignKey("Item.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class BattleSessionModel(Base):
    __tablename__ = "BattleSession"
    id = Column(Integer, primary_key=True, autoincrement=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), nullable=False)
    monster_id = Column(Integer, ForeignKey("Monster.actor_id"), nullable=False)
    current_monster_hp = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    reward_claimed = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)


# =========================
# Pydantic Schemas
# =========================
class UserLogin(BaseModel):
    user_id: str
    password: str


class UserCreate(BaseModel):
    user_identifier: str
    nickname: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    user_name: str
    role: str = "USER"
    active: bool = True


class AdminUserResponse(BaseModel):
    user_id: str
    user_name: str
    role: str
    active: bool
    character_count: int = 0


class UserActiveUpdate(BaseModel):
    active: bool


class AdminBattleStatusUpdate(BaseModel):
    status: str = "ABANDONED"


class QuantityPayload(BaseModel):
    quantity: int = Field(gt=0)


class AdminGrantItemPayload(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)


class SkillEquipPayload(BaseModel):
    skill_id: int
    slot_no: int = Field(ge=1, le=3)


class SkillUnequipPayload(BaseModel):
    slot_no: int = Field(ge=1, le=3)


class EquipmentEquipPayload(BaseModel):
    item_id: int
    equipment_part: Optional[str] = None


class EquipmentUnequipPayload(BaseModel):
    equipment_part: str


class BattleStartPayload(BaseModel):
    monster_id: int


class BattleAttackPayload(BaseModel):
    battle_id: int
    skill_id: int


class CraftingPayload(BaseModel):
    ingredient1_id: int
    ingredient2_id: int
    method: str


class SpecimenResponse(BaseModel):
    type: str
    name: str
    description: Optional[str] = None


class JobResponse(BaseModel):
    type: str
    name: str
    description: Optional[str] = None


class SpecimenInput(BaseModel):
    type: str
    fraction: float = Field(gt=0, le=1)


class CharacterCreate(BaseModel):
    character_name: str
    specimens: List[SpecimenInput] = Field(default_factory=list)
    job_type: Optional[str] = None


class CharacterResponse(BaseModel):
    actor_id: int
    user_id: str
    character_name: str
    level: int
    exp: int
    active: bool
    is_public: bool = False


app = FastAPI(title="MyRPG Game Server API", description="Streamlit RPG REST API")


def get_current_user(session_id: str | None = Cookie(default=None)):
    if not session_id:
        return None
    return session_store.get(session_id)


def require_user(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    return current_user


def require_admin(current_user=Depends(require_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return current_user


def get_active_character(db: Session, user_id: str) -> CharacterModel | None:
    return db.query(CharacterModel).filter(
        CharacterModel.user_id == user_id,
        CharacterModel.active == True,  # noqa: E712
    ).first()


def calculate_initial_stats(db: Session, specimens: list[SpecimenInput], job_type: str | None = None) -> dict[str, int]:
    stats: dict[str, float] = {}

    # Level 1 base stats
    for row in db.query(LevelBaseStatModel).filter(LevelBaseStatModel.char_level == 1).all():
        stats[row.stat_type] = stats.get(row.stat_type, 0) + row.value

    # Weighted specimen stats
    for specimen in specimens:
        rows = db.query(SpecimenBaseStatModel).filter(SpecimenBaseStatModel.specimen_type == specimen.type).all()
        for row in rows:
            stats[row.stat_type] = stats.get(row.stat_type, 0) + row.value * specimen.fraction

    # Lightweight job bonus: keep this in application code so it works even if the
    # legacy DB has no JobBaseStat table. It only affects initial stats.
    for stat_type, value in get_job_initial_bonus(job_type).items():
        stats[stat_type] = stats.get(stat_type, 0) + value

    return {stat_type: int(round(value)) for stat_type, value in stats.items()}


def normalize_job_type(job_type: str | None) -> str | None:
    if not job_type:
        return None
    return job_type.strip().upper()


def get_job_initial_bonus(job_type: str | None) -> dict[str, int]:
    job = normalize_job_type(job_type)
    # Common aliases are included because seed data may use either Korean labels or
    # English enum-like values depending on which SQL file was used.
    if job in {"WARRIOR", "KNIGHT", "FIGHTER", "전사", "기사"}:
        return {"ATK": 5, "DEF": 3, "MAX_HP": 15, "HP": 15}
    if job in {"MAGE", "WIZARD", "SORCERER", "마법사", "법사"}:
        return {"INT": 7, "MAX_MP": 20, "MP": 20}
    if job in {"ROGUE", "ASSASSIN", "THIEF", "도적", "암살자"}:
        return {"AGI": 6, "ATK": 3}
    if job in {"ARCHER", "RANGER", "궁수"}:
        return {"AGI": 4, "ATK": 4}
    return {}


def get_job_skill_keywords(job_type: str | None) -> list[str]:
    job = normalize_job_type(job_type)
    if job in {"WARRIOR", "KNIGHT", "FIGHTER", "전사", "기사"}:
        return ["slash", "strike", "power", "검", "베기", "강타"]
    if job in {"MAGE", "WIZARD", "SORCERER", "마법사", "법사"}:
        return ["fire", "magic", "ice", "bolt", "마법", "화염", "파이어", "얼음"]
    if job in {"ROGUE", "ASSASSIN", "THIEF", "도적", "암살자"}:
        return ["stab", "poison", "shadow", "독", "암습", "찌르기"]
    if job in {"ARCHER", "RANGER", "궁수"}:
        return ["arrow", "shot", "wind", "화살", "사격", "바람"]
    return []


def get_initial_skills_for_job(db: Session, job_type: str | None) -> list[SkillModel]:
    skills = db.query(SkillModel).filter(SkillModel.unlock_condition_id.is_(None)).all()
    keywords = get_job_skill_keywords(job_type)
    if keywords:
        matched = []
        for skill in db.query(SkillModel).all():
            text_value = f"{skill.name or ''} {skill.description or ''}".lower()
            if any(keyword.lower() in text_value for keyword in keywords):
                matched.append(skill)
        for skill in matched:
            if skill not in skills:
                skills.append(skill)
    return skills


def get_or_create_basic_inventory(db: Session, char_id: int) -> InventoryModel:
    inventory = db.query(InventoryModel).filter(InventoryModel.owner_id == char_id).order_by(InventoryModel.id.asc()).first()
    if inventory:
        return inventory
    inventory = InventoryModel(owner_id=char_id, type="BASIC", capacity=20)
    db.add(inventory)
    db.flush()
    return inventory


def add_item_to_character_inventory(db: Session, char_id: int, item_id: int, quantity: int) -> InventoryItemModel:
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")

    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

    inventory = get_or_create_basic_inventory(db, char_id)
    inv_item = db.query(InventoryItemModel).filter(
        InventoryItemModel.inventory_id == inventory.id,
        InventoryItemModel.item_id == item_id,
    ).first()
    if inv_item:
        inv_item.quantity += quantity
    else:
        inv_item = InventoryItemModel(inventory_id=inventory.id, item_id=item_id, quantity=quantity)
        db.add(inv_item)
    db.flush()
    return inv_item


def serialize_inventory_item(row) -> dict:
    return {
        "item_id": row.item_id,
        "name": row.name,
        "description": row.description,
        "type": row.type,
        "sub_type": row.sub_type,
        "quantity": row.quantity,
        "capacity": row.capacity,
        "icon_url": getattr(row, "icon_url", None),
        "equipment_part": getattr(row, "equipment_part", None),
        "required_level": getattr(row, "required_level", 1),
        "rarity": getattr(row, "rarity", "COMMON"),
        "is_generated": getattr(row, "is_generated", False),
    }


def get_stat_value(db: Session, actor_id: int, stat_type: str, default: int = 0) -> int:
    stat = db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == actor_id,
        ActorStatModel.stat_type == stat_type,
    ).first()
    return stat.value if stat else default


def set_stat_value(db: Session, actor_id: int, stat_type: str, value: int) -> None:
    stat = db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == actor_id,
        ActorStatModel.stat_type == stat_type,
    ).first()
    if stat:
        stat.value = int(value)
    else:
        db.add(ActorStatModel(actor_id=actor_id, stat_type=stat_type, value=int(value)))


def get_equipped_items(db: Session, actor_id: int) -> list[dict]:
    rows = (
        db.query(CharacterEquipmentModel, ItemModel)
        .join(ItemModel, CharacterEquipmentModel.item_id == ItemModel.id)
        .filter(CharacterEquipmentModel.char_id == actor_id)
        .order_by(CharacterEquipmentModel.equipment_part.asc())
        .all()
    )
    result: list[dict] = []
    for equipment, item in rows:
        bonuses = db.query(ItemBonusStatModel).filter(ItemBonusStatModel.item_id == item.id).all()
        result.append({
            "equipment_part": equipment.equipment_part,
            "inventory_id": equipment.inventory_id,
            "item_id": item.id,
            "name": item.name,
            "description": item.description,
            "type": item.type,
            "sub_type": item.sub_type,
            "required_level": getattr(item, "required_level", 1),
            "rarity": getattr(item, "rarity", "COMMON"),
            "bonuses": {bonus.stat_type: bonus.value for bonus in bonuses},
        })
    return result


def get_equipment_bonus_stats(db: Session, actor_id: int) -> dict[str, int]:
    bonuses: dict[str, int] = {}
    rows = (
        db.query(ItemBonusStatModel.stat_type, ItemBonusStatModel.value)
        .join(CharacterEquipmentModel, CharacterEquipmentModel.item_id == ItemBonusStatModel.item_id)
        .filter(CharacterEquipmentModel.char_id == actor_id)
        .all()
    )
    for stat_type, value in rows:
        bonuses[stat_type] = bonuses.get(stat_type, 0) + int(value or 0)
    return bonuses


def get_base_stats(db: Session, actor_id: int) -> dict[str, int]:
    return {row.stat_type: int(row.value) for row in db.query(ActorStatModel).filter(ActorStatModel.actor_id == actor_id).all()}


def get_final_stats(db: Session, actor_id: int) -> dict[str, dict[str, int]]:
    base = get_base_stats(db, actor_id)
    bonus = get_equipment_bonus_stats(db, actor_id)
    stat_types = sorted(set(base.keys()) | set(bonus.keys()))
    final = {stat: int(base.get(stat, 0)) + int(bonus.get(stat, 0)) for stat in stat_types}
    return {"base": base, "equipment_bonus": bonus, "final": final}


def get_final_stat_value(db: Session, actor_id: int, stat_type: str, default: int = 0) -> int:
    stats = get_final_stats(db, actor_id)["final"]
    return int(stats.get(stat_type, default))


def has_active_battle(db: Session, actor_id: int) -> bool:
    return db.query(BattleSessionModel).filter(
        BattleSessionModel.char_id == actor_id,
        BattleSessionModel.status == "ACTIVE",
    ).first() is not None


def get_character_resources(db: Session, actor_id: int) -> dict:
    # MAX_HP/MAX_MP는 장비 보너스를 포함한 최종 최대치를 사용한다.
    max_hp = get_final_stat_value(db, actor_id, "MAX_HP", default=get_stat_value(db, actor_id, "MAX_HP", default=100))
    max_mp = get_final_stat_value(db, actor_id, "MAX_MP", default=get_stat_value(db, actor_id, "MAX_MP", default=50))
    hp = get_stat_value(db, actor_id, "HP", default=max_hp)
    mp = get_stat_value(db, actor_id, "MP", default=max_mp)

    # If current HP/MP rows are missing, create them from max values so UI and battle can update them.
    if not db.query(ActorStatModel).filter(ActorStatModel.actor_id == actor_id, ActorStatModel.stat_type == "HP").first():
        set_stat_value(db, actor_id, "HP", hp)
    if not db.query(ActorStatModel).filter(ActorStatModel.actor_id == actor_id, ActorStatModel.stat_type == "MP").first():
        set_stat_value(db, actor_id, "MP", mp)

    hp = max(0, min(hp, max_hp))
    mp = max(0, min(mp, max_mp))
    return {"hp": hp, "max_hp": max_hp, "mp": mp, "max_mp": max_mp}


def apply_resource_change(db: Session, actor_id: int, hp_delta: int = 0, mp_delta: int = 0) -> dict:
    resources = get_character_resources(db, actor_id)
    new_hp = max(0, min(resources["max_hp"], resources["hp"] + hp_delta))
    new_mp = max(0, min(resources["max_mp"], resources["mp"] + mp_delta))
    set_stat_value(db, actor_id, "HP", new_hp)
    set_stat_value(db, actor_id, "MP", new_mp)
    return {"hp": new_hp, "max_hp": resources["max_hp"], "mp": new_mp, "max_mp": resources["max_mp"]}


def get_level_requirement(db: Session, level: int) -> int | None:
    row = db.execute(
        text("SELECT max_exp_to_next FROM LevelMaster WHERE level = :level"),
        {"level": level},
    ).first()
    if not row:
        return None
    return int(row.max_exp_to_next)


def apply_level_resources(db: Session, character: CharacterModel) -> dict:
    """레벨업 시 LevelMaster 기준으로 MAX_HP/MAX_MP를 갱신하고 HP/MP를 모두 회복한다."""
    row = db.execute(
        text("SELECT max_hp, max_mp FROM LevelMaster WHERE level = :level"),
        {"level": character.level},
    ).first()

    if row:
        max_hp = int(row.max_hp or get_stat_value(db, character.actor_id, "MAX_HP", 100))
        max_mp = int(row.max_mp or get_stat_value(db, character.actor_id, "MAX_MP", 50))
    else:
        # LevelMaster에 다음 레벨 데이터가 없으면 기존 최대치를 유지한다.
        max_hp = get_stat_value(db, character.actor_id, "MAX_HP", 100)
        max_mp = get_stat_value(db, character.actor_id, "MAX_MP", 50)

    set_stat_value(db, character.actor_id, "MAX_HP", max_hp)
    set_stat_value(db, character.actor_id, "MAX_MP", max_mp)
    set_stat_value(db, character.actor_id, "HP", max_hp)
    set_stat_value(db, character.actor_id, "MP", max_mp)
    return {"hp": max_hp, "max_hp": max_hp, "mp": max_mp, "max_mp": max_mp}


def add_exp_to_character(db: Session, character: CharacterModel, amount: int) -> dict:
    """경험치를 지급하고 레벨업/HP·MP 회복 결과를 반환한다.

    Character.exp는 '현재 레벨에서 진행 중인 경험치'로 사용한다.
    예: Lv.1 80/100 상태에서 +50 → Lv.2 30/다음 필요치.
    """
    result = {
        "gained_exp": max(0, int(amount or 0)),
        "level_before": character.level,
        "level_after": character.level,
        "leveled_up": False,
        "level_up_count": 0,
        "exp": character.exp,
        "exp_to_next": get_level_requirement(db, character.level),
        "resources_restored": False,
    }
    if amount <= 0:
        return result

    character.exp += int(amount)
    while True:
        needed = get_level_requirement(db, character.level)
        if needed is None or needed <= 0 or character.exp < needed:
            break
        character.exp -= needed
        character.level += 1
        result["leveled_up"] = True
        result["level_up_count"] += 1

    if result["leveled_up"]:
        apply_level_resources(db, character)
        result["resources_restored"] = True

    result["level_after"] = character.level
    result["exp"] = character.exp
    result["exp_to_next"] = get_level_requirement(db, character.level)
    return result


def grant_reward_to_character(db: Session, character: CharacterModel, reward_id: int | None) -> dict:
    if not reward_id:
        return {"exp": 0, "items": [], "level": None}

    exp_row = db.query(RewardExpModel).filter(RewardExpModel.reward_id == reward_id).first()
    exp_amount = exp_row.amount if exp_row else 0
    level_result = add_exp_to_character(db, character, exp_amount)

    granted_items: list[dict] = []
    reward_items = db.query(RewardItemModel).filter(RewardItemModel.reward_id == reward_id).all()
    for reward_item in reward_items:
        probability = reward_item.drop_probability
        if probability is None:
            probability = 1.0
        if random.random() <= float(probability):
            inv_item = add_item_to_character_inventory(db, character.actor_id, reward_item.item_id, reward_item.quantity)
            item = db.query(ItemModel).filter(ItemModel.id == reward_item.item_id).first()
            granted_items.append({
                "item_id": reward_item.item_id,
                "name": item.name if item else f"Item {reward_item.item_id}",
                "quantity": reward_item.quantity,
                "current_quantity": inv_item.quantity,
            })
    return {"exp": exp_amount, "items": granted_items, "level": level_result}


def serialize_quest(db: Session, quest: QuestModel, character: CharacterModel | None = None) -> dict:
    objectives = db.query(QuestObjectiveModel).filter(QuestObjectiveModel.quest_id == quest.id).all()
    progress_map: dict[tuple[str, int], int] = {}
    char_quest = None
    if character:
        char_quest = db.query(CharacterQuestModel).filter(
            CharacterQuestModel.char_id == character.actor_id,
            CharacterQuestModel.quest_id == quest.id,
        ).first()
        progress_rows = db.query(CharacterQuestProgressModel).filter(
            CharacterQuestProgressModel.char_id == character.actor_id,
            CharacterQuestProgressModel.quest_id == quest.id,
        ).all()
        progress_map = {(row.objective_type, row.target_id): int(row.current_count or 0) for row in progress_rows}

    objective_list = []
    can_complete = True if objectives else False
    for obj in objectives:
        current = progress_map.get((obj.objective_type, obj.target_id), 0)
        required = int(obj.required_count or 1)
        objective_list.append({
            "objective_type": obj.objective_type,
            "target_id": obj.target_id,
            "required_count": required,
            "current_count": min(current, required),
            "completed": current >= required,
        })
        if current < required:
            can_complete = False

    reward_exp = 0
    reward_items = []
    if quest.reward_id:
        exp_row = db.query(RewardExpModel).filter(RewardExpModel.reward_id == quest.reward_id).first()
        reward_exp = int(exp_row.amount) if exp_row else 0
        for reward_item in db.query(RewardItemModel).filter(RewardItemModel.reward_id == quest.reward_id).all():
            item = db.query(ItemModel).filter(ItemModel.id == reward_item.item_id).first()
            reward_items.append({
                "item_id": reward_item.item_id,
                "name": item.name if item else f"Item {reward_item.item_id}",
                "quantity": reward_item.quantity,
                "drop_probability": reward_item.drop_probability,
            })

    return {
        "quest_id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "type": quest.type,
        "is_repeatable": bool(quest.is_repeatable),
        "prerequisite_quest_id": quest.prerequisite_quest_id,
        "next_quest_id": quest.next_quest_id,
        "reward_id": quest.reward_id,
        "status": char_quest.status if char_quest else "not_accepted",
        "current_step": char_quest.current_step if char_quest else 0,
        "objectives": objective_list,
        "can_complete": can_complete and (char_quest is not None and char_quest.status == "active"),
        "reward": {"exp": reward_exp, "items": reward_items},
    }


def update_quest_progress(db: Session, char_id: int, objective_type: str, target_id: int, amount: int = 1) -> list[dict]:
    """활성 퀘스트 중 objective_type/target_id가 맞는 진행도를 증가시킨다."""
    if amount <= 0:
        return []
    updated: list[dict] = []
    active_quests = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.char_id == char_id,
        CharacterQuestModel.status == "active",
    ).all()
    for cq in active_quests:
        obj = db.query(QuestObjectiveModel).filter(
            QuestObjectiveModel.quest_id == cq.quest_id,
            QuestObjectiveModel.objective_type == objective_type,
            QuestObjectiveModel.target_id == target_id,
        ).first()
        if not obj:
            continue
        progress = db.query(CharacterQuestProgressModel).filter(
            CharacterQuestProgressModel.char_id == char_id,
            CharacterQuestProgressModel.quest_id == cq.quest_id,
            CharacterQuestProgressModel.objective_type == objective_type,
            CharacterQuestProgressModel.target_id == target_id,
        ).first()
        if not progress:
            progress = CharacterQuestProgressModel(
                char_id=char_id,
                quest_id=cq.quest_id,
                objective_type=objective_type,
                target_id=target_id,
                current_count=0,
            )
            db.add(progress)
            db.flush()
        before = int(progress.current_count or 0)
        progress.current_count = min(int(obj.required_count or 1), before + amount)
        # CharacterQuest.current_step은 전체 목표 진행도의 합으로 간단히 동기화한다.
        total_progress = db.query(CharacterQuestProgressModel).filter(
            CharacterQuestProgressModel.char_id == char_id,
            CharacterQuestProgressModel.quest_id == cq.quest_id,
        ).all()
        cq.current_step = sum(int(row.current_count or 0) for row in total_progress)
        updated.append({
            "quest_id": cq.quest_id,
            "objective_type": objective_type,
            "target_id": target_id,
            "before": before,
            "after": int(progress.current_count or 0),
            "required_count": int(obj.required_count or 1),
        })
    return updated


def get_reward_preview(db: Session, reward_id: int | None) -> dict:
    """Return expected reward information for UI only. Actual reward is granted at victory time."""
    if not reward_id:
        return {"reward_id": None, "exp": 0, "items": []}
    exp_row = db.query(RewardExpModel).filter(RewardExpModel.reward_id == reward_id).first()
    item_rows = db.query(RewardItemModel).filter(RewardItemModel.reward_id == reward_id).all()
    items = []
    for row in item_rows:
        item = db.query(ItemModel).filter(ItemModel.id == row.item_id).first()
        items.append({
            "item_id": row.item_id,
            "name": item.name if item else f"Item {row.item_id}",
            "quantity": int(row.quantity or 1),
            "drop_probability": float(row.drop_probability) if row.drop_probability is not None else 1.0,
        })
    return {
        "reward_id": reward_id,
        "exp": int(exp_row.amount if exp_row else 0),
        "items": items,
    }


def get_monster_display_name(monster: MonsterModel | None, fallback_id: int | None = None) -> str:
    if monster and getattr(monster, "name", None):
        return monster.name
    if monster:
        return f"Monster #{monster.actor_id}"
    return f"Monster #{fallback_id}" if fallback_id is not None else "Unknown Monster"


def serialize_battle(db: Session, battle: BattleSessionModel) -> dict:
    monster = db.query(MonsterModel).filter(MonsterModel.actor_id == battle.monster_id).first()
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == battle.char_id).first()
    resources = get_character_resources(db, battle.char_id)
    return {
        "battle_id": battle.id,
        "status": battle.status,
        "reward_claimed": battle.reward_claimed,
        "monster": {
            "actor_id": monster.actor_id if monster else battle.monster_id,
            "name": get_monster_display_name(monster, battle.monster_id),
            "level": int(getattr(monster, "level", 1) or 1) if monster else 1,
            "max_hp": monster.hp if monster else 0,
            "current_hp": battle.current_monster_hp,
            "atk": monster.atk if monster else 0,
            "def": monster.def_ if monster else 0,
            "expected_reward": get_reward_preview(db, monster.drop_reward_id if monster else None),
        },
        "character": {
            "actor_id": character.actor_id if character else battle.char_id,
            "character_name": character.character_name if character else "Unknown",
            "level": character.level if character else 0,
            "exp": character.exp if character else 0,
            "exp_to_next": get_level_requirement(db, character.level) if character else None,
            "hp": resources["hp"],
            "max_hp": resources["max_hp"],
            "mp": resources["mp"],
            "max_mp": resources["max_mp"],
        },
    }


CRAFTING_ATTRIBUTES = [
    "toxic", "healing", "viscous", "stable", "organic", "plant", "unstable", "burnt",
    "neutral", "pure", "metallic", "magical", "cold", "hot", "electric", "explosive",
    "fragile", "dense", "dark", "holy", "sharp", "defensive",
]


def normalize_crafting_ingredients(item1_id: int, item2_id: int) -> tuple[int, int]:
    return (item1_id, item2_id) if item1_id <= item2_id else (item2_id, item1_id)


def get_item_attribute_dict(db: Session, item_id: int) -> dict[str, float]:
    row = db.query(ItemAttributeModel).filter(ItemAttributeModel.item_id == item_id).first()
    if not row:
        return {attr: 0.0 for attr in CRAFTING_ATTRIBUTES}
    return {attr: float(getattr(row, attr, 0) or 0) for attr in CRAFTING_ATTRIBUTES}


def ensure_default_crafting_methods(db: Session) -> None:
    defaults = {
        "MIX": "재료를 단순히 섞어 제작합니다.",
        "BOIL": "재료를 끓여 추출하거나 변화시킵니다.",
        "BAKE": "재료를 가열하여 굽습니다.",
        "DISTILL": "재료를 증류하여 핵심 성분을 추출합니다.",
        "COMPRESS": "재료를 압축하여 밀도를 높입니다.",
        "INFUSE": "재료에 마력 또는 속성을 주입합니다.",
    }
    for method, description in defaults.items():
        exists = db.query(CraftingMethodModel).filter(CraftingMethodModel.method == method).first()
        if not exists:
            db.add(CraftingMethodModel(method=method, description=description))
    db.flush()


def get_owned_inventory_item(db: Session, char_id: int, item_id: int):
    return (
        db.query(InventoryItemModel, InventoryModel, ItemModel)
        .join(InventoryModel, InventoryItemModel.inventory_id == InventoryModel.id)
        .join(ItemModel, InventoryItemModel.item_id == ItemModel.id)
        .filter(InventoryModel.owner_id == char_id, InventoryItemModel.item_id == item_id)
        .first()
    )


def get_crafting_type_and_effect(attrs: dict[str, float], method: str) -> tuple[str, dict[str, int]]:
    method = method.upper()
    healing_score = attrs.get("healing", 0) + attrs.get("pure", 0) + attrs.get("holy", 0)
    poison_score = attrs.get("toxic", 0) + attrs.get("dark", 0)
    attack_score = attrs.get("sharp", 0) + attrs.get("metallic", 0) + attrs.get("hot", 0) + attrs.get("electric", 0)
    defense_score = attrs.get("defensive", 0) + attrs.get("stable", 0) + attrs.get("dense", 0)
    explosive_score = attrs.get("explosive", 0) + attrs.get("unstable", 0)

    method_bonus = {
        "BOIL": ("healing", 2),
        "DISTILL": ("toxic", 2),
        "BAKE": ("hot", 2),
        "COMPRESS": ("dense", 2),
        "INFUSE": ("magical", 2),
        "MIX": ("stable", 1),
    }.get(method)
    if method_bonus:
        attrs[method_bonus[0]] = attrs.get(method_bonus[0], 0) + method_bonus[1]

    # Recompute after method modifier.
    healing_score = attrs.get("healing", 0) + attrs.get("pure", 0) + attrs.get("holy", 0)
    poison_score = attrs.get("toxic", 0) + attrs.get("dark", 0)
    attack_score = attrs.get("sharp", 0) + attrs.get("metallic", 0) + attrs.get("hot", 0) + attrs.get("electric", 0)
    defense_score = attrs.get("defensive", 0) + attrs.get("stable", 0) + attrs.get("dense", 0)
    explosive_score = attrs.get("explosive", 0) + attrs.get("unstable", 0)

    scores = {
        "회복형": healing_score,
        "독성형": poison_score,
        "공격형": attack_score,
        "방어형": defense_score,
        "폭발형": explosive_score,
    }
    effect_type = max(scores, key=scores.get)
    base_power = max(3, int(round(max(scores.values()) * 8 + 5)))
    duration = max(3, int(round(attrs.get("viscous", 0) + attrs.get("stable", 0) + 3)))

    effect = {
        "hp": 0, "poison": 0, "duration": duration, "attack": 0, "defense": 0,
        "speed": 0, "resistance": 0, "burn": 0, "freeze": 0, "shock": 0, "explosion_damage": 0,
    }
    if effect_type == "회복형":
        effect["hp"] = min(120, base_power * 2)
        effect["resistance"] = int(attrs.get("holy", 0) + attrs.get("pure", 0))
    elif effect_type == "독성형":
        effect["poison"] = min(60, base_power)
    elif effect_type == "공격형":
        effect["attack"] = min(40, base_power)
        effect["burn"] = int(attrs.get("hot", 0) * 5)
        effect["shock"] = int(attrs.get("electric", 0) * 5)
        effect["freeze"] = int(attrs.get("cold", 0) * 5)
    elif effect_type == "방어형":
        effect["defense"] = min(40, base_power)
        effect["resistance"] = min(40, int(defense_score * 6))
    else:
        effect["explosion_damage"] = min(120, base_power * 2)
        effect["burn"] = int(attrs.get("hot", 0) * 4)
    return effect_type, effect


def build_generated_item_text(item1: ItemModel, item2: ItemModel, method: str, effect_type: str) -> tuple[str, str]:
    method_kr = {
        "MIX": "혼합", "BOIL": "끓이기", "BAKE": "굽기", "DISTILL": "증류",
        "COMPRESS": "압축", "INFUSE": "주입",
    }.get(method.upper(), method.upper())
    suffix = {
        "회복형": "회복약", "독성형": "독액", "공격형": "전투약",
        "방어형": "보호제", "폭발형": "폭탄", "속성형": "결정",
    }.get(effect_type, "제작품")
    prefix = {
        "회복형": "정화", "독성형": "맹독", "공격형": "격전",
        "방어형": "수호", "폭발형": "폭발", "속성형": "마력",
    }.get(effect_type, "AI")
    # Keep emergency fallback names compact; ingredient names stay in the description.
    name = f"{prefix} {suffix}"[:24]
    note = f"{item1.name}와 {item2.name}을(를) {method_kr} 방식으로 조합해 만든 {effect_type} 아이템입니다."
    return name, note


METHOD_NAME_PREFIX = {
    "MIX": "혼합",
    "BOIL": "끓인",
    "BAKE": "구운",
    "DISTILL": "정제",
    "COMPRESS": "압축",
    "INFUSE": "주입",
}

TYPE_NAME_SUFFIX = {
    "회복형": "회복약",
    "독성형": "독액",
    "공격형": "전투약",
    "방어형": "보호제",
    "폭발형": "폭탄",
    "속성형": "결정",
}


def compact_item_name(name: str, max_len: int = 24) -> str:
    """Inventory-friendly item name cleanup.

    LLM/fallback names can occasionally repeat words or exceed the UI width.
    This function keeps only a short, readable name before DB insertion.
    """
    import re

    words = [w for w in re.split(r"\s+", str(name or "").replace("\n", " ").strip()) if w]
    cleaned_words: list[str] = []
    for word in words:
        if cleaned_words and cleaned_words[-1] == word:
            continue
        if word in cleaned_words and len(word) >= 2:
            continue
        cleaned_words.append(word)
    cleaned = " ".join(cleaned_words).strip()
    if not cleaned:
        cleaned = "AI 제작품"
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].strip()
    return cleaned or "AI 제작품"


def make_unique_item_name(db: Session, base_name: str, method: str, effect_type: str, max_len: int = 24) -> tuple[str, dict]:
    """Return a unique item name for newly generated crafting results.

    Different recipes can share the same predicted effect, so LLM/fallback names
    may collide. Before inserting Item, check existing Item names and add method
    information or a short roman suffix when needed.
    """
    base = compact_item_name(base_name, max_len=max_len)
    method_key = (method or "").upper().strip()
    method_prefix = METHOD_NAME_PREFIX.get(method_key, method_key or "제작")
    type_suffix = TYPE_NAME_SUFFIX.get(effect_type, "제작품")

    def exists(candidate: str) -> bool:
        return db.query(ItemModel.id).filter(ItemModel.name == candidate).first() is not None

    candidates: list[str] = [base]

    # Prefer names that clearly show the crafting method when the original name collides.
    for candidate in [
        f"{method_prefix} {base}",
        f"{method_prefix} {type_suffix}",
        f"{method_prefix}{type_suffix}",
    ]:
        candidate = compact_item_name(candidate, max_len=max_len)
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    roman = ["II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    for suffix in roman:
        candidate = compact_item_name(f"{base} {suffix}", max_len=max_len)
        if candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        if not exists(candidate):
            return candidate, {
                "original_name": base_name,
                "final_name": candidate,
                "changed": candidate != base,
                "reason": "duplicate_item_name" if candidate != base else "unique",
                "method_prefix": method_prefix,
                "effect_type": effect_type,
            }

    # Extremely unlikely final fallback. Include a DB-independent increment.
    for idx in range(2, 1000):
        candidate = compact_item_name(f"{method_prefix} {type_suffix} {idx}", max_len=max_len)
        if not exists(candidate):
            return candidate, {
                "original_name": base_name,
                "final_name": candidate,
                "changed": True,
                "reason": "numbered_fallback",
                "method_prefix": method_prefix,
                "effect_type": effect_type,
            }

    return compact_item_name(f"{method_prefix} 제작품", max_len=max_len), {
        "original_name": base_name,
        "final_name": compact_item_name(f"{method_prefix} 제작품", max_len=max_len),
        "changed": True,
        "reason": "last_resort",
        "method_prefix": method_prefix,
        "effect_type": effect_type,
    }


def create_generated_crafting_result(db: Session, item1: ItemModel, item2: ItemModel, method: str) -> tuple[ItemModel, dict, dict, str, dict]:
    """Create a new crafting result item and return an AI debug payload.

    The debug payload is intentionally serializable so Streamlit can show the
    generation process: input attributes, method modifier, model source, raw
    prediction/fallback output, and final post-processed effects.
    """
    attrs1 = get_item_attribute_dict(db, item1.id)
    attrs2 = get_item_attribute_dict(db, item2.id)
    model_source = "fallback"
    ai_error = None

    try:
        from crafting_ai.crafting_predictor import predict_crafting_result, merge_attributes, apply_method_modifier, normalize_method

        method_norm = normalize_method(method)
        merged_before_method = merge_attributes(attrs1, attrs2)
        merged = apply_method_modifier(merged_before_method, method_norm)
        prediction = predict_crafting_result(
            ingredient1_name=item1.name,
            ingredient2_name=item2.name,
            method=method,
            ingredient1_attributes=attrs1,
            ingredient2_attributes=attrs2,
        )
        merged = {attr: float(prediction.attributes.get(attr, 0) or 0) for attr in CRAFTING_ATTRIBUTES}
        effect_type = prediction.type_effect
        effect = {
            "hp": 0, "poison": 0, "duration": 0, "attack": 0, "defense": 0,
            "speed": 0, "resistance": 0, "burn": 0, "freeze": 0, "shock": 0, "explosion_damage": 0,
        }
        effect.update({k: int(v or 0) for k, v in prediction.effects.items() if k in effect})
        name = prediction.item_name
        description = f"[AI:{prediction.source}|TEXT:{getattr(prediction, 'text_source', 'rule')}] {prediction.item_note}"
        model_source = prediction.source
        text_source = getattr(prediction, 'text_source', 'rule')
        llm_debug = getattr(prediction, 'llm_debug', None)
    except Exception as exc:
        ai_error = str(exc)
        merged_before_method = {attr: round((float(attrs1.get(attr, 0) or 0) + float(attrs2.get(attr, 0) or 0)) / 2, 3) for attr in CRAFTING_ATTRIBUTES}
        merged = dict(merged_before_method)
        effect_type, effect = get_crafting_type_and_effect(merged, method)
        name, description = build_generated_item_text(item1, item2, method, effect_type)
        description = f"[AI:fallback|TEXT:rule] {description}"
        text_source = "rule_fallback"
        llm_debug = {"provider": "none", "used": False, "fallback_used": True, "error": ai_error}

    original_generated_name = name
    name, unique_name_debug = make_unique_item_name(db, name, method, effect_type)

    ai_debug = {
        "is_ai_generated": True,
        "recipe_source": "new_ai_prediction",
        "model_source": model_source,
        "text_source": text_source,
        "ai_error": ai_error,
        "llm_debug": llm_debug,
        "ingredients": [
            {"item_id": item1.id, "name": item1.name, "attributes": attrs1},
            {"item_id": item2.id, "name": item2.name, "attributes": attrs2},
        ],
        "method": method.upper(),
        "merged_attributes_before_method": merged_before_method,
        "final_input_attributes": merged,
        "predicted_type_effect": effect_type,
        "post_processed_effects": effect,
        "generated_text": {
            "original_name": original_generated_name,
            "name": name,
            "description": description,
            "unique_name": unique_name_debug,
        },
    }

    result_item = ItemModel(
        name=name,
        description=description,
        type="consumable",
        sub_type="crafted",
        capacity=-1,
        rarity="CRAFTED",
        is_generated=True,
    )
    db.add(result_item)
    db.flush()

    db.add(ItemAttributeModel(item_id=result_item.id, **{attr: float(merged.get(attr, 0)) for attr in CRAFTING_ATTRIBUTES}))
    db.add(ItemEffectModel(item_id=result_item.id, type_effect=effect_type, **effect))
    db.flush()
    return result_item, merged, effect, effect_type, ai_debug


# =========================
# Auth / User
# =========================
@app.post("/login", tags=["Auth"])
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user:
        return {
            "message": "이미 로그인한 사용자입니다.",
            "user_id": current_user["id"],
            "user_name": current_user["name"],
            "role": current_user.get("role", "USER"),
        }

    user = db.query(UserModel).filter(UserModel.id == login_data.user_id).first()
    if not user or user.password != login_data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 아이디 또는 비밀번호가 다릅니다.")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비활성화된 계정입니다. 관리자에게 복구를 요청하세요.")

    session_id = str(uuid.uuid4())
    session_store[session_id] = {"id": user.id, "name": user.user_name, "role": user.role, "active": user.active}
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=3600, samesite="lax")
    return {"message": "로그인 성공", "user_id": user.id, "user_name": user.user_name, "role": user.role, "active": user.active}


@app.post("/logout", tags=["Auth"])
def logout(response: Response, session_id: str | None = Cookie(default=None)):
    if session_id and session_id in session_store:
        del session_store[session_id]
    response.delete_cookie(key="session_id")
    return {"message": "로그아웃 성공"}


@app.get("/me", response_model=UserResponse, tags=["Auth"])
def me(current_user=Depends(require_user)):
    return {"user_id": current_user["id"], "user_name": current_user["name"], "role": current_user.get("role", "USER"), "active": current_user.get("active", True)}


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.id == user.user_identifier).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 유저 ID입니다.")

    new_user = UserModel(id=user.user_identifier, user_name=user.nickname, password=user.password, role="USER", active=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.id, "user_name": new_user.user_name, "role": new_user.role, "active": new_user.active}


@app.delete("/users/me", tags=["Users"])
def deactivate_my_account(current_user=Depends(require_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
    if user.role == "ADMIN":
        raise HTTPException(status_code=400, detail="관리자 계정은 비활성화할 수 없습니다.")
    user.active = False
    db.commit()
    return {"message": "계정이 비활성화되었습니다.", "user_id": user.id, "active": user.active}


@app.get("/admin/users", response_model=List[AdminUserResponse], tags=["Admin"])
def admin_get_users(
    keyword: Optional[str] = None,
    active: Optional[bool] = None,
    role: Optional[str] = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(UserModel)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((UserModel.id.like(like)) | (UserModel.user_name.like(like)))
    if active is not None:
        query = query.filter(UserModel.active == active)
    if role and role != "ALL":
        query = query.filter(UserModel.role == role)

    users = query.order_by(UserModel.role.desc(), UserModel.id.asc()).all()
    result = []
    for user in users:
        character_count = db.query(CharacterModel).filter(CharacterModel.user_id == user.id).count()
        result.append({
            "user_id": user.id,
            "user_name": user.user_name,
            "role": user.role,
            "active": user.active,
            "character_count": character_count,
        })
    return result


@app.patch("/admin/users/{user_id}/active", tags=["Admin"])
def admin_update_user_active(
    user_id: str,
    payload: UserActiveUpdate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
    if user.role == "ADMIN" and payload.active is False:
        raise HTTPException(status_code=400, detail="관리자 계정은 비활성화할 수 없습니다.")
    user.active = payload.active
    db.commit()
    db.refresh(user)
    return {"message": "계정 상태가 변경되었습니다.", "user_id": user.id, "active": user.active}


# =========================
# Specimen / Character
# =========================
@app.get("/specimens", response_model=List[SpecimenResponse], tags=["Specimens"])
def get_specimens(db: Session = Depends(get_db)):
    return db.query(SpecimenModel).order_by(SpecimenModel.type).all()


@app.get("/jobs", response_model=List[JobResponse], tags=["Jobs"])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(JobModel).order_by(JobModel.type).all()


@app.get("/characters/me", response_model=List[CharacterResponse], tags=["Characters"])
def get_my_characters(current_user=Depends(require_user), db: Session = Depends(get_db)):
    return db.query(CharacterModel).filter(CharacterModel.user_id == current_user["id"]).order_by(CharacterModel.actor_id).all()


@app.post("/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED, tags=["Characters"])
def create_character(char_data: CharacterCreate, current_user=Depends(require_user), db: Session = Depends(get_db)):
    if not char_data.character_name.strip():
        raise HTTPException(status_code=400, detail="캐릭터 이름을 입력해주세요.")

    duplicated = db.query(CharacterModel).filter(
        CharacterModel.user_id == current_user["id"],
        CharacterModel.character_name == char_data.character_name,
    ).first()
    if duplicated:
        raise HTTPException(status_code=400, detail="이미 같은 이름의 캐릭터가 있습니다.")

    if not char_data.specimens:
        raise HTTPException(status_code=400, detail="종족을 하나 이상 선택해주세요.")

    total_fraction = sum(s.fraction for s in char_data.specimens)
    if abs(total_fraction - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail="종족 비율 합계는 100%여야 합니다.")

    valid_specimen_types = {s.type for s in db.query(SpecimenModel).all()}
    for specimen in char_data.specimens:
        if specimen.type not in valid_specimen_types:
            raise HTTPException(status_code=400, detail=f"존재하지 않는 종족입니다: {specimen.type}")

    selected_job_type = normalize_job_type(char_data.job_type)
    if selected_job_type:
        selected_job = db.query(JobModel).filter(JobModel.type == selected_job_type).first()
        if not selected_job:
            raise HTTPException(status_code=400, detail=f"존재하지 않는 직업입니다: {selected_job_type}")
    else:
        selected_job = db.query(JobModel).filter(JobModel.type.in_(["BEGINNER", "NOVICE"])).first()
        if not selected_job:
            selected_job = db.query(JobModel).first()
        selected_job_type = selected_job.type if selected_job else None

    try:
        actor = ActorModel()
        db.add(actor)
        db.flush()

        character = CharacterModel(
            actor_id=actor.id,
            user_id=current_user["id"],
            character_name=char_data.character_name,
            level=1,
            exp=0,
            active=False,
            is_public=False,
        )
        db.add(character)
        db.flush()

        for specimen in char_data.specimens:
            db.add(CharacterSpecimenModel(char_id=actor.id, type=specimen.type, fraction=specimen.fraction))

        # Initial job: selected by the user. Fallback to BEGINNER/NOVICE when omitted.
        if selected_job_type:
            db.add(CharacterJobModel(type=selected_job_type, char_id=actor.id, active=True))

        # Initial stats include level/specimen stats and a lightweight job bonus.
        initial_stats = calculate_initial_stats(db, char_data.specimens, selected_job_type)
        for stat_type, value in initial_stats.items():
            db.add(ActorStatModel(actor_id=actor.id, stat_type=stat_type, value=value))

        # Basic inventory
        db.add(InventoryModel(owner_id=actor.id, type="BASIC", capacity=20))

        # Basic skills plus job-themed skills when matching names/descriptions exist.
        basic_skills = get_initial_skills_for_job(db, selected_job_type)
        seen_skill_ids = set()
        for skill in basic_skills:
            if skill.id in seen_skill_ids:
                continue
            seen_skill_ids.add(skill.id)
            db.add(CharacterSkillModel(skill_id=skill.id, char_id=actor.id, skill_level=0.0))

        db.commit()
        db.refresh(character)
        return character
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"캐릭터 생성 실패: {exc}")


@app.patch("/characters/{char_id}/select", response_model=CharacterResponse, tags=["Characters"])
def select_character(char_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if character.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="다른 사용자의 캐릭터는 선택할 수 없습니다.")

    db.query(CharacterModel).filter(CharacterModel.user_id == current_user["id"]).update({CharacterModel.active: False})
    character.active = True
    db.commit()
    db.refresh(character)
    return character


@app.get("/characters/current", response_model=Optional[CharacterResponse], tags=["Characters"])
def get_current_character(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    return character


@app.get("/characters/current/resources", tags=["Characters"])
def get_current_character_resources(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    resources = get_character_resources(db, character.actor_id)
    db.commit()
    return {
        "character": {
            "actor_id": character.actor_id,
            "character_name": character.character_name,
            "level": character.level,
            "exp": character.exp,
            "exp_to_next": get_level_requirement(db, character.level),
        },
        "resources": resources,
    }


@app.get("/characters/public/search", tags=["Characters"])
def search_public_characters(
    name: Optional[str] = None,
    job_type: Optional[str] = None,
    specimen_type: Optional[str] = None,
    min_level: Optional[int] = None,
    max_level: Optional[int] = None,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(CharacterModel).filter(CharacterModel.is_public == True)  # noqa: E712

    if name:
        query = query.filter(CharacterModel.character_name.like(f"%{name.strip()}%"))
    if min_level is not None:
        query = query.filter(CharacterModel.level >= min_level)
    if max_level is not None:
        query = query.filter(CharacterModel.level <= max_level)
    if job_type:
        query = query.join(CharacterJobModel, CharacterJobModel.char_id == CharacterModel.actor_id).filter(
            CharacterJobModel.active == True,  # noqa: E712
            CharacterJobModel.type == normalize_job_type(job_type),
        )
    if specimen_type:
        query = query.join(CharacterSpecimenModel, CharacterSpecimenModel.char_id == CharacterModel.actor_id).filter(
            CharacterSpecimenModel.type == specimen_type
        )

    characters = query.order_by(CharacterModel.level.desc(), CharacterModel.character_name.asc()).limit(100).all()
    results = []
    for character in characters:
        active_job = (
            db.query(CharacterJobModel, JobModel)
            .join(JobModel, JobModel.type == CharacterJobModel.type)
            .filter(CharacterJobModel.char_id == character.actor_id, CharacterJobModel.active == True)  # noqa: E712
            .first()
        )
        specimens = db.query(CharacterSpecimenModel).filter(CharacterSpecimenModel.char_id == character.actor_id).all()
        results.append({
            "actor_id": character.actor_id,
            "character_name": character.character_name,
            "level": character.level,
            "exp": character.exp,
            "job_type": active_job[0].type if active_job else None,
            "job_name": active_job[1].name if active_job else None,
            "specimens": [
                {"type": s.type, "fraction": s.fraction}
                for s in specimens
            ],
        })
    return results


@app.get("/characters/{char_id}", tags=["Characters"])
def get_character_detail(char_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if character.user_id != current_user["id"] and not character.is_public and current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="비공개 캐릭터입니다.")

    specimens = db.query(CharacterSpecimenModel).filter(CharacterSpecimenModel.char_id == char_id).all()
    jobs = (
        db.query(CharacterJobModel, JobModel)
        .join(JobModel, JobModel.type == CharacterJobModel.type)
        .filter(CharacterJobModel.char_id == char_id)
        .all()
    )
    stats = db.query(ActorStatModel).filter(ActorStatModel.actor_id == char_id).all()
    final_stats = get_final_stats(db, char_id)
    equipment = get_equipped_items(db, char_id)
    skills = (
        db.query(SkillModel.id, SkillModel.name, SkillModel.description, SkillModel.mp_cost, SkillModel.cooldown_sec, CharacterSkillModel.skill_level)
        .join(CharacterSkillModel, SkillModel.id == CharacterSkillModel.skill_id)
        .filter(CharacterSkillModel.char_id == char_id)
        .all()
    )
    return {
        "character": {
            "actor_id": character.actor_id,
            "user_id": character.user_id,
            "character_name": character.character_name,
            "level": character.level,
            "exp": character.exp,
            "active": character.active,
            "is_public": character.is_public,
        },
        "specimens": [{"type": s.type, "fraction": s.fraction} for s in specimens],
        "jobs": [
            {
                "type": cj.type,
                "name": job.name,
                "description": job.description,
                "active": cj.active,
            }
            for cj, job in jobs
        ],
        "stats": {s.stat_type: s.value for s in stats},
        "final_stats": final_stats,
        "equipment": equipment,
        "skills": [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "mp_cost": row.mp_cost,
                "cooldown_sec": row.cooldown_sec,
                "skill_level": row.skill_level,
            }
            for row in skills
        ],
    }


class CharacterVisibilityUpdate(BaseModel):
    is_public: bool


@app.patch("/characters/{char_id}/visibility", response_model=CharacterResponse, tags=["Characters"])
def update_character_visibility(
    char_id: int,
    payload: CharacterVisibilityUpdate,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if character.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="다른 사용자의 캐릭터 공개 여부는 변경할 수 없습니다.")
    character.is_public = payload.is_public
    db.commit()
    db.refresh(character)
    return character


@app.delete("/characters/{char_id}", tags=["Characters"])
def delete_character(char_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if character.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="다른 사용자의 캐릭터는 삭제할 수 없습니다.")

    try:
        # 현재 단계에서는 생성 단계에서 함께 만들어진 최소 하위 데이터만 정리한다.
        # 인벤토리 아이템, 퀘스트, 전투 등은 해당 기능 구현 시 삭제 로직을 추가한다.
        db.query(CharacterEquipmentModel).filter(CharacterEquipmentModel.char_id == char_id).delete(synchronize_session=False)
        db.query(EquippedSkillModel).filter(EquippedSkillModel.char_id == char_id).delete(synchronize_session=False)
        db.query(CharacterSkillModel).filter(CharacterSkillModel.char_id == char_id).delete(synchronize_session=False)
        db.query(CharacterJobModel).filter(CharacterJobModel.char_id == char_id).delete(synchronize_session=False)
        db.query(CharacterSpecimenModel).filter(CharacterSpecimenModel.char_id == char_id).delete(synchronize_session=False)
        db.query(ActorStatModel).filter(ActorStatModel.actor_id == char_id).delete(synchronize_session=False)
        inventories = db.query(InventoryModel).filter(InventoryModel.owner_id == char_id).all()
        for inventory in inventories:
            db.query(InventoryItemModel).filter(InventoryItemModel.inventory_id == inventory.id).delete(synchronize_session=False)
        db.query(InventoryModel).filter(InventoryModel.owner_id == char_id).delete(synchronize_session=False)

        db.delete(character)
        db.flush()

        actor = db.query(ActorModel).filter(ActorModel.id == char_id).first()
        if actor:
            db.delete(actor)

        db.commit()
        return {"message": "캐릭터를 삭제했습니다.", "char_id": char_id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"캐릭터 삭제 실패: {exc}")



# =========================
# Inventory / Item
# =========================
@app.get("/inventory", tags=["Inventory"])
def get_inventory(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    inventories = db.query(InventoryModel).filter(InventoryModel.owner_id == character.actor_id).order_by(InventoryModel.id.asc()).all()
    result = []
    for inventory in inventories:
        rows = (
            db.query(
                InventoryItemModel.item_id,
                InventoryItemModel.quantity,
                ItemModel.name,
                ItemModel.description,
                ItemModel.type,
                ItemModel.sub_type,
                ItemModel.capacity,
                ItemModel.icon_url,
                ItemModel.equipment_part,
                ItemModel.required_level,
                ItemModel.rarity,
                ItemModel.is_generated,
            )
            .join(ItemModel, InventoryItemModel.item_id == ItemModel.id)
            .filter(InventoryItemModel.inventory_id == inventory.id)
            .order_by(ItemModel.type.asc(), ItemModel.name.asc())
            .all()
        )
        items = [serialize_inventory_item(row) for row in rows]
        equipped_item_ids = {eq.item_id for eq in db.query(CharacterEquipmentModel).filter(CharacterEquipmentModel.char_id == character.actor_id).all()}
        equipped_parts = {eq.item_id: eq.equipment_part for eq in db.query(CharacterEquipmentModel).filter(CharacterEquipmentModel.char_id == character.actor_id).all()}
        for item in items:
            item["equipped"] = item.get("item_id") in equipped_item_ids
            item["equipped_part"] = equipped_parts.get(item.get("item_id"))
        result.append({
            "inventory_id": inventory.id,
            "type": inventory.type,
            "capacity": inventory.capacity,
            "used_slots": len(items),
            "items": items,
        })

    return {
        "character": {
            "actor_id": character.actor_id,
            "character_name": character.character_name,
            "level": character.level,
            "exp": character.exp,
        },
        "inventories": result,
    }


@app.post("/inventory/items/{item_id}/use", tags=["Inventory"])
def use_inventory_item(item_id: int, payload: QuantityPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
    if item.type.lower() != "consumable":
        raise HTTPException(status_code=400, detail="소비 아이템만 사용할 수 있습니다.")

    inventories = db.query(InventoryModel).filter(InventoryModel.owner_id == character.actor_id).all()
    inv_item = None
    for inventory in inventories:
        inv_item = db.query(InventoryItemModel).filter(
            InventoryItemModel.inventory_id == inventory.id,
            InventoryItemModel.item_id == item_id,
        ).first()
        if inv_item:
            break

    if not inv_item or inv_item.quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="아이템 수량이 부족합니다.")

    effect = db.query(ItemEffectModel).filter(ItemEffectModel.item_id == item_id).first()
    hp_delta = 0
    mp_delta = 0
    effect_message = ""

    if effect:
        effect_type = (effect.type_effect or "").upper()
        # ItemEffect has no separate MP column, so MP recovery items can be represented
        # as type_effect='MP' with hp storing the recovery amount.
        if "MP" in effect_type or "MANA" in effect_type:
            mp_delta = effect.hp * payload.quantity
        else:
            hp_delta = effect.hp * payload.quantity
        if hp_delta or mp_delta:
            updated = apply_resource_change(db, character.actor_id, hp_delta=hp_delta, mp_delta=mp_delta)
            parts = []
            if hp_delta:
                parts.append(f"HP {updated['hp']}/{updated['max_hp']}")
            if mp_delta:
                parts.append(f"MP {updated['mp']}/{updated['max_mp']}")
            effect_message = " (" + ", ".join(parts) + ")"

    inv_item.quantity -= payload.quantity
    if inv_item.quantity <= 0:
        db.delete(inv_item)
    db.commit()
    return {
        "message": f"{item.name} {payload.quantity}개를 사용했습니다.{effect_message}",
        "item_id": item_id,
        "hp_delta": hp_delta,
        "mp_delta": mp_delta,
    }


@app.post("/inventory/items/{item_id}/discard", tags=["Inventory"])
def discard_inventory_item(item_id: int, payload: QuantityPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

    equipped = db.query(CharacterEquipmentModel).filter(
        CharacterEquipmentModel.char_id == character.actor_id,
        CharacterEquipmentModel.item_id == item_id,
    ).first()
    if equipped:
        raise HTTPException(status_code=400, detail="장착 중인 아이템은 버릴 수 없습니다. 먼저 장비를 해제해주세요.")

    inventories = db.query(InventoryModel).filter(InventoryModel.owner_id == character.actor_id).all()
    inv_item = None
    for inventory in inventories:
        inv_item = db.query(InventoryItemModel).filter(
            InventoryItemModel.inventory_id == inventory.id,
            InventoryItemModel.item_id == item_id,
        ).first()
        if inv_item:
            break

    if not inv_item or inv_item.quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="아이템 수량이 부족합니다.")

    inv_item.quantity -= payload.quantity
    if inv_item.quantity <= 0:
        db.delete(inv_item)
    db.commit()
    return {"message": f"{item.name} {payload.quantity}개를 버렸습니다.", "item_id": item_id}


# =========================
# Equipment
# =========================
@app.get("/equipment/me", tags=["Equipment"])
def get_my_equipment(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    inventory = get_inventory(current_user=current_user, db=db)
    available = []
    for inv in inventory.get("inventories", []):
        for item in inv.get("items", []):
            if str(item.get("type", "")).lower() == "equipment":
                bonus_rows = db.query(ItemBonusStatModel).filter(ItemBonusStatModel.item_id == item["item_id"]).all()
                item = dict(item)
                item["bonuses"] = {row.stat_type: row.value for row in bonus_rows}
                available.append(item)

    return {
        "character": inventory.get("character"),
        "equipment": get_equipped_items(db, character.actor_id),
        "available_items": available,
        "stats": get_final_stats(db, character.actor_id),
    }


@app.post("/equipment/equip", tags=["Equipment"])
def equip_item(payload: EquipmentEquipPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    if has_active_battle(db, character.actor_id):
        raise HTTPException(status_code=400, detail="전투 중에는 장비를 교체할 수 없습니다.")

    item = db.query(ItemModel).filter(ItemModel.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
    if str(item.type).lower() != "equipment":
        raise HTTPException(status_code=400, detail="장비 아이템만 장착할 수 있습니다.")
    if character.level < int(getattr(item, "required_level", 1) or 1):
        raise HTTPException(status_code=400, detail=f"요구 레벨이 부족합니다. 필요 레벨: {item.required_level}")

    equipment_part = payload.equipment_part or item.equipment_part or item.sub_type
    if not equipment_part:
        raise HTTPException(status_code=400, detail="장비 부위 정보가 없는 아이템입니다.")
    equipment_part = str(equipment_part).lower()
    item_part = str(item.equipment_part or item.sub_type or "").lower()
    if item_part and item_part != equipment_part:
        raise HTTPException(status_code=400, detail=f"아이템 부위({item_part})와 선택 슬롯({equipment_part})이 다릅니다.")

    inventory_item = (
        db.query(InventoryItemModel, InventoryModel)
        .join(InventoryModel, InventoryItemModel.inventory_id == InventoryModel.id)
        .filter(InventoryModel.owner_id == character.actor_id, InventoryItemModel.item_id == item.id)
        .first()
    )
    if not inventory_item:
        raise HTTPException(status_code=400, detail="현재 캐릭터의 인벤토리에 없는 아이템입니다.")
    inv_item, inv = inventory_item
    if inv_item.quantity <= 0:
        raise HTTPException(status_code=400, detail="아이템 수량이 부족합니다.")

    existing = db.query(CharacterEquipmentModel).filter(
        CharacterEquipmentModel.char_id == character.actor_id,
        CharacterEquipmentModel.equipment_part == equipment_part,
    ).first()
    if existing:
        existing.inventory_id = inv.id
        existing.item_id = item.id
    else:
        db.add(CharacterEquipmentModel(
            char_id=character.actor_id,
            equipment_part=equipment_part,
            inventory_id=inv.id,
            item_id=item.id,
        ))
    db.commit()
    return {"message": f"{item.name}을(를) {equipment_part} 슬롯에 장착했습니다.", "equipment": get_equipped_items(db, character.actor_id), "stats": get_final_stats(db, character.actor_id)}


@app.post("/equipment/unequip", tags=["Equipment"])
def unequip_item(payload: EquipmentUnequipPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    if has_active_battle(db, character.actor_id):
        raise HTTPException(status_code=400, detail="전투 중에는 장비를 해제할 수 없습니다.")

    part = payload.equipment_part.lower()
    equipment = db.query(CharacterEquipmentModel).filter(
        CharacterEquipmentModel.char_id == character.actor_id,
        CharacterEquipmentModel.equipment_part == part,
    ).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="해당 슬롯에 장착된 장비가 없습니다.")

    db.delete(equipment)
    db.commit()
    return {"message": f"{part} 슬롯 장비를 해제했습니다.", "equipment": get_equipped_items(db, character.actor_id), "stats": get_final_stats(db, character.actor_id)}


# =========================
# Skills
# =========================
@app.get("/skills/me", tags=["Skills"])
def get_my_skills(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    equipped_rows = db.query(EquippedSkillModel).filter(EquippedSkillModel.char_id == character.actor_id).all()
    equipped_by_skill = {row.skill_id: row.slot_no for row in equipped_rows}

    rows = (
        db.query(SkillModel.id, SkillModel.name, SkillModel.description, SkillModel.mp_cost, SkillModel.cooldown_sec, CharacterSkillModel.skill_level)
        .join(CharacterSkillModel, SkillModel.id == CharacterSkillModel.skill_id)
        .filter(CharacterSkillModel.char_id == character.actor_id)
        .order_by(SkillModel.id.asc())
        .all()
    )
    skills = []
    for row in rows:
        skills.append({
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "mp_cost": row.mp_cost,
            "cooldown_sec": row.cooldown_sec,
            "skill_level": row.skill_level,
            "equipped": row.id in equipped_by_skill,
            "slot_no": equipped_by_skill.get(row.id),
        })

    equipped = [skill for skill in skills if skill["equipped"]]
    equipped.sort(key=lambda x: x.get("slot_no") or 99)
    return {
        "character": {"actor_id": character.actor_id, "character_name": character.character_name},
        "skills": skills,
        "equipped": equipped,
        "max_slots": 3,
    }


@app.post("/skills/equip", tags=["Skills"])
def equip_skill(payload: SkillEquipPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    owned = db.query(CharacterSkillModel).filter(
        CharacterSkillModel.char_id == character.actor_id,
        CharacterSkillModel.skill_id == payload.skill_id,
    ).first()
    if not owned:
        raise HTTPException(status_code=400, detail="보유하지 않은 스킬은 장착할 수 없습니다.")

    duplicated = db.query(EquippedSkillModel).filter(
        EquippedSkillModel.char_id == character.actor_id,
        EquippedSkillModel.skill_id == payload.skill_id,
    ).first()
    if duplicated and duplicated.slot_no != payload.slot_no:
        db.delete(duplicated)
        db.flush()

    slot = db.query(EquippedSkillModel).filter(
        EquippedSkillModel.char_id == character.actor_id,
        EquippedSkillModel.slot_no == payload.slot_no,
    ).first()
    if slot:
        slot.skill_id = payload.skill_id
    else:
        db.add(EquippedSkillModel(char_id=character.actor_id, slot_no=payload.slot_no, skill_id=payload.skill_id))
    db.commit()
    return {"message": "스킬을 장착했습니다.", "skill_id": payload.skill_id, "slot_no": payload.slot_no}


@app.post("/skills/unequip", tags=["Skills"])
def unequip_skill(payload: SkillUnequipPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    slot = db.query(EquippedSkillModel).filter(
        EquippedSkillModel.char_id == character.actor_id,
        EquippedSkillModel.slot_no == payload.slot_no,
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="해당 슬롯에 장착된 스킬이 없습니다.")
    db.delete(slot)
    db.commit()
    return {"message": "스킬 장착을 해제했습니다.", "slot_no": payload.slot_no}


# =========================
# Monster / Battle
# =========================
@app.get("/monsters", tags=["Battle"])
def get_monsters(current_user=Depends(require_user), db: Session = Depends(get_db)):
    monsters = db.query(MonsterModel).order_by(MonsterModel.actor_id.asc()).all()
    return [
        {
            "actor_id": monster.actor_id,
            "name": get_monster_display_name(monster),
            "level": int(getattr(monster, "level", 1) or 1),
            "hp": monster.hp,
            "atk": monster.atk,
            "def": monster.def_,
            "drop_reward_id": monster.drop_reward_id,
            "expected_reward": get_reward_preview(db, monster.drop_reward_id),
        }
        for monster in monsters
    ]


@app.post("/battle/start", tags=["Battle"])
def start_battle(payload: BattleStartPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    monster = db.query(MonsterModel).filter(MonsterModel.actor_id == payload.monster_id).first()
    if not monster:
        raise HTTPException(status_code=404, detail="몬스터를 찾을 수 없습니다.")

    resources = get_character_resources(db, character.actor_id)
    if resources["hp"] <= 0:
        raise HTTPException(status_code=400, detail="HP가 0이라 전투를 시작할 수 없습니다. 회복 아이템을 사용하세요.")

    battle = BattleSessionModel(
        char_id=character.actor_id,
        monster_id=monster.actor_id,
        current_monster_hp=monster.hp,
        status="ACTIVE",
        reward_claimed=False,
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)
    return serialize_battle(db, battle)


@app.get("/battle/status", tags=["Battle"])
def get_battle_status(battle_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    battle = db.query(BattleSessionModel).filter(BattleSessionModel.id == battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="전투를 찾을 수 없습니다.")
    if battle.char_id != character.actor_id:
        raise HTTPException(status_code=403, detail="다른 캐릭터의 전투 정보는 조회할 수 없습니다.")
    return serialize_battle(db, battle)


@app.post("/battle/attack", tags=["Battle"])
def attack_battle(payload: BattleAttackPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    battle = db.query(BattleSessionModel).filter(BattleSessionModel.id == payload.battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="전투를 찾을 수 없습니다.")
    if battle.char_id != character.actor_id:
        raise HTTPException(status_code=403, detail="다른 캐릭터의 전투는 진행할 수 없습니다.")
    if battle.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="이미 종료된 전투입니다.")

    equipped = db.query(EquippedSkillModel).filter(
        EquippedSkillModel.char_id == character.actor_id,
        EquippedSkillModel.skill_id == payload.skill_id,
    ).first()
    if not equipped:
        raise HTTPException(status_code=400, detail="장착한 스킬만 전투에서 사용할 수 있습니다.")

    skill = db.query(SkillModel).filter(SkillModel.id == payload.skill_id).first()
    monster = db.query(MonsterModel).filter(MonsterModel.actor_id == battle.monster_id).first()
    if not skill or not monster:
        raise HTTPException(status_code=404, detail="스킬 또는 몬스터 정보를 찾을 수 없습니다.")

    resources_before = get_character_resources(db, character.actor_id)
    if resources_before["hp"] <= 0:
        battle.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=400, detail="캐릭터 HP가 0입니다. 전투를 진행할 수 없습니다.")

    if skill.mp_cost > 0 and resources_before["mp"] < skill.mp_cost:
        raise HTTPException(status_code=400, detail="MP가 부족합니다.")
    if skill.mp_cost > 0:
        apply_resource_change(db, character.actor_id, mp_delta=-skill.mp_cost)

    atk = get_final_stat_value(db, character.actor_id, "ATK", default=5)
    int_stat = get_final_stat_value(db, character.actor_id, "INT", default=0)
    char_def = get_final_stat_value(db, character.actor_id, "DEF", default=0)

    # 간단한 데미지 공식: 기본 공격력 + 스킬 보정 + 지능 일부 - 몬스터 방어력
    skill_bonus = max(3, int(skill.mp_cost * 0.4) + 3)
    player_damage = max(1, atk + skill_bonus + int(int_stat * 0.2) - monster.def_)
    battle.current_monster_hp = max(0, battle.current_monster_hp - player_damage)

    monster_damage = 0
    reward = None
    messages = [f"{skill.name} 사용! 몬스터에게 {player_damage} 피해를 입혔습니다."]

    if battle.current_monster_hp <= 0:
        battle.status = "COMPLETED"
        quest_updates = update_quest_progress(db, character.actor_id, "KILL_MONSTER", monster.actor_id, 1)
        if not battle.reward_claimed:
            reward = grant_reward_to_character(db, character, monster.drop_reward_id)
            battle.reward_claimed = True
        if quest_updates:
            messages.append(f"퀘스트 진행도 {len(quest_updates)}건이 갱신되었습니다.")
        messages.append("몬스터를 처치했습니다!")
    else:
        # 몬스터 반격. Streamlit 턴제 구조이므로 플레이어 행동 직후 1회 반격한다.
        monster_damage = max(1, monster.atk - int(char_def * 0.5))
        resources_after_counter = apply_resource_change(db, character.actor_id, hp_delta=-monster_damage)
        messages.append(f"몬스터가 반격하여 {monster_damage} 피해를 입혔습니다.")
        if resources_after_counter["hp"] <= 0:
            battle.status = "FAILED"
            messages.append("캐릭터 HP가 0이 되어 전투에 실패했습니다.")

    db.commit()
    db.refresh(battle)
    return {
        "message": " ".join(messages),
        "player_damage": player_damage,
        "monster_damage": monster_damage,
        "battle": serialize_battle(db, battle),
        "reward": reward,
    }


@app.post("/battle/end", tags=["Battle"])
def end_battle(battle_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    battle = db.query(BattleSessionModel).filter(BattleSessionModel.id == battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="전투를 찾을 수 없습니다.")
    if battle.char_id != character.actor_id:
        raise HTTPException(status_code=403, detail="다른 캐릭터의 전투는 종료할 수 없습니다.")
    if battle.status == "ACTIVE":
        battle.status = "CANCELLED"
        db.commit()
    return {"message": "전투를 종료했습니다.", "battle_id": battle_id, "status": battle.status}




# =========================
# Quest
# =========================
@app.get("/quests", tags=["Quests"])
def get_available_quests(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    quests = db.query(QuestModel).order_by(QuestModel.id.asc()).all()
    result = []
    for quest in quests:
        existing = db.query(CharacterQuestModel).filter(
            CharacterQuestModel.char_id == character.actor_id,
            CharacterQuestModel.quest_id == quest.id,
        ).first()

        # 비반복 퀘스트를 이미 완료했다면 표시만 하되 재수락은 막는다.
        # 선행 퀘스트가 있다면 완료 여부를 확인한다.
        if quest.prerequisite_quest_id:
            prereq = db.query(CharacterQuestModel).filter(
                CharacterQuestModel.char_id == character.actor_id,
                CharacterQuestModel.quest_id == quest.prerequisite_quest_id,
                CharacterQuestModel.status == "completed",
            ).first()
            if not prereq:
                continue

        serialized = serialize_quest(db, quest, character)
        if existing:
            serialized["status"] = existing.status
        result.append(serialized)
    return result


@app.get("/quests/me", tags=["Quests"])
def get_my_quests(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    rows = db.query(CharacterQuestModel, QuestModel).join(
        QuestModel, CharacterQuestModel.quest_id == QuestModel.id
    ).filter(
        CharacterQuestModel.char_id == character.actor_id
    ).order_by(CharacterQuestModel.start_time.desc()).all()
    return [serialize_quest(db, quest, character) for _cq, quest in rows]


@app.post("/quests/{quest_id}/accept", tags=["Quests"])
def accept_quest(quest_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    quest = db.query(QuestModel).filter(QuestModel.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="퀘스트를 찾을 수 없습니다.")

    existing = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.char_id == character.actor_id,
        CharacterQuestModel.quest_id == quest_id,
    ).first()
    if existing:
        if existing.status == "completed" and not quest.is_repeatable:
            raise HTTPException(status_code=400, detail="이미 완료한 비반복 퀘스트입니다.")
        if existing.status == "active":
            raise HTTPException(status_code=400, detail="이미 진행 중인 퀘스트입니다.")

    if quest.prerequisite_quest_id:
        prereq = db.query(CharacterQuestModel).filter(
            CharacterQuestModel.char_id == character.actor_id,
            CharacterQuestModel.quest_id == quest.prerequisite_quest_id,
            CharacterQuestModel.status == "completed",
        ).first()
        if not prereq:
            raise HTTPException(status_code=400, detail="선행 퀘스트를 먼저 완료해야 합니다.")

    try:
        if existing and quest.is_repeatable:
            existing.status = "active"
            existing.current_step = 0
            db.query(CharacterQuestProgressModel).filter(
                CharacterQuestProgressModel.char_id == character.actor_id,
                CharacterQuestProgressModel.quest_id == quest_id,
            ).delete(synchronize_session=False)
        else:
            db.add(CharacterQuestModel(
                quest_id=quest_id,
                char_id=character.actor_id,
                status="active",
                current_step=0,
            ))
            db.flush()

        objectives = db.query(QuestObjectiveModel).filter(QuestObjectiveModel.quest_id == quest_id).all()
        for obj in objectives:
            exists_progress = db.query(CharacterQuestProgressModel).filter(
                CharacterQuestProgressModel.char_id == character.actor_id,
                CharacterQuestProgressModel.quest_id == quest_id,
                CharacterQuestProgressModel.objective_type == obj.objective_type,
                CharacterQuestProgressModel.target_id == obj.target_id,
            ).first()
            if not exists_progress:
                db.add(CharacterQuestProgressModel(
                    char_id=character.actor_id,
                    quest_id=quest_id,
                    objective_type=obj.objective_type,
                    target_id=obj.target_id,
                    current_count=0,
                ))
        db.commit()
        return {"message": "퀘스트를 수락했습니다.", "quest": serialize_quest(db, quest, character)}
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"퀘스트 수락 실패: {exc}")


@app.post("/quests/{quest_id}/complete", tags=["Quests"])
def complete_quest(quest_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    quest = db.query(QuestModel).filter(QuestModel.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="퀘스트를 찾을 수 없습니다.")

    char_quest = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.char_id == character.actor_id,
        CharacterQuestModel.quest_id == quest_id,
    ).first()
    if not char_quest:
        raise HTTPException(status_code=400, detail="수락하지 않은 퀘스트입니다.")
    if char_quest.status == "completed" and not quest.is_repeatable:
        raise HTTPException(status_code=400, detail="이미 완료한 퀘스트입니다.")
    if char_quest.status != "active":
        raise HTTPException(status_code=400, detail="진행 중인 퀘스트만 완료할 수 있습니다.")

    serialized = serialize_quest(db, quest, character)
    if not serialized.get("can_complete"):
        raise HTTPException(status_code=400, detail="아직 퀘스트 목표를 모두 달성하지 못했습니다.")

    try:
        reward = grant_reward_to_character(db, character, quest.reward_id)
        char_quest.status = "completed"
        # 목표 요구치 이상으로 표시되도록 동기화
        for obj in db.query(QuestObjectiveModel).filter(QuestObjectiveModel.quest_id == quest_id).all():
            progress = db.query(CharacterQuestProgressModel).filter(
                CharacterQuestProgressModel.char_id == character.actor_id,
                CharacterQuestProgressModel.quest_id == quest_id,
                CharacterQuestProgressModel.objective_type == obj.objective_type,
                CharacterQuestProgressModel.target_id == obj.target_id,
            ).first()
            if progress:
                progress.current_count = max(int(progress.current_count or 0), int(obj.required_count or 1))
        db.commit()
        db.refresh(character)
        return {
            "message": "퀘스트를 완료하고 보상을 받았습니다.",
            "quest": serialize_quest(db, quest, character),
            "reward": reward,
        }
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"퀘스트 완료 실패: {exc}")


# =========================
# Crafting
# =========================
@app.get("/crafting/methods", tags=["Crafting"])
def get_crafting_methods(current_user=Depends(require_user), db: Session = Depends(get_db)):
    ensure_default_crafting_methods(db)
    db.commit()
    rows = db.query(CraftingMethodModel).order_by(CraftingMethodModel.method.asc()).all()
    return [{"method": row.method, "description": row.description} for row in rows]


@app.get("/crafting/materials", tags=["Crafting"])
def get_crafting_materials(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    inventories = db.query(InventoryModel).filter(InventoryModel.owner_id == character.actor_id).all()
    inventory_ids = [inv.id for inv in inventories]
    if not inventory_ids:
        return {"character": {"actor_id": character.actor_id, "character_name": character.character_name}, "materials": []}

    rows = (
        db.query(InventoryItemModel.item_id, InventoryItemModel.quantity, ItemModel.name, ItemModel.description, ItemModel.type, ItemModel.sub_type, ItemModel.rarity)
        .join(ItemModel, InventoryItemModel.item_id == ItemModel.id)
        .filter(InventoryItemModel.inventory_id.in_(inventory_ids), InventoryItemModel.quantity > 0)
        .order_by(ItemModel.type.asc(), ItemModel.name.asc())
        .all()
    )

    materials = []
    for row in rows:
        item_type = str(row.type or "").lower()
        sub_type = str(row.sub_type or "").lower()
        # material은 기본 재료, crafted 결과도 추가 조합 재료로 재사용 가능하게 허용한다.
        if item_type in {"material", "consumable"} and sub_type not in {"potion"}:
            attrs = get_item_attribute_dict(db, row.item_id)
            materials.append({
                "item_id": row.item_id,
                "name": row.name,
                "description": row.description,
                "type": row.type,
                "sub_type": row.sub_type,
                "rarity": row.rarity,
                "quantity": int(row.quantity or 0),
                "attributes": attrs,
            })
    return {"character": {"actor_id": character.actor_id, "character_name": character.character_name}, "materials": materials}


def serialize_crafting_recipe(db: Session, recipe: CraftingRecipeModel) -> dict:
    item1 = db.query(ItemModel).filter(ItemModel.id == recipe.ingredient1_id).first()
    item2 = db.query(ItemModel).filter(ItemModel.id == recipe.ingredient2_id).first()
    result = db.query(ItemModel).filter(ItemModel.id == recipe.result_item_id).first()
    effect = db.query(ItemEffectModel).filter(ItemEffectModel.item_id == recipe.result_item_id).first()
    return {
        "recipe_id": recipe.id,
        "ingredient1_id": recipe.ingredient1_id,
        "ingredient1_name": item1.name if item1 else f"Item {recipe.ingredient1_id}",
        "ingredient2_id": recipe.ingredient2_id,
        "ingredient2_name": item2.name if item2 else f"Item {recipe.ingredient2_id}",
        "method": recipe.method,
        "result_item_id": recipe.result_item_id,
        "result_item_name": result.name if result else f"Item {recipe.result_item_id}",
        "result_description": result.description if result else None,
        "created_by_ai": bool(recipe.created_by_ai),
        "created_at": str(recipe.created_at) if recipe.created_at else None,
        "effect": {
            "type_effect": effect.type_effect,
            "hp": effect.hp,
            "poison": effect.poison,
            "duration": effect.duration,
            "attack": effect.attack,
            "defense": effect.defense,
            "speed": effect.speed,
            "resistance": effect.resistance,
            "burn": effect.burn,
            "freeze": effect.freeze,
            "shock": effect.shock,
            "explosion_damage": effect.explosion_damage,
        } if effect else None,
    }


@app.get("/crafting/recipes", tags=["Crafting"])
def get_crafting_recipes(current_user=Depends(require_user), db: Session = Depends(get_db)):
    recipes = db.query(CraftingRecipeModel).order_by(CraftingRecipeModel.id.desc()).limit(100).all()
    return [serialize_crafting_recipe(db, recipe) for recipe in recipes]


@app.get("/crafting/history", tags=["Crafting"])
def get_crafting_history(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    rows = db.query(CraftingLogModel).filter(CraftingLogModel.char_id == character.actor_id).order_by(CraftingLogModel.created_at.desc()).limit(50).all()
    result = []
    for log in rows:
        recipe = db.query(CraftingRecipeModel).filter(CraftingRecipeModel.id == log.recipe_id).first()
        item1 = db.query(ItemModel).filter(ItemModel.id == log.ingredient1_id).first()
        item2 = db.query(ItemModel).filter(ItemModel.id == log.ingredient2_id).first()
        output = db.query(ItemModel).filter(ItemModel.id == log.result_item_id).first()
        result.append({
            "log_id": log.id,
            "recipe_id": log.recipe_id,
            "ingredient1_name": item1.name if item1 else f"Item {log.ingredient1_id}",
            "ingredient2_name": item2.name if item2 else f"Item {log.ingredient2_id}",
            "method": log.method,
            "result_item_name": output.name if output else f"Item {log.result_item_id}",
            "created_at": str(log.created_at) if log.created_at else None,
            "recipe_created_by_ai": bool(recipe.created_by_ai) if recipe else None,
        })
    return result


@app.post("/crafting/craft", tags=["Crafting"])
def craft_item(payload: CraftingPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")
    if has_active_battle(db, character.actor_id):
        raise HTTPException(status_code=400, detail="전투 중에는 크래프팅을 할 수 없습니다.")

    method = (payload.method or "").upper().strip()
    if not method:
        raise HTTPException(status_code=400, detail="조합 방법을 선택해주세요.")

    ensure_default_crafting_methods(db)
    method_row = db.query(CraftingMethodModel).filter(CraftingMethodModel.method == method).first()
    if not method_row:
        raise HTTPException(status_code=400, detail="존재하지 않는 조합 방법입니다.")

    item1 = db.query(ItemModel).filter(ItemModel.id == payload.ingredient1_id).first()
    item2 = db.query(ItemModel).filter(ItemModel.id == payload.ingredient2_id).first()
    if not item1 or not item2:
        raise HTTPException(status_code=404, detail="재료 아이템을 찾을 수 없습니다.")

    owned1 = get_owned_inventory_item(db, character.actor_id, payload.ingredient1_id)
    owned2 = get_owned_inventory_item(db, character.actor_id, payload.ingredient2_id)
    if not owned1 or not owned2:
        raise HTTPException(status_code=400, detail="현재 캐릭터 인벤토리에 없는 재료입니다.")
    inv_item1, _, _ = owned1
    inv_item2, _, _ = owned2

    if payload.ingredient1_id == payload.ingredient2_id:
        if inv_item1.quantity < 2:
            raise HTTPException(status_code=400, detail="같은 재료 2개를 조합하려면 수량이 2개 이상 필요합니다.")
    else:
        if inv_item1.quantity < 1 or inv_item2.quantity < 1:
            raise HTTPException(status_code=400, detail="재료 수량이 부족합니다.")

    ingredient1_id, ingredient2_id = normalize_crafting_ingredients(payload.ingredient1_id, payload.ingredient2_id)
    normalized_item1 = db.query(ItemModel).filter(ItemModel.id == ingredient1_id).first()
    normalized_item2 = db.query(ItemModel).filter(ItemModel.id == ingredient2_id).first()
    recipe = db.query(CraftingRecipeModel).filter(
        CraftingRecipeModel.ingredient1_id == ingredient1_id,
        CraftingRecipeModel.ingredient2_id == ingredient2_id,
        CraftingRecipeModel.method == method,
    ).first()

    created_new_recipe = False
    ai_debug = None
    try:
        if recipe:
            result_item = db.query(ItemModel).filter(ItemModel.id == recipe.result_item_id).first()
            if not result_item:
                raise HTTPException(status_code=500, detail="레시피 결과 아이템이 존재하지 않습니다.")
        else:
            result_item, _, _, _, ai_debug = create_generated_crafting_result(db, normalized_item1, normalized_item2, method)
            recipe = CraftingRecipeModel(
                ingredient1_id=ingredient1_id,
                ingredient2_id=ingredient2_id,
                method=method,
                result_item_id=result_item.id,
                created_by_ai=True,
            )
            db.add(recipe)
            db.flush()
            created_new_recipe = True

        # 재료 차감. 같은 재료를 두 번 쓰는 경우 같은 InventoryItem에서 2개 차감한다.
        if payload.ingredient1_id == payload.ingredient2_id:
            inv_item1.quantity -= 2
            if inv_item1.quantity <= 0:
                db.delete(inv_item1)
        else:
            inv_item1.quantity -= 1
            inv_item2.quantity -= 1
            if inv_item1.quantity <= 0:
                db.delete(inv_item1)
            if inv_item2.quantity <= 0:
                db.delete(inv_item2)

        result_inv = add_item_to_character_inventory(db, character.actor_id, result_item.id, 1)
        db.add(CraftingLogModel(
            char_id=character.actor_id,
            recipe_id=recipe.id,
            ingredient1_id=ingredient1_id,
            ingredient2_id=ingredient2_id,
            method=method,
            result_item_id=result_item.id,
        ))
        quest_updates = update_quest_progress(db, character.actor_id, "CRAFT_ITEM", result_item.id, 1)
        db.commit()

        return {
            "message": "새 조합을 발견했습니다." if created_new_recipe else "기존 레시피로 제작했습니다.",
            "created_new_recipe": created_new_recipe,
            "recipe": serialize_crafting_recipe(db, recipe),
            "result_item": {
                "item_id": result_item.id,
                "name": result_item.name,
                "description": result_item.description,
                "type": result_item.type,
                "sub_type": result_item.sub_type,
                "current_quantity": result_inv.quantity,
            },
            "quest_updates": quest_updates,
            "ai_debug": ai_debug if created_new_recipe else {
                "is_ai_generated": False,
                "recipe_source": "cached_recipe",
                "message": "이미 DB에 저장된 레시피를 재사용했습니다. AI 모델을 다시 실행하지 않았습니다.",
            },
        }
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"크래프팅 실패: {exc}")


# =========================
# Admin: users / items
# =========================
@app.get("/admin/characters", tags=["Admin"])
def admin_get_characters(
    keyword: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(CharacterModel, UserModel.user_name).join(UserModel, CharacterModel.user_id == UserModel.id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((CharacterModel.character_name.like(like)) | (CharacterModel.user_id.like(like)) | (UserModel.user_name.like(like)))
    if user_id:
        query = query.filter(CharacterModel.user_id == user_id)
    rows = query.order_by(CharacterModel.user_id.asc(), CharacterModel.actor_id.asc()).all()
    return [
        {
            "actor_id": char.actor_id,
            "user_id": char.user_id,
            "user_name": user_name,
            "character_name": char.character_name,
            "level": char.level,
            "exp": char.exp,
            "active": char.active,
            "is_public": char.is_public,
        }
        for char, user_name in rows
    ]


@app.get("/admin/items", tags=["Admin"])
def admin_get_items(
    keyword: Optional[str] = None,
    item_type: Optional[str] = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(ItemModel)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((ItemModel.name.like(like)) | (ItemModel.description.like(like)))
    if item_type and item_type != "ALL":
        query = query.filter(ItemModel.type == item_type)
    items = query.order_by(ItemModel.type.asc(), ItemModel.name.asc()).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "type": item.type,
            "sub_type": item.sub_type,
            "capacity": item.capacity,
            "equipment_part": item.equipment_part,
            "required_level": item.required_level,
            "rarity": item.rarity,
            "is_generated": item.is_generated,
        }
        for item in items
    ]


@app.post("/admin/characters/{char_id}/items", tags=["Admin"])
def admin_grant_item_to_character(
    char_id: int,
    payload: AdminGrantItemPayload,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    item = db.query(ItemModel).filter(ItemModel.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

    try:
        inv_item = add_item_to_character_inventory(db, char_id, payload.item_id, payload.quantity)
        db.commit()
        return {
            "message": "아이템을 지급했습니다.",
            "char_id": char_id,
            "item_id": payload.item_id,
            "item_name": item.name,
            "quantity_added": payload.quantity,
            "current_quantity": inv_item.quantity,
        }
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"아이템 지급 실패: {exc}")




@app.get("/admin/battles", tags=["Admin"])
def admin_get_battles(
    status_filter: Optional[str] = None,
    char_id: Optional[int] = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = (
        db.query(BattleSessionModel, CharacterModel.character_name)
        .join(CharacterModel, BattleSessionModel.char_id == CharacterModel.actor_id)
    )
    if status_filter and status_filter != "ALL":
        query = query.filter(BattleSessionModel.status == status_filter)
    if char_id:
        query = query.filter(BattleSessionModel.char_id == char_id)
    rows = query.order_by(BattleSessionModel.started_at.desc(), BattleSessionModel.id.desc()).limit(100).all()
    return [
        {
            "battle_id": battle.id,
            "char_id": battle.char_id,
            "character_name": character_name,
            "monster_id": battle.monster_id,
            "current_monster_hp": battle.current_monster_hp,
            "status": battle.status,
            "reward_claimed": battle.reward_claimed,
            "started_at": str(battle.started_at) if battle.started_at else None,
            "ended_at": str(battle.ended_at) if battle.ended_at else None,
        }
        for battle, character_name in rows
    ]


@app.patch("/admin/battles/{battle_id}/status", tags=["Admin"])
def admin_update_battle_status(
    battle_id: int,
    payload: AdminBattleStatusUpdate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    battle = db.query(BattleSessionModel).filter(BattleSessionModel.id == battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="전투 세션을 찾을 수 없습니다.")
    new_status = (payload.status or "ABANDONED").upper()
    if new_status not in {"ACTIVE", "WON", "FAILED", "ABANDONED"}:
        raise HTTPException(status_code=400, detail="허용되지 않는 전투 상태입니다.")
    battle.status = new_status
    if new_status != "ACTIVE":
        battle.ended_at = func.now()
    db.commit()
    return {"message": "전투 세션 상태를 변경했습니다.", "battle_id": battle.id, "status": battle.status}


@app.get("/admin/monsters", tags=["Admin"])
def admin_get_monsters(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    monsters = db.query(MonsterModel).order_by(MonsterModel.actor_id.asc()).all()
    return [
        {
            "actor_id": monster.actor_id,
            "name": get_monster_display_name(monster),
            "level": int(getattr(monster, "level", 1) or 1),
            "hp": monster.hp,
            "atk": monster.atk,
            "def": monster.def_,
            "drop_reward_id": monster.drop_reward_id,
            "expected_reward": get_reward_preview(db, monster.drop_reward_id),
        }
        for monster in monsters
    ]


@app.get("/admin/quests", tags=["Admin"])
def admin_get_quests(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    quests = db.query(QuestModel).order_by(QuestModel.id.asc()).all()
    result = []
    for quest in quests:
        objectives = db.query(QuestObjectiveModel).filter(QuestObjectiveModel.quest_id == quest.id).all()
        result.append({
            "id": quest.id,
            "name": quest.name,
            "type": quest.type,
            "is_repeatable": quest.is_repeatable,
            "reward_id": quest.reward_id,
            "objectives": [
                {
                    "objective_type": obj.objective_type,
                    "target_id": obj.target_id,
                    "required_count": obj.required_count,
                }
                for obj in objectives
            ],
        })
    return result


@app.get("/admin/recipes", tags=["Admin"])
def admin_get_recipes(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    try:
        rows = db.execute(text(
            """
            SELECT cr.id, cr.ingredient1_id, i1.name AS ingredient1_name,
                   cr.ingredient2_id, i2.name AS ingredient2_name,
                   cr.method, cr.result_item_id, r.name AS result_item_name,
                   cr.created_by_ai, cr.created_at
            FROM CraftingRecipe cr
            LEFT JOIN Item i1 ON cr.ingredient1_id = i1.id
            LEFT JOIN Item i2 ON cr.ingredient2_id = i2.id
            LEFT JOIN Item r ON cr.result_item_id = r.id
            ORDER BY cr.id DESC
            LIMIT 100
            """
        )).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        return []

# =========================
# Compatibility endpoints from old prototype
# =========================
@app.get("/users/{user_id}/characters", response_model=List[CharacterResponse], tags=["Characters"])
def get_user_characters_compat(user_id: str, current_user=Depends(require_user), db: Session = Depends(get_db)):
    if user_id != current_user["id"] and current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="다른 사용자의 캐릭터 목록은 조회할 수 없습니다.")
    return db.query(CharacterModel).filter(CharacterModel.user_id == user_id).all()


if __name__ == "__main__":
    uvicorn.run("backend_main_v1:app", host="0.0.0.0", port=8000, reload=True)

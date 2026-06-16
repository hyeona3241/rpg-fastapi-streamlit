import uuid
from typing import List, Optional

import uvicorn
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func
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


class QuantityPayload(BaseModel):
    quantity: int = Field(gt=0)


class AdminGrantItemPayload(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)


class SpecimenResponse(BaseModel):
    type: str
    name: str
    description: Optional[str] = None


class SpecimenInput(BaseModel):
    type: str
    fraction: float = Field(gt=0, le=1)


class CharacterCreate(BaseModel):
    character_name: str
    specimens: List[SpecimenInput] = Field(default_factory=list)


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


def calculate_initial_stats(db: Session, specimens: list[SpecimenInput]) -> dict[str, int]:
    stats: dict[str, float] = {}

    # Level 1 base stats
    for row in db.query(LevelBaseStatModel).filter(LevelBaseStatModel.char_level == 1).all():
        stats[row.stat_type] = stats.get(row.stat_type, 0) + row.value

    # Weighted specimen stats
    for specimen in specimens:
        rows = db.query(SpecimenBaseStatModel).filter(SpecimenBaseStatModel.specimen_type == specimen.type).all()
        for row in rows:
            stats[row.stat_type] = stats.get(row.stat_type, 0) + row.value * specimen.fraction

    return {stat_type: int(round(value)) for stat_type, value in stats.items()}


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

        # Basic job: use BEGINNER/NOVICE if present, otherwise first job row.
        job = db.query(JobModel).filter(JobModel.type.in_(["BEGINNER", "NOVICE"])).first()
        if not job:
            job = db.query(JobModel).first()
        if job:
            db.add(CharacterJobModel(type=job.type, char_id=actor.id, active=True))

        # Initial stats
        initial_stats = calculate_initial_stats(db, char_data.specimens)
        for stat_type, value in initial_stats.items():
            db.add(ActorStatModel(actor_id=actor.id, stat_type=stat_type, value=value))

        # Basic inventory
        db.add(InventoryModel(owner_id=actor.id, type="BASIC", capacity=20))

        # Basic skills: initially give skills with no unlock condition.
        basic_skills = db.query(SkillModel).filter(SkillModel.unlock_condition_id.is_(None)).all()
        for skill in basic_skills:
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


@app.get("/characters/{char_id}", tags=["Characters"])
def get_character_detail(char_id: int, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = db.query(CharacterModel).filter(CharacterModel.actor_id == char_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if character.user_id != current_user["id"] and not character.is_public and current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="비공개 캐릭터입니다.")

    specimens = db.query(CharacterSpecimenModel).filter(CharacterSpecimenModel.char_id == char_id).all()
    stats = db.query(ActorStatModel).filter(ActorStatModel.actor_id == char_id).all()
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
        "stats": {s.stat_type: s.value for s in stats},
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

    inv_item.quantity -= payload.quantity
    if inv_item.quantity <= 0:
        db.delete(inv_item)
    db.commit()
    return {"message": f"{item.name} {payload.quantity}개를 사용했습니다.", "item_id": item_id}


@app.post("/inventory/items/{item_id}/discard", tags=["Inventory"])
def discard_inventory_item(item_id: int, payload: QuantityPayload, current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

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
# Skills
# =========================
@app.get("/skills/me", tags=["Skills"])
def get_my_skills(current_user=Depends(require_user), db: Session = Depends(get_db)):
    character = get_active_character(db, current_user["id"])
    if not character:
        raise HTTPException(status_code=404, detail="선택된 캐릭터가 없습니다.")

    rows = (
        db.query(SkillModel.id, SkillModel.name, SkillModel.description, SkillModel.mp_cost, SkillModel.cooldown_sec, CharacterSkillModel.skill_level)
        .join(CharacterSkillModel, SkillModel.id == CharacterSkillModel.skill_id)
        .filter(CharacterSkillModel.char_id == character.actor_id)
        .order_by(SkillModel.id.asc())
        .all()
    )
    return {
        "character": {"actor_id": character.actor_id, "character_name": character.character_name},
        "skills": [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "mp_cost": row.mp_cost,
                "cooldown_sec": row.cooldown_sec,
                "skill_level": row.skill_level,
            }
            for row in rows
        ],
    }


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

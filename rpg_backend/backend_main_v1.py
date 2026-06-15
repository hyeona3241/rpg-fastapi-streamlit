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

    session_id = str(uuid.uuid4())
    session_store[session_id] = {"id": user.id, "name": user.user_name, "role": user.role}
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=3600, samesite="lax")
    return {"message": "로그인 성공", "user_id": user.id, "user_name": user.user_name, "role": user.role}


@app.post("/logout", tags=["Auth"])
def logout(response: Response, session_id: str | None = Cookie(default=None)):
    if session_id and session_id in session_store:
        del session_store[session_id]
    response.delete_cookie(key="session_id")
    return {"message": "로그아웃 성공"}


@app.get("/me", response_model=UserResponse, tags=["Auth"])
def me(current_user=Depends(require_user)):
    return {"user_id": current_user["id"], "user_name": current_user["name"], "role": current_user.get("role", "USER")}


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.id == user.user_identifier).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 유저 ID입니다.")

    new_user = UserModel(id=user.user_identifier, user_name=user.nickname, password=user.password, role="USER")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.id, "user_name": new_user.user_name, "role": new_user.role}


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

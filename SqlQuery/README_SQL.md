# Consolidated SQL Bundle for Streamlit RPG App

기존 SQL이 여러 번 누적되면서 실행 순서가 헷갈릴 수 있어, 아래 3개 파일로 정리했습니다.

## 새로 DB를 만들 때

1. 관리자/root 계정으로 DB와 rpg 계정 생성

```bash
mysql -u root -p < 00_reset_create_database_root.sql
```

2. rpg 계정으로 전체 스키마 + 테스트 데이터 생성

```bash
mysql -urpg -prpg MyRPG < 01_full_schema_and_seed.sql
```

## 이미 사용 중인 DB에 패치할 때

기존 데이터는 유지하고, 누락된 컬럼/테이블/데모 데이터를 추가합니다.

```bash
mysql -urpg -prpg MyRPG < 02_patch_existing_db_safe.sql
```

## 정리 원칙

- `RPG.sql`, `populate_rpg.sql`은 기본 베이스로 유지했습니다.
- 이후 누적된 upgrade/seed SQL은 `02_patch_existing_db_safe.sql`에 합쳤습니다.
- 컬럼 삭제는 아직 하지 않는 것을 추천합니다. 현재 FastAPI 코드와 FK 관계에서 사용 여부가 완전히 확정되지 않은 컬럼이 있을 수 있기 때문입니다.
- 사용하지 않는 컬럼은 최종 제출 직전에 `SHOW CREATE TABLE`과 코드 사용 여부를 대조한 뒤 삭제하는 것이 안전합니다.

## 현재 앱에서 중요한 확장 요소

- `User.role`, `User.active`
- `Character.is_public`, `Character.created_at`
- `Item.icon_url`, `Item.equipment_part`, `Item.required_level`, `Item.rarity`, `Item.is_generated`
- `EquippedSkill`
- `BattleSession`, `BattleSkillCooldown`, `BattleLog`
- `QuestObjective`, `CharacterQuestProgress`
- `ItemAttribute`, `ItemEffect`
- `CraftingMethod`, `CraftingRecipe`, `CraftingLog`


## 추가 파일

### 04_patch_existing_db_demo_safe.sql
기존 DB를 유지하면서 누락된 컬럼/테이블/테스트 데이터만 추가합니다.

```bash
mysql -urpg -prpg MyRPG < 02_patch_existing_db_demo_safe.sql
```

기존 플레이 데이터가 있는 경우에는 이 파일을 사용하는 것을 추천합니다.

### 99_optional_drop_unused_legacy_tables.sql
현재 앱에서 사용하지 않는 오래된 테이블을 삭제하는 선택 파일입니다.

삭제 대상 예시:

- RequirementLevel / RequirementSpecimen / RequirementJob / RequirementSkill / RequirementQuest
- StatusEffect / CharacterStatusEffect
- Shop / ShopCatalog / Villager / VillagerQuest
- SkillBonusStat

주의: 현재 앱에는 필요 없지만, 과거 과제나 다른 SQL 예제에서 쓸 수 있으므로 최종 제출 직전에만 검토해서 실행하세요.
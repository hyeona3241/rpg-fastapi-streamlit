# Streamlit RPG 애플리케이션 최종 설계 문서

## 1. 프로젝트 개요

본 프로젝트는 **Streamlit 클라이언트**, **FastAPI REST API 서버**, **MySQL 데이터베이스**를 연동하여 RPG 시나리오 기반의 테스트 애플리케이션을 구현하는 것을 목표로 한다.

사용자는 계정을 생성하고 로그인한 뒤, 캐릭터를 만들고 선택할 수 있다. 선택된 캐릭터는 종족, 직업, 스탯, 스킬, 인벤토리 정보를 가지며, 몬스터 전투, 퀘스트, 아이템 획득, 장비 장착, 동적 크래프팅 시스템과 연결된다.

---

## 2. 전체 플레이 시나리오

```text
회원가입 / 로그인
        │
        ▼
캐릭터 생성
        │
        ▼
종족 선택 및 비율 설정
        │
        ▼
초기 스탯 / 기본 직업 / 기본 스킬 / 인벤토리 생성
        │
        ▼
캐릭터 선택
        │
        ▼
캐릭터 상세 정보 확인
        │
        ▼
NPC 퀘스트 수락
        │
        ▼
스킬 장착
        │
        ▼
몬스터와 턴제 전투
        │
        ▼
아이템 및 경험치 획득
        │
        ▼
인벤토리 반영
        │
        ▼
장비 장착 / 스탯 변화 확인
        │
        ▼
아이템 크래프팅
        │
        ▼
퀘스트 진행도 갱신 및 완료
        │
        ▼
보상 지급 / 레벨업 / 스킬 해금
```

---

## 3. 주요 기능 구성

## 3.1 계정 시스템

### 기능

* 회원가입
* 로그인
* 로그아웃
* 내 계정 정보 조회
* 비밀번호 변경
* 계정 삭제
* 어드민 계정 구분

### 핵심 조건

* 중복 ID 사용 불가
* 로그인 성공 시 `session_id` 쿠키 발급
* 로그인하지 않은 사용자는 주요 기능 접근 불가
* 일반 사용자는 자신의 데이터만 접근 가능
* 어드민은 전체 유저 및 캐릭터 조회 가능

---

## 3.2 캐릭터 시스템

### 기능

* 캐릭터 생성
* 캐릭터 목록 조회
* 캐릭터 선택
* 캐릭터 삭제
* 캐릭터 공개/비공개 설정
* 공개 캐릭터 검색
* 캐릭터 상세 정보 조회

### 캐릭터 생성 시 처리

```text
Actor 생성
→ Character 생성
→ CharacterSpecimen 생성
→ 기본 직업 부여
→ 초기 스탯 계산
→ 기본 스킬 지급
→ 기본 인벤토리 생성
```

### 종족 시스템

캐릭터는 단일 종족 또는 복합 종족을 가질 수 있다.

예시:

| 종족    |  비율 |
| ----- | --: |
| Human | 50% |
| Elf   | 30% |
| Orc   | 20% |

종족 비율 총합은 반드시 100%여야 한다.

### 스탯 계산

```text
최종 초기 스탯
= 레벨 기본 스탯
+ Σ(종족 기본 스탯 × 종족 비율)
+ 장비 보너스
+ 버프 효과
```

---

## 3.3 인벤토리 및 아이템 시스템

### 기능

* 현재 선택 캐릭터의 인벤토리 조회
* 아이템 획득
* 아이템 수량 증가/감소
* 아이템 상세 정보 확인
* 장비 아이템 장착
* 크래프팅 재료 선택

### 아이템 정보

| 항목          | 설명                                |
| ----------- | --------------------------------- |
| name        | 아이템 이름                            |
| description | 아이템 설명                            |
| type        | material / equipment / consumable |
| sub_type    | weapon / armor / herb 등           |
| capacity    | 최대 보유 수량                          |
| icon_url    | 아이콘 이미지 경로 또는 URL                 |

---

## 3.4 동적 크래프팅 시스템

### 기능

* 인벤토리에서 재료 선택
* 조합 방법 선택
* 기존 레시피 검색
* 기존 레시피가 있으면 기존 결과 아이템 지급
* 새로운 조합이면 AI 기반 결과 생성
* 새 아이템과 레시피 DB 저장
* 사용한 재료 차감
* 결과 아이템 인벤토리 추가

### 크래프팅 흐름

```text
재료 1 선택
→ 재료 2 선택
→ 조합 방법 선택
→ CraftingRecipe 조회
    ├─ 기존 레시피 있음 → 기존 결과 아이템 지급
    └─ 기존 레시피 없음 → MLP + LLM으로 새 아이템 생성
→ 재료 차감
→ 결과 아이템 지급
→ CraftingLog 저장
```

### 조합 방법 예시

* Mix
* Boil
* Bake
* Distill
* Compress
* Infuse

---

## 3.5 장비 장착 시스템

### 기능

* 인벤토리 내 장비 아이템 조회
* 장비 장착
* 장비 해제
* 장비 장착 후 스탯 변화 확인

### 장비 슬롯

| 슬롯     | 설명    |
| ------ | ----- |
| weapon | 무기    |
| head   | 머리 장비 |
| armor  | 방어구   |

### 장착 조건

* `Item.type = equipment`인 아이템만 장착 가능
* 장비 부위와 슬롯이 일치해야 함
* 현재 선택 캐릭터의 인벤토리에 있는 아이템만 장착 가능
* 이미 장착된 슬롯은 기존 장비를 해제한 뒤 새 장비 장착

---

## 3.6 스킬 시스템

### 기능

* 보유 스킬 조회
* 스킬 장착
* 스킬 해제
* 전투 중 장착 스킬 사용
* 레벨업 시 스킬 자동 해금

### 스킬 장착 조건

* 캐릭터가 보유한 스킬만 장착 가능
* 최대 3개까지 장착
* 전투에서는 장착된 스킬만 사용 가능
* MP 부족 또는 쿨타임 중인 스킬은 사용 불가

---

## 3.7 몬스터 및 턴제 전투 시스템

### 기능

* 몬스터 목록 조회
* 몬스터 선택
* 전투 세션 생성
* 장착 스킬로 공격
* 몬스터 HP 감소
* 처치 시 보상 지급

### 전투 방식

Streamlit 특성상 실시간 전투가 아닌 버튼 기반 턴제 전투로 구현한다.

```text
몬스터 선택
→ 전투 시작
→ 장착 스킬 버튼 클릭
→ 데미지 계산
→ 몬스터 HP 감소
→ HP 0 이하 시 처치
→ 경험치 / 아이템 보상 지급
```

### 전투 세션 필요 이유

`Monster` 테이블은 원본 몬스터 데이터로 유지하고, 실제 전투 중 HP는 별도 전투 세션에서 관리한다.

---

## 3.8 퀘스트 및 NPC 시스템

### 기능

* NPC 목록 조회
* NPC가 제공하는 퀘스트 조회
* 퀘스트 수락
* 진행 중인 퀘스트 조회
* 퀘스트 진행도 갱신
* 퀘스트 완료
* 보상 지급

### 퀘스트 종류

| 타입           | 설명        | 예시          |
| ------------ | --------- | ----------- |
| KILL_MONSTER | 특정 몬스터 처치 | 슬라임 3마리 처치  |
| COLLECT_ITEM | 특정 아이템 수집 | 슬라임 젤 2개 수집 |
| CRAFT_ITEM   | 특정 아이템 제작 | 회복 물약 1개 제작 |

### 진행도 갱신 이벤트

* 몬스터 처치
* 아이템 획득
* 아이템 제작

---

## 3.9 보상 시스템

### 보상 종류

* 경험치
* 아이템
* 장비
* 스킬 해금
* 퀘스트/직업 해금

초기 구현에서는 **경험치 + 아이템 보상**을 우선 적용한다.

### 보상 지급 흐름

```text
Reward 조회
→ RewardExp 지급
→ RewardItem 지급
→ 인벤토리 반영
→ 레벨업 검사
→ 스킬 해금 검사
→ 퀘스트 상태 갱신
```

---

## 4. 추가 또는 수정이 필요한 데이터베이스

## 4.1 기존 테이블에 추가할 컬럼

### User

```sql
ALTER TABLE `User`
ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'USER';
```

목적:

* 일반 유저와 어드민 구분

---

### Character

```sql
ALTER TABLE `Character`
ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE;
```

목적:

* 공개 캐릭터 검색 기능 지원

선택적으로 추가:

```sql
ALTER TABLE `Character`
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
```

---

### Item

```sql
ALTER TABLE Item
ADD COLUMN icon_url TEXT;
```

목적:

* 아이템 아이콘 또는 AI 생성 이미지 저장

---

## 4.2 새로 추가할 테이블

## 4.2.1 EquippedSkill

보유 스킬과 장착 스킬을 분리하기 위한 테이블이다.

```sql
CREATE TABLE EquippedSkill (
    char_id INT NOT NULL,
    slot_no INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (char_id, slot_no),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);
```

---

## 4.2.2 BattleSession

전투 중 몬스터의 현재 HP와 보상 지급 여부를 관리한다.

```sql
CREATE TABLE BattleSession (
    id INT AUTO_INCREMENT PRIMARY KEY,
    char_id INT NOT NULL,
    monster_id INT NOT NULL,
    current_monster_hp INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    reward_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME NULL,
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (monster_id) REFERENCES Monster(actor_id)
);
```

---

## 4.2.3 QuestObjective

퀘스트 목표를 명확히 저장하기 위한 테이블이다.

```sql
CREATE TABLE QuestObjective (
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    required_count INT NOT NULL,
    PRIMARY KEY (quest_id, objective_type, target_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id)
);
```

---

## 4.2.4 CharacterQuestProgress

캐릭터별 퀘스트 진행도를 저장한다.

```sql
CREATE TABLE CharacterQuestProgress (
    char_id INT NOT NULL,
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    current_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (char_id, quest_id, objective_type, target_id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id)
);
```

---

## 4.2.5 CraftingRecipe

동적 크래프팅 레시피를 저장한다.

```sql
CREATE TABLE CraftingRecipe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient1_id INT NOT NULL,
    ingredient2_id INT NOT NULL,
    method VARCHAR(50) NOT NULL,
    result_item_id INT NOT NULL,
    created_by_ai BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient1_id) REFERENCES Item(id),
    FOREIGN KEY (ingredient2_id) REFERENCES Item(id),
    FOREIGN KEY (result_item_id) REFERENCES Item(id)
);
```

추천 제약:

```sql
ALTER TABLE CraftingRecipe
ADD UNIQUE KEY uq_recipe (ingredient1_id, ingredient2_id, method);
```

단, 재료 순서를 무시하려면 서버 코드에서 작은 ID를 `ingredient1_id`, 큰 ID를 `ingredient2_id`로 정렬하여 저장한다.

---

## 4.2.6 ItemAttribute

아이템의 속성을 저장한다.

```sql
CREATE TABLE ItemAttribute (
    item_id INT PRIMARY KEY,
    toxic FLOAT DEFAULT 0,
    healing FLOAT DEFAULT 0,
    viscous FLOAT DEFAULT 0,
    stable FLOAT DEFAULT 0,
    organic FLOAT DEFAULT 0,
    plant FLOAT DEFAULT 0,
    unstable FLOAT DEFAULT 0,
    burnt FLOAT DEFAULT 0,
    metallic FLOAT DEFAULT 0,
    magical FLOAT DEFAULT 0,
    cold FLOAT DEFAULT 0,
    hot FLOAT DEFAULT 0,
    electric FLOAT DEFAULT 0,
    explosive FLOAT DEFAULT 0,
    defensive FLOAT DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);
```

---

## 4.2.7 ItemEffect

아이템의 실제 효과를 저장한다.

```sql
CREATE TABLE ItemEffect (
    item_id INT PRIMARY KEY,
    type_effect VARCHAR(50),
    hp INT DEFAULT 0,
    poison INT DEFAULT 0,
    duration INT DEFAULT 0,
    attack INT DEFAULT 0,
    defense INT DEFAULT 0,
    speed INT DEFAULT 0,
    resistance INT DEFAULT 0,
    burn INT DEFAULT 0,
    freeze INT DEFAULT 0,
    shock INT DEFAULT 0,
    explosion_damage INT DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);
```

---

## 4.2.8 CraftingLog

캐릭터의 제작 기록을 저장한다.

```sql
CREATE TABLE CraftingLog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    char_id INT NOT NULL,
    recipe_id INT NOT NULL,
    ingredient1_id INT NOT NULL,
    ingredient2_id INT NOT NULL,
    method VARCHAR(50) NOT NULL,
    result_item_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (recipe_id) REFERENCES CraftingRecipe(id),
    FOREIGN KEY (ingredient1_id) REFERENCES Item(id),
    FOREIGN KEY (ingredient2_id) REFERENCES Item(id),
    FOREIGN KEY (result_item_id) REFERENCES Item(id)
);
```

---

## 5. Streamlit 화면 구성

## 5.1 로그인 전

| 화면   | 기능      |
| ---- | ------- |
| 로그인  | 계정 로그인  |
| 회원가입 | 새 계정 생성 |

---

## 5.2 로그인 후

| 탭      | 주요 기능                     |
| ------ | ------------------------- |
| 내 계정   | 계정 정보, 로그아웃, 비밀번호 변경      |
| 캐릭터    | 캐릭터 생성, 선택, 삭제, 공개 설정     |
| 캐릭터 상세 | 종족, 직업, 레벨, 스탯, 스킬 확인     |
| 인벤토리   | 아이템 목록, 수량, 상세 정보         |
| 장비     | 장비 장착, 해제, 스탯 변화 확인       |
| 스킬     | 보유 스킬, 장착 스킬 관리           |
| 전투     | 몬스터 선택, 턴제 전투, 보상 획득      |
| 퀘스트    | NPC 퀘스트 조회, 수락, 진행, 완료    |
| 크래프팅   | 재료 선택, 조합 방법 선택, 결과 생성    |
| 레시피 도감 | 등록된 조합식 확인                |
| 어드민    | 유저, 캐릭터, 아이템, 몬스터, 퀘스트 관리 |

---

## 6. 추천 API 구성

## 6.1 Auth / User

```text
POST   /login
POST   /logout
GET    /me
POST   /users
PATCH  /me/password
DELETE /users/me
```

---

## 6.2 Character

```text
GET    /characters/me
POST   /characters
PATCH  /characters/{char_id}/select
GET    /characters/{char_id}
GET    /characters/{char_id}/stats
GET    /characters/{char_id}/skills
PATCH  /characters/{char_id}/visibility
DELETE /characters/{char_id}
GET    /characters/public/search
```

---

## 6.3 Inventory / Item

```text
GET    /inventory
GET    /inventory/items
GET    /items
GET    /items/{item_id}
GET    /items/search
```

---

## 6.4 Equipment

```text
GET  /equipment/me
POST /equipment/equip
POST /equipment/unequip
```

---

## 6.5 Skill

```text
GET  /skills/me
POST /skills/equip
POST /skills/unequip
GET  /skills/unlocked
```

---

## 6.6 Battle / Monster

```text
GET  /monsters
GET  /monsters/{monster_id}
POST /battle/start
POST /battle/attack
GET  /battle/status
POST /battle/end
```

---

## 6.7 Quest / NPC / Reward

```text
GET  /npcs
GET  /npcs/{npc_id}/quests
GET  /quests
POST /quests/{quest_id}/accept
GET  /quests/me
POST /quests/{quest_id}/complete
```

---

## 6.8 Crafting

```text
POST /crafting/craft
GET  /crafting/recipes
GET  /crafting/history
```

---

## 6.9 Admin

```text
GET  /admin/users
GET  /admin/characters
GET  /admin/items
POST /admin/items
GET  /admin/monsters
POST /admin/monsters
GET  /admin/quests
POST /admin/quests
```

---

## 7. 구현 순서

## 1단계: DB 스키마 정리

1. 기존 SQL 실행 확인
2. `User.role` 추가
3. `Character.is_public` 추가
4. `Item.icon_url` 추가
5. 추가 테이블 생성

   * `EquippedSkill`
   * `BattleSession`
   * `QuestObjective`
   * `CharacterQuestProgress`
   * `CraftingRecipe`
   * `ItemAttribute`
   * `ItemEffect`
   * `CraftingLog`
6. 테스트 데이터 삽입

   * 기본 유저
   * 어드민 유저
   * 종족
   * 직업
   * 스킬
   * 몬스터
   * 아이템
   * 퀘스트
   * 보상

---

## 2단계: 계정 기능 구현

1. 회원가입
2. 로그인
3. 로그아웃
4. 세션 쿠키 저장
5. 내 계정 정보 조회
6. 어드민 권한 구분

---

## 3단계: 캐릭터 기능 구현

1. 종족 목록 조회
2. 캐릭터 생성 화면 제작
3. 종족 비율 슬라이더 구현
4. 캐릭터 생성 API 확장
5. 초기 스탯 계산
6. 기본 직업 지급
7. 기본 스킬 지급
8. 기본 인벤토리 생성
9. 캐릭터 선택 기능
10. 캐릭터 상세 화면 제작

---

## 4단계: 인벤토리 및 아이템 구현

1. 현재 선택 캐릭터 기준 인벤토리 조회
2. 아이템 상세 표시
3. 테스트용 아이템 지급 API 또는 어드민 지급 기능
4. 아이템 수량 증가/감소 처리

---

## 5단계: 장비 및 스킬 구현

1. 장비 아이템 필터링
2. 장비 장착/해제
3. 장비 보너스 스탯 반영
4. 보유 스킬 목록 조회
5. 스킬 장착/해제
6. 장착 스킬만 전투에서 사용 가능하도록 제한

---

## 6단계: 몬스터 전투 구현

1. 몬스터 목록 조회
2. 전투 시작
3. `BattleSession` 생성
4. 장착 스킬 버튼 표시
5. 스킬 공격 처리
6. 몬스터 HP 감소
7. 몬스터 처치 처리
8. 보상 지급
9. 경험치 증가 및 레벨업 검사
10. 인벤토리 반영

---

## 7단계: 퀘스트 구현

1. NPC 목록 조회
2. NPC별 퀘스트 조회
3. 퀘스트 수락
4. `CharacterQuest` 생성
5. `CharacterQuestProgress` 생성
6. 몬스터 처치/아이템 획득/크래프팅 시 진행도 갱신
7. 퀘스트 완료
8. 보상 지급

---

## 8단계: 동적 크래프팅 구현

1. 인벤토리의 재료 아이템 조회
2. 재료 2개 선택
3. 조합 방법 선택
4. 기존 레시피 조회
5. 기존 결과 아이템 지급
6. 새 조합이면 AI 결과 생성
7. 새 아이템 저장
8. 새 레시피 저장
9. 재료 차감
10. 결과 아이템 지급
11. 제작 기록 저장

---

## 9단계: 어드민 및 테스트 화면 구현

1. 전체 유저 조회
2. 전체 캐릭터 조회
3. 아이템 관리
4. 몬스터 관리
5. 퀘스트 관리
6. 레시피 조회
7. 테스트 데이터 확인

---

## 10단계: 시연 흐름 구성

최종 시연은 다음 순서로 진행한다.

```text
1. 회원가입
2. 로그인
3. 캐릭터 생성
4. 종족 비율 선택
5. 캐릭터 선택
6. 캐릭터 상세 정보 확인
7. NPC 퀘스트 수락
8. 스킬 장착
9. 몬스터 전투
10. 보상 아이템 획득
11. 인벤토리 확인
12. 장비 장착
13. 크래프팅 실행
14. 새 레시피 저장 확인
15. 퀘스트 완료
16. 경험치 획득 및 레벨업 확인
```

---

## 8. 우선 구현할 최소 기능 범위

시간이 부족할 경우 다음 기능까지만 구현해도 과제 요구사항을 충족하기 좋다.

```text
회원가입 / 로그인
→ 캐릭터 생성 및 선택
→ 인벤토리 조회
→ 몬스터 전투
→ 보상 아이템 획득
→ 크래프팅 실행
→ 새 레시피 DB 저장
```

이 최소 범위만으로도 다음을 보여줄 수 있다.

* Streamlit 클라이언트
* FastAPI REST API
* MySQL 연동
* 로그인 세션
* DB 조회/삽입/수정
* 캐릭터별 데이터 분리
* 아이템 획득
* 동적 크래프팅
* 새로운 결과 DB 저장

---

## 9. 핵심 예외 처리

| 구분   | 예외 상황          | 처리       |
| ---- | -------------- | -------- |
| 인증   | 로그인하지 않은 접근    | 401      |
| 권한   | 다른 계정 캐릭터 접근   | 403      |
| 캐릭터  | 선택 캐릭터 없음      | 기능 제한    |
| 종족   | 비율 합계 100% 아님  | 생성 불가    |
| 인벤토리 | 아이템 수량 부족      | 실패       |
| 장비   | 장비 타입 아님       | 장착 불가    |
| 스킬   | 장착하지 않은 스킬 사용  | 사용 불가    |
| 전투   | 이미 처치한 몬스터 재공격 | 실패       |
| 보상   | 보상 중복 수령       | 차단       |
| 퀘스트  | 조건 미달성 완료 시도   | 실패       |
| 크래프팅 | 기존 레시피 중복 생성   | 기존 결과 사용 |
| DB   | 처리 중 오류 발생     | Rollback |

---

## 10. 결론

본 애플리케이션은 단순한 CRUD 예제가 아니라, RPG 시나리오를 기반으로 여러 데이터베이스 테이블이 서로 연결되는 구조를 보여준다.

특히 다음 흐름이 핵심이다.

```text
캐릭터
→ 인벤토리
→ 몬스터 전투
→ 보상
→ 퀘스트 진행
→ 크래프팅
→ 새 아이템 및 레시피 저장
```

이를 통해 Streamlit 클라이언트와 FastAPI 서버, MySQL 데이터베이스가 REST API를 통해 유기적으로 동작하는 것을 시연할 수 있다.

-- ============================================================
-- MyRPG Streamlit App Extension Schema
-- Run order:
--   1) create_db.sql
--   2) RPG(3).sql
--   3) populate_rpg(2).sql
--   4) this file
--
-- Note:
--   This patch assumes a fresh MyRPG database.
--   If you run it twice, ALTER TABLE duplicate-column errors can occur.
-- ============================================================


-- ============================================================
-- 패치에서 추가/수정한 내용
--  User.role
--  Character.is_public
--  Character.created_at
--  Item.icon_url
--  Item.equipment_part
--  Item.required_level
--  Monster.name
--  Monster.description
--  Monster.level
--  Monster.respawn_time_sec
--  Quest.prerequisite_quest_id
--  Quest.next_quest_id
--  Quest.reward_id

-- 새로 추가한 테이블
--  EquippedSkill
--  BattleSession
--  BattleSkillCooldown
--  BattleLog
--  QuestObjective
--  CharacterQuestProgress
--  ItemRequirementStat
--  CraftingRecipe
--  ItemAttribute
--  ItemEffect
--  CraftingLog
--  RewardLog

--  계정 활성/비활성화 속성 추가
-- ============================================================

USE MyRPG;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. Extend existing master/player tables
-- ============================================================

-- User role for USER / ADMIN access control
ALTER TABLE `User`
ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'USER';

-- Character public profile and creation time
ALTER TABLE `Character`
ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Item metadata for Streamlit UI, equipment validation, and AI icons
ALTER TABLE Item
ADD COLUMN icon_url TEXT NULL,
ADD COLUMN equipment_part VARCHAR(50) NULL,
ADD COLUMN required_level INT NOT NULL DEFAULT 1;

ALTER TABLE Item
ADD CONSTRAINT fk_item_equipment_part
FOREIGN KEY (equipment_part) REFERENCES EquipmentPart(type);

-- Monster display data for Streamlit battle screen
ALTER TABLE Monster
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Unknown Monster',
ADD COLUMN description TEXT NULL,
ADD COLUMN level INT NOT NULL DEFAULT 1,
ADD COLUMN respawn_time_sec INT NOT NULL DEFAULT 300;

-- Quest chaining and direct reward mapping
ALTER TABLE Quest
ADD COLUMN prerequisite_quest_id INT NULL,
ADD COLUMN next_quest_id INT NULL,
ADD COLUMN reward_id INT NULL;

ALTER TABLE Quest
ADD CONSTRAINT fk_quest_prerequisite
FOREIGN KEY (prerequisite_quest_id) REFERENCES Quest(id);

ALTER TABLE Quest
ADD CONSTRAINT fk_quest_next
FOREIGN KEY (next_quest_id) REFERENCES Quest(id);

ALTER TABLE Quest
ADD CONSTRAINT fk_quest_reward
FOREIGN KEY (reward_id) REFERENCES Reward(id);

-- ============================================================
-- 2. Skill equip table
-- ============================================================

CREATE TABLE EquippedSkill (
    char_id INT NOT NULL,
    slot_no INT NOT NULL,
    skill_id INT NOT NULL,
    equipped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (char_id, slot_no),
    UNIQUE KEY uq_equipped_skill_once (char_id, skill_id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id),
    CHECK (slot_no BETWEEN 1 AND 3)
);

-- ============================================================
-- 3. Battle session tables
-- ============================================================

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

CREATE TABLE BattleSkillCooldown (
    battle_id INT NOT NULL,
    skill_id INT NOT NULL,
    remaining_turns INT NOT NULL DEFAULT 0,
    PRIMARY KEY (battle_id, skill_id),
    FOREIGN KEY (battle_id) REFERENCES BattleSession(id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

CREATE TABLE BattleLog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    battle_id INT NOT NULL,
    char_id INT NOT NULL,
    monster_id INT NOT NULL,
    skill_id INT NULL,
    damage INT NOT NULL DEFAULT 0,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (battle_id) REFERENCES BattleSession(id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (monster_id) REFERENCES Monster(actor_id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

-- ============================================================
-- 4. Quest objective/progress tables
-- ============================================================

CREATE TABLE QuestObjective (
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    required_count INT NOT NULL,
    PRIMARY KEY (quest_id, objective_type, target_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id),
    CHECK (required_count > 0)
);

CREATE TABLE CharacterQuestProgress (
    char_id INT NOT NULL,
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    current_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (char_id, quest_id, objective_type, target_id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id),
    CHECK (current_count >= 0)
);

-- ============================================================
-- 5. Item requirements for equipment
-- ============================================================

CREATE TABLE ItemRequirementStat (
    item_id INT NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    required_value INT NOT NULL,
    PRIMARY KEY (item_id, stat_type),
    FOREIGN KEY (item_id) REFERENCES Item(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

-- ============================================================
-- 6. Dynamic crafting tables
-- ============================================================

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
    FOREIGN KEY (result_item_id) REFERENCES Item(id),
    UNIQUE KEY uq_recipe (ingredient1_id, ingredient2_id, method)
);

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

-- ============================================================
-- 7. Optional reward log for debugging / report evidence
-- ============================================================

CREATE TABLE RewardLog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    char_id INT NOT NULL,
    reward_id INT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (reward_id) REFERENCES Reward(id)
);

-- ============================================================
-- 8. Minimal updates for existing seed data
--    These are safe sample adjustments for Streamlit display.
-- ============================================================

UPDATE `User`
SET role = 'ADMIN'
WHERE id IN ('admin', 'gm', 'root');

-- If no explicit admin exists in populate data, this creates a simple test admin.
INSERT INTO `User` (id, user_name, password, role)
SELECT 'admin', 'Administrator', 'admin', 'ADMIN'
WHERE NOT EXISTS (SELECT 1 FROM `User` WHERE id = 'admin');

-- Set item equipment_part based on common sub_type values.
UPDATE Item
SET equipment_part = 'RIGHT_HAND'
WHERE LOWER(sub_type) IN ('weapon', 'right_hand', 'sword', 'staff');

UPDATE Item
SET equipment_part = 'HEAD'
WHERE LOWER(sub_type) IN ('head', 'helmet');

UPDATE Item
SET equipment_part = 'BODY'
WHERE LOWER(sub_type) IN ('armor', 'body', 'wearable');

UPDATE Item
SET equipment_part = 'CARRIER'
WHERE LOWER(sub_type) IN ('carrier', 'bag');

SET FOREIGN_KEY_CHECKS = 1;

COMMIT;


USE MyRPG;

ALTER TABLE `User`
ADD COLUMN active BOOLEAN NOT NULL DEFAULT TRUE;
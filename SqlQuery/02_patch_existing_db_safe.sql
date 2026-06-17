-- ============================================================
-- 02_patch_existing_db_safe.sql
-- Purpose: Safely update an existing MyRPG database used by the Streamlit RPG app.
-- Run with rpg user:
--   mysql -urpg -prpg MyRPG < 02_patch_existing_db_safe.sql
--
-- This file does NOT drop the database or base tables.
-- It adds missing columns/tables and upserts demo data where possible.
-- ============================================================

USE MyRPG;



-- ===== STREAMLIT APP EXTENSION SCHEMA SAFE =====
-- ============================================================
-- MyRPG Streamlit App Extension Schema - SAFE / RE-RUNNABLE
-- This version can be run multiple times on the same DB.
-- ============================================================

USE MyRPG;

SET FOREIGN_KEY_CHECKS = 0;

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_not_exists $$
CREATE PROCEDURE add_column_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_column_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD COLUMN ', p_column_definition);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DROP PROCEDURE IF EXISTS add_fk_if_not_exists $$
CREATE PROCEDURE add_fk_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_constraint_name VARCHAR(64),
    IN p_fk_sql TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND CONSTRAINT_NAME = p_constraint_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD CONSTRAINT ', p_constraint_name, ' ', p_fk_sql);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DROP PROCEDURE IF EXISTS add_index_if_not_exists $$
CREATE PROCEDURE add_index_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_index_sql TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND INDEX_NAME = p_index_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD ', p_index_sql);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DELIMITER ;

-- ============================================================
-- 1. Extend existing tables safely
-- ============================================================

CALL add_column_if_not_exists('User', 'role', "role VARCHAR(20) NOT NULL DEFAULT 'USER'");
CALL add_column_if_not_exists('User', 'active', "active BOOLEAN NOT NULL DEFAULT TRUE");

CALL add_column_if_not_exists('Character', 'is_public', "is_public BOOLEAN NOT NULL DEFAULT FALSE");
CALL add_column_if_not_exists('Character', 'created_at', "created_at DATETIME DEFAULT CURRENT_TIMESTAMP");

CALL add_column_if_not_exists('Item', 'icon_url', "icon_url TEXT NULL");
CALL add_column_if_not_exists('Item', 'equipment_part', "equipment_part VARCHAR(50) NULL");
CALL add_column_if_not_exists('Item', 'required_level', "required_level INT NOT NULL DEFAULT 1");

CALL add_column_if_not_exists('Monster', 'name', "name VARCHAR(255) NOT NULL DEFAULT 'Unknown Monster'");
CALL add_column_if_not_exists('Monster', 'description', "description TEXT NULL");
CALL add_column_if_not_exists('Monster', 'level', "level INT NOT NULL DEFAULT 1");
CALL add_column_if_not_exists('Monster', 'respawn_time_sec', "respawn_time_sec INT NOT NULL DEFAULT 300");

CALL add_column_if_not_exists('Quest', 'prerequisite_quest_id', "prerequisite_quest_id INT NULL");
CALL add_column_if_not_exists('Quest', 'next_quest_id', "next_quest_id INT NULL");
CALL add_column_if_not_exists('Quest', 'reward_id', "reward_id INT NULL");

-- Optional FK constraints. These are skipped if already present.
CALL add_fk_if_not_exists('Item', 'fk_item_equipment_part', 'FOREIGN KEY (equipment_part) REFERENCES EquipmentPart(type)');
CALL add_fk_if_not_exists('Quest', 'fk_quest_prerequisite', 'FOREIGN KEY (prerequisite_quest_id) REFERENCES Quest(id)');
CALL add_fk_if_not_exists('Quest', 'fk_quest_next', 'FOREIGN KEY (next_quest_id) REFERENCES Quest(id)');
CALL add_fk_if_not_exists('Quest', 'fk_quest_reward', 'FOREIGN KEY (reward_id) REFERENCES Reward(id)');

-- ============================================================
-- 2. New extension tables, safely
-- ============================================================

CREATE TABLE IF NOT EXISTS EquippedSkill (
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

CREATE TABLE IF NOT EXISTS BattleSession (
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

CREATE TABLE IF NOT EXISTS BattleSkillCooldown (
    battle_id INT NOT NULL,
    skill_id INT NOT NULL,
    remaining_turns INT NOT NULL DEFAULT 0,
    PRIMARY KEY (battle_id, skill_id),
    FOREIGN KEY (battle_id) REFERENCES BattleSession(id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

CREATE TABLE IF NOT EXISTS BattleLog (
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

CREATE TABLE IF NOT EXISTS QuestObjective (
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    required_count INT NOT NULL,
    PRIMARY KEY (quest_id, objective_type, target_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id),
    CHECK (required_count > 0)
);

CREATE TABLE IF NOT EXISTS CharacterQuestProgress (
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

CREATE TABLE IF NOT EXISTS ItemRequirementStat (
    item_id INT NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    required_value INT NOT NULL,
    PRIMARY KEY (item_id, stat_type),
    FOREIGN KEY (item_id) REFERENCES Item(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

CREATE TABLE IF NOT EXISTS CraftingRecipe (
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

CREATE TABLE IF NOT EXISTS ItemAttribute (
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

CREATE TABLE IF NOT EXISTS ItemEffect (
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

CREATE TABLE IF NOT EXISTS CraftingLog (
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

CREATE TABLE IF NOT EXISTS RewardLog (
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
-- 3. Safe seed adjustments
-- ============================================================

UPDATE `User`
SET role = 'ADMIN', active = TRUE
WHERE id IN ('admin', 'gm', 'root');

INSERT INTO `User` (id, user_name, password, role, active)
SELECT 'admin', 'Administrator', 'admin', 'ADMIN', TRUE
WHERE NOT EXISTS (SELECT 1 FROM `User` WHERE id = 'admin');

UPDATE Item
SET equipment_part = 'RIGHT_HAND'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('weapon', 'right_hand', 'sword', 'staff');

UPDATE Item
SET equipment_part = 'HEAD'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('head', 'helmet');

UPDATE Item
SET equipment_part = 'BODY'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('armor', 'body', 'wearable');

UPDATE Item
SET equipment_part = 'CARRIER'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('carrier', 'bag');

SET FOREIGN_KEY_CHECKS = 1;

DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DROP PROCEDURE IF EXISTS add_fk_if_not_exists;
DROP PROCEDURE IF EXISTS add_index_if_not_exists;



-- ===== CHARACTER / INVENTORY / CRAFTING EXTENSION SCHEMA =====
-- ============================================================
-- MyRPG Character Foundation + Inventory + Crafting Attribute Schema
-- Safe patch for Streamlit RPG app
--
-- Purpose:
--  1) Support current character foundation features:
--     - User role/active
--     - Character public profile/created_at
--     - character specimen, stats, job, skills, inventory already exist in base RPG schema
--  2) Prepare item attribute/effect schema for dynamic crafting:
--     - ItemAttribute
--     - ItemEffect
--     - CraftingMethod
--     - CraftingRecipe
--     - CraftingLog
--  3) Prepare skill equipment and future battle/quest tables.
--
-- Run:
--   mysql -urpg -prpg myrpg < upgrade_character_inventory_crafting_schema.sql
-- ============================================================

USE MyRPG;

SET FOREIGN_KEY_CHECKS = 0;

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_not_exists $$
CREATE PROCEDURE add_column_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_column_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD COLUMN ', p_column_definition);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DROP PROCEDURE IF EXISTS add_index_if_not_exists $$
CREATE PROCEDURE add_index_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_index_sql TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND INDEX_NAME = p_index_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD ', p_index_sql);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DELIMITER ;

-- ============================================================
-- 1. Columns required by account / character foundation features
-- ============================================================

CALL add_column_if_not_exists('User', 'role', "role VARCHAR(20) NOT NULL DEFAULT 'USER'");
CALL add_column_if_not_exists('User', 'active', "active BOOLEAN NOT NULL DEFAULT TRUE");

CALL add_column_if_not_exists('Character', 'is_public', "is_public BOOLEAN NOT NULL DEFAULT FALSE");
CALL add_column_if_not_exists('Character', 'created_at', "created_at DATETIME DEFAULT CURRENT_TIMESTAMP");

-- Character HP/MP can be represented through ActorStat, but these columns are optional cache fields.
-- The current FastAPI code mainly uses ActorStat, so these are not required. Keep them omitted for now.

-- ============================================================
-- 2. Item metadata for inventory, equipment, icons, and crafting
-- ============================================================

CALL add_column_if_not_exists('Item', 'icon_url', "icon_url TEXT NULL");
CALL add_column_if_not_exists('Item', 'equipment_part', "equipment_part VARCHAR(50) NULL");
CALL add_column_if_not_exists('Item', 'required_level', "required_level INT NOT NULL DEFAULT 1");

-- Optional inventory UI metadata
CALL add_column_if_not_exists('Item', 'rarity', "rarity VARCHAR(50) NOT NULL DEFAULT 'COMMON'");
CALL add_column_if_not_exists('Item', 'is_generated', "is_generated BOOLEAN NOT NULL DEFAULT FALSE");

-- Fill equipment_part from existing sub_type values when possible.
UPDATE Item
SET equipment_part = 'RIGHT_HAND'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('weapon', 'right_hand', 'sword', 'staff');

UPDATE Item
SET equipment_part = 'HEAD'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('head', 'helmet');

UPDATE Item
SET equipment_part = 'BODY'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('armor', 'body', 'wearable', 'chest');

UPDATE Item
SET equipment_part = 'CARRIER'
WHERE equipment_part IS NULL
  AND LOWER(sub_type) IN ('carrier', 'bag');

-- ============================================================
-- 3. Tables for skill equip / inventory extension / battle foundation
-- ============================================================

CREATE TABLE IF NOT EXISTS EquippedSkill (
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

CREATE TABLE IF NOT EXISTS BattleSession (
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

CREATE TABLE IF NOT EXISTS BattleSkillCooldown (
    battle_id INT NOT NULL,
    skill_id INT NOT NULL,
    remaining_turns INT NOT NULL DEFAULT 0,
    PRIMARY KEY (battle_id, skill_id),
    FOREIGN KEY (battle_id) REFERENCES BattleSession(id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

CREATE TABLE IF NOT EXISTS BattleLog (
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
-- 4. Dynamic crafting: item attributes/effects
--
-- These columns are based on the uploaded crafting datasets:
-- toxic, healing, viscous, stable, organic, plant, unstable, burnt,
-- metallic, magical, cold, hot, electric, explosive, defensive
-- ============================================================

CREATE TABLE IF NOT EXISTS ItemAttribute (
    item_id INT PRIMARY KEY,
    toxic FLOAT NOT NULL DEFAULT 0,
    healing FLOAT NOT NULL DEFAULT 0,
    viscous FLOAT NOT NULL DEFAULT 0,
    stable FLOAT NOT NULL DEFAULT 0,
    organic FLOAT NOT NULL DEFAULT 0,
    plant FLOAT NOT NULL DEFAULT 0,
    unstable FLOAT NOT NULL DEFAULT 0,
    burnt FLOAT NOT NULL DEFAULT 0,
    metallic FLOAT NOT NULL DEFAULT 0,
    magical FLOAT NOT NULL DEFAULT 0,
    cold FLOAT NOT NULL DEFAULT 0,
    hot FLOAT NOT NULL DEFAULT 0,
    electric FLOAT NOT NULL DEFAULT 0,
    explosive FLOAT NOT NULL DEFAULT 0,
    defensive FLOAT NOT NULL DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

CREATE TABLE IF NOT EXISTS ItemEffect (
    item_id INT PRIMARY KEY,
    type_effect VARCHAR(50),
    hp INT NOT NULL DEFAULT 0,
    poison INT NOT NULL DEFAULT 0,
    duration INT NOT NULL DEFAULT 0,
    attack INT NOT NULL DEFAULT 0,
    defense INT NOT NULL DEFAULT 0,
    speed INT NOT NULL DEFAULT 0,
    resistance INT NOT NULL DEFAULT 0,
    burn INT NOT NULL DEFAULT 0,
    freeze INT NOT NULL DEFAULT 0,
    shock INT NOT NULL DEFAULT 0,
    explosion_damage INT NOT NULL DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

CREATE TABLE IF NOT EXISTS CraftingMethod (
    method VARCHAR(50) PRIMARY KEY,
    description TEXT
);

INSERT IGNORE INTO CraftingMethod (method, description) VALUES
('MIX', '재료를 단순히 섞어 제작합니다.'),
('BOIL', '재료를 끓여 추출하거나 변화시킵니다.'),
('BAKE', '재료를 가열하여 굽습니다.'),
('DISTILL', '재료를 증류하여 핵심 성분을 추출합니다.'),
('COMPRESS', '재료를 압축하여 밀도를 높입니다.'),
('INFUSE', '재료에 마력 또는 속성을 주입합니다.');

CREATE TABLE IF NOT EXISTS CraftingRecipe (
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
    FOREIGN KEY (method) REFERENCES CraftingMethod(method),
    UNIQUE KEY uq_recipe (ingredient1_id, ingredient2_id, method)
);

CREATE TABLE IF NOT EXISTS CraftingLog (
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
    FOREIGN KEY (result_item_id) REFERENCES Item(id),
    FOREIGN KEY (method) REFERENCES CraftingMethod(method)
);

-- ============================================================
-- 5. Quest progress foundation
-- ============================================================

CREATE TABLE IF NOT EXISTS QuestObjective (
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    required_count INT NOT NULL,
    PRIMARY KEY (quest_id, objective_type, target_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id),
    CHECK (required_count > 0)
);

CREATE TABLE IF NOT EXISTS CharacterQuestProgress (
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
-- 6. Seed/default data required by character creation
--    These INSERT IGNORE statements are safe if data already exists.
-- ============================================================

INSERT IGNORE INTO Stat (type, name, description) VALUES
('HP', 'Health Points', '현재 체력'),
('MAX_HP', 'Max Health', '최대 체력'),
('MP', 'Mana Points', '현재 마나'),
('MAX_MP', 'Max Mana', '최대 마나'),
('ATK', 'Attack Power', '공격력'),
('DEF', 'Defense', '방어력'),
('INT', 'Intelligence', '지능'),
('AGI', 'Agility', '민첩');

INSERT IGNORE INTO EquipmentPart (type) VALUES
('RIGHT_HAND'), ('LEFT_HAND'), ('HEAD'), ('BODY'), ('ACCESSORY'), ('CARRIER');

INSERT IGNORE INTO LevelMaster (level, max_exp_to_next, max_hp, max_mp) VALUES
(1, 100, 100, 50),
(2, 250, 120, 60),
(3, 500, 150, 80);

INSERT IGNORE INTO LevelBaseStat (char_level, stat_type, value) VALUES
(1, 'HP', 100),
(1, 'MAX_HP', 100),
(1, 'MP', 50),
(1, 'MAX_MP', 50),
(1, 'ATK', 5),
(1, 'DEF', 5),
(1, 'INT', 5),
(1, 'AGI', 5);

INSERT IGNORE INTO Specimen (type, name, description) VALUES
('HUMAN', '인간', '균형 잡힌 스탯을 가진 종족'),
('ELF', '엘프', '지능과 마나가 높은 마법 친화적 종족'),
('ORC', '오크', '강력한 체력과 물리 공격력을 지닌 종족');

INSERT IGNORE INTO SpecimenBaseStat (specimen_type, stat_type, value) VALUES
('HUMAN', 'ATK', 2),
('HUMAN', 'DEF', 2),
('HUMAN', 'AGI', 2),
('ELF', 'INT', 5),
('ELF', 'MAX_MP', 20),
('ELF', 'AGI', 10),
('ORC', 'MAX_HP', 50),
('ORC', 'ATK', 5),
('ORC', 'DEF', 3);

INSERT IGNORE INTO Job (type, name, description, reference_image, unlock_condition_id) VALUES
('NOVICE', '초보자', '기본 직업입니다.', 'img/novice.png', NULL);

INSERT IGNORE INTO Skill (id, name, description, mp_cost, cooldown_sec, unlock_condition_id) VALUES
(1, '기본 베기', '무기로 세게 공격합니다.', 0, 1, NULL),
(5, '파이어볼', '화염구를 날립니다.', 10, 2, NULL),
(6, '치유', 'HP를 회복합니다.', 10, 5, NULL);

-- Admin user safety
INSERT INTO `User` (id, user_name, password, role, active)
SELECT 'admin', 'Administrator', 'admin', 'ADMIN', TRUE
WHERE NOT EXISTS (SELECT 1 FROM `User` WHERE id = 'admin');

UPDATE `User`
SET role = 'ADMIN', active = TRUE
WHERE id IN ('admin', 'gm', 'root');

-- Helpful indexes
CALL add_index_if_not_exists('Inventory', 'idx_inventory_owner', 'INDEX idx_inventory_owner (owner_id)');
CALL add_index_if_not_exists('InventoryItem', 'idx_inventory_item', 'INDEX idx_inventory_item (item_id)');
CALL add_index_if_not_exists('CharacterSkill', 'idx_character_skill_char', 'INDEX idx_character_skill_char (char_id)');
CALL add_index_if_not_exists('CharacterJob', 'idx_character_job_char', 'INDEX idx_character_job_char (char_id)');

SET FOREIGN_KEY_CHECKS = 1;

DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DROP PROCEDURE IF EXISTS add_index_if_not_exists;

-- ============================================================
-- End of patch
-- ============================================================


-- ===== HP / MP ITEM EFFECT SEED =====
USE MyRPG;

-- 소비 아이템 사용 시 HP/MP가 실제 ActorStat에 반영되도록 하는 기본 효과 데이터입니다.
-- ItemEffect.hp는 HP 회복량으로 사용하며, type_effect='MP'인 경우에는 MP 회복량으로 해석합니다.
INSERT INTO ItemEffect (item_id, type_effect, hp, poison, duration, attack, defense, speed, resistance, burn, freeze, shock, explosion_damage)
VALUES
(6, 'HP', 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(7, 'MP', 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(8, 'RECOVERY', 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE
    type_effect = VALUES(type_effect),
    hp = VALUES(hp),
    poison = VALUES(poison),
    duration = VALUES(duration),
    attack = VALUES(attack),
    defense = VALUES(defense),
    speed = VALUES(speed),
    resistance = VALUES(resistance),
    burn = VALUES(burn),
    freeze = VALUES(freeze),
    shock = VALUES(shock),
    explosion_damage = VALUES(explosion_damage);


-- ===== MONSTER EXP / EQUIPMENT SEED =====
USE MyRPG;

-- =========================================================
-- Safe patch for monster EXP rewards and equipment test data
-- MySQL 8.4 compatible: no ADD COLUMN IF NOT EXISTS
-- =========================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_missing $$
CREATE PROCEDURE add_column_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_column_def TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table_name, '` ADD COLUMN `', p_column_name, '` ', p_column_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DELIMITER ;

-- ---------------------------------------------------------
-- 1. Item columns needed for equipment / generated items
-- ---------------------------------------------------------
CALL add_column_if_missing('Item', 'equipment_part', 'VARCHAR(50) NULL');
CALL add_column_if_missing('Item', 'required_level', 'INT NOT NULL DEFAULT 1');
CALL add_column_if_missing('Item', 'rarity', 'VARCHAR(50) NOT NULL DEFAULT \'COMMON\'');
CALL add_column_if_missing('Item', 'icon_url', 'TEXT NULL');
CALL add_column_if_missing('Item', 'is_generated', 'BOOLEAN NOT NULL DEFAULT FALSE');

DROP PROCEDURE IF EXISTS add_column_if_missing;

-- ---------------------------------------------------------
-- 2. Ensure equipment slots exist
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS EquipmentPart (
    type VARCHAR(50) PRIMARY KEY
);

INSERT IGNORE INTO EquipmentPart(type)
VALUES ('weapon'), ('head'), ('armor'), ('carrier');

-- ---------------------------------------------------------
-- 3. Ensure CharacterEquipment exists
-- If your original schema already has this table, this will not modify it.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS CharacterEquipment (
    char_id INT NOT NULL,
    equipment_part VARCHAR(50) NOT NULL,
    inventory_id INT NOT NULL,
    item_id INT NOT NULL,
    PRIMARY KEY (char_id, equipment_part),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (inventory_id, item_id) REFERENCES InventoryItem(inventory_id, item_id)
);

-- ---------------------------------------------------------
-- 4. Ensure ItemBonusStat exists
-- If your original schema already has this table, this will not modify it.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS ItemBonusStat (
    item_id INT NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    value INT NOT NULL DEFAULT 0,
    PRIMARY KEY (item_id, stat_type),
    FOREIGN KEY (item_id) REFERENCES Item(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

-- ---------------------------------------------------------
-- 5. Monster EXP reward seed
-- Fill RewardExp only when missing or amount is 0.
-- ---------------------------------------------------------
INSERT INTO RewardExp (reward_id, amount)
SELECT DISTINCT
    m.drop_reward_id,
    GREATEST(10, COALESCE(m.hp, 0) + COALESCE(m.atk, 0) * 5)
FROM Monster m
WHERE m.drop_reward_id IS NOT NULL
ON DUPLICATE KEY UPDATE
    amount = CASE
        WHEN RewardExp.amount IS NULL OR RewardExp.amount = 0 THEN VALUES(amount)
        ELSE RewardExp.amount
    END;

-- ---------------------------------------------------------
-- 6. Test equipment items
-- ---------------------------------------------------------
INSERT INTO Item (name, description, type, sub_type, capacity, equipment_part, required_level, rarity, is_generated)
SELECT 'Training Sword', '훈련용 검. ATK를 올려준다.', 'equipment', 'weapon', -1, 'weapon', 1, 'COMMON', FALSE
WHERE NOT EXISTS (SELECT 1 FROM Item WHERE name = 'Training Sword');

INSERT INTO Item (name, description, type, sub_type, capacity, equipment_part, required_level, rarity, is_generated)
SELECT 'Cloth Hood', '천 후드. 약간의 방어력을 제공한다.', 'equipment', 'head', -1, 'head', 1, 'COMMON', FALSE
WHERE NOT EXISTS (SELECT 1 FROM Item WHERE name = 'Cloth Hood');

INSERT INTO Item (name, description, type, sub_type, capacity, equipment_part, required_level, rarity, is_generated)
SELECT 'Leather Armor', '가죽 갑옷. DEF와 MAX_HP를 올려준다.', 'equipment', 'armor', -1, 'armor', 1, 'COMMON', FALSE
WHERE NOT EXISTS (SELECT 1 FROM Item WHERE name = 'Leather Armor');

-- ---------------------------------------------------------
-- 7. Test equipment bonus stats
-- ---------------------------------------------------------
INSERT INTO ItemBonusStat (item_id, stat_type, value)
SELECT id, 'ATK', 5 FROM Item WHERE name = 'Training Sword'
ON DUPLICATE KEY UPDATE value = VALUES(value);

INSERT INTO ItemBonusStat (item_id, stat_type, value)
SELECT id, 'DEF', 2 FROM Item WHERE name = 'Cloth Hood'
ON DUPLICATE KEY UPDATE value = VALUES(value);

INSERT INTO ItemBonusStat (item_id, stat_type, value)
SELECT id, 'DEF', 5 FROM Item WHERE name = 'Leather Armor'
ON DUPLICATE KEY UPDATE value = VALUES(value);

INSERT INTO ItemBonusStat (item_id, stat_type, value)
SELECT id, 'MAX_HP', 20 FROM Item WHERE name = 'Leather Armor'
ON DUPLICATE KEY UPDATE value = VALUES(value);

-- ---------------------------------------------------------
-- 8. Check results
-- ---------------------------------------------------------
SELECT
    m.actor_id AS monster_id,
    m.drop_reward_id,
    re.amount AS reward_exp
FROM Monster m
LEFT JOIN RewardExp re ON m.drop_reward_id = re.reward_id
ORDER BY m.actor_id;


-- ===== QUEST DEMO SEED =====
USE MyRPG;

-- Quest 기능에 필요한 컬럼을 안전하게 추가한다.
DROP PROCEDURE IF EXISTS add_column_if_missing;
DELIMITER $$
CREATE PROCEDURE add_column_if_missing(
    IN p_table VARCHAR(64),
    IN p_column VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table
          AND COLUMN_NAME = p_column
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN ', p_column, ' ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_column_if_missing('Quest', 'prerequisite_quest_id', 'INT NULL');
CALL add_column_if_missing('Quest', 'next_quest_id', 'INT NULL');
CALL add_column_if_missing('Quest', 'reward_id', 'INT NULL');

DROP PROCEDURE IF EXISTS add_column_if_missing;

CREATE TABLE IF NOT EXISTS QuestObjective (
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    required_count INT NOT NULL DEFAULT 1,
    PRIMARY KEY (quest_id, objective_type, target_id),
    CONSTRAINT fk_quest_objective_quest
        FOREIGN KEY (quest_id) REFERENCES Quest(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CharacterQuestProgress (
    char_id INT NOT NULL,
    quest_id INT NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    current_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (char_id, quest_id, objective_type, target_id),
    CONSTRAINT fk_cqp_character
        FOREIGN KEY (char_id) REFERENCES `Character`(actor_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_cqp_quest
        FOREIGN KEY (quest_id) REFERENCES Quest(id)
        ON DELETE CASCADE
);

-- 데모 보상 생성
INSERT IGNORE INTO UnlockCondition (id, logical_op) VALUES (9001, 'AND');
INSERT IGNORE INTO Reward (id, unlock_condition_id) VALUES (9001, 9001);
INSERT INTO RewardExp (reward_id, amount)
VALUES (9001, 100)
ON DUPLICATE KEY UPDATE amount = VALUES(amount);

-- 데모 아이템 보상. 고정 ID를 사용해 재실행 가능하게 한다.
INSERT INTO Item (id, name, description, type, sub_type, capacity)
VALUES (9001, 'Quest Potion', '퀘스트 보상으로 지급되는 기본 회복 물약입니다.', 'consumable', 'potion', 99)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    type = VALUES(type),
    sub_type = VALUES(sub_type),
    capacity = VALUES(capacity);

INSERT INTO ItemEffect (item_id, type_effect, hp, duration)
VALUES (9001, 'HEAL', 30, 0)
ON DUPLICATE KEY UPDATE
    type_effect = VALUES(type_effect),
    hp = VALUES(hp),
    duration = VALUES(duration);

INSERT INTO RewardItem (reward_id, item_id, quantity, drop_probability)
VALUES (9001, 9001, 1, 1.0)
ON DUPLICATE KEY UPDATE
    quantity = VALUES(quantity),
    drop_probability = VALUES(drop_probability);

-- 데모 퀘스트 생성. 목표 몬스터는 현재 DB의 첫 번째 몬스터를 사용한다.
INSERT INTO Quest (id, unlock_condition_id, name, description, max_steps, type, is_repeatable, reward_id)
VALUES (
    9001,
    9001,
    '첫 번째 사냥 의뢰',
    '마을 경비병이 근처 몬스터 3마리를 처치해 달라고 부탁했습니다. Battle 페이지에서 몬스터를 처치하면 진행도가 증가합니다.',
    3,
    'side',
    FALSE,
    9001
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    max_steps = VALUES(max_steps),
    type = VALUES(type),
    is_repeatable = VALUES(is_repeatable),
    reward_id = VALUES(reward_id);

INSERT INTO QuestObjective (quest_id, objective_type, target_id, required_count)
SELECT 9001, 'KILL_MONSTER', actor_id, 3
FROM Monster
ORDER BY actor_id
LIMIT 1
ON DUPLICATE KEY UPDATE required_count = VALUES(required_count);


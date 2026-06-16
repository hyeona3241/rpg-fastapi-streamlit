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

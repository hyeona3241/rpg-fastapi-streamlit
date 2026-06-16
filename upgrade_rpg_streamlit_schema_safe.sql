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


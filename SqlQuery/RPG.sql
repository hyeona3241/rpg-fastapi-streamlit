-- mysql -u rpg -prpg MyRPG < RPG.sql

USE MyRPG;

-- ========================================
-- RPG Game Database Schema (MySQL DDL)
-- ========================================

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------
-- 1. Core & Actor Systems
-- ----------------------------------------

DROP TABLE IF EXISTS User;
CREATE TABLE User (
    id VARCHAR(20) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS Actor;
CREATE TABLE Actor (
    id INT AUTO_INCREMENT PRIMARY KEY
);

DROP TABLE IF EXISTS `Character`; 
-- "Character"는 SQL 예약어일 수 있으므로 Table 명을 조정 (혹은 `Character` 백틱 사용)
CREATE TABLE `Character` (
    actor_id INT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    level INT NOT NULL DEFAULT 1,
    exp INT NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES User(id),
    FOREIGN KEY (actor_id) REFERENCES Actor(id)
);

DROP TABLE IF EXISTS Stat;
CREATE TABLE Stat (
    type VARCHAR(50) PRIMARY KEY, -- 'ATK', 'DEF', 'INT', 'HP', 'MAX_HP', ...
    name VARCHAR(255) NOT NULL,
    description TEXT
);

DROP TABLE IF EXISTS ActorStat;
CREATE TABLE ActorStat (
    actor_id INT,
    stat_type VARCHAR(50),
    value INT NOT NULL,
    PRIMARY KEY (actor_id, stat_type),
    FOREIGN KEY (actor_id) REFERENCES Actor(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

DROP TABLE IF EXISTS LevelMaster;
CREATE TABLE LevelMaster (
    level INT PRIMARY KEY,
    max_exp_to_next INT NOT NULL,
    max_hp INT NOT NULL,
    max_mp INT NOT NULL
);

DROP TABLE IF EXISTS LevelBaseStat;
CREATE TABLE LevelBaseStat (
    char_level INT,
    stat_type VARCHAR(50),
    value INT NOT NULL,
    PRIMARY KEY (char_level, stat_type),
    FOREIGN KEY (char_level) REFERENCES LevelMaster(level),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

-- ----------------------------------------
-- 2. Items & Inventory
-- ----------------------------------------

DROP TABLE IF EXISTS Item;
CREATE TABLE Item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    sub_type VARCHAR(50),
    capacity INT DEFAULT -1
);

DROP TABLE IF EXISTS ItemBonusStat;
CREATE TABLE ItemBonusStat (
    item_id INT,
    stat_type VARCHAR(50),
    value INT NOT NULL,
    PRIMARY KEY (item_id, stat_type),
    FOREIGN KEY (item_id) REFERENCES Item(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

DROP TABLE IF EXISTS Inventory;
CREATE TABLE Inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES `Character`(actor_id)
);

DROP TABLE IF EXISTS InventoryItem;
CREATE TABLE InventoryItem (
    inventory_id INT,
    item_id INT,
    quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY (inventory_id, item_id),
    FOREIGN KEY (inventory_id) REFERENCES Inventory(id),
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

DROP TABLE IF EXISTS EquipmentPart;
CREATE TABLE EquipmentPart (
    type VARCHAR(50) PRIMARY KEY
);

DROP TABLE IF EXISTS CharacterEquipment;
CREATE TABLE CharacterEquipment (
    char_id INT,
    equipment_part VARCHAR(50),
    inventory_id INT NOT NULL,
    item_id INT NOT NULL,
    PRIMARY KEY (char_id, equipment_part),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (equipment_part) REFERENCES EquipmentPart(type),
    FOREIGN KEY (inventory_id, item_id) REFERENCES InventoryItem(inventory_id, item_id)
);

-- ----------------------------------------
-- 3. Skills, Jobs & Specimen
-- ----------------------------------------

DROP TABLE IF EXISTS Specimen;
CREATE TABLE Specimen (
    type VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

DROP TABLE IF EXISTS SpecimenBaseStat;
CREATE TABLE SpecimenBaseStat (
    specimen_type VARCHAR(50),
    stat_type VARCHAR(50),
    value INT NOT NULL,
    PRIMARY KEY (specimen_type, stat_type),
    FOREIGN KEY (specimen_type) REFERENCES Specimen(type),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

DROP TABLE IF EXISTS CharacterSpecimen;
CREATE TABLE CharacterSpecimen (
    char_id INT,
    type VARCHAR(50),
    fraction FLOAT NOT NULL,
    PRIMARY KEY (char_id, type),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (type) REFERENCES Specimen(type)
);

DROP TABLE IF EXISTS Job;
CREATE TABLE Job (
    type VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reference_image VARCHAR(255),
    unlock_condition_id INT
);

DROP TABLE IF EXISTS CharacterJob;
CREATE TABLE CharacterJob (
    type VARCHAR(50),
    char_id INT,
    obtain_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (type, char_id),
    FOREIGN KEY (type) REFERENCES Job(type),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id)
);

DROP TABLE IF EXISTS Skill;
CREATE TABLE Skill (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mp_cost INT NOT NULL DEFAULT 0,
    cooldown_sec INT NOT NULL DEFAULT 0,
    unlock_condition_id INT
);

DROP TABLE IF EXISTS SkillBonusStat;
CREATE TABLE SkillBonusStat (
    skill_id INT,
    stat_type VARCHAR(50),
    value INT NOT NULL,
    PRIMARY KEY (skill_id, stat_type),
    FOREIGN KEY (skill_id) REFERENCES Skill(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

DROP TABLE IF EXISTS CharacterSkill;
CREATE TABLE CharacterSkill (
    skill_id INT,
    char_id INT,
    skill_level FLOAT NOT NULL DEFAULT 0.0,
    PRIMARY KEY (skill_id, char_id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id)
);

-- ----------------------------------------
-- 4. Status Effects
-- ----------------------------------------

DROP TABLE IF EXISTS StatusEffect;
CREATE TABLE StatusEffect (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration INT NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    is_reusable BOOLEAN NOT NULL DEFAULT TRUE,
    modifier_type ENUM('ADDITIVE', 'MULTIPLICATIVE') NOT NULL,
    modifier_value FLOAT NOT NULL,
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

DROP TABLE IF EXISTS CharacterStatusEffect;
CREATE TABLE CharacterStatusEffect (
    char_id INT,
    effect_id INT,
    remaining_duration INT NOT NULL,
    PRIMARY KEY (char_id, effect_id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (effect_id) REFERENCES StatusEffect(id)
);

-- ----------------------------------------
-- 5. Quests & Unlock Conditions
-- ----------------------------------------

DROP TABLE IF EXISTS UnlockCondition;
CREATE TABLE UnlockCondition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    logical_op ENUM('AND', 'OR') DEFAULT 'AND'
);

-- Foreign keys mapping back to UnlockCondition
ALTER TABLE Job ADD CONSTRAINT fk_job_unlock FOREIGN KEY (unlock_condition_id) REFERENCES UnlockCondition(id);
ALTER TABLE Skill ADD CONSTRAINT fk_skill_unlock FOREIGN KEY (unlock_condition_id) REFERENCES UnlockCondition(id);

DROP TABLE IF EXISTS Quest;
CREATE TABLE Quest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unlock_condition_id INT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_steps INT DEFAULT 1,
    type VARCHAR(50),
    is_repeatable BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (unlock_condition_id) REFERENCES UnlockCondition(id)
);

DROP TABLE IF EXISTS CharacterQuest;
CREATE TABLE CharacterQuest (
    quest_id INT,
    char_id INT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- 'active', 'completed', 'failed'
    current_step INT NOT NULL DEFAULT 0,
    PRIMARY KEY (quest_id, char_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id)
);

DROP TABLE IF EXISTS RequirementLevel;
CREATE TABLE RequirementLevel (
    condition_id INT,
    required_level INT,
    PRIMARY KEY (condition_id, required_level),
    FOREIGN KEY (condition_id) REFERENCES UnlockCondition(id)
);

DROP TABLE IF EXISTS RequirementSpecimen;
CREATE TABLE RequirementSpecimen (
    condition_id INT,
    specimen_type VARCHAR(50),
    PRIMARY KEY (condition_id, specimen_type),
    FOREIGN KEY (condition_id) REFERENCES UnlockCondition(id),
    FOREIGN KEY (specimen_type) REFERENCES Specimen(type)
);

DROP TABLE IF EXISTS RequirementJob;
CREATE TABLE RequirementJob (
    condition_id INT,
    job_type VARCHAR(50),
    PRIMARY KEY (condition_id, job_type),
    FOREIGN KEY (condition_id) REFERENCES UnlockCondition(id),
    FOREIGN KEY (job_type) REFERENCES Job(type)
);

DROP TABLE IF EXISTS RequirementSkill;
CREATE TABLE RequirementSkill (
    condition_id INT,
    skill_id INT,
    PRIMARY KEY (condition_id, skill_id),
    FOREIGN KEY (condition_id) REFERENCES UnlockCondition(id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

DROP TABLE IF EXISTS RequirementQuest;
CREATE TABLE RequirementQuest (
    condition_id INT,
    quest_id INT,
    PRIMARY KEY (condition_id, quest_id),
    FOREIGN KEY (condition_id) REFERENCES UnlockCondition(id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id)
);

-- ----------------------------------------
-- 6. Rewards, NPCs, Monsters & Shops
-- ----------------------------------------

DROP TABLE IF EXISTS Reward;
CREATE TABLE Reward (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unlock_condition_id INT,
    FOREIGN KEY (unlock_condition_id) REFERENCES UnlockCondition(id)
);

DROP TABLE IF EXISTS RewardItem;
CREATE TABLE RewardItem (
    reward_id INT,
    item_id INT,
    quantity INT NOT NULL DEFAULT 1,
    drop_probability FLOAT,
    PRIMARY KEY (reward_id, item_id),
    FOREIGN KEY (reward_id) REFERENCES Reward(id),
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

DROP TABLE IF EXISTS RewardExp;
CREATE TABLE RewardExp (
    reward_id INT PRIMARY KEY,
    amount INT NOT NULL,
    FOREIGN KEY (reward_id) REFERENCES Reward(id)
);

DROP TABLE IF EXISTS Monster;
CREATE TABLE Monster (
    actor_id INT PRIMARY KEY,
    hp INT NOT NULL,
    atk INT NOT NULL,
    def INT NOT NULL,
    drop_reward_id INT,
    FOREIGN KEY (actor_id) REFERENCES Actor(id),
    FOREIGN KEY (drop_reward_id) REFERENCES Reward(id)
);

DROP TABLE IF EXISTS Shop;
CREATE TABLE Shop (
    id INT AUTO_INCREMENT PRIMARY KEY
);

DROP TABLE IF EXISTS Villager;
CREATE TABLE Villager (
    npc_id INT PRIMARY KEY,
    shop_id INT,
    FOREIGN KEY (npc_id) REFERENCES Actor(id),
    FOREIGN KEY (shop_id) REFERENCES Shop(id)
);

DROP TABLE IF EXISTS VillagerQuest;
CREATE TABLE VillagerQuest (
    villager_id INT,
    quest_id INT,
    PRIMARY KEY (villager_id, quest_id),
    FOREIGN KEY (villager_id) REFERENCES Villager(npc_id),
    FOREIGN KEY (quest_id) REFERENCES Quest(id)
);

DROP TABLE IF EXISTS ShopCatalog;
CREATE TABLE ShopCatalog (
    shop_id INT,
    item_id INT,
    remaining_quantity INT NOT NULL DEFAULT -1,
    price INT NOT NULL DEFAULT 0,
    PRIMARY KEY (shop_id, item_id),
    FOREIGN KEY (shop_id) REFERENCES Shop(id),
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

SET FOREIGN_KEY_CHECKS = 1;

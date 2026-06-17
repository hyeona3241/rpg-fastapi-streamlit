-- ============================================================
-- 01_full_schema_and_seed.sql
-- Purpose: Build all tables and insert test/demo data for the Streamlit RPG app.
-- Run after 00_reset_create_database_root.sql:
--   mysql -urpg -prpg MyRPG < 01_full_schema_and_seed.sql
--
-- Contents:
--   1) Base RPG schema
--   2) Base RPG seed data
--   3) Streamlit app extension schema
--   4) Character / inventory / crafting schema
--   5) HP/MP item effects
--   6) Monster EXP / equipment test data
--   7) Quest demo data
-- ============================================================



-- ===== 1. BASE RPG SCHEMA =====
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


-- ===== 2. BASE RPG SEED DATA =====
USE MyRPG;
SET FOREIGN_KEY_CHECKS = 0;

-- ==============================================================================
-- 1. 마스터 데이터 세팅 (Stats, Level, Equipment Parts)
-- ==============================================================================
INSERT INTO Stat (type, name, description) VALUES
('HP', 'Health Points', '체력'), ('MAX_HP', 'Max Health', '최대 체력'),
('MP', 'Mana Points', '마나'), ('MAX_MP', 'Max Mana', '최대 마나'),
('ATK', 'Attack Power', '물리 공격력'), ('DEF', 'Defense', '물리 방어력'),
('INT', 'Intelligence', '마법 공격력 및 마나 베이스'), ('AGI', 'Agility', '민첩성');

-- 장착 부위
INSERT INTO EquipmentPart (type) VALUES
('RIGHT_HAND'), ('LEFT_HAND'), ('HEAD'), ('BODY'), ('ACCESSORY'), ('CARRIER');

-- 레벨 마스터
INSERT INTO LevelMaster (level, max_exp_to_next, max_hp, max_mp) VALUES
(1, 100, 100, 50), (2, 250, 120, 60), (3, 500, 150, 80),
(5, 1200, 250, 120), (10, 5000, 500, 200), (15, 12000, 800, 400), 
(18, 20000, 1000, 500), (20, 30000, 1200, 600), (50, 999999, 5000, 2000);

-- 레벨업 기본 부여 스탯 (초반 레벨용)
INSERT INTO LevelBaseStat (char_level, stat_type, value) VALUES
(1, 'ATK', 5), (1, 'DEF', 5), (1, 'INT', 5),
(2, 'ATK', 7), (2, 'DEF', 6), (2, 'INT', 7);

-- ==============================================================================
-- 2. 해금 조건 마스터 (Unlock Conditions) - 복합 시나리오 검증용
-- ==============================================================================
INSERT INTO UnlockCondition (id, logical_op) VALUES
(1, 'AND'), -- [MAGE 전직용] 레벨 15 이상
(2, 'AND'), -- [BERSERKER 전직용] 오크 종족 전용
(3, 'AND'), -- [분노의 일격 스킬용] 레벨 5 이상 + 오크 종족
(4, 'AND'), -- [마왕 토벌 퀘스트용] 레벨 50 이상
(5, 'AND'), -- [엘프 궁수 특수 퀘스트용] 엘프 종족 + 궁수 직업
(6, 'AND'); -- [연속 베기 스킬용] 선행 스킬(기본 베기) 습득 필요

INSERT INTO RequirementLevel (condition_id, required_level) VALUES 
(1, 15), (3, 5), (4, 50);

INSERT INTO RequirementSpecimen (condition_id, specimen_type) VALUES 
(2, 'ORC'), (3, 'ORC'), (5, 'ELF');

-- ==============================================================================
-- 3. 종족, 직업, 스킬 세팅 (Specimen, Job, Skill)
-- ==============================================================================
INSERT INTO Specimen (type, name, description) VALUES
('HUMAN', '인간', '균형 잡힌 스탯을 가진 종족'), 
('ELF', '엘프', '지능과 마나가 높은 마법 친화적 종족'), 
('ORC', '오크', '강력한 체력과 물리 공격력을 지닌 종족');

INSERT INTO SpecimenBaseStat (specimen_type, stat_type, value) VALUES
('HUMAN', 'ATK', 2), ('HUMAN', 'DEF', 2),
('ELF', 'INT', 5), ('ELF', 'MAX_MP', 20), ('ELF', 'AGI', 10),
('ORC', 'MAX_HP', 50), ('ORC', 'ATK', 5);

INSERT INTO Job (type, name, description, reference_image, unlock_condition_id) VALUES
('NOVICE', '초보자', '기본 직업', 'img/novice.png', NULL),
('WARRIOR', '전사', '강력한 물리 공격', 'img/warrior.png', NULL),
('MAGE', '마법사', '지능이 높은 직업', 'img/mage.png', 1),
('BERSERKER', '버서커', '오크 전용', 'img/berserk.png', 2),
('ARCHER', '궁수', '활 사용', 'img/archer.png', NULL),
('PALADIN', '성기사', '신성 마법', 'img/paladin.png', NULL),
('THIEF', '도적', '민첩함', 'img/thief.png', NULL);

-- 엘프 궁수 퀘스트(조건5)를 위한 요구 직업 맵핑
INSERT INTO RequirementJob (condition_id, job_type) VALUES (5, 'ARCHER');

INSERT INTO Skill (id, name, description, mp_cost, cooldown_sec, unlock_condition_id) VALUES
(1, '기본 베기', '무기로 세게 때립니다.', 0, 1, NULL),
(2, '연속 베기', '빠르게 2번 타격합니다.', 10, 5, 6),
(3, '분노의 일격', '오크 전용 강타', 20, 10, 3),
(4, '궁극기', '보스 처치 보상 스킬', 100, 120, NULL),
(5, '파이어볼', '화염구를 날립니다.', 30, 2, NULL),
(6, '치유', 'HP를 회복합니다.', 20, 5, NULL),
(7, '돌진', '적에게 빠르게 접근합니다.', 10, 15, NULL),
(8, '마나 단련', '최대 마나를 증가시키는 패시브', 0, 0, NULL);

INSERT INTO SkillBonusStat (skill_id, stat_type, value) VALUES (8, 'MAX_MP', 50);
INSERT INTO RequirementSkill (condition_id, skill_id) VALUES (6, 1); -- 연속베기(2)는 기본베기(1) 요구

-- ==============================================================================
-- 4. 아이템, 상점, 상태이상 세팅 (Items, Shop, StatusEffect)
-- ==============================================================================
INSERT INTO Item (id, name, description, type, sub_type, capacity) VALUES
(1, '초보자의 검', '기본 지급 무기', 'EQUIPMENT', 'RIGHT_HAND', -1),
(2, '가죽 갑옷', '질긴 가죽 갑옷', 'EQUIPMENT', 'BODY', -1),
(3, '강철 검', '레벨 20 권장 무기', 'EQUIPMENT', 'RIGHT_HAND', -1),
(4, '가죽 투구', '머리 장비', 'EQUIPMENT', 'HEAD', -1),
(5, '마법사 로브', '마법사 전용 갑옷', 'EQUIPMENT', 'BODY', -1),
(6, '빨간 포션', 'HP 50 회복', 'CONSUMABLE', 'POTION', -1),
(7, '마나 포션', 'MP 30 회복', 'CONSUMABLE', 'POTION', -1),
(8, '희귀한 물약', '모든 상태이상 회복', 'CONSUMABLE', 'POTION', -1),
(9, '해독제', '중독 상태 해제', 'CONSUMABLE', 'POTION', -1),
(10, '슬라임의 점액', '몬스터 전리품', 'MATERIAL', 'JUNK', -1),
(11, '낡은 뼈다귀', '쓸모없는 전리품', 'MATERIAL', 'JUNK', -1),
(12, '촌장의 편지', '퀘스트용', 'QUEST', 'DOCUMENT', -1),
(13, '기본 모험가 가방', '기본 가방', 'EQUIPMENT', 'CARRIER', 20),
(14, '확장된 모험가 가방', '큰 가방', 'EQUIPMENT', 'CARRIER', 50);

INSERT INTO ItemBonusStat (item_id, stat_type, value) VALUES 
(1, 'ATK', 5), (2, 'DEF', 10), (3, 'ATK', 15), (4, 'DEF', 5), (5, 'DEF', 3), (5, 'INT', 10);

INSERT INTO StatusEffect (id, name, duration, stat_type, is_reusable, modifier_type, modifier_value) VALUES
(1, '중독', 10, 'HP', TRUE, 'ADDITIVE', -5),
(2, '축복', 300, 'DEF', TRUE, 'MULTIPLICATIVE', 1.2),
(3, '기절', 3, 'AGI', TRUE, 'MULTIPLICATIVE', 0),
(4, '화상', 10, 'HP', TRUE, 'ADDITIVE', -10),
(5, '공격력 증가', 60, 'ATK', FALSE, 'ADDITIVE', 20);

-- ==============================================================================
-- 5. 계정, 액터 인스턴스 데이터 (Users, Characters, NPCs)
-- ==============================================================================
INSERT INTO User (id, user_name, password) VALUES 
('user_001', 'ArthurKing', 'pwd_111'),
('Hero123', 'Hero123', 'pwd_222');

-- Actor ID 할당 (1,2,3: 유저 캐릭터 / 4,5: 몬스터 / 6,7,8: NPC)
INSERT INTO Actor (id) VALUES (1), (2), (3), (4), (5), (6), (7), (8);

INSERT INTO `Character` (actor_id, user_id, character_name, level, exp, active) VALUES
(1, 'user_001', '아더왕', 1, 0, FALSE),
(2, 'Hero123', '전사지망생', 10, 4000, TRUE),  -- 테스트를 위해 레벨 10으로 설정
(3, 'Hero123', '삭제할부캐', 1, 0, FALSE);

-- 아더왕: 순수 인간 초보자
INSERT INTO CharacterSpecimen (char_id, type, fraction) VALUES (1, 'HUMAN', 1.0);
INSERT INTO CharacterJob (type, char_id, active) VALUES ('NOVICE', 1, TRUE);

-- 전사지망생: 혼혈 (인간 50, 엘프 50), 직업: 전사
INSERT INTO CharacterSpecimen (char_id, type, fraction) VALUES (2, 'HUMAN', 0.5), (2, 'ELF', 0.5);
INSERT INTO CharacterJob (type, char_id, active) VALUES ('WARRIOR', 2, TRUE);

-- 몬스터 셋팅 (4: 슬라임, 5: 오크 전사)
INSERT INTO Monster (actor_id, hp, atk, def, drop_reward_id) VALUES 
(4, 30, 2, 1, NULL), 
(5, 100, 10, 5, NULL); -- 보상 ID는 뒤에서 매핑

-- 상점 및 상인 NPC (6: 대장장이, 7: 잡화상인, 8: 퀘스트 NPC)
INSERT INTO Shop (id) VALUES (1), (2);
INSERT INTO Villager (npc_id, shop_id) VALUES (6, 1), (7, 2), (8, NULL);

INSERT INTO ShopCatalog (shop_id, item_id, remaining_quantity, price) VALUES
(1, 1, 5, 100),    -- 초보자의 검 (5개 남음)
(1, 3, -1, 1500),  -- 강철 검 (무한)
(2, 6, -1, 50),    -- 빨간 포션 (무한)
(2, 8, 0, 5000);   -- 희귀한 물약 (품절)

-- ==============================================================================
-- 6. 인벤토리 및 장비 매핑
-- ==============================================================================
-- 인벤토리(가방) 생성
INSERT INTO Inventory (id, owner_id, type, capacity) VALUES 
(1, 1, 'MAIN_BAG', 20), -- 아더왕 가방
(2, 2, 'MAIN_BAG', 50); -- 전사지망생 가방

-- 아더왕 아이템 지급
INSERT INTO InventoryItem (inventory_id, item_id, quantity) VALUES
(1, 1, 1), (1, 2, 1), (1, 6, 5);

-- 전사지망생 아이템 지급
INSERT INTO InventoryItem (inventory_id, item_id, quantity) VALUES
(2, 3, 1), (2, 4, 1), (2, 6, 10), (2, 9, 1), (2, 11, 2), (2, 12, 1);

-- 장착 (아더왕: 초보자 검, 가죽 갑옷 / 전사지망생: 강철 검, 가죽 투구)
INSERT INTO CharacterEquipment (char_id, equipment_part, inventory_id, item_id) VALUES
(1, 'RIGHT_HAND', 1, 1), (1, 'BODY', 1, 2),
(2, 'RIGHT_HAND', 2, 3), (2, 'HEAD', 2, 4);

-- ==============================================================================
-- 7. 퀘스트 마스터 및 보상 (Quests & Rewards)
-- ==============================================================================
INSERT INTO Quest (id, unlock_condition_id, name, description, max_steps, type, is_repeatable) VALUES
(1, NULL, '마을의 위기', '고블린 처치', 5, 'MAIN', FALSE),
(2, 4, '마왕 토벌', 'Lv 50 제한', 1, 'MAIN', FALSE),
(3, 5, '엘프 궁수의 길', '엘프+궁수 전용', 1, 'SUB', FALSE),
(4, NULL, '일일 토벌', '매일 반복', 10, 'DAILY', TRUE);

-- 보상 테이블 (1: 퀘스트 보상, 2: 슬라임 드랍, 3: 오크 드랍)
INSERT INTO Reward (id, unlock_condition_id) VALUES (1, NULL), (2, NULL), (3, NULL);

-- 퀘스트 보상 (빨간 포션 3개 확정)
INSERT INTO RewardItem (reward_id, item_id, quantity, drop_probability) VALUES (1, 6, 3, 1.0);
INSERT INTO RewardExp (reward_id, amount) VALUES (1, 500);

-- 몬스터 드랍 보상
INSERT INTO RewardItem (reward_id, item_id, quantity, drop_probability) VALUES 
(2, 10, 1, 0.8), -- 슬라임 점액 80% 드랍
(3, 11, 1, 0.5); -- 낡은 뼈다귀 50% 드랍

-- 위에서 만든 몬스터에 보상 ID 업데이트 매핑
UPDATE Monster SET drop_reward_id = 2 WHERE actor_id = 4;
UPDATE Monster SET drop_reward_id = 3 WHERE actor_id = 5;

SET FOREIGN_KEY_CHECKS = 1;

-- ===== 3. STREAMLIT APP EXTENSION SCHEMA SAFE =====
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



-- ===== 4. CHARACTER / INVENTORY / CRAFTING EXTENSION SCHEMA =====
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


-- ===== 5. HP / MP ITEM EFFECT SEED =====
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


-- ===== 6. MONSTER EXP / EQUIPMENT SEED =====
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


-- ===== 7. QUEST DEMO SEED =====
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


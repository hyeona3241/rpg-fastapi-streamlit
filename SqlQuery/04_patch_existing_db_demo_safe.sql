-- ============================================================
-- 02_patch_existing_db_demo_safe.sql
-- Purpose: Safely update an existing MyRPG DB for current Streamlit app testing.
-- Run with rpg user:
--   mysql -urpg -prpg MyRPG < 02_patch_existing_db_demo_safe.sql
--
-- This patch:
--   - adds app-used columns if missing
--   - creates missing app extension tables
--   - inserts demo materials/equipment/monsters/quests/recipes
--   - does NOT drop existing data
-- ============================================================

USE MyRPG;
SET FOREIGN_KEY_CHECKS = 0;

DROP PROCEDURE IF EXISTS add_column_if_missing;
DELIMITER $$
CREATE PROCEDURE add_column_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_column_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD COLUMN ', p_column_definition);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_column_if_missing('User','role',"role VARCHAR(20) NOT NULL DEFAULT 'USER'");
CALL add_column_if_missing('User','active',"active BOOLEAN NOT NULL DEFAULT TRUE");
CALL add_column_if_missing('Character','is_public',"is_public BOOLEAN NOT NULL DEFAULT FALSE");
CALL add_column_if_missing('Character','created_at',"created_at DATETIME DEFAULT CURRENT_TIMESTAMP");
CALL add_column_if_missing('Item','icon_url',"icon_url TEXT");
CALL add_column_if_missing('Item','equipment_part',"equipment_part VARCHAR(50) NULL");
CALL add_column_if_missing('Item','required_level',"required_level INT NOT NULL DEFAULT 1");
CALL add_column_if_missing('Item','rarity',"rarity VARCHAR(50) NOT NULL DEFAULT 'COMMON'");
CALL add_column_if_missing('Item','is_generated',"is_generated BOOLEAN NOT NULL DEFAULT FALSE");
CALL add_column_if_missing('Monster','name',"name VARCHAR(255)");
CALL add_column_if_missing('Monster','description',"description TEXT");
CALL add_column_if_missing('Monster','level',"level INT NOT NULL DEFAULT 1");
CALL add_column_if_missing('Monster','respawn_time_sec',"respawn_time_sec INT NOT NULL DEFAULT 30");
CALL add_column_if_missing('Quest','prerequisite_quest_id',"prerequisite_quest_id INT NULL");
CALL add_column_if_missing('Quest','next_quest_id',"next_quest_id INT NULL");
CALL add_column_if_missing('Quest','reward_id',"reward_id INT NULL");

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

CREATE TABLE IF NOT EXISTS EquipmentPart (
    type VARCHAR(50) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS ItemBonusStat (
    item_id INT NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    value INT NOT NULL,
    PRIMARY KEY (item_id, stat_type),
    FOREIGN KEY (item_id) REFERENCES Item(id),
    FOREIGN KEY (stat_type) REFERENCES Stat(type)
);

CREATE TABLE IF NOT EXISTS CharacterEquipment (
    char_id INT NOT NULL,
    equipment_part VARCHAR(50) NOT NULL,
    inventory_id INT NOT NULL,
    item_id INT NOT NULL,
    PRIMARY KEY (char_id, equipment_part),
    FOREIGN KEY (char_id) REFERENCES `Character`(actor_id),
    FOREIGN KEY (equipment_part) REFERENCES EquipmentPart(type),
    FOREIGN KEY (inventory_id, item_id) REFERENCES InventoryItem(inventory_id, item_id)
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
    neutral FLOAT DEFAULT 0,
    pure FLOAT DEFAULT 0,
    metallic FLOAT DEFAULT 0,
    magical FLOAT DEFAULT 0,
    cold FLOAT DEFAULT 0,
    hot FLOAT DEFAULT 0,
    electric FLOAT DEFAULT 0,
    explosive FLOAT DEFAULT 0,
    fragile FLOAT DEFAULT 0,
    dense FLOAT DEFAULT 0,
    dark FLOAT DEFAULT 0,
    holy FLOAT DEFAULT 0,
    sharp FLOAT DEFAULT 0,
    defensive FLOAT DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

CALL add_column_if_missing('ItemAttribute','neutral',"neutral FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','pure',"pure FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','fragile',"fragile FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','dense',"dense FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','dark',"dark FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','holy',"holy FLOAT DEFAULT 0");
CALL add_column_if_missing('ItemAttribute','sharp',"sharp FLOAT DEFAULT 0");

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

CREATE TABLE IF NOT EXISTS CraftingMethod (
    method VARCHAR(50) PRIMARY KEY,
    description TEXT
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

DROP PROCEDURE IF EXISTS add_column_if_missing;

-- ============================================================
-- UPSERT / DEMO DATA
-- ============================================================

INSERT IGNORE INTO `User` (id, user_name, password, role, active) VALUES
('admin', '관리자', 'admin', 'ADMIN', TRUE),
('hero', '테스트유저', 'hero', 'USER', TRUE);
UPDATE `User` SET role='ADMIN', active=TRUE WHERE id='admin';

INSERT IGNORE INTO Stat (type, name, description) VALUES
('HP','현재 체력','전투 중 현재 체력'),
('MAX_HP','최대 체력','최대 체력'),
('MP','현재 마나','스킬 사용 자원'),
('MAX_MP','최대 마나','최대 마나'),
('ATK','공격력','물리 공격력'),
('DEF','방어력','피해 감소'),
('INT','지능','마법 공격력'),
('AGI','민첩','속도/회피 관련');

INSERT IGNORE INTO LevelMaster (level, max_exp_to_next, max_hp, max_mp) VALUES
(1,100,100,50),(2,180,120,60),(3,300,145,75),(4,460,175,90),(5,650,210,110);

INSERT IGNORE INTO LevelBaseStat (char_level, stat_type, value) VALUES
(1,'HP',100),(1,'MAX_HP',100),(1,'MP',50),(1,'MAX_MP',50),(1,'ATK',12),(1,'DEF',6),(1,'INT',8),(1,'AGI',8);

INSERT IGNORE INTO Specimen (type, name, description) VALUES
('HUMAN','인간','균형 잡힌 종족'),
('ELF','엘프','마력과 민첩이 높은 종족'),
('ORC','오크','체력과 공격력이 높은 종족'),
('DWARF','드워프','방어와 금속성이 강한 종족');

INSERT IGNORE INTO SpecimenBaseStat (specimen_type, stat_type, value) VALUES
('HUMAN','MAX_HP',10),('HUMAN','MAX_MP',5),('HUMAN','ATK',2),('HUMAN','DEF',2),('HUMAN','INT',2),('HUMAN','AGI',2),
('ELF','MAX_MP',20),('ELF','INT',6),('ELF','AGI',4),('ELF','MAX_HP',-5),
('ORC','MAX_HP',30),('ORC','ATK',6),('ORC','DEF',3),('ORC','INT',-2),
('DWARF','MAX_HP',20),('DWARF','DEF',6),('DWARF','ATK',3),('DWARF','AGI',-2);

INSERT IGNORE INTO Job (type, name, description) VALUES
('NOVICE','초보자','기본 직업'),
('WARRIOR','전사','높은 체력과 공격력을 가진 근접 직업'),
('MAGE','마법사','높은 마나와 지능을 가진 마법 직업'),
('ROGUE','도적','민첩과 빠른 공격에 특화된 직업'),
('ARCHER','궁수','민첩과 원거리 공격에 특화된 직업');

INSERT IGNORE INTO Skill (id, name, description, mp_cost, cooldown_sec) VALUES
(1001,'Slash','검으로 베는 기본 물리 공격',3,0),
(1002,'Power Strike','강한 일격으로 큰 피해를 준다',8,1),
(1003,'Fire Ball','화염구를 날리는 마법 공격',10,1),
(1004,'Ice Bolt','냉기 화살을 발사한다',9,1),
(1005,'Quick Stab','빠르게 찌르는 도적 기술',5,0),
(1006,'Healing Light','자신의 체력을 회복한다',12,2),
(1007,'Arrow Shot','원거리 화살 공격',5,0);

INSERT IGNORE INTO EquipmentPart (type) VALUES ('weapon'),('head'),('armor');

INSERT IGNORE INTO Item (id, name, description, type, sub_type, capacity, rarity, equipment_part, required_level, is_generated) VALUES
(50001,'슬라임 젤','점성이 강한 기본 크래프팅 재료','material','slime',99,'COMMON',NULL,1,FALSE),
(50002,'야생 약초','회복 성분이 있는 약초','material','herb',99,'COMMON',NULL,1,FALSE),
(50003,'낡은 뼈다귀','언데드 몬스터에게서 얻은 뼈 재료','material','bone',99,'COMMON',NULL,1,FALSE),
(50004,'철광석','장비 강화와 제작에 쓰이는 금속 재료','material','ore',99,'COMMON',NULL,1,FALSE),
(50005,'화염꽃','뜨거운 화염 속성을 가진 꽃','material','flower',99,'RARE',NULL,1,FALSE),
(50006,'마나 결정','마력이 응축된 결정','material','crystal',99,'RARE',NULL,1,FALSE),
(50007,'서리 조각','차가운 냉기가 깃든 조각','material','crystal',99,'RARE',NULL,1,FALSE),
(50008,'독버섯','독성이 강한 버섯','material','mushroom',99,'COMMON',NULL,1,FALSE),
(50009,'전류 파편','전격 속성이 남아 있는 파편','material','crystal',99,'RARE',NULL,1,FALSE),
(50010,'어둠 가루','어둠 속성이 스며든 가루','material','powder',99,'RARE',NULL,1,FALSE),
(50020,'소형 회복 물약','HP를 회복하는 기본 물약','consumable','potion',20,'COMMON',NULL,1,FALSE),
(50021,'소형 마나 물약','MP를 회복하는 기본 물약','consumable','potion',20,'COMMON',NULL,1,FALSE),
(50022,'해독 물약','독 효과를 완화하는 물약','consumable','potion',20,'COMMON',NULL,1,FALSE),
(50201,'철검','공격력을 올려주는 기본 무기','equipment','weapon',1,'COMMON','weapon',1,FALSE),
(50202,'수습 마법사 지팡이','지능과 마나를 올려주는 지팡이','equipment','weapon',1,'COMMON','weapon',1,FALSE),
(50203,'가죽 투구','방어력을 조금 올려주는 머리 장비','equipment','head',1,'COMMON','head',1,FALSE),
(50204,'여행자 갑옷','방어와 최대 체력을 올려주는 방어구','equipment','armor',1,'COMMON','armor',1,FALSE),
(50205,'뼈 칼날','낡은 뼈를 가공한 공격형 무기','equipment','weapon',1,'RARE','weapon',2,FALSE),
(50101,'혼합 회복 젤','슬라임 젤과 약초를 혼합한 회복 재료','consumable','crafted',20,'COMMON',NULL,1,FALSE),
(50102,'압축 뼈 합금','낡은 뼈와 철광석을 압축한 강화 재료','material','crafted',99,'RARE',NULL,1,FALSE),
(50103,'주입 화염 영약','화염꽃에 마나를 주입한 전투 영약','consumable','crafted',20,'RARE',NULL,1,FALSE);

INSERT IGNORE INTO ItemAttribute (item_id, toxic, healing, viscous, stable, organic, plant, unstable, burnt, neutral, pure, metallic, magical, cold, hot, electric, explosive, fragile, dense, dark, holy, sharp, defensive) VALUES
(50001,0,2,9,3,5,0,1,0,2,0,0,1,0,0,0,0,1,2,0,0,0,1),
(50002,0,8,1,5,8,9,0,0,2,5,0,2,0,0,0,0,2,0,0,1,0,1),
(50003,1,0,0,6,7,0,2,1,2,0,0,1,0,0,0,0,4,5,5,0,3,2),
(50004,0,0,0,8,0,0,0,0,4,0,9,0,0,0,1,0,1,8,0,0,3,6),
(50005,0,1,0,3,7,8,5,2,0,0,0,4,0,9,0,2,3,0,0,0,0,0),
(50006,0,3,0,6,0,0,1,0,0,8,0,9,0,0,3,0,1,3,0,3,0,1),
(50007,0,1,0,7,0,0,1,0,0,4,0,5,9,0,0,0,4,3,0,0,2,1),
(50008,9,0,2,2,8,3,5,0,0,0,0,2,0,0,0,0,5,0,4,0,0,0),
(50009,0,0,0,4,0,0,6,1,0,0,4,5,0,0,9,2,5,2,0,0,1,0),
(50010,3,0,0,3,0,0,4,0,0,0,0,4,0,0,0,0,6,1,9,0,0,0),
(50101,0,9,5,6,7,6,0,0,1,6,0,2,0,0,0,0,1,1,0,2,0,1),
(50102,0,0,0,9,3,0,0,0,1,0,9,1,0,0,0,0,2,9,1,0,5,8),
(50103,0,2,0,5,4,4,2,2,0,0,0,7,0,9,0,1,2,1,0,0,0,0);

INSERT IGNORE INTO ItemEffect (item_id, type_effect, hp, poison, duration, attack, defense, speed, resistance, burn, freeze, shock, explosion_damage) VALUES
(50020,'healing',35,0,0,0,0,0,0,0,0,0,0),
(50021,'mana',0,0,0,0,0,0,0,0,0,0,0),
(50022,'cure',10,-10,0,0,0,0,0,0,0,0,0),
(50101,'healing',45,0,0,0,0,0,2,0,0,0,0),
(50102,'defensive',0,0,0,0,5,0,4,0,0,0,0),
(50103,'attack',0,0,3,8,0,0,0,4,0,0,0);

INSERT IGNORE INTO ItemBonusStat (item_id, stat_type, value) VALUES
(50201,'ATK',5),
(50202,'INT',7),(50202,'MAX_MP',10),
(50203,'DEF',2),(50203,'MAX_HP',5),
(50204,'DEF',5),(50204,'MAX_HP',10),
(50205,'ATK',8),(50205,'AGI',2);

INSERT IGNORE INTO CraftingMethod (method, description) VALUES
('mix','두 재료를 단순 혼합한다. 회복/균형형 결과가 잘 나온다.'),
('boil','재료를 끓여 성분을 추출한다. 회복/독성 변화에 적합하다.'),
('bake','재료를 구워 안정화한다. 화염/금속 계열 결과가 잘 나온다.'),
('distill','성분을 증류해 정제한다. 순수/마법 계열 결과가 잘 나온다.'),
('compress','재료를 압축한다. 방어/금속/강화 계열 결과가 잘 나온다.'),
('infuse','마나를 주입한다. 마법/속성 계열 결과가 잘 나온다.');

INSERT IGNORE INTO CraftingRecipe (id, ingredient1_id, ingredient2_id, method, result_item_id, created_by_ai) VALUES
(51001,50001,50002,'mix',50101,FALSE),
(51002,50003,50004,'compress',50102,FALSE),
(51003,50005,50006,'infuse',50103,FALSE);

INSERT IGNORE INTO Reward (id) VALUES (70001),(70002),(70003),(70004),(70005),(70101),(70102),(70103),(70104);
INSERT IGNORE INTO RewardExp (reward_id, amount) VALUES
(70001,30),(70002,45),(70003,70),(70004,90),(70005,80),
(70101,100),(70102,120),(70103,150),(70104,130);
INSERT IGNORE INTO RewardItem (reward_id, item_id, quantity, drop_probability) VALUES
(70001,50001,1,1.0),(70001,50020,1,0.25),
(70002,50003,1,1.0),
(70003,50004,1,0.7),(70003,50021,1,0.35),
(70004,50005,1,0.8),(70004,50006,1,0.4),
(70005,50007,1,0.8),
(70101,50020,2,1.0),
(70102,50003,2,1.0),
(70103,50205,1,1.0),
(70104,50021,2,1.0);

INSERT IGNORE INTO Actor (id) VALUES (60001),(60002),(60003),(60004),(60005);
INSERT IGNORE INTO Monster (actor_id, name, description, hp, atk, `def`, level, drop_reward_id, respawn_time_sec) VALUES
(60001,'슬라임','초보자 사냥터의 기본 몬스터',35,6,1,1,70001,15),
(60002,'해골 병사','낡은 뼈다귀를 떨어뜨리는 언데드',55,9,3,2,70002,25),
(60003,'고블린 정찰병','철광석과 소모품을 떨어뜨릴 수 있다',75,12,4,3,70003,30),
(60004,'화염 임프','화염꽃과 마나 결정을 떨어뜨리는 속성 몬스터',90,15,5,4,70004,45),
(60005,'얼음 박쥐','서리 조각을 떨어뜨리는 냉기 몬스터',80,13,4,3,70005,35);

INSERT IGNORE INTO Quest (id, name, description, max_steps, type, is_repeatable, prerequisite_quest_id, next_quest_id, reward_id) VALUES
(80001,'슬라임 정리','마을 주변의 슬라임 3마리를 처치하세요.',1,'KILL_MONSTER',FALSE,NULL,80003,70101),
(80002,'해골 잔해 조사','해골 병사 2마리를 처치해 낡은 뼈 재료를 확보하세요.',1,'KILL_MONSTER',FALSE,NULL,NULL,70102),
(80003,'고블린 정찰 저지','슬라임 정리를 마친 뒤 고블린 정찰병 2마리를 처치하세요.',1,'KILL_MONSTER',FALSE,80001,NULL,70103),
(80004,'회복 젤 제작 실험','슬라임 젤과 야생 약초를 mix로 조합해 혼합 회복 젤을 제작하세요.',1,'CRAFT_ITEM',TRUE,NULL,NULL,70104);
UPDATE Quest SET next_quest_id = 80003 WHERE id = 80001;

INSERT IGNORE INTO QuestObjective (quest_id, objective_type, target_id, required_count) VALUES
(80001,'KILL_MONSTER',60001,3),
(80002,'KILL_MONSTER',60002,2),
(80003,'KILL_MONSTER',60003,2),
(80004,'CRAFT_ITEM',50101,1);

-- Optional demo character. If actor id 61001 already exists, these INSERT IGNORE statements do not overwrite data.
INSERT IGNORE INTO Actor (id) VALUES (61001);
INSERT IGNORE INTO `Character` (actor_id, user_id, character_name, level, exp, active, is_public) VALUES
(61001,'hero','DemoHero',1,0,TRUE,TRUE);
INSERT IGNORE INTO CharacterSpecimen (char_id, type, fraction) VALUES (61001,'HUMAN',0.7),(61001,'ELF',0.3);
INSERT IGNORE INTO CharacterJob (type, char_id, active) VALUES ('WARRIOR',61001,TRUE);
INSERT IGNORE INTO ActorStat (actor_id, stat_type, value) VALUES
(61001,'HP',110),(61001,'MAX_HP',110),(61001,'MP',55),(61001,'MAX_MP',55),(61001,'ATK',18),(61001,'DEF',9),(61001,'INT',11),(61001,'AGI',10);
INSERT IGNORE INTO CharacterSkill (skill_id, char_id, skill_level) VALUES
(1001,61001,1),(1002,61001,1),(1003,61001,1),(1006,61001,1);
INSERT IGNORE INTO Inventory (id, owner_id, type, capacity) VALUES (62001,61001,'BASIC',30);
INSERT IGNORE INTO InventoryItem (inventory_id, item_id, quantity) VALUES
(62001,50001,5),(62001,50002,5),(62001,50003,3),(62001,50004,3),(62001,50005,2),(62001,50006,2),(62001,50020,5),(62001,50021,3),(62001,50201,1),(62001,50203,1),(62001,50204,1);

SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Existing DB safe patch and demo seed completed.' AS message;

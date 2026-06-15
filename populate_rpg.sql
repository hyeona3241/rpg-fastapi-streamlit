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
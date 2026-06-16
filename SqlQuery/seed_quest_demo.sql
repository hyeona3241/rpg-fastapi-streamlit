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

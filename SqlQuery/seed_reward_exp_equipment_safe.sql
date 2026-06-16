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

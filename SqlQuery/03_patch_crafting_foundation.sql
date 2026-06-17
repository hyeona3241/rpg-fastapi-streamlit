USE MyRPG;

-- ============================================================
-- Crafting foundation patch
-- Safe for existing DB: creates missing crafting tables and adds columns
-- needed by the Streamlit crafting page and FastAPI /crafting APIs.
-- ============================================================

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

-- Item columns used by generated crafting results.
CALL add_column_if_missing('Item', 'icon_url', 'icon_url TEXT NULL');
CALL add_column_if_missing('Item', 'equipment_part', 'equipment_part VARCHAR(50) NULL');
CALL add_column_if_missing('Item', 'required_level', 'required_level INT NOT NULL DEFAULT 1');
CALL add_column_if_missing('Item', 'rarity', 'rarity VARCHAR(50) NOT NULL DEFAULT ''COMMON''');
CALL add_column_if_missing('Item', 'is_generated', 'is_generated BOOLEAN NOT NULL DEFAULT FALSE');

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
    neutral FLOAT NOT NULL DEFAULT 0,
    pure FLOAT NOT NULL DEFAULT 0,
    metallic FLOAT NOT NULL DEFAULT 0,
    magical FLOAT NOT NULL DEFAULT 0,
    cold FLOAT NOT NULL DEFAULT 0,
    hot FLOAT NOT NULL DEFAULT 0,
    electric FLOAT NOT NULL DEFAULT 0,
    explosive FLOAT NOT NULL DEFAULT 0,
    fragile FLOAT NOT NULL DEFAULT 0,
    dense FLOAT NOT NULL DEFAULT 0,
    dark FLOAT NOT NULL DEFAULT 0,
    holy FLOAT NOT NULL DEFAULT 0,
    sharp FLOAT NOT NULL DEFAULT 0,
    defensive FLOAT NOT NULL DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(id)
);

-- Add attributes that may be missing from older ItemAttribute table versions.
CALL add_column_if_missing('ItemAttribute', 'neutral', 'neutral FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'pure', 'pure FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'fragile', 'fragile FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'dense', 'dense FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'dark', 'dark FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'holy', 'holy FLOAT NOT NULL DEFAULT 0');
CALL add_column_if_missing('ItemAttribute', 'sharp', 'sharp FLOAT NOT NULL DEFAULT 0');

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

-- Ensure all existing material items have an attribute row, even if values are zero.
INSERT IGNORE INTO ItemAttribute (item_id)
SELECT id FROM Item WHERE LOWER(type) IN ('material', 'consumable');

DROP PROCEDURE IF EXISTS add_column_if_missing;

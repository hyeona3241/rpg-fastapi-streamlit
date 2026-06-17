USE MyRPG;

-- Add demo/UI columns for monster display if they are missing.
SET @schema_name := DATABASE();

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE Monster ADD COLUMN name VARCHAR(100) NULL',
        'SELECT 1'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @schema_name AND TABLE_NAME = 'Monster' AND COLUMN_NAME = 'name'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE Monster ADD COLUMN description TEXT NULL',
        'SELECT 1'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @schema_name AND TABLE_NAME = 'Monster' AND COLUMN_NAME = 'description'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE Monster ADD COLUMN level INT NOT NULL DEFAULT 1',
        'SELECT 1'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @schema_name AND TABLE_NAME = 'Monster' AND COLUMN_NAME = 'level'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Fill readable names/levels for demo monsters without overwriting custom names.
UPDATE Monster
SET
    name = COALESCE(name, CONCAT('몬스터 #', actor_id)),
    level = CASE
        WHEN level IS NULL OR level < 1 THEN 1
        ELSE level
    END;

-- More friendly names for the first few demo monsters.
UPDATE Monster
SET name = CASE actor_id
    WHEN 1 THEN '초원 슬라임'
    WHEN 2 THEN '늑대 정찰병'
    WHEN 3 THEN '고블린 약탈자'
    WHEN 4 THEN '오염된 골렘'
    WHEN 5 THEN '동굴 박쥐'
    ELSE name
END,
level = CASE actor_id
    WHEN 1 THEN 1
    WHEN 2 THEN 2
    WHEN 3 THEN 3
    WHEN 4 THEN 5
    WHEN 5 THEN 2
    ELSE level
END,
description = CASE actor_id
    WHEN 1 THEN '초보자도 상대할 수 있는 약한 슬라임입니다.'
    WHEN 2 THEN '빠르게 접근해 물어뜯는 야생 늑대입니다.'
    WHEN 3 THEN '낡은 무기를 들고 다니는 작은 약탈자입니다.'
    WHEN 4 THEN '오염된 돌덩어리로 이루어진 단단한 골렘입니다.'
    WHEN 5 THEN '동굴에서 날아다니며 습격하는 박쥐입니다.'
    ELSE description
END
WHERE actor_id IN (1,2,3,4,5);

-- ============================================================
-- 99_optional_drop_unused_legacy_tables.sql
-- Purpose: Optional cleanup of legacy tables not used by the current Streamlit/FastAPI app.
--
-- WARNING:
--   - Do NOT run this unless you intentionally want to remove old/unused base RPG tables.
--   - This is safe for the current app code generated in this conversation,
--     but may break old assignments or older SQL examples that still reference these tables.
--   - Recommended: keep this file for documentation and only run near final submission if needed.
--
-- Run:
--   mysql -urpg -prpg MyRPG < 99_optional_drop_unused_legacy_tables.sql
-- ============================================================

USE MyRPG;
SET FOREIGN_KEY_CHECKS = 0;

-- Requirement tables are not used by the current Streamlit app routes.
DROP TABLE IF EXISTS RequirementLevel;
DROP TABLE IF EXISTS RequirementSpecimen;
DROP TABLE IF EXISTS RequirementJob;
DROP TABLE IF EXISTS RequirementSkill;
DROP TABLE IF EXISTS RequirementQuest;

-- Status effect tables are not used by current battle/inventory/equipment logic.
DROP TABLE IF EXISTS CharacterStatusEffect;
DROP TABLE IF EXISTS StatusEffect;

-- Shop/NPC catalog tables are not used by current Quest page implementation.
-- Current quests are shown directly from Quest / QuestObjective.
DROP TABLE IF EXISTS ShopCatalog;
DROP TABLE IF EXISTS VillagerQuest;
DROP TABLE IF EXISTS Villager;
DROP TABLE IF EXISTS Shop;

-- SkillBonusStat is not used by current stat/combat calculation.
DROP TABLE IF EXISTS SkillBonusStat;

SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Optional legacy cleanup completed.' AS message;

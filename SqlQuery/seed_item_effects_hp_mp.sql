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

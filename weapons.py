import random

import pygame

import effects
import sprites
from bullet import Bullet
from settings import (
    FIRE_RANGE,
    BULLET_SPEED,
    MULTISHOT_SPREAD,
    KNIFE_INTERVAL,
    KNIFE_SPEED,
    BLADE_DISTANCE,
    BLADE_SPIN,
    BLADE_HIT_COOLDOWN,
    AURA_RADIUS,
    AURA_TICK,
    LIGHTNING_INTERVAL,
    LIGHTNING_RANGE,
    BOOMERANG_INTERVAL,
    BOOMERANG_SPEED,
    BOOMERANG_TIME,
    METEOR_INTERVAL,
    METEOR_DELAY,
    METEOR_RADIUS,
    FIRE_DROP_TIME,
    FIRE_LIFE,
    FIRE_RADIUS,
    FIRE_TICK,
)


def nearest(pos, enemies, max_distance):
    target = None
    best = max_distance
    for enemy in enemies:
        distance = pos.distance_to(enemy.pos)
        if distance < best:
            best = distance
            target = enemy
    return target


def spread_shots(player, direction, count, damage, sprite, speed, pierce, radius=4):
    bullets = []
    for i in range(count):
        angle = (i - (count - 1) / 2) * MULTISHOT_SPREAD
        amount, crit = player.roll_damage(damage)
        bullets.append(Bullet(player.pos, direction.rotate(angle), amount, sprite, speed, pierce, radius, crit=crit))
    return bullets


class Wand:
    key = "wand"

    def __init__(self):
        self.level = 1
        self.timer = 0

    def update(self, dt, player, enemies):
        self.timer -= dt
        if self.timer > 0:
            return []
        target = nearest(player.pos, enemies, FIRE_RANGE)
        if target is None:
            return []
        self.timer = player.fire_interval * 0.9 ** (self.level - 1)
        direction = (target.pos - player.pos).normalize()
        count = 1 + player.multishot
        if self.level >= 3:
            count += 1
        if self.level >= 5:
            count += 1
        damage = player.damage + (self.level - 1) // 2
        return spread_shots(player, direction, count, damage, player.bullet_sprite, BULLET_SPEED, player.pierce)

    def draw(self, screen, camera, player):
        pass


class Knives:
    key = "knives"

    def __init__(self):
        self.level = 1
        self.timer = 0

    def update(self, dt, player, enemies):
        self.timer -= dt
        if self.timer > 0:
            return []
        self.timer = KNIFE_INTERVAL * 0.9 ** (self.level - 1)
        count = 1 + player.multishot
        if self.level >= 2:
            count += 1
        if self.level >= 4:
            count += 1
        damage = player.damage + self.level
        pierce = 1 + self.level // 2 + player.pierce
        return spread_shots(player, player.facing, count, damage, "knife", KNIFE_SPEED, pierce, 6)

    def draw(self, screen, camera, player):
        pass


class Blades:
    key = "blades"

    def __init__(self):
        self.level = 1
        self.angle = 0
        self.cooldowns = {}

    def positions(self, player):
        count = 1 + self.level
        result = []
        for i in range(count):
            offset = pygame.Vector2(BLADE_DISTANCE, 0).rotate(self.angle + i * 360 / count)
            result.append(player.pos + offset)
        return result

    def update(self, dt, player, enemies):
        self.angle += BLADE_SPIN * 57.3 * dt * (1 + 0.1 * self.level)
        for enemy in list(self.cooldowns.keys()):
            self.cooldowns[enemy] -= dt
            if self.cooldowns[enemy] <= 0:
                del self.cooldowns[enemy]

        damage = player.damage + self.level
        for pos in self.positions(player):
            for enemy in enemies:
                if enemy in self.cooldowns:
                    continue
                if pos.distance_to(enemy.pos) < enemy.radius + 14:
                    amount, crit = player.roll_damage(damage)
                    enemy.hurt(amount, crit)
                    self.cooldowns[enemy] = BLADE_HIT_COOLDOWN
        return []

    def draw(self, screen, camera, player):
        image = sprites.get("blade")
        for pos in self.positions(player):
            sprites.draw_centered(screen, sprites.rotated(image, -self.angle * 3), pos - camera)


class Aura:
    key = "aura"

    def __init__(self):
        self.level = 1
        self.timer = 0

    def radius(self):
        return AURA_RADIUS + 15 * (self.level - 1)

    def update(self, dt, player, enemies):
        self.timer -= dt
        if self.timer > 0:
            return []
        self.timer = AURA_TICK
        damage = max(1, player.damage // 2 + self.level - 1)
        for enemy in enemies:
            if player.pos.distance_to(enemy.pos) < self.radius() + enemy.radius:
                amount, crit = player.roll_damage(damage)
                enemy.hurt(amount, crit)
        return []

    def draw(self, screen, camera, player):
        image = sprites.get("aura")
        image = sprites.scaled(image, self.radius() * 2 / image.get_width())
        sprites.draw_centered(screen, image, player.pos - camera)


class Lightning:
    key = "lightning"

    def __init__(self):
        self.level = 1
        self.timer = 1
        self.strikes = []

    def update(self, dt, player, enemies):
        for strike in self.strikes:
            strike["life"] -= dt
        self.strikes = [s for s in self.strikes if s["life"] > 0]

        self.timer -= dt
        if self.timer > 0:
            return []
        targets = [e for e in enemies if player.pos.distance_to(e.pos) < LIGHTNING_RANGE]
        if not targets:
            return []
        self.timer = LIGHTNING_INTERVAL * 0.88 ** (self.level - 1)
        count = min(len(targets), 1 + self.level // 2)
        damage = 3 + 2 * self.level + player.damage
        for enemy in random.sample(targets, count):
            amount, crit = player.roll_damage(damage)
            enemy.hurt(amount, crit)
            effects.burst(enemy.pos, (255, 230, 80), 6)
            self.strikes.append({"pos": pygame.Vector2(enemy.pos), "life": 0.2})
        return []

    def draw(self, screen, camera, player):
        image = sprites.get("lightning")
        for strike in self.strikes:
            pos = strike["pos"] - camera
            for i in range(4):
                y = pos.y - image.get_height() * (i + 0.5)
                screen.blit(image, (pos.x - image.get_width() / 2, y))


class Boomerang:
    key = "boomerang"

    def __init__(self):
        self.level = 1
        self.timer = 0
        self.flying = []

    def update(self, dt, player, enemies):
        damage = player.damage + self.level
        for boomerang in self.flying:
            boomerang["time"] += dt
            boomerang["angle"] += 900 * dt
            if boomerang["time"] < BOOMERANG_TIME:
                boomerang["pos"] += boomerang["dir"] * BOOMERANG_SPEED * dt
            else:
                # terug naar de speler
                back = player.pos - boomerang["pos"]
                if back.length() < 20:
                    boomerang["done"] = True
                    continue
                boomerang["pos"] += back.normalize() * BOOMERANG_SPEED * 1.2 * dt
            for enemy in enemies:
                if enemy in boomerang["hit"]:
                    continue
                if boomerang["pos"].distance_to(enemy.pos) < enemy.radius + 14:
                    amount, crit = player.roll_damage(damage)
                    enemy.hurt(amount, crit)
                    boomerang["hit"].append(enemy)
            if boomerang["time"] >= BOOMERANG_TIME and not boomerang["back"]:
                # op de terugweg mag hij alles weer raken
                boomerang["back"] = True
                boomerang["hit"] = []
        self.flying = [b for b in self.flying if not b.get("done")]

        self.timer -= dt
        if self.timer > 0:
            return []
        target = nearest(player.pos, enemies, FIRE_RANGE)
        if target is None:
            return []
        self.timer = BOOMERANG_INTERVAL * 0.9 ** (self.level - 1)
        direction = (target.pos - player.pos).normalize()
        count = 1 + self.level // 3
        for i in range(count):
            angle = (i - (count - 1) / 2) * 25
            self.flying.append({"pos": pygame.Vector2(player.pos), "dir": direction.rotate(angle), "time": 0,
                                "angle": 0, "hit": [], "back": False})
        return []

    def draw(self, screen, camera, player):
        image = sprites.get("boomerang")
        for boomerang in self.flying:
            sprites.draw_centered(screen, sprites.rotated(image, boomerang["angle"]), boomerang["pos"] - camera)


class Meteor:
    key = "meteor"

    def __init__(self):
        self.level = 1
        self.timer = 1.5
        self.falling = []

    def radius(self):
        return METEOR_RADIUS + 10 * (self.level - 1)

    def update(self, dt, player, enemies):
        for meteor in self.falling:
            meteor["timer"] -= dt
            if meteor["timer"] <= 0 and not meteor["landed"]:
                meteor["landed"] = True
                land(meteor["pos"], self.radius(), 4 + 3 * self.level + player.damage, player, enemies)
        self.falling = [m for m in self.falling if m["timer"] > -0.2]

        self.timer -= dt
        if self.timer > 0:
            return []
        targets = [e for e in enemies if player.pos.distance_to(e.pos) < FIRE_RANGE]
        if not targets:
            return []
        self.timer = METEOR_INTERVAL * 0.9 ** (self.level - 1)
        count = min(len(targets), 1 + self.level // 2)
        for enemy in random.sample(targets, count):
            self.falling.append({"pos": pygame.Vector2(enemy.pos), "timer": METEOR_DELAY, "landed": False})
        return []

    def draw(self, screen, camera, player):
        for meteor in self.falling:
            draw_meteor(screen, camera, meteor, self.radius())


def land(pos, radius, damage, player, enemies):
    for enemy in enemies:
        if pos.distance_to(enemy.pos) < radius + enemy.radius:
            amount, crit = player.roll_damage(damage)
            enemy.hurt(amount, crit)
    effects.burst(pos, (255, 140, 40), 14)
    effects.shake(4)


def draw_meteor(screen, camera, meteor, radius):
    pos = meteor["pos"] - camera
    if meteor["landed"]:
        pygame.draw.circle(screen, (255, 200, 80), pos, radius, 4)
        return
    # schaduw wordt groter, meteoor valt van boven naar beneden
    progress = 1 - meteor["timer"] / METEOR_DELAY
    shadow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(shadow, (0, 0, 0, 90), (radius, radius), radius * progress)
    pygame.draw.circle(shadow, (255, 80, 40, 160), (radius, radius), radius, 2)
    screen.blit(shadow, (pos.x - radius, pos.y - radius))
    image = sprites.get("meteor")
    sprites.draw_centered(screen, image, pos - (0, 300 * (1 - progress)))


class FireTrail:
    key = "fire"

    def __init__(self):
        self.level = 1
        self.drop_timer = 0
        self.tick_timer = 0
        self.flames = []

    def update(self, dt, player, enemies):
        for flame in self.flames:
            flame["life"] -= dt
            flame["time"] += dt
        self.flames = [f for f in self.flames if f["life"] > 0]

        self.drop_timer -= dt
        if self.drop_timer <= 0 and player.move.length() > 0:
            self.drop_timer = FIRE_DROP_TIME
            self.flames.append({"pos": pygame.Vector2(player.pos), "life": FIRE_LIFE + 0.3 * self.level,
                                "time": random.uniform(0, 1)})

        self.tick_timer -= dt
        if self.tick_timer > 0:
            return []
        self.tick_timer = FIRE_TICK
        damage = 1 + self.level + player.damage // 2
        radius = FIRE_RADIUS + 3 * self.level
        for enemy in enemies:
            for flame in self.flames:
                if flame["pos"].distance_to(enemy.pos) < radius + enemy.radius:
                    amount, crit = player.roll_damage(damage)
                    enemy.hurt(amount, crit)
                    break
        return []

    def draw(self, screen, camera, player):
        for flame in self.flames:
            image = sprites.frame("fire", flame["time"], 8)
            if flame["life"] < 0.5:
                image = sprites.faded(image, flame["life"] * 2)
            sprites.draw_centered(screen, image, flame["pos"] - camera)


WEAPON_CLASSES = {
    "wand": Wand,
    "knives": Knives,
    "blades": Blades,
    "aura": Aura,
    "lightning": Lightning,
    "boomerang": Boomerang,
    "meteor": Meteor,
    "fire": FireTrail,
}


def make_weapon(key):
    return WEAPON_CLASSES[key]()

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


WEAPON_CLASSES = {
    "wand": Wand,
    "knives": Knives,
    "blades": Blades,
    "aura": Aura,
    "lightning": Lightning,
}


def make_weapon(key):
    return WEAPON_CLASSES[key]()

import math
import random

import pygame

import effects
import sprites
from bullet import Bullet
from settings import (
    ENEMY_TYPES,
    SPAWN_DISTANCE,
    SPAWN_TABLE,
    HP_GROWTH,
    SPEED_GROWTH,
    SPEED_FACTOR_MAX,
    ELITE_CHANCE,
    ELITE_START,
    ELITE_HP,
    ELITE_SCALE,
    SHOOTER_RANGE,
    SHOOTER_COOLDOWN,
    DASH_RANGE,
    DASH_WINDUP,
    DASH_TIME,
    DASH_SPEED_FACTOR,
    DASH_COOLDOWN,
    BOSS_SHOT_COOLDOWN,
    BOSS_SHOTS,
    ENEMY_BULLET_SPEED,
    ENEMY_BULLET_RADIUS,
    ENEMY_BULLET_LIFETIME,
)


class Enemy:
    def __init__(self, kind, pos, minutes=0, hp_mult=1, speed_mult=1, elite=False):
        stats = ENEMY_TYPES[kind]
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        speed_factor = min(1 + SPEED_GROWTH * minutes, SPEED_FACTOR_MAX)
        self.speed = stats["speed"] * speed_factor * speed_mult
        self.radius = stats["radius"]
        self.color = stats["color"]
        self.hp = max(1, round(stats["hp"] * (1 + HP_GROWTH * minutes) * hp_mult))
        self.xp = stats["xp"]
        self.ai = stats["ai"]
        self.sprite = stats["sprite"]
        self.elite = elite
        if elite:
            self.hp *= ELITE_HP
            self.xp *= 3
            self.radius = int(self.radius * ELITE_SCALE)
        self.max_hp = self.hp
        self.minutes = minutes
        self.anim_time = random.uniform(0, 1)
        self.flash = 0
        self.facing_left = False
        self.shoot_timer = random.uniform(0.5, SHOOTER_COOLDOWN)
        self.dash_state = "walk"
        self.dash_timer = 0
        self.dash_dir = pygame.Vector2(0, 0)
        self.stuck_time = 0
        self.detour_time = 0
        self.detour_dir = pygame.Vector2(0, 0)

    def steer(self, target):
        """Als hij vastzit tegen water of een berg even opzij lopen."""
        if self.detour_time > 0:
            return self.pos + self.detour_dir * 100
        return target

    def check_stuck(self, old_pos, target, dt):
        if self.detour_time > 0:
            self.detour_time -= dt
            return
        # schutters en stormende zwijnen staan soms expres stil
        if self.ai == "shooter" or self.dash_state != "walk":
            self.stuck_time = 0
            return
        moved = self.pos.distance_to(old_pos)
        if moved < self.speed * dt * 0.3 and self.pos.distance_to(target) > self.radius * 3:
            self.stuck_time += dt
        else:
            self.stuck_time = 0
        if self.stuck_time > 0.4:
            self.stuck_time = 0
            self.detour_time = 0.8
            direction = target - self.pos
            if direction.length() == 0:
                return
            # links of rechts om, willekeurig zodat ze niet allemaal dezelfde kant op gaan
            self.detour_dir = direction.normalize().rotate(random.choice([-90, 90]))

    def hurt(self, amount, crit=False):
        self.hp -= amount
        self.flash = 0.1
        effects.damage_text(self.pos, amount, crit)

    def update(self, dt, target):
        """Beweeg richting de speler, geeft een lijst met nieuwe vijandelijke kogels terug."""
        self.anim_time += dt
        self.flash = max(0, self.flash - dt)
        direction = target - self.pos
        distance = direction.length()
        if distance == 0:
            return []
        direction = direction.normalize()
        self.facing_left = direction.x < 0

        if self.ai == "shooter":
            return self.update_shooter(dt, direction, distance)
        if self.ai == "dasher":
            self.update_dasher(dt, direction, distance)
            return []
        self.pos += direction * self.speed * dt
        if self.ai == "boss":
            return self.update_boss(dt)
        return []

    def update_shooter(self, dt, direction, distance):
        if distance > SHOOTER_RANGE:
            self.pos += direction * self.speed * dt
        elif distance < SHOOTER_RANGE - 80:
            self.pos -= direction * self.speed * dt
        self.shoot_timer -= dt
        if self.shoot_timer <= 0 and distance < SHOOTER_RANGE + 120:
            self.shoot_timer = SHOOTER_COOLDOWN
            return [enemy_bullet(self.pos, direction, "enemy_arrow")]
        return []

    def update_dasher(self, dt, direction, distance):
        self.dash_timer -= dt
        if self.dash_state == "walk":
            self.pos += direction * self.speed * dt
            if distance < DASH_RANGE and self.dash_timer <= 0:
                self.dash_state = "windup"
                self.dash_timer = DASH_WINDUP
        elif self.dash_state == "windup":
            if self.dash_timer <= 0:
                self.dash_state = "dash"
                self.dash_timer = DASH_TIME
                self.dash_dir = direction
        elif self.dash_state == "dash":
            self.pos += self.dash_dir * self.speed * DASH_SPEED_FACTOR * dt
            self.facing_left = self.dash_dir.x < 0
            if self.dash_timer <= 0:
                self.dash_state = "walk"
                self.dash_timer = DASH_COOLDOWN

    def update_boss(self, dt):
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = BOSS_SHOT_COOLDOWN
        bullets = []
        start = random.uniform(0, 360)
        for i in range(BOSS_SHOTS):
            direction = pygame.Vector2(1, 0).rotate(start + i * 360 / BOSS_SHOTS)
            bullets.append(enemy_bullet(self.pos, direction, "enemy_orb"))
        return bullets

    def draw(self, screen, camera):
        image = sprites.frame(self.sprite, self.anim_time, 5)
        # sprites kijken naar rechts
        if self.facing_left:
            image = sprites.flipped(image)
        if self.elite:
            image = sprites.scaled(image, ELITE_SCALE)
        if self.flash > 0:
            image = sprites.white(image)

        pos = self.pos - camera
        if self.dash_state == "windup":
            pos += (random.uniform(-2, 2), 0)
        shadow_w = self.radius * 2
        pygame.draw.ellipse(screen, (30, 60, 30), (pos.x - shadow_w / 2, pos.y + image.get_height() / 2 - 8, shadow_w, 10))
        if self.elite:
            pygame.draw.circle(screen, (250, 210, 60), pos, self.radius + 6, 3)
        sprites.draw_centered(screen, image, pos)

        if self.elite and self.hp < self.max_hp:
            width = self.radius * 2
            y = pos.y - image.get_height() / 2 - 8
            pygame.draw.rect(screen, (60, 20, 20), (pos.x - width / 2, y, width, 4))
            pygame.draw.rect(screen, (250, 210, 60), (pos.x - width / 2, y, width * self.hp / self.max_hp, 4))


def enemy_bullet(pos, direction, sprite):
    return Bullet(pos, direction, 0, sprite, ENEMY_BULLET_SPEED, radius=ENEMY_BULLET_RADIUS, life=ENEMY_BULLET_LIFETIME)


def spawn_position(player_pos, world=None):
    # niet in het water of in een berg laten spawnen
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * SPAWN_DISTANCE
        pos = player_pos + offset
        if world is None or not world.is_blocked(pos):
            return pos
    return pos


def spawn_enemy(player_pos, game_time=0, difficulty=None, world=None):
    kinds = []
    weights = []
    for kind, entry in SPAWN_TABLE.items():
        if game_time >= entry["start"]:
            kinds.append(kind)
            weights.append(entry["weight"])
    kind = random.choices(kinds, weights)[0]
    hp_mult = 1
    speed_mult = 1
    if difficulty:
        hp_mult = difficulty["enemy_hp"]
        speed_mult = difficulty["enemy_speed"]
    elite = game_time >= ELITE_START and random.random() < ELITE_CHANCE
    return Enemy(kind, spawn_position(player_pos, world), game_time / 60, hp_mult, speed_mult, elite)


def spawn_boss(player_pos, game_time, difficulty, world=None):
    return Enemy("boss", spawn_position(player_pos, world), game_time / 60, difficulty["enemy_hp"], 1)


def split(enemy, kind, count):
    children = []
    for i in range(count):
        offset = pygame.Vector2(enemy.radius, 0).rotate(i * 360 / count + 45)
        child = Enemy(kind, enemy.pos + offset, enemy.minutes)
        children.append(child)
    return children

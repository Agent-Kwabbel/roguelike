import math
import random

import pygame

import effects
import sound
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
    GHOST_FADE_SPEED,
    EXPLODE_RANGE,
    EXPLODE_FUSE,
    SUMMON_RANGE,
    SUMMON_COOLDOWN,
    SUMMON_COUNT,
    ZIGZAG_WIDTH,
    ZIGZAG_SPEED,
    HEAL_COOLDOWN,
    HEAL_RADIUS,
    HEAL_AMOUNT,
    MIMIC_WAKE,
)


# every enemy gets its own number, so online players know which one is which
next_id = 0


class Enemy:
    def __init__(self, kind, pos, minutes=0, hp_mult=1, speed_mult=1, elite=False):
        global next_id
        next_id += 1
        self.id = next_id
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
        self.fuse = -1
        self.exploded = False
        self.spawned = []
        self.summon_timer = SUMMON_COOLDOWN / 2
        self.heal_timer = HEAL_COOLDOWN
        self.heal_ready = False
        self.heal_flash = 0
        self.awake = self.ai != "mimic"
        self.last_hit = None

    def steer(self, target):
        """Step aside for a bit when stuck against water or a mountain."""
        if self.detour_time > 0:
            return self.pos + self.detour_dir * 100
        return target

    def check_stuck(self, old_pos, target, dt):
        if self.detour_time > 0:
            self.detour_time -= dt
            return
        # shooters and charging boars sometimes stand still on purpose
        if self.ai in ("shooter", "summoner", "healer", "ghost") or self.dash_state != "walk" or not self.awake:
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
            # go around left or right, random so they don't all pick the same side
            self.detour_dir = direction.normalize().rotate(random.choice([-90, 90]))

    def hurt(self, amount, crit=False):
        self.hp -= amount
        self.flash = 0.1
        self.awake = True
        effects.damage_text(self.pos, amount, crit)
        effects.sparks(self.pos)
        sound.play("crit" if crit else "hit")

    def update(self, dt, target):
        """Move towards the player, returns a list of new enemy bullets."""
        self.anim_time += dt
        self.flash = max(0, self.flash - dt)
        self.heal_flash = max(0, self.heal_flash - dt)
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
        if self.ai == "exploder":
            self.update_exploder(dt, direction, distance)
            return []
        if self.ai == "summoner":
            self.update_summoner(dt, direction, distance)
            return []
        if self.ai == "healer":
            self.update_healer(dt, direction, distance)
            return []
        if self.ai == "mimic" and not self.awake:
            self.facing_left = False
            if distance < MIMIC_WAKE:
                self.awake = True
                effects.add_text(self.pos + (0, -30), "It's a mimic!", (240, 80, 80), 26)
                sound.play("mimic")
            return []
        if self.ai == "zigzag":
            side = direction.rotate(90) * math.sin(self.anim_time * ZIGZAG_SPEED) * ZIGZAG_WIDTH
            self.pos += (direction + side).normalize() * self.speed * dt
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
            sound.play("enemy_shoot", 0.7)
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

    def update_exploder(self, dt, direction, distance):
        if self.fuse < 0:
            self.pos += direction * self.speed * dt
            if distance < EXPLODE_RANGE:
                self.fuse = EXPLODE_FUSE
                sound.play("fuse")
            return
        self.pos += direction * self.speed * 0.3 * dt
        self.fuse -= dt
        if self.fuse <= 0:
            self.exploded = True
            self.hp = 0

    def update_summoner(self, dt, direction, distance):
        if distance > SUMMON_RANGE:
            self.pos += direction * self.speed * dt
        elif distance < SUMMON_RANGE - 100:
            self.pos -= direction * self.speed * dt
        self.summon_timer -= dt
        if self.summon_timer <= 0 and distance < SUMMON_RANGE + 200:
            self.summon_timer = SUMMON_COOLDOWN
            for i in range(SUMMON_COUNT):
                offset = pygame.Vector2(40, 0).rotate(i * 360 / SUMMON_COUNT)
                self.spawned.append(Enemy("skeleton", self.pos + offset, self.minutes))
            effects.burst(self.pos, (120, 240, 120), 12)
            sound.play("summon")

    def update_healer(self, dt, direction, distance):
        if distance > 220:
            self.pos += direction * self.speed * dt
        elif distance < 140:
            self.pos -= direction * self.speed * dt
        self.heal_timer -= dt
        if self.heal_timer <= 0:
            self.heal_timer = HEAL_COOLDOWN
            self.heal_ready = True
            self.heal_flash = 0.4

    def update_boss(self, dt):
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = BOSS_SHOT_COOLDOWN
        sound.play("enemy_shoot")
        bullets = []
        start = random.uniform(0, 360)
        for i in range(BOSS_SHOTS):
            direction = pygame.Vector2(1, 0).rotate(start + i * 360 / BOSS_SHOTS)
            bullets.append(enemy_bullet(self.pos, direction, "enemy_orb"))
        return bullets

    def draw(self, screen, camera, frozen=False):
        image = sprites.frame(self.sprite, self.anim_time, 5)
        if not self.awake:
            image = sprites.get("chest")
        # sprites face right
        if self.facing_left:
            image = sprites.flipped(image)
        if self.elite:
            image = sprites.scaled(image, ELITE_SCALE)
        if self.flash > 0 or (self.fuse >= 0 and int(self.fuse * 12) % 2 == 0):
            image = sprites.white(image)
        elif frozen:
            image = sprites.blue(image)
        if self.ai == "ghost":
            alpha = 0.45 + 0.35 * math.sin(self.anim_time * GHOST_FADE_SPEED)
            image = sprites.faded(image, alpha)

        pos = self.pos - camera
        if self.heal_flash > 0:
            radius = HEAL_RADIUS * (1 - self.heal_flash / 0.4)
            pygame.draw.circle(screen, (120, 255, 140), pos, radius, 3)
        if self.dash_state == "windup":
            pos += (random.uniform(-2, 2), 0)
        shadow_w = self.radius * 2
        screen.blit(sprites.shadow(shadow_w), (pos.x - shadow_w / 2, pos.y + image.get_height() / 2 - 8))
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
    # don't spawn in water or inside a mountain
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


def heal_nearby(healer, enemies):
    healer.heal_ready = False
    for enemy in enemies:
        if enemy is healer or enemy.hp <= 0 or enemy.hp >= enemy.max_hp:
            continue
        if healer.pos.distance_to(enemy.pos) < HEAL_RADIUS:
            enemy.hp = min(enemy.max_hp, enemy.hp + HEAL_AMOUNT)
            effects.add_text(enemy.pos + (0, -20), f"+{HEAL_AMOUNT}", (120, 255, 140), 20)


def spawn_kind(kind, player_pos, game_time, difficulty, world=None):
    return Enemy(kind, spawn_position(player_pos, world), game_time / 60, difficulty["enemy_hp"], difficulty["enemy_speed"])


def split(enemy, kind, count):
    children = []
    for i in range(count):
        offset = pygame.Vector2(enemy.radius, 0).rotate(i * 360 / count + 45)
        child = Enemy(kind, enemy.pos + offset, enemy.minutes)
        children.append(child)
    return children

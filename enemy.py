import math
import random

import pygame

import effects
import phases
import sound
import sprites
from bullet import Bullet
from settings import (
    W,
    H,
    ENEMY_TYPES,
    SPAWN_DISTANCE,
    SPAWN_IN_TIME,
    COOP_HP_BONUS,
    COOP_BOSS_HP,
    HP_GROWTH,
    HP_CURVE,
    SPEED_GROWTH,
    SPEED_FACTOR_MAX,
    ELITE_HP,
    ELITE_SCALE,
    ELITE_COLOR,
    AFFIXES,
    SWIFT_SPEED,
    SHIELD_PART,
    VAMPIRE_HEAL,
    BOSS_HP_GROWTH,
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
    BLINK_COOLDOWN,
    BLINK_TELL,
    BLINK_DISTANCE,
    SPIRAL_TIME,
    SPIRAL_REST,
    SPIRAL_STEP,
    CHARGE_WINDUP,
    CHARGE_TIME,
    CHARGE_COOLDOWN,
    CHARGE_SHOTS,
    ENRAGE_HP,
    PUDDLE_INTERVAL,
)


# every enemy gets its own number, so online players know which one is which
next_id = 0


def hp_factor(minutes):
    return 1 + HP_GROWTH * minutes + HP_CURVE * minutes * minutes


class Enemy:
    def __init__(self, kind, pos, minutes=0, hp_mult=1, speed_mult=1, elite=False, affix=None):
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
        self.hp = max(1, round(stats["hp"] * hp_factor(minutes) * hp_mult))
        self.xp = stats["xp"]
        self.ai = stats["ai"]
        self.sprite = stats["sprite"]
        self.armor = stats.get("armor", 0)
        self.shots = stats.get("shots", 1)
        self.pattern = stats.get("pattern", "ring")
        self.makes_puddles = stats.get("puddles", False)
        self.elite = elite
        if elite:
            self.hp *= ELITE_HP
            self.xp *= 3
            self.radius = int(self.radius * ELITE_SCALE)
        self.max_hp = self.hp
        self.affix = affix
        self.shield = 0
        if affix == "swift":
            self.speed *= SWIFT_SPEED
        elif affix == "shielded":
            self.shield = round(self.max_hp * SHIELD_PART)
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
        self.blink_timer = random.uniform(1, BLINK_COOLDOWN)
        self.puddle_timer = PUDDLE_INTERVAL
        self.puddles = []
        self.pattern_timer = 2.0
        self.spiral_angle = 0
        self.can_enrage = False
        self.enraged = False
        self.spawn_time = SPAWN_IN_TIME
        if self.ai == "mimic":
            # a mimic just lies there looking like a chest
            self.spawn_time = 0
        # in co-op a boss chases one player for a while
        self.focus = None
        self.focus_timer = 0

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

    def hurt(self, amount, crit=False, true_damage=False):
        if not true_damage:
            amount = max(1, amount - self.armor)
            if self.shield > 0:
                blocked = min(self.shield, amount)
                self.shield -= blocked
                amount -= blocked
                if self.shield == 0:
                    effects.burst(self.pos, (170, 170, 255), 10)
        self.hp -= amount
        self.flash = 0.1
        self.awake = True
        effects.damage_text(self.pos, amount, crit)
        effects.sparks(self.pos)
        sound.play("crit" if crit else "hit")

    def update(self, dt, target):
        """Move towards the player, returns a list of new enemy bullets."""
        self.anim_time += dt
        if self.spawn_time > 0:
            self.spawn_time -= dt
            return []
        self.flash = max(0, self.flash - dt)
        self.heal_flash = max(0, self.heal_flash - dt)
        direction = target - self.pos
        distance = direction.length()
        if distance == 0:
            return []
        direction = direction.normalize()
        self.facing_left = direction.x < 0

        if self.makes_puddles:
            self.puddle_timer -= dt
            if self.puddle_timer <= 0:
                self.puddle_timer = PUDDLE_INTERVAL
                self.puddles.append(self.pos.copy())
        if self.ai == "boss":
            return self.update_boss(dt, direction, distance)
        if self.ai == "blinker":
            self.update_blinker(dt, direction, distance, target)
            return []
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
            if self.shots == 1:
                return [enemy_bullet(self.pos, direction, "enemy_arrow")]
            bullets = []
            for i in range(self.shots):
                angle = (i - (self.shots - 1) / 2) * 15
                bullets.append(enemy_bullet(self.pos, direction.rotate(angle), "enemy_orb"))
            return bullets
        return []

    def update_blinker(self, dt, direction, distance, target):
        self.pos += direction * self.speed * dt
        self.blink_timer -= dt
        if self.blink_timer > 0:
            return
        self.blink_timer = BLINK_COOLDOWN
        if distance > 550:
            return
        # pops up right next to you, from a random side
        effects.burst(self.pos, self.color, 10)
        side = direction.rotate(random.uniform(-70, 70))
        self.pos = target - side * BLINK_DISTANCE
        effects.burst(self.pos, self.color, 10)
        sound.play("dash")

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

    def update_boss(self, dt, direction, distance):
        if self.can_enrage and not self.enraged and self.hp < self.max_hp * ENRAGE_HP:
            self.enraged = True
            effects.add_text(self.pos + (0, -60), "ENRAGED!", (255, 60, 60), 34)
            sound.play("boss")
        # an angry boss does everything twice as fast
        if self.enraged:
            dt *= 2
        if self.pattern == "charge":
            return self.update_charge(dt, direction, distance)
        self.pos += direction * self.speed * dt
        if self.pattern == "spiral":
            return self.update_spiral(dt)
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = BOSS_SHOT_COOLDOWN
        sound.play("enemy_shoot")
        return ring(self.pos, BOSS_SHOTS, random.uniform(0, 360))

    def update_spiral(self, dt):
        self.pattern_timer -= dt
        if self.pattern_timer <= -SPIRAL_TIME:
            self.pattern_timer = SPIRAL_REST
            # every round a few skeletons come to help
            for i in range(2):
                offset = pygame.Vector2(60, 0).rotate(i * 180 + 90)
                self.spawned.append(Enemy("skeleton", self.pos + offset, self.minutes))
            sound.play("summon")
        if self.pattern_timer > 0:
            return []
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = SPIRAL_STEP
        self.spiral_angle += 17
        sound.play("enemy_shoot", 0.5)
        return ring(self.pos, 3, self.spiral_angle)

    def update_charge(self, dt, direction, distance):
        self.dash_timer -= dt
        if self.dash_state == "walk":
            self.pos += direction * self.speed * dt
            if self.dash_timer <= 0 and distance < 500:
                self.dash_state = "windup"
                self.dash_timer = CHARGE_WINDUP
                effects.add_text(self.pos + (0, -60), "!", (255, 80, 60), 44)
        elif self.dash_state == "windup":
            if self.dash_timer <= 0:
                self.dash_state = "dash"
                self.dash_timer = CHARGE_TIME
                self.dash_dir = direction
        elif self.dash_state == "dash":
            self.pos += self.dash_dir * self.speed * 7 * dt
            self.facing_left = self.dash_dir.x < 0
            if self.dash_timer <= 0:
                self.dash_state = "walk"
                self.dash_timer = CHARGE_COOLDOWN
                effects.shake(10)
                effects.ring(self.pos, (255, 200, 80), 160)
                sound.play("meteor")
                return ring(self.pos, CHARGE_SHOTS, random.uniform(0, 360))
        return []

    def ring_color(self):
        if self.affix:
            return AFFIXES[self.affix]["color"]
        if self.elite:
            return ELITE_COLOR
        return None

    def draw_spawning(self, screen, camera, image):
        # rises out of a dark portal and fades in
        part = 1 - self.spawn_time / SPAWN_IN_TIME
        pos = self.pos - camera
        size = self.radius * 1.4 * min(1, part * 3)
        portal = pygame.Rect(0, 0, size * 2, size)
        portal.center = (pos.x, pos.y + image.get_height() / 2 - 6)
        pygame.draw.ellipse(screen, (40, 15, 60), portal)
        pygame.draw.ellipse(screen, (170, 90, 230), portal, 2)
        image = sprites.scaled(image, round(0.3 + 0.7 * part, 1))
        image = sprites.faded(image, part)
        sprites.draw_centered(screen, image, pos + (0, (1 - part) * 14))

    def draw(self, screen, camera, frozen=False):
        image = sprites.frame(self.sprite, self.anim_time, 5)
        if not self.awake:
            image = sprites.get("chest")
        # sprites face right
        if self.facing_left:
            image = sprites.flipped(image)
        if self.elite:
            image = sprites.scaled(image, ELITE_SCALE)
        blinking = self.ai == "blinker" and self.blink_timer < BLINK_TELL and int(self.blink_timer * 14) % 2 == 0
        if self.flash > 0 or blinking or (self.fuse >= 0 and int(self.fuse * 12) % 2 == 0):
            image = sprites.white(image)
        elif frozen:
            image = sprites.blue(image)
        if self.ai in ("ghost", "blinker"):
            alpha = 0.45 + 0.35 * math.sin(self.anim_time * GHOST_FADE_SPEED)
            image = sprites.faded(image, alpha)
        if self.spawn_time > 0:
            self.draw_spawning(screen, camera, image)
            return

        pos = self.pos - camera
        if self.heal_flash > 0:
            radius = HEAL_RADIUS * (1 - self.heal_flash / 0.4)
            pygame.draw.circle(screen, (120, 255, 140), pos, radius, 3)
        if self.dash_state == "windup":
            pos += (random.uniform(-2, 2), 0)
        shadow_w = self.radius * 2
        screen.blit(sprites.shadow(shadow_w), (pos.x - shadow_w / 2, pos.y + image.get_height() / 2 - 8))
        color = self.ring_color()
        if color:
            pygame.draw.circle(screen, color, pos, self.radius + 6, 3)
        if self.shield > 0:
            pygame.draw.circle(screen, (170, 170, 255), pos, self.radius + 11, 2)
        if self.enraged:
            pygame.draw.circle(screen, (255, 40, 40), pos, self.radius + 8 + math.sin(self.anim_time * 10) * 3, 3)
        sprites.draw_centered(screen, image, pos)

        if self.elite and self.hp < self.max_hp:
            width = self.radius * 2
            y = pos.y - image.get_height() / 2 - 8
            pygame.draw.rect(screen, (60, 20, 20), (pos.x - width / 2, y, width, 4))
            pygame.draw.rect(screen, color, (pos.x - width / 2, y, width * self.hp / self.max_hp, 4))


def enemy_bullet(pos, direction, sprite):
    return Bullet(pos, direction, 0, sprite, ENEMY_BULLET_SPEED, radius=ENEMY_BULLET_RADIUS, life=ENEMY_BULLET_LIFETIME)


def ring(pos, count, start):
    bullets = []
    for i in range(count):
        direction = pygame.Vector2(1, 0).rotate(start + i * 360 / count)
        bullets.append(enemy_bullet(pos, direction, "enemy_orb"))
    return bullets


def on_screen(state, pos):
    """True if any player could see this spot (with a small border)."""
    for player in state["players"]:
        if player.downed:
            continue
        offset = pos - player.pos
        if abs(offset.x) < W / 2 + 60 and abs(offset.y) < H / 2 + 60:
            return True
    return False


def spawn_position(state, center):
    # not in water or a mountain, and not where a teammate can see it pop up
    fallback = None
    for _ in range(16):
        angle = random.uniform(0, 2 * math.pi)
        pos = center + pygame.Vector2(math.cos(angle), math.sin(angle)) * SPAWN_DISTANCE
        if state["world"].is_blocked(pos):
            continue
        if not on_screen(state, pos):
            return pos
        if fallback is None:
            fallback = pos
    if fallback is not None:
        return fallback
    return pos


def coop_mult(state, bonus):
    return 1 + bonus * (len(state["players"]) - 1)


def random_affix():
    return random.choice(list(AFFIXES.keys()))


def random_kind(state):
    enemies = phases.current(state)["enemies"]
    return random.choices(list(enemies.keys()), list(enemies.values()))[0]


def spawn_enemy(state, player_pos):
    elite = random.random() < phases.elite_chance(state)
    affix = None
    if elite and phases.affixes_on(state):
        affix = random_affix()
    pos = spawn_position(state, player_pos)
    return spawn_kind(random_kind(state), pos, state, elite, affix)


def spawn_boss(state, player_pos, kind):
    difficulty = state["difficulty"]
    hp_mult = difficulty["enemy_hp"] * (1 + BOSS_HP_GROWTH * state["boss_count"]) * coop_mult(state, COOP_BOSS_HP)
    affix = None
    if difficulty.get("boss_affix"):
        affix = random_affix()
    pos = spawn_position(state, player_pos)
    boss = Enemy(kind, pos, phases.effective_minutes(state), hp_mult, 1, affix=affix)
    boss.can_enrage = difficulty.get("boss_enrage", False)
    return boss


def heal_nearby(healer, enemies):
    healer.heal_ready = False
    for enemy in enemies:
        if enemy is healer or enemy.hp <= 0 or enemy.hp >= enemy.max_hp:
            continue
        if healer.pos.distance_to(enemy.pos) < HEAL_RADIUS:
            enemy.hp = min(enemy.max_hp, enemy.hp + HEAL_AMOUNT)
            effects.add_text(enemy.pos + (0, -20), f"+{HEAL_AMOUNT}", (120, 255, 140), 20)


def spawn_kind(kind, pos, state, elite=False, affix=None):
    difficulty = state["difficulty"]
    hp_mult = difficulty["enemy_hp"] * coop_mult(state, COOP_HP_BONUS)
    return Enemy(kind, pos, phases.effective_minutes(state), hp_mult, difficulty["enemy_speed"], elite, affix)


def split(enemy, kind, count):
    children = []
    for i in range(count):
        offset = pygame.Vector2(enemy.radius, 0).rotate(i * 360 / count + 45)
        child = Enemy(kind, enemy.pos + offset, enemy.minutes)
        child.spawn_time = 0
        children.append(child)
    return children


def vampire_bite(vampire, enemies):
    """A vampiric elite that hits you heals itself and everything around it."""
    for enemy in enemies:
        if enemy.hp <= 0 or enemy.hp >= enemy.max_hp:
            continue
        if vampire.pos.distance_to(enemy.pos) < HEAL_RADIUS:
            amount = round(enemy.max_hp * VAMPIRE_HEAL)
            enemy.hp = min(enemy.max_hp, enemy.hp + amount)
            effects.add_text(enemy.pos + (0, -20), f"+{amount}", (230, 40, 70), 20)

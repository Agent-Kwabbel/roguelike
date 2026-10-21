import random

import pygame

import effects
import sprites
from settings import (
    PLAYER_SPEED,
    PLAYER_RADIUS,
    PLAYER_MAX_HP,
    INVIS_TIME,
    FIRE_INTERVAL,
    BULLET_DAMAGE,
    PICKUP_RANGE,
    XP_BASE,
    XP_GROWTH,
    PLAYER_SPRITE,
    BULLET_SPRITE,
    CRIT_MULTIPLIER,
    REGEN_TIME,
    BOOTS_SPEED,
    DASH_SPEED,
    DASH_DURATION,
    DASH_COOLDOWN_PLAYER,
)
from weapons import Wand


class Player:
    def __init__(self, max_hp=PLAYER_MAX_HP, sprite=PLAYER_SPRITE, bullet_sprite=BULLET_SPRITE):
        self.pos = pygame.Vector2(0, 0)
        self.move = pygame.Vector2(0, 0)
        self.facing = pygame.Vector2(1, 0)
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.max_hp = max_hp
        self.hp = max_hp
        self.fire_interval = FIRE_INTERVAL
        self.damage = BULLET_DAMAGE
        self.pickup_range = PICKUP_RANGE
        self.crit_chance = 0.05
        self.multishot = 0
        self.pierce = 0
        self.regen = 0
        self.regen_timer = 0
        self.armor = 0
        self.xp_mult = 1
        self.luck = 1
        self.invis_timer = 0
        self.xp = 0
        self.level = 1
        self.pending_upgrades = 0
        self.sprite = sprite
        self.bullet_sprite = bullet_sprite
        self.weapons = [Wand()]
        self.anim_time = 0
        self.lifesteal = 0
        self.thorns = 0
        self.can_dash = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.boots_timer = 0
        self.potion_timer = 0
        self.still_time = 0

    def read_input(self):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1

        if move.length() > 0:
            move = move.normalize()
            self.facing = move
        self.move = move

    def dash(self):
        if not self.can_dash or self.dash_cooldown > 0:
            return
        self.dash_timer = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN_PLAYER
        self.invis_timer = max(self.invis_timer, DASH_DURATION + 0.1)
        effects.burst(self.pos, (200, 220, 255), 8)

    def update(self, dt):
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.boots_timer = max(0, self.boots_timer - dt)
        self.potion_timer = max(0, self.potion_timer - dt)
        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.pos += self.facing * DASH_SPEED * dt
        elif self.boots_timer > 0:
            self.pos += self.move * self.speed * BOOTS_SPEED * dt
            if self.move.length() > 0 and random.random() < 0.3:
                effects.burst(self.pos + (0, 16), (255, 220, 80), 1)
        else:
            self.pos += self.move * self.speed * dt
        self.invis_timer = max(0, self.invis_timer - dt)
        if self.move.length() > 0:
            self.anim_time += dt
            self.still_time = 0
        else:
            self.still_time += dt
        if self.regen > 0 and self.hp < self.max_hp:
            self.regen_timer += dt * self.regen
            if self.regen_timer >= REGEN_TIME:
                self.regen_timer = 0
                self.hp += 1
                effects.add_text(self.pos + (0, -24), "+1", (120, 240, 120))

    def take_damage(self, amount):
        """Geeft True als de klap echt aankwam (ook als hij geblokt werd)."""
        if self.invis_timer > 0:
            return False
        self.invis_timer = INVIS_TIME
        if random.random() < self.armor:
            effects.add_text(self.pos + (0, -24), "Geblokt", (140, 190, 255))
            return True
        self.hp -= amount
        effects.burst(self.pos, (220, 40, 40), 10)
        effects.shake(6)
        return True

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def roll_damage(self, damage):
        if random.random() < self.crit_chance:
            return damage * CRIT_MULTIPLIER, True
        return damage, False

    def xp_needed(self):
        return XP_BASE + (self.level - 1) * XP_GROWTH

    def add_xp(self, amount):
        if self.potion_timer > 0:
            amount *= 2
        self.xp += amount * self.xp_mult
        while self.xp >= self.xp_needed():
            self.xp -= self.xp_needed()
            self.level += 1
            self.pending_upgrades += 1

    def has_weapon(self, key):
        for weapon in self.weapons:
            if weapon.key == key:
                return True
        return False

    def update_weapons(self, dt, enemies):
        bullets = []
        for weapon in self.weapons:
            bullets += weapon.update(dt, self, enemies)
        return bullets

    def draw(self, screen, camera):
        for weapon in self.weapons:
            weapon.draw(screen, camera, self)
        # knipperen tijdens invis frames
        if self.invis_timer > 0 and int(self.invis_timer * 10) % 2 == 0:
            return
        pos = self.pos - camera
        image = sprites.frame(self.sprite, self.anim_time, 8)
        if self.facing.x < 0:
            image = sprites.flipped(image)
        if self.dash_timer > 0:
            sprites.draw_centered(screen, sprites.faded(image, 0.3), pos - self.facing * 20)
            sprites.draw_centered(screen, sprites.faded(image, 0.5), pos - self.facing * 10)

        pygame.draw.ellipse(screen, (30, 60, 30), (pos.x - 14, pos.y + image.get_height() / 2 - 8, 28, 10))
        sprites.draw_centered(screen, image, pos)

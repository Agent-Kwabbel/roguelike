import random

import pygame

import effects
import sound
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
    XP_CURVE,
    PLAYER_SPRITE,
    BULLET_SPRITE,
    CRIT_MULTIPLIER,
    REGEN_TIME,
    BOOTS_SPEED,
    DASH_SPEED,
    DASH_DURATION,
    DASH_COOLDOWN_PLAYER,
    REVIVE_TIME,
    TEAM_COOLDOWN,
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
        # heal 1 hp every so many kills, 0 means no lifesteal
        self.lifesteal_kills = 0
        self.kill_counter = 0
        self.cooldown = 1
        self.area = 1
        self.chest_upgrades = 0
        self.bonus_coins = 0
        self.streak = 0
        self.streak_timer = 0
        self.best_streak = 0
        # co-op
        self.coop = False
        self.team_bonus = False
        self.team_timer = 0
        self.revives = 0
        self.revive_speed = 1
        self.medic = 0
        self.medic_timer = 0
        self.bond = 0
        # a boss is chasing this player
        self.hunted = False
        self.thorns = 0
        self.can_dash = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.boots_timer = 0
        self.potion_timer = 0
        self.still_time = 0
        # online co-op
        self.id = 0
        self.name = "Player 1"
        self.color = (255, 255, 255)
        self.remote = False
        self.downed = False
        self.revive_timer = 0
        self.choices = None
        self.choice_timer = 0

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
            return False
        self.dash_timer = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN_PLAYER
        self.invis_timer = max(self.invis_timer, DASH_DURATION + 0.1)
        effects.burst(self.pos, (200, 220, 255), 8)
        sound.play("dash")
        return True

    def update(self, dt):
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.boots_timer = max(0, self.boots_timer - dt)
        self.potion_timer = max(0, self.potion_timer - dt)
        self.invis_timer = max(0, self.invis_timer - dt)
        if self.downed:
            self.move = pygame.Vector2(0, 0)
            return
        if self.remote:
            # online players move on their own computer, the host only gets the position
            if self.move.length() > 0:
                self.anim_time += dt
            self.update_regen(dt)
            return
        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.pos += self.facing * DASH_SPEED * dt
            effects.dust(self.pos + (0, 16), 2)
        elif self.boots_timer > 0:
            self.pos += self.move * self.speed * BOOTS_SPEED * dt
            if self.move.length() > 0 and random.random() < 0.3:
                effects.burst(self.pos + (0, 16), (255, 220, 80), 1)
        else:
            self.pos += self.move * self.speed * dt
        if self.move.length() > 0:
            self.anim_time += dt
            self.still_time = 0
            if random.random() < 6 * dt:
                effects.dust(self.pos + (0, 16))
        else:
            self.still_time += dt
        self.update_regen(dt)

    def update_regen(self, dt):
        if self.regen > 0 and self.hp < self.max_hp:
            self.regen_timer += dt * self.regen
            if self.regen_timer >= REGEN_TIME:
                self.regen_timer = 0
                self.hp += 1
                effects.add_text(self.pos + (0, -24), "+1", (120, 240, 120))

    def take_damage(self, amount, unblockable=False):
        """Returns True if the hit really landed (also when it was blocked)."""
        if self.downed:
            return False
        if self.invis_timer > 0 and not unblockable:
            return False
        self.invis_timer = INVIS_TIME
        if random.random() < self.armor and not unblockable:
            effects.add_text(self.pos + (0, -24), "Blocked", (140, 190, 255))
            sound.play("blocked")
            return True
        self.hp -= amount
        effects.burst(self.pos, (220, 40, 40), 10)
        # online players get the shake and sound on their own computer
        if not self.remote:
            effects.shake(6, local=True)
            sound.play_local("hurt")
        return True

    def cooldown_factor(self):
        if self.team_bonus:
            return self.cooldown * (TEAM_COOLDOWN - 0.05 * self.bond)
        return self.cooldown

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def roll_damage(self, damage):
        if random.random() < self.crit_chance:
            return damage * CRIT_MULTIPLIER, True
        return damage, False

    def xp_needed(self):
        level = self.level - 1
        return XP_BASE + level * XP_GROWTH + XP_CURVE * level * level

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

    def draw(self, screen, camera, name_tag=False):
        if self.downed:
            self.draw_downed(screen, camera)
            return
        if name_tag:
            pos = self.pos - camera
            pygame.draw.circle(screen, self.color, (pos.x, pos.y + 18), 16, 2)
            draw_name(screen, self.name, self.color, (pos.x, pos.y - 42))
        for weapon in self.weapons:
            weapon.draw(screen, camera, self)
        # blink during invincibility frames
        if self.invis_timer > 0 and int(self.invis_timer * 10) % 2 == 0:
            return
        pos = self.pos - camera
        image = sprites.frame(self.sprite, self.anim_time, 8)
        if self.facing.x < 0:
            image = sprites.flipped(image)
        if self.dash_timer > 0:
            sprites.draw_centered(screen, sprites.faded(image, 0.3), pos - self.facing * 20)
            sprites.draw_centered(screen, sprites.faded(image, 0.5), pos - self.facing * 10)

        screen.blit(sprites.shadow(28), (pos.x - 14, pos.y + image.get_height() / 2 - 8))
        sprites.draw_centered(screen, image, pos)

    def draw_downed(self, screen, camera):
        pos = self.pos - camera
        image = sprites.frame(self.sprite, 0, 8)
        image = sprites.faded(pygame.transform.rotate(image, 90), 0.6)
        screen.blit(sprites.shadow(28), (pos.x - 14, pos.y + 6))
        sprites.draw_centered(screen, image, pos)
        pygame.draw.circle(screen, (240, 80, 80), pos, 30, 2)
        if self.revive_timer > 0:
            rect = pygame.Rect(pos.x - 30, pos.y - 30, 60, 60)
            angle = self.revive_timer / REVIVE_TIME * 6.283
            pygame.draw.arc(screen, (120, 240, 120), rect, 1.571, 1.571 + angle, 4)
        draw_name(screen, self.name, (240, 80, 80), (pos.x, pos.y - 46))


def draw_name(screen, name, color, pos):
    image = sprites.font(18).render(name, True, color)
    shadow = sprites.font(18).render(name, True, (0, 0, 0))
    screen.blit(shadow, (pos[0] - image.get_width() / 2 + 1, pos[1] + 1))
    screen.blit(image, (pos[0] - image.get_width() / 2, pos[1]))

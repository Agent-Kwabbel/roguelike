import pygame

from settings import (
    PLAYER_SPEED,
    PLAYER_RADIUS,
    PLAYER_MAX_HP,
    INVIS_TIME,
    FIRE_INTERVAL,
    FIRE_RANGE,
)
from bullet import Bullet


class Player:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.move = pygame.Vector2(0, 0)
        self.radius = PLAYER_RADIUS
        self.hp = PLAYER_MAX_HP
        self.invis_timer = 0
        self.fire_timer = 0

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
        self.move = move

    def update(self, dt):
        self.pos += self.move * PLAYER_SPEED * dt
        self.invis_timer = max(0, self.invis_timer - dt)
        self.fire_timer = max(0, self.fire_timer - dt)

    def take_damage(self, amount):
        if self.invis_timer > 0:
            return
        self.hp -= amount
        self.invis_timer = INVIS_TIME

    def shoot(self, enemies):
        if self.fire_timer > 0:
            return None
        target = None
        best = FIRE_RANGE
        for enemy in enemies:
            distance = self.pos.distance_to(enemy.pos)
            if distance < best:
                best = distance
                target = enemy
        if target is None:
            return None
        self.fire_timer = FIRE_INTERVAL
        direction = (target.pos - self.pos).normalize()
        return Bullet(self.pos, direction)

    def draw(self, screen, camera):
        # knipperen tijdens invis frames
        if self.invis_timer > 0 and int(self.invis_timer * 10) % 2 == 0:
            return
        pygame.draw.circle(screen, (60, 120, 220), self.pos - camera, self.radius)

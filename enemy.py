import math
import random

import pygame

from settings import ENEMY_TYPES, SPAWN_DISTANCE


class Enemy:
    def __init__(self, kind, pos):
        stats = ENEMY_TYPES[kind]
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.speed = stats["speed"]
        self.radius = stats["radius"]
        self.color = stats["color"]
        self.hp = stats["hp"]
        self.xp = stats["xp"]

    def update(self, dt, target):
        direction = target - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed * dt

    def draw(self, screen, camera):
        pygame.draw.circle(screen, self.color, self.pos - camera, self.radius)


def spawn_enemy(player_pos):
    angle = random.uniform(0, 2 * math.pi)
    offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * SPAWN_DISTANCE
    kind = random.choice(list(ENEMY_TYPES))
    return Enemy(kind, player_pos + offset)

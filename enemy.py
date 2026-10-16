import math
import random

import pygame

from settings import (
    ENEMY_TYPES,
    SPAWN_DISTANCE,
    SPAWN_TABLE,
    HP_GROWTH,
    SPEED_GROWTH,
    SPEED_FACTOR_MAX,
)


class Enemy:
    def __init__(self, kind, pos, minutes=0):
        stats = ENEMY_TYPES[kind]
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        speed_factor = min(1 + SPEED_GROWTH * minutes, SPEED_FACTOR_MAX)
        self.speed = stats["speed"] * speed_factor
        self.radius = stats["radius"]
        self.color = stats["color"]
        self.hp = round(stats["hp"] * (1 + HP_GROWTH * minutes))
        self.xp = stats["xp"]

    def update(self, dt, target):
        direction = target - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed * dt

    def draw(self, screen, camera):
        pygame.draw.circle(screen, self.color, self.pos - camera, self.radius)


def spawn_enemy(player_pos, game_time=0):
    angle = random.uniform(0, 2 * math.pi)
    offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * SPAWN_DISTANCE

    kinds = []
    weights = []
    for kind, entry in SPAWN_TABLE.items():
        if game_time >= entry["start"]:
            kinds.append(kind)
            weights.append(entry["weight"])
    kind = random.choices(kinds, weights)[0]
    return Enemy(kind, player_pos + offset, game_time / 60)

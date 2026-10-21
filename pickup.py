import math
import random

import pygame

import sprites
from settings import PICKUP_RADIUS, PICKUP_LIFETIME, PICKUP_DROP_CHANCE, PICKUP_WEIGHTS


class Pickup:
    def __init__(self, kind, pos):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.radius = PICKUP_RADIUS
        self.life = PICKUP_LIFETIME
        if kind == "chest":
            # kisten blijven liggen
            self.life = 9999

    def update(self, dt):
        self.life -= dt

    def draw(self, screen, camera, time):
        # knipperen als hij bijna verdwijnt
        if self.life < 5 and int(self.life * 8) % 2 == 0:
            return
        bob = math.sin(time * 3 + self.pos.y) * 3
        pos = self.pos - camera
        pygame.draw.ellipse(screen, (30, 60, 30), (pos.x - 12, pos.y + 12, 24, 8))
        sprites.draw_centered(screen, sprites.get(self.kind), pos + (0, bob))


def random_drop(pos, luck):
    if random.random() > PICKUP_DROP_CHANCE * luck:
        return None
    kinds = list(PICKUP_WEIGHTS.keys())
    weights = list(PICKUP_WEIGHTS.values())
    return Pickup(random.choices(kinds, weights)[0], pos)

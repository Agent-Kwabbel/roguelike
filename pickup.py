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
            # chests stay around
            self.life = 9999

    def update(self, dt):
        self.life -= dt

    def draw(self, screen, camera, time):
        # blink when it's about to disappear
        if self.life < 5 and int(self.life * 8) % 2 == 0:
            return
        bob = math.sin(time * 3 + self.pos.y) * 3
        pos = self.pos - camera
        screen.blit(sprites.shadow(24), (pos.x - 12, pos.y + 12))
        sprites.draw_glow(screen, 22 + bob, (255, 230, 150), pos + (0, bob))
        sprites.draw_centered(screen, sprites.get(self.kind), pos + (0, bob))


def random_drop(pos, luck):
    if random.random() > PICKUP_DROP_CHANCE * luck:
        return None
    kinds = list(PICKUP_WEIGHTS.keys())
    weights = list(PICKUP_WEIGHTS.values())
    return Pickup(random.choices(kinds, weights)[0], pos)

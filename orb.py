import math

import pygame

import sprites
from settings import ORB_RADIUS


class Orb:
    def __init__(self, pos, value):
        self.pos = pygame.Vector2(pos)
        self.value = value
        self.radius = ORB_RADIUS
        self.magnet = False
        if value >= 20:
            self.sprite = "gem_red"
        elif value >= 3:
            self.sprite = "gem_big"
        else:
            self.sprite = "gem_small"

    def update(self, dt, target, pickup_range):
        direction = target - self.pos
        if direction.length() == 0:
            return
        if self.magnet:
            self.pos += direction.normalize() * 600 * dt
        elif direction.length() < pickup_range:
            self.pos += direction.normalize() * 300 * dt

    def draw(self, screen, camera, time):
        bob = math.sin(time * 4 + self.pos.x) * 2
        sprites.draw_centered(screen, sprites.get(self.sprite), self.pos - camera + (0, bob))

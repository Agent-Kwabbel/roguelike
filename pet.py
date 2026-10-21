import math

import pygame

import sprites

PET_RANGE = 160


class Pet:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos) + (30, 0)
        self.time = 0

    def update(self, dt, player, orbs):
        self.time += dt
        # loopt een stukje achter de speler aan
        target = player.pos - player.facing * 40
        self.pos += (target - self.pos) * min(1, 5 * dt)
        for orb in orbs:
            if orb.pos.distance_to(self.pos) < PET_RANGE:
                orb.magnet = True

    def draw(self, screen, camera):
        bob = math.sin(self.time * 6) * 3
        image = sprites.frame("pet", self.time, 4)
        pos = self.pos - camera
        pygame.draw.ellipse(screen, (30, 60, 30), (pos.x - 10, pos.y + 8, 20, 6))
        sprites.draw_centered(screen, image, pos + (0, bob))

import pygame

from settings import ORB_RADIUS, ORB_COLOR


class Orb:
    def __init__(self, pos, value):
        self.pos = pygame.Vector2(pos)
        self.value = value
        self.radius = ORB_RADIUS

    def update(self, dt, target, pickup_range):
        direction = target - self.pos
        if 0 < direction.length() < pickup_range:
            self.pos += direction.normalize() * 300 * dt

    def draw(self, screen, camera):
        pygame.draw.circle(screen, ORB_COLOR, self.pos - camera, self.radius)

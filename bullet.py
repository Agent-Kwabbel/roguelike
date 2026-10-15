import pygame

from settings import BULLET_SPEED, BULLET_RADIUS, BULLET_LIFETIME


class Bullet:
    def __init__(self, pos, direction, damage):
        self.pos = pygame.Vector2(pos)
        self.velocity = direction * BULLET_SPEED
        self.radius = BULLET_RADIUS
        self.damage = damage
        self.life = BULLET_LIFETIME

    def update(self, dt):
        self.pos += self.velocity * dt
        self.life -= dt

    def draw(self, screen, camera):
        pygame.draw.circle(screen, (250, 240, 120), self.pos - camera, self.radius)

import pygame

import sprites
from settings import BULLET_SPEED, BULLET_RADIUS, BULLET_LIFETIME, BULLET_SPRITE


class Bullet:
    def __init__(self, pos, direction, damage, sprite=BULLET_SPRITE, speed=BULLET_SPEED,
                 pierce=0, radius=BULLET_RADIUS, life=BULLET_LIFETIME, crit=False):
        self.pos = pygame.Vector2(pos)
        self.velocity = direction * speed
        self.radius = radius
        self.damage = damage
        self.life = life
        self.sprite = sprite
        self.pierce = pierce
        self.crit = crit
        self.hit = []
        self.owner = None
        self.trail = []

    def update(self, dt):
        self.trail.append(self.pos.copy())
        if len(self.trail) > 3:
            self.trail.pop(0)
        self.pos += self.velocity * dt
        self.life -= dt

    def hit_enemy(self, enemy):
        """Returns False if this bullet already hit the enemy before."""
        if enemy in self.hit:
            return False
        self.hit.append(enemy)
        if self.pierce > 0:
            self.pierce -= 1
        else:
            self.life = 0
        return True

    def draw(self, screen, camera):
        image = sprites.get(self.sprite)
        angle = -self.velocity.as_polar()[1]
        for i, pos in enumerate(self.trail):
            ghost = sprites.faded(image, 0.15 + i * 0.12)
            sprites.draw_centered(screen, sprites.rotated(ghost, angle), pos - camera)
        sprites.draw_centered(screen, sprites.rotated(image, angle), self.pos - camera)

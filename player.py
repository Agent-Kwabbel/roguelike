import pygame

from settings import PLAYER_SPEED, PLAYER_RADIUS


class Player:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.move = pygame.Vector2(0, 0)

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

    def draw(self, screen, camera):
        pygame.draw.circle(screen, (60, 120, 220), self.pos - camera, PLAYER_RADIUS)

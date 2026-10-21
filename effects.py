import math
import random

import pygame

import sprites

texts = []
particles = []


def clear():
    texts.clear()
    particles.clear()


def add_text(pos, text, color=(255, 255, 255), size=22):
    texts.append({"pos": pygame.Vector2(pos), "text": str(text), "color": color, "size": size, "life": 0.7})


def damage_text(pos, amount, crit):
    offset = pygame.Vector2(random.uniform(-8, 8), -10)
    if crit:
        add_text(pos + offset, f"{amount}!", (255, 210, 60), 28)
    else:
        add_text(pos + offset, amount)


def burst(pos, color, count=8):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 180)
        velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        particles.append({"pos": pygame.Vector2(pos), "vel": velocity, "color": color, "life": random.uniform(0.3, 0.6)})


def update(dt):
    for text in texts:
        text["pos"].y -= 40 * dt
        text["life"] -= dt
    for particle in particles:
        particle["pos"] += particle["vel"] * dt
        particle["vel"] *= 0.9
        particle["life"] -= dt
    texts[:] = [t for t in texts if t["life"] > 0]
    particles[:] = [p for p in particles if p["life"] > 0]


def draw(screen, camera):
    for particle in particles:
        x, y = particle["pos"] - camera
        size = 3 + int(particle["life"] * 6)
        pygame.draw.rect(screen, particle["color"], (x, y, size, size))
    for text in texts:
        image = sprites.font(text["size"]).render(text["text"], True, text["color"])
        shadow = sprites.font(text["size"]).render(text["text"], True, (0, 0, 0))
        x, y = text["pos"] - camera
        screen.blit(shadow, (x - image.get_width() / 2 + 2, y + 2))
        screen.blit(image, (x - image.get_width() / 2, y))

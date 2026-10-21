import math
import random

import pygame

import config
import sprites

texts = []
particles = []
rings = []
banners = []
shaking = 0
# in an online game the host writes effects in here, they get sent to the other players
outbox = None


def clear():
    global shaking
    texts.clear()
    particles.clear()
    rings.clear()
    banners.clear()
    shaking = 0


def record(name, *args):
    if outbox is None:
        return
    values = []
    for value in args:
        if isinstance(value, pygame.Vector2):
            value = [round(value.x), round(value.y)]
        values.append(value)
    outbox.append([name] + values)


def replay(items):
    functions = {"shake": shake, "announce": announce, "add_text": add_text, "burst": burst,
                 "sparks": sparks, "ring": ring}
    for item in items:
        functions[item[0]](*item[1:])


def shake(amount, local=False):
    global shaking
    if not local:
        record("shake", amount)
    if not config.get("screen_shake"):
        return
    shaking = max(shaking, amount)


def shake_offset():
    if shaking <= 0:
        return pygame.Vector2(0, 0)
    return pygame.Vector2(random.uniform(-shaking, shaking), random.uniform(-shaking, shaking))


def announce(text, color=(255, 220, 60), size=64):
    # big text in the middle of the screen, old banners slide away
    record("announce", text, color, size)
    banners.clear()
    banners.append({"text": text, "color": color, "size": size, "life": 1.6})


def add_text(pos, text, color=(255, 255, 255), size=22):
    record("add_text", pygame.Vector2(pos), str(text), color, size)
    texts.append({"pos": pygame.Vector2(pos), "text": str(text), "color": color, "size": size, "life": 0.7})


def add_particle(pos, velocity, color, life, size=4, gravity=0):
    # not too many, otherwise it starts to stutter
    if len(particles) > 600:
        return
    particles.append({"pos": pygame.Vector2(pos), "vel": velocity, "color": color, "life": life,
                      "max_life": life, "size": size, "gravity": gravity})


def damage_text(pos, amount, crit):
    offset = pygame.Vector2(random.uniform(-8, 8), -10)
    if crit:
        add_text(pos + offset, f"{amount}!", (255, 210, 60), 28)
    else:
        add_text(pos + offset, amount)


def burst(pos, color, count=8):
    record("burst", pygame.Vector2(pos), color, count)
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 180)
        velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        add_particle(pos, velocity, color, random.uniform(0.3, 0.6), random.randint(3, 6), 200)


def sparks(pos, color=(255, 240, 180)):
    record("sparks", pygame.Vector2(pos), color)
    for _ in range(3):
        velocity = pygame.Vector2(random.uniform(120, 260), 0).rotate(random.uniform(0, 360))
        add_particle(pos, velocity, color, random.uniform(0.1, 0.25), 2)


def dust(pos, amount=1):
    for _ in range(amount):
        velocity = pygame.Vector2(random.uniform(-25, 25), random.uniform(-30, -5))
        add_particle(pos + (random.uniform(-6, 6), 0), velocity, (200, 190, 160), random.uniform(0.3, 0.5), 4)


def ring(pos, color=(255, 255, 255), radius=40):
    record("ring", pygame.Vector2(pos), color, radius)
    rings.append({"pos": pygame.Vector2(pos), "color": color, "radius": radius, "life": 0.25})


def update(dt):
    global shaking
    shaking = max(0, shaking - 30 * dt)
    for banner in banners:
        banner["life"] -= dt
    banners[:] = [b for b in banners if b["life"] > 0]
    for text in texts:
        text["pos"].y -= 40 * dt
        text["life"] -= dt
    for particle in particles:
        particle["pos"] += particle["vel"] * dt
        particle["vel"] *= 0.9
        particle["vel"].y += particle["gravity"] * dt
        particle["life"] -= dt
    for item in rings:
        item["life"] -= dt
    texts[:] = [t for t in texts if t["life"] > 0]
    particles[:] = [p for p in particles if p["life"] > 0]
    rings[:] = [r for r in rings if r["life"] > 0]


def draw(screen, camera):
    for item in rings:
        grow = 1 - item["life"] / 0.25
        width = max(1, int(item["life"] * 20))
        pygame.draw.circle(screen, item["color"], item["pos"] - camera, item["radius"] * (0.3 + grow), width)
    for particle in particles:
        pos = particle["pos"] - camera
        size = max(1, particle["size"] * particle["life"] / particle["max_life"])
        pygame.draw.circle(screen, particle["color"], pos, size)
    for text in texts:
        # big for a moment, then normal
        size = text["size"]
        if text["life"] > 0.6:
            size = int(size * 1.4)
        image = sprites.font(size).render(text["text"], True, text["color"])
        shadow = sprites.font(size).render(text["text"], True, (0, 0, 0))
        x, y = text["pos"] - camera
        screen.blit(shadow, (x - image.get_width() / 2 + 2, y + 2))
        screen.blit(image, (x - image.get_width() / 2, y))


def draw_banners(screen):
    for banner in banners:
        # big for a moment, then normal
        grow = 1 + max(0, banner["life"] - 1.4) * 2
        size = int(banner["size"] * grow)
        image = sprites.font(size).render(banner["text"], True, banner["color"])
        shadow = sprites.font(size).render(banner["text"], True, (0, 0, 0))
        if banner["life"] < 0.4:
            image.set_alpha(int(banner["life"] / 0.4 * 255))
            shadow.set_alpha(int(banner["life"] / 0.4 * 255))
        x = screen.get_width() / 2 - image.get_width() / 2
        screen.blit(shadow, (x + 3, 163))
        screen.blit(image, (x, 160))

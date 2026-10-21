import os

import pygame

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

images = {}
cache = {}
fonts = {}


def load_all():
    """Laad alle plaatjes uit assets/, aanroepen na pygame.display.set_mode."""
    for root, _, names in os.walk(ASSETS):
        for name in names:
            if name.endswith(".png"):
                image = pygame.image.load(os.path.join(root, name)).convert_alpha()
                images[name[:-4]] = image


def get(name):
    if name in images:
        return images[name]
    # sprites met animatie heten naam_0, naam_1
    if name + "_0" in images:
        return images[name + "_0"]
    return images["bullet_default"]


def frame(name, time, speed=6):
    key = f"{name}_{int(time * speed) % 2}"
    if key in images:
        return images[key]
    return get(name)


def flipped(image):
    key = ("flip", image)
    if key not in cache:
        cache[key] = pygame.transform.flip(image, True, False)
    return cache[key]


def scaled(image, factor):
    key = ("scale", image, factor)
    if key not in cache:
        size = (int(image.get_width() * factor), int(image.get_height() * factor))
        cache[key] = pygame.transform.scale(image, size)
    return cache[key]


def rotated(image, angle):
    # afronden op 10 graden zodat de cache klein blijft
    angle = round(angle / 10) * 10
    key = ("rotate", image, angle)
    if key not in cache:
        cache[key] = pygame.transform.rotate(image, angle)
    return cache[key]


def white(image):
    key = ("white", image)
    if key not in cache:
        copy = image.copy()
        copy.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        cache[key] = copy
    return cache[key]


def font(size):
    if size not in fonts:
        fonts[size] = pygame.font.Font(None, size)
    return fonts[size]


def draw_centered(screen, image, pos):
    screen.blit(image, (pos[0] - image.get_width() / 2, pos[1] - image.get_height() / 2))

import os

import pygame

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

images = {}
cache = {}
fonts = {}


def load_all():
    """Load all images from assets/, call after pygame.display.set_mode."""
    for root, _, names in os.walk(ASSETS):
        for name in names:
            if name.endswith(".png"):
                image = pygame.image.load(os.path.join(root, name)).convert_alpha()
                images[name[:-4]] = image


def get(name):
    if name in images:
        return images[name]
    # animated sprites are called name_0, name_1
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
    # round to 10 degrees so the cache stays small
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


def blue(image):
    key = ("blue", image)
    if key not in cache:
        copy = image.copy()
        copy.fill((120, 160, 255), special_flags=pygame.BLEND_RGB_MULT)
        copy.fill((40, 60, 90), special_flags=pygame.BLEND_RGB_ADD)
        cache[key] = copy
    return cache[key]


def faded(image, alpha):
    # alpha from 0 to 1, rounded so the cache stays small
    alpha = round(alpha * 10) / 10
    key = ("fade", image, alpha)
    if key not in cache:
        copy = image.copy()
        copy.fill((255, 255, 255, int(alpha * 255)), special_flags=pygame.BLEND_RGBA_MULT)
        cache[key] = copy
    return cache[key]


def font(size):
    if size not in fonts:
        fonts[size] = pygame.font.Font(None, size)
    return fonts[size]


def draw_centered(screen, image, pos):
    screen.blit(image, (pos[0] - image.get_width() / 2, pos[1] - image.get_height() / 2))


def shadow(width):
    width = int(width)
    key = ("shadow", width)
    if key not in cache:
        surface = pygame.Surface((width, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (0, 0, 0, 80), surface.get_rect())
        cache[key] = surface
    return cache[key]


def glow(radius, color):
    # soft circle, draw with BLEND_RGB_ADD
    radius = int(radius)
    key = ("glow", radius, color)
    if key not in cache:
        surface = pygame.Surface((radius * 2, radius * 2))
        steps = 8
        for i in range(steps):
            strength = (i + 1) / steps / 3
            c = (int(color[0] * strength), int(color[1] * strength), int(color[2] * strength))
            pygame.draw.circle(surface, c, (radius, radius), radius * (steps - i) / steps)
        cache[key] = surface
    return cache[key]


def draw_glow(screen, radius, color, pos):
    image = glow(radius, color)
    screen.blit(image, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_RGB_ADD)

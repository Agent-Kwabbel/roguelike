import math
import random

import pygame

import config
import sprites
from settings import W, H, TILE, DAY_LENGTH

# everything here is atmosphere: cloud shadows, fluff, fireflies, glints on the water
MARGIN = 60
SPAN_W = W + MARGIN * 2
SPAN_H = H + MARGIN * 2
CLOUD_SPAN_W = 2400
CLOUD_SPAN_H = 1800
WIND = pygame.Vector2(18, 6)

clouds = []
motes = []
glints = []
state = {"time": 0, "glint_timer": 0}
vignette = None


def darkness(time):
    phase = (time % DAY_LENGTH) / DAY_LENGTH
    return max(0, -math.cos(phase * 2 * math.pi))


def make_cloud(rng):
    width = rng.randint(260, 460)
    height = int(width * rng.uniform(0.45, 0.65))
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(7):
        w = rng.randint(width // 3, width // 2)
        h = rng.randint(height // 3, height // 2 + 10)
        x = rng.randint(0, width - w)
        y = rng.randint(0, height - h)
        pygame.draw.ellipse(surface, (0, 0, 0, 40), (x, y, w, h))
    # soften by scaling down and back up
    small = pygame.transform.smoothscale(surface, (width // 8, height // 8))
    return pygame.transform.smoothscale(small, (width, height))


def make_vignette():
    small = pygame.Surface((48, 32), pygame.SRCALPHA)
    for x in range(48):
        for y in range(32):
            dx = (x - 23.5) / 24
            dy = (y - 15.5) / 16
            distance = math.hypot(dx, dy)
            alpha = max(0, min(150, int((distance - 0.6) * 260)))
            small.set_at((x, y), (5, 0, 15, alpha))
    return pygame.transform.smoothscale(small, (W, H))


def init():
    global vignette
    rng = random.Random(5)
    for _ in range(7):
        pos = pygame.Vector2(rng.uniform(0, CLOUD_SPAN_W), rng.uniform(0, CLOUD_SPAN_H))
        clouds.append({"pos": pos, "image": make_cloud(rng)})
    for _ in range(55):
        motes.append({
            "pos": pygame.Vector2(rng.uniform(0, SPAN_W), rng.uniform(0, SPAN_H)),
            "speed": rng.uniform(0.5, 1.5),
            "wobble": rng.uniform(0, 6.3),
            "size": rng.choice([1, 2, 2, 3]),
        })
    vignette = make_vignette()


def update(dt):
    state["time"] += dt
    state["glint_timer"] -= dt
    for cloud in clouds:
        cloud["pos"] += WIND * dt
    for mote in motes:
        mote["pos"].x += WIND.x * mote["speed"] * dt
        mote["pos"].y += (WIND.y + math.sin(state["time"] + mote["wobble"]) * 12) * mote["speed"] * dt
    for glint in glints:
        glint["life"] -= dt
    glints[:] = [g for g in glints if g["life"] > 0]


def wrap(pos, camera, span_w, span_h, margin):
    x = (pos.x - camera.x) % span_w - margin
    y = (pos.y - camera.y) % span_h - margin
    return x, y


def spawn_glints(camera, world):
    if state["glint_timer"] > 0:
        return
    state["glint_timer"] = 0.05
    x = camera.x + random.uniform(0, W)
    y = camera.y + random.uniform(0, H)
    if world.terrain.level(math.floor(x / TILE), math.floor(y / TILE)) in ("water", "deep_water"):
        glints.append({"pos": pygame.Vector2(x, y), "life": 0.6})


def draw(screen, camera, world, dark=0, only_lights=False):
    if not config.get("effects"):
        return
    if only_lights:
        draw_fireflies(screen, camera)
        return
    spawn_glints(camera, world)
    for glint in glints:
        x, y = glint["pos"] - camera
        size = 4 * math.sin(glint["life"] / 0.6 * math.pi)
        color = (230, 245, 255)
        pygame.draw.line(screen, color, (x - size, y), (x + size, y), 2)
        pygame.draw.line(screen, color, (x, y - size / 2), (x, y + size / 2), 2)

    for cloud in clouds:
        image = cloud["image"]
        x, y = wrap(cloud["pos"], camera, CLOUD_SPAN_W, CLOUD_SPAN_H, image.get_width())
        screen.blit(image, (x, y))

    # fluff during the day, at night the fireflies are drawn after the darkness
    if dark > 0.45:
        return
    for mote in motes:
        x, y = wrap(mote["pos"], camera, SPAN_W, SPAN_H, MARGIN)
        pygame.draw.circle(screen, (255, 250, 215), (x, y), mote["size"])


def draw_fireflies(screen, camera):
    time = state["time"]
    for i, mote in enumerate(motes):
        if i % 2 == 1:
            continue
        x, y = wrap(mote["pos"], camera, SPAN_W, SPAN_H, MARGIN)
        # blink softly, rounded so the glow cache stays small
        flicker = 0.5 + 0.5 * math.sin(time * 3 + mote["wobble"] * 4)
        flicker = round(flicker * 5) / 5
        if flicker < 0.2:
            continue
        sprites.draw_glow(screen, 10, (int(200 * flicker), int(255 * flicker), int(90 * flicker)), (x, y))
        pygame.draw.circle(screen, (240, 255, 170), (x, y), 2)


def draw_vignette(screen):
    if config.get("effects") and vignette:
        screen.blit(vignette, (0, 0))

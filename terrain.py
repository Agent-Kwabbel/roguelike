import math

import pygame

from settings import (
    TILE,
    CHUNK_TILES,
    TERRAIN_SCALE,
    TERRAIN_OCTAVES,
    MOUNTAIN_SCALE,
    MOISTURE_SCALE,
    SAFE_RADIUS,
    TERRAIN_LEVELS,
    BLOCKED_LEVELS,
)


def lattice(x, y, seed):
    # vaste willekeurige waarde tussen 0 en 1 voor elk rasterpunt
    h = (x * 374761393 + y * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return h / 0xFFFFFFFF


def smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(x, y, seed):
    x0 = math.floor(x)
    y0 = math.floor(y)
    fx = smooth(x - x0)
    fy = smooth(y - y0)
    top = lattice(x0, y0, seed) + (lattice(x0 + 1, y0, seed) - lattice(x0, y0, seed)) * fx
    bottom = lattice(x0, y0 + 1, seed) + (lattice(x0 + 1, y0 + 1, seed) - lattice(x0, y0 + 1, seed)) * fx
    return top + (bottom - top) * fy


def fractal_noise(x, y, seed, octaves):
    total = 0
    amplitude = 1
    max_total = 0
    for i in range(octaves):
        total += value_noise(x, y, seed + i * 101) * amplitude
        max_total += amplitude
        amplitude *= 0.5
        x *= 2
        y *= 2
    return total / max_total


class Terrain:
    def __init__(self, seed):
        self.seed = seed
        self.grids = {}

    def height(self, x, y, octaves=TERRAIN_OCTAVES):
        base = fractal_noise(x / TERRAIN_SCALE, y / TERRAIN_SCALE, self.seed, octaves)
        # bergen komen in groepjes voor, niet overal
        mountain = value_noise(x / MOUNTAIN_SCALE, y / MOUNTAIN_SCALE, self.seed + 7)
        mountain = smooth(min(1, max(0, (mountain - 0.5) / 0.3)))
        height = base * 0.85 + mountain * 0.32 - 0.06
        distance = math.hypot(x, y)
        if distance < SAFE_RADIUS:
            t = smooth(max(0, (distance - 200) / (SAFE_RADIUS - 200)))
            height = 0.42 * (1 - t) + height * t
        return min(1, max(0, height))

    def moisture(self, x, y):
        return fractal_noise(x / MOISTURE_SCALE, y / MOISTURE_SCALE, self.seed + 500, 2)

    def level_of_height(self, height):
        name = TERRAIN_LEVELS[0][0]
        for level, start in TERRAIN_LEVELS:
            if height >= start:
                name = level
        return name

    def grid(self, cx, cy):
        if (cx, cy) not in self.grids:
            rows = []
            for ty in range(CHUNK_TILES):
                row = []
                for tx in range(CHUNK_TILES):
                    x = (cx * CHUNK_TILES + tx + 0.5) * TILE
                    y = (cy * CHUNK_TILES + ty + 0.5) * TILE
                    row.append(self.level_of_height(self.height(x, y)))
                rows.append(row)
            self.grids[(cx, cy)] = rows
        return self.grids[(cx, cy)]

    def level(self, tx, ty):
        cx = math.floor(tx / CHUNK_TILES)
        cy = math.floor(ty / CHUNK_TILES)
        return self.grid(cx, cy)[ty - cy * CHUNK_TILES][tx - cx * CHUNK_TILES]

    def is_blocked(self, tx, ty):
        return self.level(tx, ty) in BLOCKED_LEVELS

    def blocked_rects(self, pos, radius):
        rects = []
        first_tx = math.floor((pos.x - radius) / TILE)
        last_tx = math.floor((pos.x + radius) / TILE)
        first_ty = math.floor((pos.y - radius) / TILE)
        last_ty = math.floor((pos.y + radius) / TILE)
        for tx in range(first_tx, last_tx + 1):
            for ty in range(first_ty, last_ty + 1):
                if self.is_blocked(tx, ty):
                    rects.append(pygame.Rect(tx * TILE, ty * TILE, TILE, TILE))
        return rects

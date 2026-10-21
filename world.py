import math
import random

import pygame

import sprites
from buildings import Building, push_out
from terrain import Terrain
from settings import (
    W,
    H,
    TILE,
    CHUNK_TILES,
    CHUNKS_CACHED,
    DIRT_PATCH_CHANCE,
    FLOWER_TILE_CHANCE,
    DECO_PER_CHUNK,
    DECORATIONS,
    STRUCTURE_CHANCE,
    STRUCTURES,
    BUILDING_CHANCE,
    BUILDINGS,
    TERRAIN_LEVELS,
    GRASS_LEVELS,
    SHADE_STRENGTH,
    CLIFF_HEIGHT,
    FOREST_MOISTURE,
)

CHUNK_SIZE = CHUNK_TILES * TILE
SHADE_STEP = 32
LEVEL_RANK = {}
for rank, (name, start) in enumerate(TERRAIN_LEVELS):
    LEVEL_RANK[name] = rank
WATER = ("deep_water", "water")
MOUNTAIN = ("rock", "snow")
TILE_SPRITES = {"deep_water": "water_deep", "water": "water", "sand": "sand", "grass_high": "grass_dark",
                "rock": "mountain", "snow": "snow"}
# vijvers en strand worden voor de schaduw als vlak water gezien
FLAT_HEIGHT = TERRAIN_LEVELS[2][1]
MOUNTAIN_HEIGHT = TERRAIN_LEVELS[6][1]
# binnen een berg om de zoveel hoogte een richeltje
MOUNTAIN_STEP = 0.035


class World:
    def __init__(self, seed=None):
        if seed is None:
            seed = random.randrange(1000000)
        self.seed = seed
        self.chunks = {}
        self.terrain = Terrain(seed)
        # gebouwen worden nooit vergeten, anders kan je ze opnieuw leeghalen
        self.buildings = {}
        self.looted = set()

    def building_in(self, cx, cy):
        if (cx, cy) in self.buildings:
            return self.buildings[(cx, cy)]
        rng = random.Random(hash((self.seed, cx, cy, 7)))
        building = None
        if rng.random() < BUILDING_CHANCE:
            kind = rng.choices(list(BUILDINGS.keys()), [b["weight"] for b in BUILDINGS.values()])[0]
            w, h = BUILDINGS[kind]["size"]
            # minstens een tegel van de rand, zo past hij altijd in een chunk
            tx = rng.randint(1, CHUNK_TILES - 1 - w)
            ty = rng.randint(1, CHUNK_TILES - 1 - h)
            if self.flat_area(cx * CHUNK_TILES + tx - 1, cy * CHUNK_TILES + ty - 1, w + 2, h + 2):
                building = Building(kind, cx * CHUNK_SIZE + tx * TILE, cy * CHUNK_SIZE + ty * TILE, rng)
        self.buildings[(cx, cy)] = building
        return building

    def flat_area(self, first_tx, first_ty, w, h):
        level = self.terrain.level(first_tx, first_ty)
        if level not in GRASS_LEVELS:
            return False
        for tx in range(first_tx, first_tx + w):
            for ty in range(first_ty, first_ty + h):
                if self.terrain.level(tx, ty) != level:
                    return False
        return True

    def is_blocked(self, pos):
        return self.terrain.is_blocked(math.floor(pos.x / TILE), math.floor(pos.y / TILE))

    def nearby_buildings(self, pos, reach=1):
        cx = math.floor(pos.x / CHUNK_SIZE)
        cy = math.floor(pos.y / CHUNK_SIZE)
        found = []
        for x in range(cx - reach, cx + reach + 1):
            for y in range(cy - reach, cy + reach + 1):
                building = self.building_in(x, y)
                if building:
                    found.append(building)
        return found

    def building_at(self, pos):
        for building in self.nearby_buildings(pos, 0):
            if building.is_inside(pos):
                return building
        return None

    def collide(self, pos, radius):
        for building in self.nearby_buildings(pos):
            if building.rect.inflate(radius * 2, radius * 2).collidepoint(pos):
                push_out(pos, radius, building.walls)
        push_out(pos, radius, self.terrain.blocked_rects(pos, radius))
        return pos

    def update(self, dt, player_pos):
        """Daken laten vervagen en loot geven voor gebouwen waar je in de buurt komt."""
        pickups = []
        orbs = []
        for building in self.nearby_buildings(player_pos):
            building.update(dt, player_pos)
            key = building.rect.topleft
            if key not in self.looted:
                self.looted.add(key)
                new_pickups, new_orbs = building.spawn_loot()
                pickups += new_pickups
                orbs += new_orbs
        return pickups, orbs

    def build_chunk(self, cx, cy):
        # zelfde seed per chunk, zodat hij er hetzelfde uitziet als je terugkomt
        rng = random.Random(hash((self.seed, cx, cy)))
        surface = pygame.Surface((CHUNK_SIZE, CHUNK_SIZE))
        grid = self.terrain.grid(cx, cy)

        dirt = []
        if rng.random() < DIRT_PATCH_CHANCE:
            center = (rng.randrange(1, CHUNK_TILES - 1), rng.randrange(1, CHUNK_TILES - 1))
            size = rng.uniform(1.2, 2.6)
            for tx in range(CHUNK_TILES):
                for ty in range(CHUNK_TILES):
                    if math.dist((tx, ty), center) < size:
                        dirt.append((tx, ty))

        for tx in range(CHUNK_TILES):
            for ty in range(CHUNK_TILES):
                level = grid[ty][tx]
                if level in TILE_SPRITES:
                    name = TILE_SPRITES[level]
                elif (tx, ty) in dirt:
                    name = "dirt"
                elif rng.random() < FLOWER_TILE_CHANCE:
                    name = "flowers"
                else:
                    name = f"grass_{rng.randrange(3)}"
                image = sprites.get(name)
                if rng.random() < 0.5:
                    image = sprites.flipped(image)
                surface.blit(image, (tx * TILE, ty * TILE))
                # hoger gras is iets donkerder, zo zie je de terrassen beter
                if level == "grass_mid":
                    surface.fill((228, 232, 226), (tx * TILE, ty * TILE, TILE, TILE), special_flags=pygame.BLEND_RGB_MULT)
                elif level == "grass_low":
                    surface.fill((10, 12, 0), (tx * TILE, ty * TILE, TILE, TILE), special_flags=pygame.BLEND_RGB_ADD)

        self.draw_shading(surface, cx, cy)
        self.draw_edges(surface, cx, cy)

        offset = (cx * CHUNK_SIZE, cy * CHUNK_SIZE)
        building = self.building_in(cx, cy)
        blocked = None
        if building:
            building.draw_floor(surface, offset)
            blocked = building.rect.move(-offset[0], -offset[1]).inflate(32, 32)

        decorations = []
        if rng.random() < STRUCTURE_CHANCE:
            kind = rng.choices(list(STRUCTURES.keys()), list(STRUCTURES.values()))[0]
            image = sprites.get(kind)
            x = rng.randrange(0, CHUNK_SIZE - image.get_width())
            y = rng.randrange(0, CHUNK_SIZE - image.get_height())
            if self.deco_level(grid, x + image.get_width() / 2, y + image.get_height()) in GRASS_LEVELS:
                decorations.append((y + image.get_height(), x, image))

        # in vochtige stukken staat een bos
        moisture = self.terrain.moisture((cx + 0.5) * CHUNK_SIZE, (cy + 0.5) * CHUNK_SIZE)
        weights = dict(DECORATIONS)
        amount = rng.randint(DECO_PER_CHUNK[0], DECO_PER_CHUNK[1])
        if moisture > FOREST_MOISTURE:
            weights["tree"] *= 5
            weights["pine"] *= 5
            amount *= 2
        for _ in range(amount):
            kind = rng.choices(list(weights.keys()), list(weights.values()))[0]
            image = sprites.get(kind)
            x = rng.randrange(0, CHUNK_SIZE - image.get_width())
            y = rng.randrange(0, CHUNK_SIZE - image.get_height())
            level = self.deco_level(grid, x + image.get_width() / 2, y + image.get_height())
            if level == "grass_high" and kind == "tree":
                kind = "pine"
                image = sprites.get(kind)
            if level == "sand" and kind not in ("rock", "tuft"):
                continue
            if level not in GRASS_LEVELS and level != "sand":
                continue
            decorations.append((y + image.get_height(), x, image))
        # van boven naar onder tekenen zodat dingen goed overlappen
        if blocked:
            free = []
            for deco in decorations:
                bottom, x, image = deco
                rect = pygame.Rect(x, bottom - image.get_height(), image.get_width(), image.get_height())
                if not rect.colliderect(blocked):
                    free.append(deco)
            decorations = free
        decorations.sort(key=lambda d: d[0])
        for bottom, x, image in decorations:
            if rng.random() < 0.5:
                image = sprites.flipped(image)
            shadow = pygame.Surface((image.get_width() - 8, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
            surface.blit(shadow, (x + 4, bottom - 8))
            surface.blit(image, (x, bottom - image.get_height()))
        return surface

    def deco_level(self, grid, x, y):
        tx = min(CHUNK_TILES - 1, int(x // TILE))
        ty = min(CHUNK_TILES - 1, int(y // TILE))
        return grid[ty][tx]

    def draw_shading(self, surface, cx, cy):
        """Hellingen naar het noordwesten lichter, naar het zuidoosten donkerder."""
        count = CHUNK_SIZE // SHADE_STEP + 1
        heights = []
        for j in range(-1, count + 1):
            row = []
            for i in range(-1, count + 1):
                x = cx * CHUNK_SIZE + i * SHADE_STEP
                y = cy * CHUNK_SIZE + j * SHADE_STEP
                # minder detail dan het echte terrein, anders lijkt het op wolken
                row.append(max(FLAT_HEIGHT, self.terrain.height(x, y, 2)))
            heights.append(row)

        dark = pygame.Surface((count, count))
        light = pygame.Surface((count, count))
        for j in range(count):
            for i in range(count):
                slope_x = heights[j + 1][i + 2] - heights[j + 1][i]
                slope_y = heights[j + 2][i + 1] - heights[j][i + 1]
                # hoe hoger, hoe iets lichter
                value = (slope_x + slope_y) * SHADE_STRENGTH * 255
                if heights[j + 1][i + 1] > MOUNTAIN_HEIGHT:
                    value *= 2.5
                if value < 0:
                    shade = max(150, 255 + int(value * 1.5))
                    dark.set_at((i, j), (shade, shade, shade))
                    light.set_at((i, j), (0, 0, 0))
                else:
                    bright = min(70, int(value))
                    dark.set_at((i, j), (255, 255, 255))
                    light.set_at((i, j), (bright, bright, bright - 10 if bright > 10 else 0))
        size = CHUNK_SIZE + SHADE_STEP
        start = -SHADE_STEP // 2
        surface.blit(pygame.transform.smoothscale(dark, (size, size)), (start, start), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(pygame.transform.smoothscale(light, (size, size)), (start, start), special_flags=pygame.BLEND_RGB_ADD)

    def draw_edges(self, surface, cx, cy):
        """Randjes van terrassen, rotswanden en schuim langs het water."""
        overlay = pygame.Surface((CHUNK_SIZE, CHUNK_SIZE), pygame.SRCALPHA)
        for tx in range(CHUNK_TILES):
            for ty in range(CHUNK_TILES):
                gx = cx * CHUNK_TILES + tx
                gy = cy * CHUNK_TILES + ty
                level = self.terrain.level(gx, gy)
                north = self.terrain.level(gx, gy - 1)
                south = self.terrain.level(gx, gy + 1)
                west = self.terrain.level(gx - 1, gy)
                east = self.terrain.level(gx + 1, gy)
                x = tx * TILE
                y = ty * TILE

                if level in WATER:
                    for side, other in (("n", north), ("s", south), ("w", west), ("e", east)):
                        if other not in WATER:
                            self.draw_foam(overlay, x, y, side)
                    continue

                if level in MOUNTAIN:
                    if west not in MOUNTAIN:
                        pygame.draw.rect(overlay, (20, 15, 30, 110), (x, y, 6, TILE))
                    if east not in MOUNTAIN:
                        pygame.draw.rect(overlay, (20, 15, 30, 80), (x + TILE - 6, y, 6, TILE))
                    if north not in MOUNTAIN:
                        pygame.draw.rect(overlay, (255, 255, 255, 70), (x, y, TILE, 4))
                    if south not in MOUNTAIN:
                        self.draw_cliff(surface, x, y, CLIFF_HEIGHT, gx * 31 + gy)
                        continue
                    step = self.mountain_step(gx, gy)
                    if self.mountain_step(gx, gy + 1) < step:
                        self.draw_cliff(surface, x, y, CLIFF_HEIGHT // 2, gx * 31 + gy)
                    if self.mountain_step(gx, gy - 1) > step:
                        pygame.draw.rect(overlay, (0, 0, 0, 60), (x, y, TILE, 8))
                    if level == "snow" and south == "rock":
                        pygame.draw.rect(overlay, (255, 255, 255, 120), (x, y + TILE - 6, TILE, 6))
                    continue
                if north in MOUNTAIN and level not in MOUNTAIN:
                    pygame.draw.rect(overlay, (0, 0, 0, 90), (x, y, TILE, 14))
                    pygame.draw.rect(overlay, (0, 0, 0, 45), (x, y + 14, TILE, 8))
                    continue

                rank = LEVEL_RANK[level]
                if north not in WATER and LEVEL_RANK[north] > rank:
                    # voorkant van het terras erboven
                    pygame.draw.rect(overlay, (40, 30, 20, 110), (x, y, TILE, 6))
                    pygame.draw.rect(overlay, (0, 0, 0, 45), (x, y + 6, TILE, 6))
                if south not in WATER and LEVEL_RANK[south] < rank:
                    pygame.draw.rect(overlay, (255, 255, 230, 60), (x, y + TILE - 3, TILE, 3))
                if west not in WATER and LEVEL_RANK[west] > rank:
                    pygame.draw.rect(overlay, (0, 0, 0, 60), (x, y, 4, TILE))
                if east not in WATER and LEVEL_RANK[east] > rank:
                    pygame.draw.rect(overlay, (0, 0, 0, 40), (x + TILE - 3, y, 3, TILE))
        surface.blit(overlay, (0, 0))

    def mountain_step(self, tx, ty):
        height = self.terrain.height((tx + 0.5) * TILE, (ty + 0.5) * TILE, 2)
        return int(height / MOUNTAIN_STEP)

    def draw_foam(self, overlay, x, y, side):
        color = (235, 245, 255, 150)
        if side == "n":
            pygame.draw.rect(overlay, color, (x, y, TILE, 4))
        elif side == "s":
            pygame.draw.rect(overlay, color, (x, y + TILE - 4, TILE, 4))
        elif side == "w":
            pygame.draw.rect(overlay, color, (x, y, 4, TILE))
        else:
            pygame.draw.rect(overlay, color, (x + TILE - 4, y, 4, TILE))

    def draw_cliff(self, surface, x, y, height, rng_seed):
        rng = random.Random(rng_seed)
        top = y + TILE - height
        pygame.draw.rect(surface, (96, 88, 96), (x, top, TILE, height))
        # onderkant van de wand ligt in de schaduw
        pygame.draw.rect(surface, (74, 68, 78), (x, top + height // 2, TILE, height - height // 2))
        pygame.draw.rect(surface, (180, 175, 176), (x, top - 4, TILE, 4))
        line_x = x + rng.randrange(4, 12)
        while line_x < x + TILE - 2:
            length = rng.randrange(height // 2, height)
            pygame.draw.line(surface, (58, 52, 62), (line_x, top + 2), (line_x, top + length), 2)
            pygame.draw.line(surface, (128, 120, 126), (line_x + 2, top + 2), (line_x + 2, top + length // 2), 1)
            line_x += rng.randrange(7, 14)
        pygame.draw.line(surface, (40, 34, 44), (x, y + TILE - 2), (x + TILE, y + TILE - 2), 3)

    def get_chunk(self, cx, cy):
        if (cx, cy) not in self.chunks:
            self.chunks[(cx, cy)] = self.build_chunk(cx, cy)
        return self.chunks[(cx, cy)]

    def forget_far_chunks(self, center_cx, center_cy):
        if len(self.chunks) <= CHUNKS_CACHED:
            return
        for key in list(self.chunks.keys()):
            if abs(key[0] - center_cx) > 3 or abs(key[1] - center_cy) > 3:
                del self.chunks[key]

    def visible_chunks(self, camera):
        first_cx = math.floor(camera.x / CHUNK_SIZE)
        first_cy = math.floor(camera.y / CHUNK_SIZE)
        last_cx = math.floor((camera.x + W) / CHUNK_SIZE)
        last_cy = math.floor((camera.y + H) / CHUNK_SIZE)
        chunks = []
        for cx in range(first_cx, last_cx + 1):
            for cy in range(first_cy, last_cy + 1):
                chunks.append((cx, cy))
        return chunks

    def draw_roofs(self, screen, camera):
        for cx, cy in self.visible_chunks(camera):
            building = self.building_in(cx, cy)
            if building:
                building.draw_roof(screen, camera)

    def draw(self, screen, camera):
        first_cx = math.floor(camera.x / CHUNK_SIZE)
        first_cy = math.floor(camera.y / CHUNK_SIZE)
        last_cx = math.floor((camera.x + W) / CHUNK_SIZE)
        last_cy = math.floor((camera.y + H) / CHUNK_SIZE)
        for cx in range(first_cx, last_cx + 1):
            for cy in range(first_cy, last_cy + 1):
                x = cx * CHUNK_SIZE - camera.x
                y = cy * CHUNK_SIZE - camera.y
                screen.blit(self.get_chunk(cx, cy), (round(x), round(y)))
        self.forget_far_chunks(first_cx, first_cy)
        self.prepare_next_chunk(first_cx, first_cy, last_cx, last_cy)

    def prepare_next_chunk(self, first_cx, first_cy, last_cx, last_cy):
        # een rand om het scherm alvast klaarzetten, hooguit een per frame tegen haperen
        for cx in range(first_cx - 1, last_cx + 2):
            for cy in range(first_cy - 1, last_cy + 2):
                if (cx, cy) not in self.chunks:
                    self.chunks[(cx, cy)] = self.build_chunk(cx, cy)
                    return

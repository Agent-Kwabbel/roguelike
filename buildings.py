import math
import random

import pygame

import sprites
from orb import Orb
from pickup import Pickup
from settings import TILE, WALL, ROOF_FADE, ROOF_NEAR_ALPHA, ROOF_NEAR_RANGE, BUILDINGS

OUTLINE = (28, 22, 38)


def darker(color, amount=35):
    return (max(0, color[0] - amount), max(0, color[1] - amount), max(0, color[2] - amount))


class Building:
    def __init__(self, kind, x, y, rng):
        stats = BUILDINGS[kind]
        self.kind = kind
        self.stats = stats
        self.tiles_w, self.tiles_h = stats["size"]
        self.rect = pygame.Rect(x, y, self.tiles_w * TILE, self.tiles_h * TILE)
        # the door is always in the bottom wall, never in a corner
        self.door_tile = rng.randrange(1, self.tiles_w - 1)
        self.door_x = x + self.door_tile * TILE + TILE / 2
        self.walls = self.make_walls(rng)

        free = []
        for tx in range(self.tiles_w):
            for ty in range(self.tiles_h):
                # keep the space in front of the door free so you can get in
                if tx == self.door_tile and ty == self.tiles_h - 1:
                    continue
                free.append((tx, ty))
        rng.shuffle(free)
        self.furniture = []
        for name in stats["furniture"]:
            if not free:
                break
            tx, ty = free.pop()
            self.furniture.append((name, (tx, ty)))
        self.free_tiles = free

        self.roof = None
        if stats["roof"]:
            self.roof = self.make_roof(rng)
        self.roof_alpha = 255

    def make_walls(self, rng):
        x, y = self.rect.topleft
        walls = []
        for i in range(self.tiles_w):
            walls.append(pygame.Rect(x + i * TILE, y, TILE, WALL))
            if i != self.door_tile:
                walls.append(pygame.Rect(x + i * TILE, self.rect.bottom - WALL, TILE, WALL))
        for j in range(self.tiles_h):
            walls.append(pygame.Rect(x, y + j * TILE, WALL, TILE))
            walls.append(pygame.Rect(self.rect.right - WALL, y + j * TILE, WALL, TILE))
        if self.kind == "ruin":
            # ruins are half collapsed
            walls = [w for w in walls if rng.random() > 0.3]
        return walls

    def make_roof(self, rng):
        roof = self.rect.inflate(16, 16)
        surface = pygame.Surface(roof.size, pygame.SRCALPHA)
        color = self.stats["roof"]
        width, height = roof.size
        middle = height // 2
        surface.fill(color)
        # bottom half a bit darker, like the roof slopes down
        pygame.draw.rect(surface, darker(color, 20), (0, middle, width, height - middle))
        for row, line_y in enumerate(range(10, height, 12)):
            pygame.draw.line(surface, darker(color), (0, line_y), (width, line_y), 2)
            start = 0 if row % 2 == 0 else 8
            for line_x in range(start, width, 16):
                pygame.draw.line(surface, darker(color), (line_x, line_y - 10), (line_x, line_y), 2)
        pygame.draw.rect(surface, darker(color, 60), (0, middle - 3, width, 6))
        if self.kind == "house":
            cx = rng.randrange(20, width - 40)
            pygame.draw.rect(surface, (150, 150, 160), (cx, 10, 20, 24))
            pygame.draw.rect(surface, OUTLINE, (cx, 10, 20, 24), 3)
        self.draw_front(surface, width, height)
        pygame.draw.rect(surface, OUTLINE, (0, 0, width, height), 3)
        return surface

    def draw_front(self, surface, width, height):
        # front wall with the door, so you can see from outside where to get in
        wall = self.stats["wall"]
        front = 16
        pygame.draw.rect(surface, wall, (0, height - front, width, front))
        pygame.draw.line(surface, darker(wall), (0, height - front), (width, height - front), 3)
        door_x = 8 + self.door_tile * TILE + TILE // 2
        pygame.draw.rect(surface, darker(self.stats["roof"], 50), (door_x - 30, height - front - 10, 60, 10))
        pygame.draw.rect(surface, OUTLINE, (door_x - 30, height - front - 10, 60, 10), 2)
        pygame.draw.rect(surface, (40, 28, 30), (door_x - 18, height - front - 2, 36, front + 2))
        pygame.draw.rect(surface, (70, 50, 45), (door_x - 18, height - front - 2, 36, front + 2), 2)
        # little lamp next to the door
        pygame.draw.circle(surface, (255, 220, 120), (door_x + 26, height - front + 6), 4)
        pygame.draw.circle(surface, OUTLINE, (door_x + 26, height - front + 6), 4, 1)

    def tile_center(self, tile):
        return pygame.Vector2(self.rect.x + tile[0] * TILE + TILE / 2, self.rect.y + tile[1] * TILE + TILE / 2)

    def draw_floor(self, surface, offset):
        left = self.rect.x - offset[0]
        top = self.rect.y - offset[1]
        pygame.draw.rect(surface, (45, 95, 48), (left + 6, top + 8, self.rect.width, self.rect.height))
        floor = sprites.get(self.stats["floor"])
        for tx in range(self.tiles_w):
            for ty in range(self.tiles_h):
                surface.blit(floor, (left + tx * TILE, top + ty * TILE))
        for name, tile in self.furniture:
            pos = self.tile_center(tile) - offset
            sprites.draw_centered(surface, sprites.get(name), pos)

        self.draw_path(surface, left, top)

        # first all the edges, then the walls on top so the pieces look connected
        color = self.stats["wall"]
        for wall in self.walls:
            rect = wall.move(-offset[0], -offset[1])
            pygame.draw.rect(surface, OUTLINE, rect.inflate(4, 4))
        for wall in self.walls:
            rect = wall.move(-offset[0], -offset[1])
            pygame.draw.rect(surface, color, rect)
            pygame.draw.line(surface, darker(color), (rect.left, rect.bottom - 2), (rect.right - 1, rect.bottom - 2), 3)

    def draw_path(self, surface, left, top):
        # stepping stones from the door outwards
        rng = random.Random(hash(self.rect.topleft))
        door_x = left + self.door_tile * TILE + TILE // 2
        bottom = top + self.rect.height
        pygame.draw.rect(surface, (150, 115, 78), (door_x - 20, bottom - 4, 40, TILE - 8), border_radius=8)
        for i in range(3):
            x = door_x + rng.randint(-8, 8)
            y = bottom + 8 + i * 18
            stone = pygame.Rect(x - 10, y - 6, 20, 12)
            pygame.draw.ellipse(surface, OUTLINE, stone.inflate(4, 4))
            pygame.draw.ellipse(surface, (165, 160, 165), stone)
            pygame.draw.ellipse(surface, (195, 190, 195), (stone.x + 3, stone.y + 2, 9, 4))

    def path_rect(self):
        return pygame.Rect(self.door_x - 28, self.rect.bottom, 56, TILE)

    def is_inside(self, pos):
        return self.rect.collidepoint(pos)

    def update(self, dt, player_pos):
        if self.is_inside(player_pos):
            target = 0
        elif self.rect.inflate(ROOF_NEAR_RANGE * 2, ROOF_NEAR_RANGE * 2).collidepoint(player_pos):
            target = ROOF_NEAR_ALPHA
        else:
            target = 255
        if self.roof_alpha > target:
            self.roof_alpha = max(target, self.roof_alpha - ROOF_FADE * dt)
        else:
            self.roof_alpha = min(target, self.roof_alpha + ROOF_FADE * dt)

    def draw_roof(self, screen, camera):
        if self.roof is None or self.roof_alpha <= 0:
            return
        self.roof.set_alpha(int(self.roof_alpha))
        screen.blit(self.roof, (round(self.rect.x - 8 - camera.x), round(self.rect.y - 8 - camera.y)))

    def random_spot(self):
        if self.free_tiles:
            tile = random.choice(self.free_tiles)
        else:
            tile = (random.randrange(self.tiles_w), random.randrange(self.tiles_h))
        return self.tile_center(tile) + (random.uniform(-14, 14), random.uniform(-14, 14))

    def spawn_loot(self):
        pickups = []
        orbs = []
        for kind, amount in self.stats["loot"].items():
            if amount < 1:
                count = 1 if random.random() < amount else 0
            else:
                count = random.randint(1, int(amount))
            for _ in range(count):
                if kind == "gems":
                    orbs.append(Orb(self.random_spot(), 3))
                else:
                    pickup = Pickup(kind, self.random_spot())
                    pickup.life = 9999
                    pickups.append(pickup)
        return pickups, orbs

    def path_target(self, pos, target):
        """Where an enemy should walk to reach the player through the door."""
        if self.is_inside(pos) or not self.is_inside(target):
            return target
        left = self.rect.left - 40
        right = self.rect.right + 40
        below = self.rect.bottom + 40
        # straight below the door, then walk straight in
        if abs(pos.x - self.door_x) < 16 and pos.y > self.rect.bottom - 20:
            return pygame.Vector2(self.door_x, self.rect.bottom - 40)
        if pos.y < self.rect.bottom:
            side = left if pos.x < self.rect.centerx else right
            if left < pos.x < right:
                return pygame.Vector2(side, pos.y)
            return pygame.Vector2(side, below)
        return pygame.Vector2(self.door_x, below)


def push_out(pos, radius, walls):
    for wall in walls:
        closest_x = max(wall.left, min(pos.x, wall.right))
        closest_y = max(wall.top, min(pos.y, wall.bottom))
        dx = pos.x - closest_x
        dy = pos.y - closest_y
        distance = math.hypot(dx, dy)
        if distance >= radius:
            continue
        if distance > 0:
            pos.x += dx / distance * (radius - distance)
            pos.y += dy / distance * (radius - distance)
        else:
            # center is inside the wall, take the shortest way out
            gaps = [pos.x - wall.left, wall.right - pos.x, pos.y - wall.top, wall.bottom - pos.y]
            smallest = min(gaps)
            if smallest == gaps[0]:
                pos.x = wall.left - radius
            elif smallest == gaps[1]:
                pos.x = wall.right + radius
            elif smallest == gaps[2]:
                pos.y = wall.top - radius
            else:
                pos.y = wall.bottom + radius
    return pos

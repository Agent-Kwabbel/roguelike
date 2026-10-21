# Makes all pixel-art sprites in assets/. Run with: uv run tools/make_sprites.py
import os
import random

import pygame

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
OUTLINE = (28, 22, 38)


def make_surface(rows, palette):
    width = max(len(row) for row in rows)
    surface = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == ".":
                continue
            if char == "o":
                surface.set_at((x, y), OUTLINE)
            elif char in palette:
                surface.set_at((x, y), palette[char])
            else:
                print("onbekend teken", char)
    return surface


def save(surface, folder, name, scale):
    size = (surface.get_width() * scale, surface.get_height() * scale)
    big = pygame.transform.scale(surface, size)
    path = os.path.join(ASSETS, folder)
    os.makedirs(path, exist_ok=True)
    pygame.image.save(big, os.path.join(path, name + ".png"))


def save_grid(rows, palette, folder, name, scale):
    width = len(rows[0])
    for row in rows:
        if len(row) != width:
            print("waarschuwing:", name, "rij heeft lengte", len(row), "in plaats van", width)
    save(make_surface(rows, palette), folder, name, scale)


def save_frames(body, legs_a, legs_b, palette, folder, name, scale):
    save_grid(body + legs_a, palette, folder, name + "_0", scale)
    save_grid(body + legs_b, palette, folder, name + "_1", scale)


# ---------- player ----------

LEGS_A = [
    "....oLLooLLo....",
    "....oLLooLLo....",
    "....oooooooo....",
]
LEGS_B = [
    "....oLLooLLo....",
    "...oLLo..oLLo...",
    "...ooo....ooo...",
]

HERO = [
    "................",
    ".....oooooo.....",
    "....oHHHHHHo....",
    "...oHHHHHHHHo...",
    "...oHSSSSSSHo...",
    "...oSSESSESSo...",
    "...oSSSSSSSSo...",
    "....oSSSSSSo....",
    "...ooBBBBBBoo...",
    "..oSoBBAABBoSo..",
    "..oSoBBAABBoSo..",
    "..ooBBBBBBBBoo..",
    "...ooBBBBBBoo...",
]

KNIGHT = [
    "................",
    ".....oooooo.....",
    "....oHHHHHHo....",
    "...oHHHAHHHHo...",
    "...oHVVVVVVHo...",
    "...oHVEVVEVHo...",
    "...oHHHHHHHHo...",
    "....oHHHHHHo....",
    "...ooBBBBBBoo...",
    "..oSoBBAABBoSo..",
    "..oSoBAAAABoSo..",
    "..ooBBBAABBBoo..",
    "...ooBBBBBBoo...",
]

WIZARD = [
    ".......oo.......",
    "......oHHo......",
    ".....oHHHHo.....",
    ".....oHHAHo.....",
    "....oHHHHHHo....",
    "..ooHHHHHHHHoo..",
    "..oHHHHHHHHHHo..",
    "...oSSESSESSo...",
    "...oSSSSSSSSo...",
    "....oWWWWWWo....",
    "..oSoBWWWWBoSo..",
    "..ooBBBWWBBBoo..",
    "...ooBBBBBBoo...",
]

ROBOT = [
    ".......oo.......",
    ".......oAo......",
    ".....oooooo.....",
    "....oHHHHHHo....",
    "....oHEHHEHo....",
    "....oHHHHHHo....",
    "....oHVVVVHo....",
    ".....oooooo.....",
    "...ooBBBBBBoo...",
    "..oHoBAAAABoHo..",
    "..oHoBAAAABoHo..",
    "..ooBBBBBBBBoo..",
    "...ooBBBBBBoo...",
]

HOOD = [
    "................",
    ".....oooooo.....",
    "....oHHHHHHo....",
    "...oHHHHHHHHo...",
    "...oHHHHHHHHo...",
    "...oHSESSESHo...",
    "...oHHHHHHHHo...",
    "....oHHHHHHo....",
    "...ooBBBBBBoo...",
    "..oHoBBAABBoHo..",
    "..oHoBBAABBoHo..",
    "..ooBBBBBBBBoo..",
    "...ooBBBBBBoo...",
]

SKIN = (240, 195, 150)
DARK = (25, 25, 35)


def hero_palette(shirt, accent, hair=(110, 70, 40), legs=(50, 50, 80), skin=SKIN):
    return {"H": hair, "S": skin, "E": DARK, "B": shirt, "A": accent, "L": legs}


SKINS = {
    "skin_default": (HERO, hero_palette((60, 120, 220), (140, 190, 255))),
    "skin_green": (HERO, hero_palette((60, 170, 80), (150, 230, 140))),
    "skin_red": (HERO, hero_palette((200, 55, 55), (255, 150, 130))),
    "skin_silver": (HERO, hero_palette((170, 170, 185), (230, 230, 240), (60, 60, 70))),
    "skin_orange": (HERO, hero_palette((235, 135, 40), (255, 210, 120))),
    "skin_purple": (HERO, hero_palette((140, 65, 190), (210, 150, 255), (40, 30, 30))),
    "skin_black": (HERO, hero_palette((35, 35, 45), (90, 90, 110), (20, 20, 20), (30, 30, 30))),
    "skin_cyan": (HERO, hero_palette((50, 200, 215), (190, 250, 255))),
    "skin_gold": (HERO, hero_palette((235, 190, 50), (255, 240, 150), (120, 70, 30))),
    "skin_frog": (HERO, hero_palette((70, 160, 60), (230, 220, 120), (70, 160, 60), (50, 110, 40), (110, 200, 90))),
    "skin_skeleton": (HERO, hero_palette((215, 215, 200), (120, 120, 110), (235, 235, 220), (180, 180, 165), (235, 235, 220))),
    "skin_pirate": (HERO, hero_palette((235, 235, 225), (60, 40, 30), (200, 40, 40), (90, 60, 40))),
    "skin_vampire": (HERO, hero_palette((60, 20, 30), (200, 30, 40), (20, 20, 30), (25, 20, 25), (225, 215, 225))),
    "skin_knight": (KNIGHT, {"H": (180, 185, 200), "V": (40, 40, 55), "E": (120, 200, 255), "B": (150, 155, 175), "A": (200, 50, 50), "S": (110, 110, 125), "L": (90, 90, 105)}),
    "skin_gold_knight": (KNIGHT, {"H": (245, 200, 60), "V": (90, 55, 20), "E": (255, 255, 200), "B": (230, 180, 50), "A": (255, 240, 150), "S": (190, 140, 40), "L": (160, 110, 30)}),
    "skin_astronaut": (KNIGHT, {"H": (235, 235, 240), "V": (40, 90, 140), "E": (150, 220, 255), "B": (225, 225, 230), "A": (240, 130, 40), "S": (200, 200, 210), "L": (170, 170, 180)}),
    "skin_legend": (KNIGHT, {"H": (255, 255, 255), "V": (120, 60, 200), "E": (255, 120, 220), "B": (250, 240, 200), "A": (80, 220, 240), "S": (255, 215, 90), "L": (240, 200, 80)}),
    "skin_wizard": (WIZARD, {"H": (90, 60, 190), "A": (255, 220, 70), "S": SKIN, "E": DARK, "W": (235, 235, 240), "B": (90, 60, 190), "L": (60, 40, 120)}),
    "skin_dark_wizard": (WIZARD, {"H": (40, 30, 50), "A": (220, 40, 60), "S": (190, 170, 200), "E": (220, 40, 60), "W": (110, 110, 120), "B": (50, 30, 60), "L": (30, 20, 40)}),
    "skin_robot": (ROBOT, {"H": (150, 160, 175), "E": (80, 240, 255), "V": (220, 60, 60), "A": (80, 240, 255), "B": (90, 95, 110), "L": (70, 75, 90)}),
    "skin_ninja": (HOOD, {"H": (35, 35, 45), "S": SKIN, "E": DARK, "B": (40, 40, 50), "A": (210, 40, 40), "L": (30, 30, 40)}),
}

# ---------- enemies ----------

SLIME_0 = [
    "................",
    "................",
    "................",
    "......oooo......",
    "....ooGGGGoo....",
    "...oGGHGGGGGo...",
    "..oGGHGGGGGGGo..",
    "..oGGGEGGGEGGo..",
    "..oGGGEGGGEGGo..",
    ".oGGGGGGGGGGGGo.",
    ".oGGGGGMMGGGGGo.",
    ".oGDGGGGGGGGDGo.",
    ".oGDDGGGGGGDDGo.",
    "..oDDDDDDDDDDo..",
    "...oooooooooo...",
    "................",
]
SLIME_1 = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....oooooo.....",
    "...ooGGGGGGoo...",
    "..oGGHGGGGGGGo..",
    ".oGGHGEGGGEGGGo.",
    ".oGGGGEGGGEGGGo.",
    "oGGGGGGGGGGGGGGo",
    "oGGGGGGMMGGGGGGo",
    "oGDGGGGGGGGGGDGo",
    ".oDDDDDDDDDDDDo.",
    "..oooooooooooo..",
    "................",
]

BAT_0 = [
    "................",
    ".o............o.",
    ".oo..o....o..oo.",
    ".oWo.oo..oo.oWo.",
    ".oWWooBBBBooWWo.",
    ".oWWWBBBBBBWWWo.",
    "..oWWBEBBEBWWo..",
    "..oWWBBBBBBWWo..",
    "...oWoBBBBoWo...",
    "...oo.oBBo.oo...",
    ".......oo.......",
    "................",
]
BAT_1 = [
    "................",
    "................",
    ".....o....o.....",
    ".....oo..oo.....",
    "....ooBBBBoo....",
    "...oWBBBBBBWo...",
    "..oWWBEBBEBWWo..",
    ".oWWWBBBBBBWWWo.",
    ".oWWooBBBBooWWo.",
    ".oWo..oBBo..oWo.",
    ".oo....oo....oo.",
    "................",
]

GOLEM = [
    ".....oooooo.....",
    "....oRRRRRRo....",
    "...oRRLRRRRDo...",
    "...oRCRRRRCDo...",
    "...oRRRRRRRDo...",
    "..ooRDDDDDDDoo..",
    ".oRRoRRRRRRoRRo.",
    "oRRRoRRPRRRoRRRo",
    "oRRRoRPPRRRoRRRo",
    "oRDDoRRRRRDoDDRo",
    ".ooo.oRRRRDo.ooo",
    ".....oRDDDDo....",
]
GOLEM_LEGS_A = [
    "....oRRo.oRRo...",
    "....oDDo.oDDo...",
    "....oooo.oooo...",
]
GOLEM_LEGS_B = [
    "...oRRo...oRRo..",
    "...oDDo...oDDo..",
    "...oooo...oooo..",
]

BOAR = [
    ".................",
    "...o..oooooooo...",
    "..oBooBBBBBBBBo..",
    ".oBBBBBBBBBBBBBo.",
    "oBBBBBBBBBBBBEBo.",
    "oBBBBBBBBBBBBBBPo",
    "oDBBBBBBBBBBBWPPo",
    ".oDBBBBBBBBBBoWo.",
    "..oDDDDDDDDDDo...",
]
BOAR_LEGS_A = [
    "..oDo.oDo.oDo.oDo",
    "..ooo.ooo.ooo.ooo",
    ".................",
]
BOAR_LEGS_B = [
    "...oDooDo..oDooDo",
    "...oooooo..oooooo",
    ".................",
]

BOSS = [
    ".oo................oo.",
    "oHHo..............oHHo",
    "oHHo...oooooooo...oHHo",
    ".oHHo.oRRRRRRRRo.oHHo.",
    "..oHHoRRRRRRRRRRoHHo..",
    "...oRRRRRRRRRRRRRRo...",
    "..oRRRRRRRRRRRRRRRRo..",
    "..oRRYYYRRRRRRYYYRRo..",
    "..oRRYEYRRRRRRYEYRRo..",
    "..oRRRRRRRRRRRRRRRRo..",
    "..oRRRRoooooooooRRRo..",
    "..oRRRoWoWoWoWoWoRRo..",
    "..oDRRRooooooooooRDo..",
    "...oDRRRRRRRRRRRRDo...",
    "..ooDDDDDDDDDDDDDDoo..",
    ".oRRoDDDDDDDDDDDDoRRo.",
    "oRRRRoDDDDDDDDDDoRRRRo",
    "oRRRRoDDDDDDDDDDoRRRRo",
    "oCCCCooDDDDDDDDooCCCCo",
    ".oooo..oDDDooDDo.oooo.",
    ".......oRRo.oRRo......",
    ".......oooo.oooo......",
]

# ---------- bullets and weapons ----------

BOLT = [
    "..oo..",
    ".oWLo.",
    "oWLLCo",
    "oLLCCo",
    ".oCCo.",
    "..oo..",
]
FIREBALL = [
    "...oooo...",
    ".ooRRYYoo.",
    "oRRRYWWYo.",
    "oRRRYWWYo.",
    ".ooRRYYoo.",
    "...oooo...",
]
ARROW = [
    ".o.......o...",
    "oFo......oWo.",
    ".oBBBBBBBWWWo",
    "oFo......oWo.",
    ".o.......o...",
]
KNIFE = [
    "oo.....ooo..",
    "oHoooooWWWo.",
    "oHHHoWWWWWWo",
    "oHoooooLLLo.",
    "oo.....ooo..",
]
STAR = [
    "....o....",
    "...oYo...",
    "oooYYYooo",
    "oYYYWYYYo",
    ".oYYYYYo.",
    "..oYYYo..",
    ".oYYoYYo.",
    ".oYo.oYo.",
    ".oo...oo.",
]
ICE = [
    "...oooo...",
    ".ooCCWWoo.",
    "oLLCCCWWWo",
    ".ooCCWWoo.",
    "...oooo...",
]
HEART = [
    ".oo...oo.",
    "oRRo.oRRo",
    "oRWRoRRRo",
    "oRRRRRRRo",
    ".oRRRRRo.",
    "..oRRRo..",
    "...oRo...",
    "....o....",
]
BLADE = [
    "....o.....",
    "...oWo....",
    "...oWLo...",
    "oooWLLoooo",
    "oWWLLDLLWo",
    "oWLLDLLWWo",
    "ooooLLWooo",
    "....oLWo..",
    "....oWo...",
    ".....o....",
]
LIGHTNING = [
    "....oo..",
    "...oYo..",
    "..oYWo..",
    "..oYo...",
    ".oYWo...",
    ".oYYooo.",
    "oYWWYYo.",
    ".oooWYo.",
    "...oYo..",
    "...oWo..",
    "..oYo...",
    "..oYo...",
    ".oWo....",
    ".oo.....",
]

# ---------- items ----------

GEM = [
    "..oo..",
    ".oLBo.",
    "oLBBBo",
    "oBBBDo",
    ".oBDo.",
    "..oo..",
]
COIN = [
    "..oooo..",
    ".oYYYYo.",
    "oYWYYYDo",
    "oYYDYYDo",
    "oYYDYYDo",
    "oYYYYYDo",
    ".oDDDDo.",
    "..oooo..",
]
MAGNET = [
    ".oo....oo.",
    "oWWo..oWWo",
    "oRRo..oRRo",
    "oRRo..oRRo",
    "oRRo..oRRo",
    "oRRooooRRo",
    "oRRRRRRRRo",
    ".oRRRRRRo.",
    "..oooooo..",
]
BOMB = [
    "......oYo.",
    ".....oo...",
    "...oooo...",
    "..oKKKKo..",
    ".oKWKKKKo.",
    "oKWKKKKKKo",
    "oKKKKKKKKo",
    "oKKKKKKKDo",
    ".oKKKKKDo.",
    "..oooooo..",
]
CHEST = [
    "..oooooooooo..",
    ".oBBBBBBBBBBo.",
    "oBBYBBBBBBYBBo",
    "oBBYBBBBBBYBBo",
    "ooooooYYoooooo",
    "oBBYBBYYBBYBBo",
    "oBBYBBBBBBYBBo",
    "oBBYBBBBBBYBBo",
    "oDDYDDDDDDYDDo",
    ".oooooooooooo.",
]

# ---------- decoration ----------

ROCK = [
    "....oooo....",
    "..ooRRRRoo..",
    ".oRRLLRRRRo.",
    ".oRLLRRRRDo.",
    "oRRRRRRRRDDo",
    "oRRRRRRRDDDo",
    "oDRRRRRDDDDo",
    ".oDDDDDDDDo.",
    "..oooooooo..",
]
BUSH = [
    "....oooooo....",
    "..ooGGLLGGoo..",
    ".oGGLLGGGGGGo.",
    "oGGLGGGGBGGGGo",
    "oGGGGGGGGGGDGo",
    "oGGBGGGGGGDDGo",
    ".oGGGGGGBDDGo.",
    ".oDGGGGDDDDDo.",
    "..ooDDDDDDoo..",
    "....oooooo....",
]
TREE = [
    ".....oooooo.....",
    "...ooGGGLLGoo...",
    "..oGGGLLLGGGGo..",
    ".oGGLLGGGGGGGGo.",
    ".oGLGGGGGGGGDGo.",
    "oGGGGGGGGGGGDDGo",
    "oGGGGGGGGGGDDDGo",
    "oGDGGGGGGGDDDGGo",
    ".oDDGGGGDDDDGGo.",
    ".oGDDDDDDDDDDDo.",
    "..ooDDDDDDDDoo..",
    "....oooTTooo....",
    "......oTTo......",
    "......oTTo......",
    ".....oTTTTo.....",
    "....oooooooo....",
]
MUSHROOM = [
    "..oooo..",
    ".oRRWRo.",
    "oRWRRRRo",
    "oRRRRWRo",
    ".oooooo.",
    "..oSSo..",
    "..oSSo..",
    "..oooo..",
]
STUMP = [
    "..oooooo..",
    ".oYYYYYYo.",
    "oBYyyyyYBo",
    "oBBYYYYBBo",
    "oBBBBBBBBo",
    "oBDBBBBDBo",
    ".oooooooo.",
]
TUFT = [
    "..o...o..",
    ".oGo.oGo.",
    ".oGo.oGoo",
    "oGGooGGGo",
    "oGGGGGGGo",
]
PINE = [
    "......o......",
    ".....oGo.....",
    "....oLGGo....",
    "...oLGGGDo...",
    "....oGGDo....",
    "...oLGGGDo...",
    "..oLGGGGGDo..",
    ".oLGGGGGGGDo.",
    "..oGGGGGGDo..",
    ".oLGGGGGGDDo.",
    "oLGGGGGGGGDDo",
    "oDDDGGGGDDDDo",
    ".ooooTTToooo.",
    "....oTTTo....",
    "....ooooo....",
]
FENCE = [
    "ooo....ooo....ooo",
    "oPo....oPo....oPo",
    "oPooooooPooooooPo",
    "oPBBBBBBPBBBBBBPo",
    "oPooooooPooooooPo",
    "oPo....oPo....oPo",
    "oPooooooPooooooPo",
    "oPBBBBBBPBBBBBBPo",
    "oPooooooPooooooPo",
    "oDo....oDo....oDo",
    "ooo....ooo....ooo",
]
BED = [
    "oooooooooooo",
    "oWWWWWWWWWWo",
    "oWPPPPPPPPWo",
    "oWPPPPPPPPWo",
    "oooooooooooo",
    "oBBBBBBBBBBo",
    "oBbBBBBBBbBo",
    "oBBBBBBBBBBo",
    "oBBBBBBBBBBo",
    "oBbBBBBBBbBo",
    "oBBBBBBBBBBo",
    "oBBBBBBBBBBo",
    "oDDDDDDDDDDo",
    "oooooooooooo",
]
TABLE = [
    ".oooooooooooo.",
    "oTTTTTTTTTTTTo",
    "oTttTTTTTTttTo",
    "oTTTTTTTTTTTTo",
    "oTTTTTTTTTTTTo",
    "oTttTTTTTTttTo",
    "oTTTTTTTTTTTTo",
    "oDDDDDDDDDDDDo",
    "oDo........oDo",
    "ooo........ooo",
]
BARREL = [
    "..oooooo..",
    ".oBBBBBBo.",
    "oBbBBBBbBo",
    "oIIIIIIIIo",
    "oBbBBBBbBo",
    "oBbBBBBbBo",
    "oBbBBBBbBo",
    "oBbBBBBbBo",
    "oIIIIIIIIo",
    "oBbBBBBbBo",
    ".oBBBBBBo.",
    "..oooooo..",
]
CRATE = [
    "oooooooooooo",
    "oCCCCCCCCCCo",
    "oCDCCCCCCDCo",
    "oCCDCCCCDCCo",
    "oCCCDCCDCCCo",
    "oCCCCDDCCCCo",
    "oCCCCDDCCCCo",
    "oCCCDCCDCCCo",
    "oCCDCCCCDCCo",
    "oCDCCCCCCDCo",
    "oCCCCCCCCCCo",
    "oooooooooooo",
]
HAY = [
    ".oooooooooooo.",
    "oYYyYYYYyYYYYo",
    "oYyYYYyYYYyYYo",
    "oRRRRRRRRRRRRo",
    "oYYYyYYYYyYYYo",
    "oYyYYYYyYYYyYo",
    "oRRRRRRRRRRRRo",
    "oYYyYYYYYyYYYo",
    "oyYYYyYYYYYyYo",
    ".oooooooooooo.",
]
SHELF = [
    "oooooooooooooooo",
    "oSSSSSSSSSSSSSSo",
    "oSRGBRYGBRRGYBSo",
    "oSRGBRYGBRRGYBSo",
    "oSSSSSSSSSSSSSSo",
    "oSBYRGBRYGBRGRSo",
    "oSSSSSSSSSSSSSSo",
    "oooooooooooooooo",
]
RUBBLE = [
    "....ooo.....",
    "...oSSSo.oo.",
    ".ooSsSSooSSo",
    "oSSSoSsoSSso",
    "oSsSSoooSSo.",
    ".oSSSSo.oo..",
    "..ooooo.....",
]
WELL = [
    "..oooooooo..",
    ".oRRRRRRRRo.",
    "oRRRRRRRRRRo",
    "oooooooooooo",
    ".oPo.Y..oPo.",
    ".oPo.Y..oPo.",
    ".oPo.Y..oPo.",
    "oooooooooooo",
    "oSSSsSSSsSSo",
    "osSSSsSSSSso",
    "oSSsSSSsSSSo",
    ".oooooooooo.",
]

# ---------- icons ----------

ICONS = {
    "icon_damage": ([
        "........oo",
        ".......oWo",
        "......oWLo",
        ".....oWLo.",
        ".o..oWLo..",
        "oYo.oLo...",
        ".oYoLo....",
        "..oYo.....",
        ".oBooYo...",
        "oBo...oo..",
    ], {"W": (240, 240, 250), "L": (160, 170, 190), "Y": (230, 180, 50), "B": (120, 80, 40)}),
    "icon_speed": ([
        "..oooo....",
        "..oBBo....",
        "..oBBo....",
        "..oBBo....",
        "..oBBo....",
        "..oBBBooo.",
        ".oBBBBBBBo",
        ".oDDDDDDDo",
        "..ooooooo.",
        "..........",
    ], {"B": (150, 95, 50), "D": (90, 55, 30)}),
    "icon_armor": ([
        ".oooooooo.",
        "oBBBWWBBBo",
        "oBBBWWBBBo",
        "oWWWWWWWWo",
        "oBBBWWBBBo",
        ".oBBWWBBo.",
        ".oBBWWBBo.",
        "..oBWWBo..",
        "...oWWo...",
        "....oo....",
    ], {"B": (60, 110, 200), "W": (230, 200, 70)}),
    "icon_luck": ([
        "..oo.oo...",
        ".oGGoGGo..",
        ".oGGGGGo..",
        "..oGLGo...",
        ".oGGGGGo..",
        "oGGGoGGGo.",
        ".oGo.oGo..",
        "....oBo...",
        "....oBo...",
        "....oo....",
    ], {"G": (70, 190, 80), "L": (160, 240, 150), "B": (90, 140, 60)}),
    "icon_crit": ([
        "....oo....",
        "....oRo...",
        "..oooRooo.",
        ".oR..R..Ro",
        "ooRRRWRRRo",
        ".oR..R..Ro",
        "..oooRooo.",
        "....oRo...",
        "....oo....",
        "..........",
    ], {"R": (230, 50, 50), "W": (255, 255, 255)}),
    "icon_multishot": ([
        ".o..o..o..",
        "oWooWooWo.",
        ".Bo.Bo.Bo.",
        ".Bo.Bo.Bo.",
        ".Bo.Bo.Bo.",
        ".Bo.Bo.Bo.",
        "oFooFooFo.",
        ".o..o..o..",
        "..........",
        "..........",
    ], {"W": (230, 230, 240), "B": (150, 100, 50), "F": (220, 60, 60)}),
    "icon_pierce": ([
        ".........o",
        "........oW",
        ".......oWo",
        "......oLo.",
        ".....oBo..",
        "....oBo...",
        "...oBo....",
        "..oBo.....",
        ".oBo......",
        ".oo.......",
    ], {"W": (240, 240, 250), "L": (170, 170, 190), "B": (150, 100, 50)}),
    "icon_regen": ([
        "...oooo...",
        "...oGLo...",
        "...oGLo...",
        "oooGGLLooo",
        "oGGGGLLLLo",
        "oDDDDGGGGo",
        "oooDDGGooo",
        "...oDGo...",
        "...oDGo...",
        "...oooo...",
    ], {"G": (80, 210, 90), "L": (170, 250, 160), "D": (40, 140, 60)}),
    "icon_fire_rate": ([
        ".....ooo..",
        "....oYYo..",
        "...oYYo...",
        "..oYYoo...",
        ".oYYYYYo..",
        ".ooooYYo..",
        "....oYo...",
        "...oYo....",
        "...oo.....",
        "..........",
    ], {"Y": (255, 220, 60)}),
    "icon_aura": ([
        "..oooooo..",
        ".oCCCCCCo.",
        "oCCooooCCo",
        "oCo....oCo",
        "oCo.oo.oCo",
        "oCo.oo.oCo",
        "oCo....oCo",
        "oCCooooCCo",
        ".oCCCCCCo.",
        "..oooooo..",
    ], {"C": (250, 230, 120)}),
    "icon_wand": ([
        "......ooo.",
        ".....oYWYo",
        ".....oYYYo",
        "....oBooo.",
        "...oBo....",
        "..oBo.....",
        ".oBo......",
        "oBo.......",
        "oo........",
        "..........",
    ], {"Y": (255, 220, 60), "W": (255, 255, 230), "B": (120, 80, 50)}),
}


# ---------- tiles ----------

def speckled_tile(base, specks, seed, flowers=0):
    rng = random.Random(seed)
    tile = pygame.Surface((16, 16))
    tile.fill(base)
    for color, count in specks:
        for _ in range(count):
            tile.set_at((rng.randrange(16), rng.randrange(16)), color)
    # grass blades, with a light tip
    if base[1] > base[0]:
        for _ in range(6):
            x = rng.randrange(1, 15)
            y = rng.randrange(2, 15)
            tile.set_at((x, y), (55, 115, 58))
            tile.set_at((x - 1, y - 1), (55, 115, 58))
            tile.set_at((x + 1, y - 1), (55, 115, 58))
            tile.set_at((x + 1, y - 2), (110, 182, 98))
    colors = [(250, 250, 250), (255, 220, 70), (240, 120, 180), (150, 170, 255)]
    for _ in range(flowers):
        x = rng.randrange(1, 15)
        y = rng.randrange(1, 15)
        color = rng.choice(colors)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            tile.set_at((x + dx, y + dy), color)
        tile.set_at((x, y), (250, 200, 50))
    return tile


def plank_tile(base, line, specks, seed):
    rng = random.Random(seed)
    tile = pygame.Surface((16, 16))
    tile.fill(base)
    for color, count in specks:
        for _ in range(count):
            tile.set_at((rng.randrange(16), rng.randrange(16)), color)
    for y in (0, 4, 8, 12):
        for x in range(16):
            tile.set_at((x, y + 3), line)
        seam = rng.randrange(16)
        for dy in range(3):
            tile.set_at((seam, y + dy), line)
    return tile


def stone_tile(base, line, specks, seed):
    rng = random.Random(seed)
    tile = pygame.Surface((16, 16))
    tile.fill(base)
    for color, count in specks:
        for _ in range(count):
            tile.set_at((rng.randrange(16), rng.randrange(16)), color)
    # stones in a brick pattern
    for x in range(16):
        tile.set_at((x, 7), line)
        tile.set_at((x, 15), line)
    for y in range(8):
        tile.set_at((7, y), line)
        tile.set_at((15, y), line)
        tile.set_at((3, y + 8), line)
        tile.set_at((11, y + 8), line)
    return tile


def water_tile(base, ripple, seed):
    rng = random.Random(seed)
    tile = pygame.Surface((16, 16))
    tile.fill(base)
    # short little waves
    for _ in range(5):
        x = rng.randrange(0, 13)
        y = rng.randrange(1, 15)
        for dx in range(3):
            tile.set_at((x + dx, y), ripple)
    return tile


def make_tiles():
    grass = (72, 142, 72)
    grass_specks = [((64, 128, 64), 22), ((86, 158, 82), 16), ((78, 150, 70), 12), ((100, 168, 88), 5)]
    for i in range(4):
        save(speckled_tile(grass, grass_specks, i + 1), "tiles", f"grass_{i}", 4)
    save(speckled_tile(grass, grass_specks, 10, flowers=3), "tiles", "flowers", 4)
    dirt_specks = [((125, 92, 60), 26), ((158, 122, 84), 18), ((110, 110, 105), 4)]
    save(speckled_tile((142, 106, 70), dirt_specks, 20), "tiles", "dirt", 4)
    save(plank_tile((165, 115, 70), (120, 80, 48), [((150, 102, 62), 20)], 30), "tiles", "floor_wood", 4)
    save(plank_tile((128, 92, 58), (88, 60, 38), [((112, 80, 50), 20), ((190, 160, 90), 6)], 31), "tiles", "floor_planks", 4)
    save(stone_tile((150, 150, 158), (105, 105, 115), [((135, 135, 145), 20), ((170, 170, 178), 12)], 32), "tiles", "floor_stone", 4)

    dark = (58, 120, 62)
    save(speckled_tile(dark, [((50, 106, 54), 22), ((70, 136, 70), 14)], 40), "tiles", "grass_dark", 4)
    save(speckled_tile((218, 200, 140), [((200, 182, 122), 24), ((235, 220, 165), 14)], 41), "tiles", "sand", 4)
    save(water_tile((70, 140, 205), (100, 170, 225), 42), "tiles", "water", 4)
    save(water_tile((40, 92, 165), (62, 118, 190), 43), "tiles", "water_deep", 4)
    save(speckled_tile((120, 116, 118), [((100, 96, 100), 26), ((145, 140, 140), 16), ((85, 82, 88), 8)], 44), "tiles", "mountain", 4)
    save(speckled_tile((242, 242, 250), [((218, 222, 235), 20), ((250, 252, 255), 14)], 45), "tiles", "snow", 4)


def make_aura():
    size = 64
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surface, (250, 230, 120, 50), (size // 2, size // 2), size // 2)
    pygame.draw.circle(surface, (250, 230, 120, 160), (size // 2, size // 2), size // 2, 2)
    path = os.path.join(ASSETS, "projectiles")
    os.makedirs(path, exist_ok=True)
    pygame.image.save(surface, os.path.join(path, "aura.png"))


def bolt_palette(white, light, color):
    return {"W": white, "L": light, "C": color}


# ---------- new enemies, weapons and shop items ----------

GHOST_BODY = [
    "................",
    ".....oooooo.....",
    "....oWWWWWWo....",
    "...oWWWWWWWWo...",
    "..oWWWWWWWWWWo..",
    "..oWWEEWWEEWWo..",
    "..oWWEEWWEEWWo..",
    "..oWWWWWWWWWWo..",
    "..oWWWWMMWWWWo..",
    "..oWWWWMMWWWWo..",
    "..oWWWWWWWWWWo..",
]
GHOST_TAIL_A = [
    "..oWLWWWWWWLWo..",
    "..oLWoWLLWoWLo..",
    "..oo.o.oo.o.oo..",
]
GHOST_TAIL_B = [
    "..oWLWWWWWWLWo..",
    "..oWLoWLLWoLWo..",
    "..o.oo.oo.oo.o..",
]

BOMBER = [
    "..........oY....",
    ".........oYo....",
    "........oo......",
    ".....ooooooo....",
    "....oKKKKKKKo...",
    "...oKWKKKKKKKo..",
    "..oKWKKKKKKKKKo.",
    "..oKKKEKKKEKKKo.",
    "..oKKKEKKKEKKKo.",
    "..oKKKKKKKKKKKo.",
    "..oKKKRRRRRKKKo.",
    "...oKKKKKKKKKo..",
    "....oDDDDDDDo...",
]
BOMBER_LEGS_A = [
    "....oFo..oFo....",
    "....ooo..ooo....",
    "................",
]
BOMBER_LEGS_B = [
    "...oFo....oFo...",
    "...ooo....ooo...",
    "................",
]

SPIDER_0 = [
    "................",
    "o..o........o..o",
    ".o..o......o..o.",
    "..o..oooooo..o..",
    "...ooBBBBBBoo...",
    "oooBBBBBBBBBBooo",
    "...oBBEBBEBBo...",
    "..ooBBBBBBBBoo..",
    ".o..oBBRRBBo..o.",
    "o..o..oooo..o..o",
    "...o........o...",
    "................",
]
SPIDER_1 = [
    "................",
    "................",
    "o..o........o..o",
    ".o.o.oooooo.o.o.",
    "..oooBBBBBBooo..",
    "oooBBBBBBBBBBooo",
    "...oBBEBBEBBo...",
    "..ooBBBBBBBBoo..",
    "..o.oBBRRBBo.o..",
    ".o..o.oooo.o..o.",
    "o..o........o..o",
    "................",
]

MIMIC_0 = [
    "................",
    "..oooooooooooo..",
    ".oBBBBBBBBBBBBo.",
    ".oBDBBBBBBBBDBo.",
    ".oooooooooooooo.",
    ".oRWRWRWRWRWRRo.",
    ".oRRRRERRERRRRo.",
    ".oRRRRRRRRRRRRo.",
    ".oRWRWRWRWRWRRo.",
    ".ooooooYYoooooo.",
    ".oBBBBBYYBBBBBo.",
    ".oBDBBBBBBBBDBo.",
    ".oDDDDDDDDDDDDo.",
    "..oooooooooooo..",
]
MIMIC_1 = MIMIC_0[:5] + [
    ".oWRWRWRWRWRWRo.",
    ".oRRRRERRERRRRo.",
    ".oRRRRRRRRRRRRo.",
    ".oWRWRWRWRWRWRo.",
] + MIMIC_0[9:]

CROWN = [
    "....oYoYYoYo....",
    "....oYYYYYYo....",
    "....oooooooo....",
]

BOOMERANG = [
    "oo........",
    "oBo.......",
    "oBBo......",
    ".oBBo.....",
    "..oBBo....",
    "..oBBBoooo",
    "...oBBBBWo",
    "....ooooo.",
]

METEOR = [
    "...oooo...",
    "..oRRRRo..",
    ".oRYYRRRo.",
    "oRYWYRRRDo",
    "oRYYRRRDDo",
    "oRRRRRDDDo",
    "oRRRDDDDDo",
    ".oRDDDDDo.",
    "..oDDDDo..",
    "...oooo...",
]

FLAME_0 = [
    "...o....",
    "..oRo...",
    "..oRRo..",
    ".oRYRo..",
    ".oRYYRo.",
    "oRYWYRo.",
    "oRYWWYRo",
    "oRYWWYRo",
    ".oRYYRo.",
    "..oooo..",
]
FLAME_1 = [
    "....o...",
    "...oRo..",
    "..oRRo..",
    "..oRYRo.",
    ".oRYYRo.",
    ".oRYWYRo",
    "oRYWWYRo",
    "oRYWWYRo",
    ".oRYYRo.",
    "..oooo..",
]

SNOWFLAKE = [
    "....oo....",
    ".o.oWWo.o.",
    "oWooWWooWo",
    ".oWoWWoWo.",
    "ooooWWoooo",
    "oWWWWWWWWo",
    "ooooWWoooo",
    ".oWoWWoWo.",
    "oWooWWooWo",
    ".o.oWWo.o.",
    "....oo....",
]

BOOTS = [
    "..oooo....",
    "..oBBo....",
    "..oBBo.oo.",
    "..oBBoWWYo",
    "..oBBo.oo.",
    "..oBBBooo.",
    ".oBBBBBBBo",
    ".oDDDDDDDo",
    "..ooooooo.",
]

POTION = [
    "...oooo...",
    "...oCCo...",
    "....oo....",
    "...oWWo...",
    "..oWPPWo..",
    ".oPPWPPPo.",
    "oPPWPPPPPo",
    "oPPPPPPPDo",
    "oPPPPPPDDo",
    ".oPPPPDDo.",
    "..oooooo..",
]


CAT = [
    "...oo......oo...",
    "...oHo....oHo...",
    "...oHHooooHHo...",
    "...oHHHHHHHHo...",
    "...oHHHHHHHHo...",
    "...oHEHHHHEHo...",
    "...oHHHPPHHHo...",
    "....oHWWWWHo....",
    "...ooBBBBBBoo...",
    "..oHoBBAABBoHo..",
    "..oHoBBAABBoHo..",
    "..ooBBBBBBBBoo..",
    "...ooBBBBBBoo...",
]

DINO = [
    "......oo........",
    ".....oAAo.......",
    "....oHHHHooooo..",
    "...oHHHHHHHHHHo.",
    "...oHHHHHEHHHHo.",
    "..oAoHHHHHHHHHo.",
    "...oHHHHHWWWWWo.",
    "....oHHHHHooooo.",
    "...ooHHHHHHoo...",
    "..oHoHHWWHHoHo..",
    "..oHoHHWWHHoHo..",
    "..ooHHHHHHHHoo..",
    "...ooHHHHHHoo...",
]

GEM_SKINS = {
    "skin_banana": (HERO, hero_palette((250, 220, 60), (255, 245, 150), (120, 90, 30), (240, 200, 50), (250, 230, 90))),
    "skin_clown": (HERO, hero_palette((230, 60, 160), (80, 200, 250), (250, 80, 40), (60, 180, 80), (250, 240, 240))),
    "skin_whale": (HERO, hero_palette((70, 110, 170), (200, 220, 240), (70, 110, 170), (50, 80, 130), (120, 160, 210))),
    "skin_cat": (CAT, {"H": (240, 150, 60), "E": (60, 200, 80), "P": (250, 150, 170), "W": (250, 240, 230), "B": (80, 80, 160), "A": (250, 240, 230), "L": (200, 110, 40)}),
    "skin_dino": (DINO, {"H": (90, 190, 80), "A": (240, 200, 60), "E": DARK, "W": (230, 240, 200), "L": (60, 140, 60)}),
}


def make_extra():
    for name, (body, palette) in GEM_SKINS.items():
        save_frames(body, LEGS_A, LEGS_B, palette, "players", name, 3)

    ghost = {"W": (230, 235, 255), "L": (170, 180, 220), "E": DARK, "M": (60, 60, 90)}
    save_grid(GHOST_BODY + GHOST_TAIL_A, ghost, "enemies", "ghost_0", 3)
    save_grid(GHOST_BODY[1:] + GHOST_TAIL_B + ["................"], ghost, "enemies", "ghost_1", 3)

    bomber = {"K": (55, 55, 70), "W": (150, 150, 170), "E": (255, 80, 60), "R": (200, 40, 40), "D": (35, 35, 45), "Y": (255, 200, 50), "F": (255, 140, 40)}
    save_frames(BOMBER, BOMBER_LEGS_A, BOMBER_LEGS_B, bomber, "enemies", "bomber", 3)

    necro = {"H": (50, 30, 70), "S": (170, 190, 170), "E": (255, 60, 60), "B": (70, 40, 90), "A": (120, 240, 120), "L": (40, 25, 50)}
    save_frames(HOOD, LEGS_A, LEGS_B, necro, "enemies", "necro", 3)

    skeleton = hero_palette((215, 215, 200), (120, 120, 110), (235, 235, 220), (180, 180, 165), (235, 235, 220))
    skeleton["E"] = (255, 60, 60)
    save_frames(HERO, LEGS_A, LEGS_B, skeleton, "enemies", "skeleton", 3)

    shaman = {"H": (60, 140, 70), "A": (120, 255, 140), "S": (200, 160, 110), "E": DARK, "W": (240, 230, 200), "B": (90, 70, 40), "L": (60, 45, 30)}
    save_frames(WIZARD, LEGS_A, LEGS_B, shaman, "enemies", "shaman", 3)

    spider = {"B": (50, 40, 50), "E": (255, 60, 60), "R": (180, 30, 60)}
    save_grid(SPIDER_0, spider, "enemies", "spider_0", 3)
    save_grid(SPIDER_1, spider, "enemies", "spider_1", 3)

    mimic = {"B": (160, 100, 50), "D": (110, 65, 35), "Y": (245, 200, 60), "R": (120, 20, 30), "W": (245, 245, 230), "E": (255, 220, 60)}
    save_grid(MIMIC_0, mimic, "enemies", "mimic_0", 3)
    save_grid(MIMIC_1, mimic, "enemies", "mimic_1", 3)

    king = {"G": (80, 140, 230), "H": (180, 210, 255), "E": DARK, "M": (30, 50, 110), "D": (50, 90, 180), "Y": (255, 215, 60)}
    save_grid(CROWN + SLIME_0[3:], king, "enemies", "king_slime_0", 5)
    save_grid(["................"] * 2 + CROWN + SLIME_1[5:], king, "enemies", "king_slime_1", 5)

    save_grid(BOOMERANG, {"B": (200, 130, 60), "W": (250, 220, 150)}, "projectiles", "boomerang", 3)
    save_grid(METEOR, {"R": (200, 70, 40), "Y": (255, 180, 60), "W": (255, 250, 200), "D": (110, 50, 40)}, "projectiles", "meteor", 3)
    flame = {"R": (220, 60, 30), "Y": (255, 170, 40), "W": (255, 240, 180)}
    save_grid(FLAME_0, flame, "projectiles", "fire_0", 3)
    save_grid(FLAME_1, flame, "projectiles", "fire_1", 3)
    save_grid(BOLT, bolt_palette((255, 255, 255), (255, 120, 220), (80, 160, 255)), "projectiles", "bullet_rainbow", 3)
    save_grid(COIN, {"Y": (245, 200, 60), "W": (255, 250, 210), "D": (190, 140, 30)}, "projectiles", "bullet_coin", 2)

    save_grid(SNOWFLAKE, {"W": (200, 235, 255)}, "items", "freeze", 3)
    save_grid(BOOTS, {"B": (220, 60, 60), "D": (120, 30, 30), "W": (240, 240, 250), "Y": (255, 220, 80)}, "items", "boots", 3)
    save_grid(POTION, {"C": (150, 100, 50), "W": (230, 250, 230), "P": (120, 230, 120), "D": (60, 160, 80)}, "items", "potion", 3)


def main():
    pygame.init()

    for name, (body, palette) in SKINS.items():
        save_frames(body, LEGS_A, LEGS_B, palette, "players", name, 3)

    slime = {"G": (90, 200, 80), "H": (190, 250, 170), "E": DARK, "M": (40, 90, 40), "D": (55, 140, 55)}
    blob = {"G": (170, 80, 200), "H": (240, 190, 255), "E": DARK, "M": (80, 30, 100), "D": (120, 50, 150)}
    for name, palette, scale in [("slime", slime, 3), ("blob", blob, 3), ("mini_blob", blob, 2)]:
        save_grid(SLIME_0, palette, "enemies", name + "_0", scale)
        save_grid(SLIME_1, palette, "enemies", name + "_1", scale)

    bat = {"W": (90, 50, 120), "B": (60, 35, 80), "E": (255, 80, 80)}
    save_grid(BAT_0, bat, "enemies", "bat_0", 2)
    save_grid(BAT_1, bat, "enemies", "bat_1", 2)

    golem = {"R": (130, 120, 140), "L": (180, 170, 190), "D": (90, 80, 100), "C": (220, 80, 255), "P": (200, 90, 240)}
    save_frames(GOLEM, GOLEM_LEGS_A, GOLEM_LEGS_B, golem, "enemies", "golem", 3)

    goblin = {"H": (110, 75, 40), "S": (120, 190, 80), "E": (255, 60, 60), "B": (80, 110, 50), "A": (180, 140, 60), "L": (70, 50, 30)}
    save_frames(HOOD, LEGS_A, LEGS_B, goblin, "enemies", "archer", 3)

    boar = {"B": (130, 85, 55), "D": (90, 55, 35), "E": DARK, "P": (230, 150, 140), "W": (245, 245, 230)}
    save_frames(BOAR, BOAR_LEGS_A, BOAR_LEGS_B, boar, "enemies", "boar", 3)

    boss = {"H": (230, 220, 200), "R": (180, 40, 50), "D": (120, 25, 35), "Y": (255, 220, 60), "E": DARK, "W": (250, 250, 250), "C": (60, 50, 50)}
    save_grid(BOSS, boss, "enemies", "boss", 4)

    bolts = {
        "bullet_default": bolt_palette((255, 255, 230), (250, 240, 120), (220, 180, 40)),
        "bullet_white": bolt_palette((255, 255, 255), (235, 235, 245), (180, 180, 200)),
        "bullet_green": bolt_palette((220, 255, 220), (120, 240, 120), (40, 170, 60)),
        "bullet_pink": bolt_palette((255, 230, 245), (250, 130, 200), (200, 60, 150)),
        "bullet_blue": bolt_palette((230, 240, 255), (110, 170, 255), (50, 90, 220)),
        "bullet_red": bolt_palette((255, 220, 220), (255, 90, 90), (190, 30, 40)),
        "bullet_gold": bolt_palette((255, 255, 210), (255, 215, 50), (200, 140, 20)),
        "bullet_void": bolt_palette((230, 200, 255), (130, 60, 200), (40, 20, 60)),
    }
    for name, palette in bolts.items():
        save_grid(BOLT, palette, "projectiles", name, 3)
    save_grid(FIREBALL, {"R": (230, 70, 30), "Y": (255, 190, 50), "W": (255, 250, 210)}, "projectiles", "bullet_fire", 3)
    save_grid(ICE, {"C": (120, 210, 255), "W": (235, 250, 255), "L": (70, 140, 230)}, "projectiles", "bullet_ice", 3)
    save_grid(STAR, {"Y": (255, 220, 60), "W": (255, 255, 220)}, "projectiles", "bullet_star", 2)
    save_grid(HEART, {"R": (250, 110, 190), "W": (255, 230, 245)}, "projectiles", "bullet_heart", 2)
    save_grid(ARROW, {"F": (60, 160, 230), "B": (150, 100, 50), "W": (220, 220, 230)}, "projectiles", "bullet_arrow", 2)
    save_grid(ARROW, {"F": (200, 40, 40), "B": (90, 60, 40), "W": (200, 60, 60)}, "projectiles", "enemy_arrow", 2)
    save_grid(BOLT, bolt_palette((255, 200, 220), (240, 60, 90), (150, 20, 50)), "projectiles", "enemy_orb", 3)
    save_grid(KNIFE, {"H": (120, 80, 50), "W": (235, 235, 245), "L": (160, 165, 185)}, "projectiles", "knife", 2)
    save_grid(BLADE, {"W": (235, 235, 245), "L": (160, 165, 185), "D": (80, 80, 100)}, "projectiles", "blade", 3)
    save_grid(LIGHTNING, {"Y": (255, 230, 80), "W": (255, 255, 240)}, "projectiles", "lightning", 3)
    make_aura()

    save_grid(GEM, {"L": (170, 240, 255), "B": (80, 200, 240), "D": (40, 120, 190)}, "items", "gem_small", 2)
    save_grid(GEM, {"L": (190, 255, 190), "B": (80, 220, 110), "D": (40, 150, 70)}, "items", "gem_big", 3)
    save_grid(GEM, {"L": (255, 190, 190), "B": (230, 60, 70), "D": (150, 30, 40)}, "items", "gem_red", 3)
    save_grid(COIN, {"Y": (245, 200, 60), "W": (255, 250, 210), "D": (190, 140, 30)}, "items", "coin", 3)
    save_grid(HEART, {"R": (225, 45, 55), "W": (255, 200, 200)}, "items", "heart", 3)
    save_grid(HEART, {"R": (75, 40, 50), "W": (100, 60, 70)}, "items", "heart_empty", 3)
    save_grid(MAGNET, {"W": (220, 220, 230), "R": (220, 50, 50)}, "items", "magnet", 3)
    save_grid(BOMB, {"K": (55, 55, 70), "W": (150, 150, 170), "D": (35, 35, 45), "Y": (255, 200, 50)}, "items", "bomb", 3)
    save_grid(CHEST, {"B": (160, 100, 50), "D": (110, 65, 35), "Y": (245, 200, 60)}, "items", "chest", 3)

    make_tiles()
    save_grid(ROCK, {"R": (140, 140, 150), "L": (190, 190, 200), "D": (100, 100, 112)}, "deco", "rock", 3)
    save_grid(BUSH, {"G": (50, 130, 55), "L": (100, 180, 90), "D": (35, 95, 42), "B": (220, 50, 60)}, "deco", "bush", 3)
    save_grid(TREE, {"G": (45, 125, 55), "L": (95, 175, 85), "D": (30, 90, 40), "T": (110, 70, 40)}, "deco", "tree", 4)
    save_grid(MUSHROOM, {"R": (220, 50, 50), "W": (250, 250, 250), "S": (235, 225, 200)}, "deco", "mushroom", 3)
    save_grid(STUMP, {"Y": (215, 175, 110), "y": (170, 125, 70), "B": (120, 80, 45), "D": (85, 55, 30)}, "deco", "stump", 3)
    save_grid(TUFT, {"G": (60, 130, 60)}, "deco", "tuft", 3)
    save_grid(PINE, {"G": (35, 110, 65), "L": (70, 150, 90), "D": (25, 80, 50), "T": (110, 70, 40)}, "deco", "pine", 4)
    save_grid(FENCE, {"P": (170, 120, 70), "B": (150, 100, 60), "D": (110, 75, 45)}, "deco", "fence", 3)
    save_grid(BED, {"W": (240, 235, 225), "P": (250, 250, 250), "B": (70, 110, 200), "b": (50, 80, 160), "D": (120, 75, 40)}, "deco", "bed", 3)
    save_grid(TABLE, {"T": (170, 115, 65), "t": (140, 92, 52), "D": (110, 70, 40)}, "deco", "table", 3)
    save_grid(BARREL, {"B": (150, 100, 55), "b": (115, 75, 40), "I": (120, 120, 130)}, "deco", "barrel", 3)
    save_grid(CRATE, {"C": (190, 140, 80), "D": (140, 95, 50)}, "deco", "crate", 3)
    save_grid(HAY, {"Y": (230, 200, 100), "y": (190, 160, 70), "R": (140, 100, 55)}, "deco", "hay", 3)
    save_grid(SHELF, {"S": (120, 80, 45), "R": (200, 60, 60), "G": (70, 160, 80), "B": (70, 110, 200), "Y": (230, 190, 60)}, "deco", "shelf", 3)
    save_grid(RUBBLE, {"S": (140, 140, 150), "s": (105, 105, 115)}, "deco", "rubble", 3)
    save_grid(WELL, {"R": (150, 90, 50), "P": (120, 80, 45), "Y": (210, 180, 120), "S": (160, 160, 170), "s": (115, 115, 125)}, "deco", "well", 4)

    for name, (rows, palette) in ICONS.items():
        save_grid(rows, palette, "icons", name, 3)

    make_extra()

    print("sprites gemaakt in", os.path.abspath(ASSETS))


if __name__ == "__main__":
    main()

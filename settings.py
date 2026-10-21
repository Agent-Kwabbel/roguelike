# Screen
W, H = 960, 640
FPS = 60
TILE = 64

# World
CHUNK_TILES = 8
CHUNKS_CACHED = 80
DIRT_PATCH_CHANCE = 0.35
FLOWER_TILE_CHANCE = 0.06
DECO_PER_CHUNK = (3, 8)
DECORATIONS = {"tuft": 6, "rock": 3, "bush": 3, "mushroom": 2, "stump": 1, "tree": 2, "pine": 2, "fence": 1}
# big things, at most one per chunk
STRUCTURE_CHANCE = 0.08
STRUCTURES = {"well": 1}

# Terrain. Height goes from 0 to 1, each level starts at its threshold.
TERRAIN_SCALE = 1300
TERRAIN_OCTAVES = 4
MOUNTAIN_SCALE = 2600
MOISTURE_SCALE = 1400
# around the start it's always flat grass
SAFE_RADIUS = 700
TERRAIN_LEVELS = [
    ("deep_water", 0.0),
    ("water", 0.22),
    ("sand", 0.28),
    ("grass_low", 0.32),
    ("grass_mid", 0.47),
    ("grass_high", 0.6),
    ("rock", 0.72),
    ("snow", 0.85),
]
BLOCKED_LEVELS = ("deep_water", "rock", "snow")
GRASS_LEVELS = ("grass_low", "grass_mid", "grass_high")
SHADE_STRENGTH = 6
CLIFF_HEIGHT = 36
FOREST_MOISTURE = 0.6

# Buildings you can enter, at most one per chunk. size is in tiles.
# loot: a number below 1 is a chance, 1 or higher is the max amount
BUILDING_CHANCE = 0.18
WALL = 16
ROOF_FADE = 600
# roof becomes see-through when you're close
ROOF_NEAR_ALPHA = 110
ROOF_NEAR_RANGE = 180
LOOT_COIN_VALUE = 3
BUILDINGS = {
    "house": {"weight": 4, "size": (5, 4), "floor": "floor_wood", "wall": (225, 205, 165), "roof": (185, 75, 60),
              "furniture": ["bed", "table", "barrel"], "loot": {"chest": 0.4, "heart": 0.5, "coin": 3}},
    "barn": {"weight": 2, "size": (6, 4), "floor": "floor_planks", "wall": (150, 95, 60), "roof": (130, 85, 55),
             "furniture": ["hay", "hay", "crate", "crate"], "loot": {"coin": 4, "gems": 6}},
    "tower": {"weight": 1, "size": (4, 4), "floor": "floor_stone", "wall": (150, 150, 160), "roof": (90, 95, 130),
              "furniture": ["shelf", "barrel"], "loot": {"chest": 1.0, "bomb": 0.3, "magnet": 0.3}},
    "ruin": {"weight": 2, "size": (5, 3), "floor": "floor_stone", "wall": (130, 130, 140), "roof": None,
             "furniture": ["rubble", "rubble"], "loot": {"coin": 2, "heart": 0.3}},
}

# Player
PLAYER_SPEED = 220
PLAYER_RADIUS = 14
PLAYER_SPRITE = "skin_default"

# Enemies
SPAWN_INTERVAL = 1.2
SPAWN_INTERVAL_MIN = 0.3
SPAWN_INTERVAL_DECAY = 0.01
SPAWN_DISTANCE = 600

# Difficulty (per minute of play time)
HP_GROWTH = 0.45
SPEED_GROWTH = 0.06
SPEED_FACTOR_MAX = 1.4
MAX_ENEMIES = 150

# Difficulty levels, normal is the default balance
DIFFICULTIES = {
    "easy": {"name": "Easy", "spawn": 1.3, "enemy_hp": 0.8, "enemy_speed": 0.9, "enemy_damage": 1, "player_hp": 6},
    "normal": {"name": "Normal", "spawn": 0.9, "enemy_hp": 1.1, "enemy_speed": 1.05, "enemy_damage": 1, "player_hp": 5},
    "hard": {"name": "Hard", "spawn": 0.7, "enemy_hp": 1.4, "enemy_speed": 1.12, "enemy_damage": 1, "player_hp": 4},
    "extreme": {"name": "Extreme", "spawn": 0.5, "enemy_hp": 1.8, "enemy_speed": 1.25, "enemy_damage": 2, "player_hp": 3},
    "nightmare": {"name": "Nightmare", "spawn": 0.4, "enemy_hp": 2.3, "enemy_speed": 1.35, "enemy_damage": 2,
                  "player_hp": 2},
}

# ai: chase walks straight at you, shooter keeps distance and shoots,
# dasher charges at you, boss shoots bullets in a ring,
# ghost goes through walls, exploder explodes, summoner calls skeletons,
# zigzag swerves, healer heals other enemies, mimic pretends to be a chest
ENEMY_TYPES = {
    "walker": {"speed": 70, "radius": 16, "color": (90, 200, 80), "hp": 3, "xp": 1, "ai": "chase", "sprite": "slime"},
    "runner": {"speed": 140, "radius": 10, "color": (90, 50, 120), "hp": 1, "xp": 2, "ai": "chase", "sprite": "bat"},
    "tank": {"speed": 50, "radius": 22, "color": (130, 120, 140), "hp": 12, "xp": 5, "ai": "chase", "sprite": "golem"},
    "archer": {"speed": 65, "radius": 14, "color": (120, 190, 80), "hp": 4, "xp": 3, "ai": "shooter", "sprite": "archer"},
    "blob": {"speed": 60, "radius": 18, "color": (170, 80, 200), "hp": 6, "xp": 3, "ai": "chase", "sprite": "blob"},
    "mini_blob": {"speed": 105, "radius": 10, "color": (170, 80, 200), "hp": 1, "xp": 1, "ai": "chase", "sprite": "mini_blob"},
    "boar": {"speed": 75, "radius": 16, "color": (130, 85, 55), "hp": 6, "xp": 3, "ai": "dasher", "sprite": "boar"},
    "boss": {"speed": 45, "radius": 38, "color": (180, 40, 50), "hp": 220, "xp": 40, "ai": "boss", "sprite": "boss"},
    "ghost": {"speed": 80, "radius": 15, "color": (220, 225, 255), "hp": 3, "xp": 2, "ai": "ghost", "sprite": "ghost"},
    "bomber": {"speed": 95, "radius": 15, "color": (255, 140, 40), "hp": 2, "xp": 2, "ai": "exploder", "sprite": "bomber"},
    "necro": {"speed": 55, "radius": 15, "color": (120, 240, 120), "hp": 8, "xp": 6, "ai": "summoner", "sprite": "necro"},
    "skeleton": {"speed": 90, "radius": 13, "color": (215, 215, 200), "hp": 2, "xp": 1, "ai": "chase", "sprite": "skeleton"},
    "spider": {"speed": 130, "radius": 14, "color": (50, 40, 50), "hp": 2, "xp": 2, "ai": "zigzag", "sprite": "spider"},
    "shaman": {"speed": 55, "radius": 15, "color": (120, 255, 140), "hp": 7, "xp": 5, "ai": "healer", "sprite": "shaman"},
    "mimic": {"speed": 120, "radius": 18, "color": (160, 100, 50), "hp": 15, "xp": 8, "ai": "mimic", "sprite": "mimic"},
    "king_slime": {"speed": 40, "radius": 36, "color": (80, 140, 230), "hp": 80, "xp": 25, "ai": "chase", "sprite": "king_slime"},
}

# From when and how often
SPAWN_TABLE = {
    "walker": {"start": 0, "weight": 10},
    "runner": {"start": 20, "weight": 5},
    "archer": {"start": 45, "weight": 3},
    "tank": {"start": 60, "weight": 2},
    "boar": {"start": 90, "weight": 3},
    "blob": {"start": 120, "weight": 3},
    "spider": {"start": 30, "weight": 3},
    "ghost": {"start": 50, "weight": 3},
    "bomber": {"start": 75, "weight": 2},
    "mimic": {"start": 100, "weight": 0.5},
    "shaman": {"start": 140, "weight": 1},
    "necro": {"start": 160, "weight": 1},
    "king_slime": {"start": 240, "weight": 0.3},
}

SPLIT_INTO = {"blob": "mini_blob", "king_slime": "walker"}
SPLIT_COUNT = {"blob": 2, "king_slime": 5}

ELITE_CHANCE = 0.025
ELITE_START = 60
ELITE_HP = 4
ELITE_SCALE = 1.4
BOSS_INTERVAL = 180

SHOOTER_RANGE = 260
SHOOTER_COOLDOWN = 2.5
DASH_RANGE = 280
DASH_WINDUP = 0.7
DASH_TIME = 0.5
DASH_SPEED_FACTOR = 5
DASH_COOLDOWN = 2.0
BOSS_SHOT_COOLDOWN = 3.0
BOSS_SHOTS = 12
ENEMY_BULLET_SPEED = 220
ENEMY_BULLET_RADIUS = 6
ENEMY_BULLET_LIFETIME = 3.0

GHOST_FADE_SPEED = 2.5
EXPLODE_RANGE = 60
EXPLODE_FUSE = 0.8
EXPLODE_RADIUS = 90
SUMMON_RANGE = 300
SUMMON_COOLDOWN = 5.0
SUMMON_COUNT = 3
ZIGZAG_WIDTH = 0.9
ZIGZAG_SPEED = 6
HEAL_COOLDOWN = 3.0
HEAL_RADIUS = 160
HEAL_AMOUNT = 3
MIMIC_WAKE = 140

# Shooting
FIRE_INTERVAL = 0.5
FIRE_INTERVAL_MIN = 0.15
FIRE_RANGE = 450
BULLET_SPEED = 500
BULLET_RADIUS = 4
BULLET_DAMAGE = 1
BULLET_LIFETIME = 1.5
BULLET_SPRITE = "bullet_default"
MULTISHOT_SPREAD = 12

# Weapons
MAX_WEAPONS = 6
WEAPON_MAX_LEVEL = 5
WEAPONS = {
    "wand": {"name": "Magic wand", "desc": "Shoots at the nearest enemy", "icon": "icon_wand"},
    "knives": {"name": "Throwing knives", "desc": "Throws piercing knives where you walk", "icon": "knife"},
    "blades": {"name": "Spinning stars", "desc": "Stars circle around you", "icon": "blade"},
    "aura": {"name": "Holy circle", "desc": "Damages everything close by", "icon": "icon_aura"},
    "lightning": {"name": "Lightning", "desc": "Strikes random enemies", "icon": "lightning"},
    "boomerang": {"name": "Boomerang", "desc": "Flies out and comes back", "icon": "boomerang"},
    "meteor": {"name": "Meteor", "desc": "Drops meteors on enemies", "icon": "meteor"},
    "fire": {"name": "Fire trail", "desc": "Leaves burning flames behind you", "icon": "fire"},
}
KNIFE_INTERVAL = 1.1
KNIFE_SPEED = 600
BLADE_DISTANCE = 75
BLADE_SPIN = 3.0
BLADE_HIT_COOLDOWN = 0.5
AURA_RADIUS = 70
AURA_TICK = 0.5
LIGHTNING_INTERVAL = 2.6
LIGHTNING_RANGE = 500
BOOMERANG_INTERVAL = 1.6
BOOMERANG_SPEED = 450
BOOMERANG_TIME = 0.6
METEOR_INTERVAL = 3.0
METEOR_DELAY = 0.8
METEOR_RADIUS = 70
FIRE_DROP_TIME = 0.25
FIRE_LIFE = 2.0
FIRE_RADIUS = 22
FIRE_TICK = 0.4

# Damage
PLAYER_MAX_HP = 5
INVIS_TIME = 1.0
ENEMY_DAMAGE = 1
CRIT_MULTIPLIER = 2
REGEN_TIME = 30

# XP
ORB_RADIUS = 5
ORB_COLOR = (80, 220, 240)
PICKUP_RANGE = 90
XP_BASE = 5
XP_GROWTH = 3

# Pickups on the map
PICKUP_DROP_CHANCE = 0.015
PICKUP_WEIGHTS = {"heart": 4, "magnet": 2, "bomb": 1, "freeze": 1, "boots": 1, "potion": 1}
PICKUP_RADIUS = 14
PICKUP_LIFETIME = 30
BOMB_RANGE = 600
BOMB_BOSS_DAMAGE = 25
CHEST_COINS = 15
FREEZE_TIME = 4
BOOTS_TIME = 8
BOOTS_SPEED = 1.5
POTION_TIME = 15

# Upgrades
UPGRADE_CHOICES = 3
UPGRADE_FIRE_FACTOR = 0.8
UPGRADE_DAMAGE = 1
UPGRADE_SPEED = 30
PLAYER_SPEED_MAX = 360
UPGRADE_PICKUP = 40
UPGRADE_HP = 1
UPGRADE_CRIT = 0.08
CRIT_MAX = 0.5
UPGRADE_ARMOR = 0.1
ARMOR_MAX = 0.5
UPGRADE_XP = 0.2
UPGRADE_LUCK = 0.3
MULTISHOT_MAX = 3
PIERCE_MAX = 4
REGEN_MAX = 3
UPGRADE_LIFESTEAL = 0.03
LIFESTEAL_MAX = 0.15
UPGRADE_THORNS = 3
DASH_SPEED = 900
DASH_DURATION = 0.15
DASH_COOLDOWN_PLAYER = 2.0

# Kill streaks: after this many kills in a row a text shows up
STREAK_TIME = 1.5
STREAK_TEXTS = {2: "DOUBLE KILL", 3: "TRIPLE KILL", 5: "MULTI KILL", 10: "RAMPAGE", 25: "UNSTOPPABLE",
                50: "GODLIKE", 100: "WHAT IS THIS", 250: "CALL THE POLICE"}

# Random events
EVENT_FIRST = 90
EVENT_INTERVAL = 120

# Day and night, a full day takes this many seconds
DAY_LENGTH = 240
NIGHT_DARKNESS = 150

# Coins after a run
COINS_PER_KILLS = 10
PLAYER_COLOR = (60, 120, 220)
BULLET_COLOR = (250, 240, 120)

# Online co-op
NET_PORT = 50555
SNAPSHOT_RATE = 30
MAX_PLAYERS = 4
# seconds to pick an upgrade, after that you get a random one
CHOICE_TIME = 8
REVIVE_TIME = 3
REVIVE_RANGE = 60
REVIVE_HP = 1
# every extra player makes enemies come this much faster
COOP_SPAWN_BONUS = 0.6
COOP_COLORS = [(110, 200, 255), (255, 140, 90), (140, 230, 120), (230, 130, 230)]

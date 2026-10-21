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
SPAWN_DISTANCE = 640
# new enemies rise out of a portal for this long, they can't hurt you yet
SPAWN_IN_TIME = 0.5

# Difficulty, m is minutes of "effective" time (play time * ramp of the difficulty).
# Enemy hp is 1 + HP_GROWTH * m + HP_CURVE * m * m, so it speeds up the longer you play
HP_GROWTH = 0.28
HP_CURVE = 0.022
SPEED_GROWTH = 0.04
SPEED_FACTOR_MAX = 1.6

# Difficulty levels. ramp is how fast you go through the phases,
# so the hard ones start almost like normal but get hard much sooner
DIFFICULTIES = {
    "easy": {"name": "Easy", "spawn": 1.3, "enemy_hp": 0.8, "enemy_speed": 0.9, "enemy_damage": 1, "player_hp": 6,
             "ramp": 0.8, "elite": 0.7},
    "normal": {"name": "Normal", "spawn": 0.9, "enemy_hp": 1.0, "enemy_speed": 1.0, "enemy_damage": 1, "player_hp": 5,
               "ramp": 1.0, "elite": 1},
    "hard": {"name": "Hard", "spawn": 0.8, "enemy_hp": 1.15, "enemy_speed": 1.05, "enemy_damage": 1, "player_hp": 5,
             "ramp": 1.2, "elite": 1.5},
    "extreme": {"name": "Extreme", "spawn": 0.7, "enemy_hp": 1.3, "enemy_speed": 1.1, "enemy_damage": 1, "player_hp": 4,
                "ramp": 1.4, "elite": 1.5, "boss_affix": True, "elite_affix": True},
    "nightmare": {"name": "Nightmare", "spawn": 0.6, "enemy_hp": 1.5, "enemy_speed": 1.15, "enemy_damage": 1,
                  "player_hp": 3, "ramp": 1.7, "elite": 2, "boss_affix": True, "elite_affix": True, "boss_enrage": True},
}

# A run goes through phases. start is in effective seconds. spawn is the time between spawns,
# pack how many come at once. Between two phases spawn slides smoothly to the next value.
# damage is extra damage on top of the difficulty, events is the time between random events.
PHASES = [
    {"name": "Meadow", "start": 0, "color": (140, 220, 120), "spawn": 1.1, "pack": 1, "elite": 0, "damage": 0,
     "max_enemies": 150, "events": 120,
     "enemies": {"walker": 10, "runner": 4, "spider": 2, "archer": 1}},
    {"name": "Woods", "start": 150, "color": (90, 190, 110), "spawn": 0.45, "pack": 1, "elite": 0.015, "damage": 0,
     "max_enemies": 150, "events": 120,
     "enemies": {"walker": 8, "runner": 5, "spider": 3, "archer": 3, "ghost": 3, "boar": 3, "tank": 2}},
    {"name": "Dusk", "start": 360, "color": (250, 170, 80), "spawn": 0.55, "pack": 2, "elite": 0.025, "damage": 0,
     "max_enemies": 150, "events": 100,
     "enemies": {"walker": 5, "runner": 4, "spider": 3, "archer": 3, "ghost": 3, "boar": 3, "tank": 3, "bomber": 2,
                 "blob": 3, "mimic": 0.5, "shaman": 1, "necro": 1}},
    {"name": "Cursed lands", "start": 600, "color": (190, 110, 240), "spawn": 0.45, "pack": 2, "elite": 0.035,
     "damage": 1, "max_enemies": 160, "events": 90,
     "enemies": {"spider": 3, "archer": 2, "ghost": 3, "boar": 3, "tank": 3, "bomber": 3, "blob": 3, "mimic": 0.5,
                 "shaman": 1.5, "necro": 1.5, "king_slime": 0.3, "knight": 4, "mage": 3, "lava_slime": 3}},
    {"name": "The abyss", "start": 900, "color": (230, 60, 80), "spawn": 0.4, "pack": 3, "elite": 0.05, "damage": 1,
     "max_enemies": 180, "events": 75, "affixes": True, "double_boss": True,
     "enemies": {"ghost": 2, "boar": 2, "tank": 3, "bomber": 3, "blob": 2, "mimic": 0.5, "shaman": 1.5, "necro": 1.5,
                 "king_slime": 0.5, "knight": 4, "mage": 3, "lava_slime": 3, "wraith": 3, "crystal_golem": 1.5}},
    {"name": "Last stand", "start": 1320, "color": (255, 60, 40), "spawn": 0.3, "pack": 4, "elite": 0.07, "damage": 2,
     "max_enemies": 200, "events": 60, "affixes": True, "double_boss": True,
     "enemies": {"tank": 3, "bomber": 3, "blob": 2, "mimic": 0.5, "shaman": 2, "necro": 2, "king_slime": 1,
                 "knight": 5, "mage": 4, "lava_slime": 3, "wraith": 4, "crystal_golem": 2.5}},
]
# in real seconds, on every difficulty
REAPER_TIME = 1800
REAPER_DAMAGE = 99
WIN_COINS = 150
PHASE_COINS = 10

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
    # later phases. armor takes that much off every hit (a hit always does at least 1)
    "knight": {"speed": 60, "radius": 15, "color": (160, 165, 180), "hp": 10, "xp": 6, "ai": "chase", "sprite": "knight",
               "armor": 2},
    "mage": {"speed": 60, "radius": 14, "color": (110, 50, 170), "hp": 6, "xp": 5, "ai": "shooter", "sprite": "mage",
             "shots": 3},
    "lava_slime": {"speed": 65, "radius": 16, "color": (240, 110, 40), "hp": 8, "xp": 4, "ai": "chase",
                   "sprite": "lava_slime", "puddles": True},
    "wraith": {"speed": 70, "radius": 15, "color": (120, 30, 50), "hp": 7, "xp": 5, "ai": "blinker", "sprite": "wraith"},
    "crystal_golem": {"speed": 45, "radius": 26, "color": (90, 200, 230), "hp": 40, "xp": 15, "ai": "chase",
                      "sprite": "crystal_golem", "armor": 1},
    "mini_golem": {"speed": 80, "radius": 12, "color": (90, 200, 230), "hp": 6, "xp": 2, "ai": "chase",
                   "sprite": "mini_golem"},
    # bosses, pattern says how they attack
    "bone_lord": {"speed": 50, "radius": 36, "color": (120, 240, 120), "hp": 260, "xp": 50, "ai": "boss",
                  "sprite": "bone_lord", "pattern": "spiral"},
    "golem_king": {"speed": 40, "radius": 40, "color": (200, 160, 80), "hp": 320, "xp": 60, "ai": "boss",
                   "sprite": "golem_king", "pattern": "charge", "armor": 1},
    "reaper": {"speed": 560, "radius": 40, "color": (40, 30, 50), "hp": 999999, "xp": 0, "ai": "reaper",
               "sprite": "reaper"},
}

SPLIT_INTO = {"blob": "mini_blob", "king_slime": "walker", "crystal_golem": "mini_golem"}
SPLIT_COUNT = {"blob": 2, "king_slime": 5, "crystal_golem": 3}

ELITE_HP = 4
ELITE_SCALE = 1.4
BOSS_INTERVAL = 180
# the bosses take turns
BOSS_ORDER = ["boss", "bone_lord", "golem_king"]
# every next boss has this much more hp
BOSS_HP_GROWTH = 0.5
BOSS_NAMES = {"boss": "The Butcher", "bone_lord": "Bone Lord", "golem_king": "Golem King", "reaper": "THE REAPER"}

# Elites can get an extra power from the abyss on (and always on extreme and nightmare)
AFFIXES = {
    "swift": {"name": "Swift", "color": (120, 220, 255)},
    "shielded": {"name": "Shielded", "color": (170, 170, 255)},
    "vampiric": {"name": "Vampiric", "color": (230, 40, 70)},
    "volatile": {"name": "Volatile", "color": (255, 140, 40)},
}
ELITE_COLOR = (250, 210, 60)
SWIFT_SPEED = 1.5
SHIELD_PART = 0.5
VAMPIRE_HEAL = 0.25

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
BLINK_COOLDOWN = 4.0
BLINK_TELL = 0.6
BLINK_DISTANCE = 90
SPIRAL_TIME = 2.5
SPIRAL_REST = 2.0
SPIRAL_STEP = 0.18
CHARGE_WINDUP = 1.0
CHARGE_TIME = 0.7
CHARGE_COOLDOWN = 4.0
CHARGE_SHOTS = 16
ENRAGE_HP = 0.5

# Puddles of lava and cursed ground
PUDDLE_INTERVAL = 1.2
PUDDLE_RADIUS = 24
PUDDLE_LIFE = 4

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
# A weapon at max level together with the right upgrade can evolve, offered from a chest
EVOLUTIONS = {
    "wand": {"name": "Arcane storm", "desc": "+2 bullets that pierce 2 more enemies", "needs": "Faster fire rate"},
    "knives": {"name": "Thousand edges", "desc": "Also throws knives in all directions", "needs": "Multishot"},
    "blades": {"name": "Guardian stars", "desc": "Twice the stars, wider circle", "needs": "Armor"},
    "aura": {"name": "Sanctuary", "desc": "Much bigger and heals you now and then", "needs": "Regeneration"},
    "lightning": {"name": "Thunder god", "desc": "Every strike jumps to 2 more enemies", "needs": "Critical hit"},
    "boomerang": {"name": "Storm rang", "desc": "+2 boomerangs that fly further", "needs": "Pierce"},
    "meteor": {"name": "Armageddon", "desc": "Twice the meteors, bigger blasts", "needs": "Luck"},
    "fire": {"name": "Inferno", "desc": "Flames burn longer and faster", "needs": "Faster movement"},
}
SANCTUARY_HEAL = 20
CHAIN_RANGE = 160
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
# makes high levels take a lot longer
XP_CURVE = 0.12

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
UPGRADE_FIRE_FACTOR = 0.85
UPGRADE_DAMAGE = 1
UPGRADE_SPEED = 30
PLAYER_SPEED_MAX = 360
UPGRADE_PICKUP = 40
UPGRADE_HP = 1
UPGRADE_CRIT = 0.08
CRIT_MAX = 0.5
UPGRADE_ARMOR = 0.07
ARMOR_MAX = 0.35
UPGRADE_XP = 0.1
XP_MULT_MAX = 1.4
UPGRADE_LUCK = 0.3
MULTISHOT_MAX = 3
PIERCE_MAX = 4
REGEN_MAX = 3
# lifesteal heals 1 hp every so many kills, every pick needs fewer kills
LIFESTEAL_STEPS = [50, 40, 30, 25]
UPGRADE_THORNS = 3
UPGRADE_COOLDOWN = 0.92
COOLDOWN_MIN = 0.7
UPGRADE_AREA = 0.12
AREA_MAX = 1.48
FALLBACK_COINS = 20
DASH_SPEED = 900
DASH_DURATION = 0.15
DASH_COOLDOWN_PLAYER = 2.0

# Kill streaks: after this many kills in a row a text shows up
STREAK_TIME = 1.5
STREAK_TEXTS = {2: "DOUBLE KILL", 3: "TRIPLE KILL", 5: "MULTI KILL", 10: "RAMPAGE", 25: "UNSTOPPABLE",
                50: "GODLIKE", 100: "WHAT IS THIS", 250: "CALL THE POLICE"}

# Random events
EVENT_FIRST = 90

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
# you come back with this part of your max hp
REVIVE_HP_PART = 0.5
REVIVE_INVIS = 2.5
# every extra player makes enemies come this much faster
COOP_SPAWN_BONUS = 0.6
# and a bit more hp, a team does a lot more damage
COOP_HP_BONUS = 0.25
COOP_BOSS_HP = 0.5
COOP_COIN_BONUS = 0.25
# standing close to a teammate gives "team spirit": faster weapons and some regen
TEAM_RANGE = 260
TEAM_COOLDOWN = 0.85
TEAM_REGEN = 25
# teammates close by get this part of the xp you pick up
SHARED_XP = 0.4
SHARED_XP_RANGE = 700
MEDIC_TIME = 15
# a boss picks someone new to chase every so many seconds
BOSS_FOCUS_TIME = 6
COOP_COLORS = [(110, 200, 255), (255, 140, 90), (140, 230, 120), (230, 130, 230)]

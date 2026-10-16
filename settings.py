# Beeldscherm
W, H = 960, 640
FPS = 60
TILE = 64

# Speler
PLAYER_SPEED = 220
PLAYER_RADIUS = 14

# Enemies
SPAWN_INTERVAL = 1.2
SPAWN_INTERVAL_MIN = 0.3
SPAWN_INTERVAL_DECAY = 0.01
SPAWN_DISTANCE = 600

# Difficulty (per minuut speeltijd)
HP_GROWTH = 0.4
SPEED_GROWTH = 0.06
SPEED_FACTOR_MAX = 1.4
MAX_ENEMIES = 150

ENEMY_TYPES = {
    "walker": {"speed": 70, "radius": 16, "color": (200, 50, 50), "hp": 3, "xp": 1},
    "runner": {"speed": 140, "radius": 10, "color": (230, 150, 40), "hp": 1, "xp": 2},
    "tank": {"speed": 50, "radius": 22, "color": (140, 40, 160), "hp": 12, "xp": 5},
}

# Vanaf wanneer en hoe vaak
SPAWN_TABLE = {
    "walker": {"start": 0, "weight": 10},
    "runner": {"start": 20, "weight": 5},
    "tank": {"start": 60, "weight": 2},
}

# Schieten
FIRE_INTERVAL = 0.5
FIRE_INTERVAL_MIN = 0.15
FIRE_RANGE = 450
BULLET_SPEED = 500
BULLET_RADIUS = 4
BULLET_DAMAGE = 1
BULLET_LIFETIME = 1.5

# Damage
PLAYER_MAX_HP = 5
INVIS_TIME = 1.0
ENEMY_DAMAGE = 1

# XP
ORB_RADIUS = 5
ORB_COLOR = (80, 220, 240)
PICKUP_RANGE = 90
XP_BASE = 5
XP_GROWTH = 3

# Upgrades
UPGRADE_CHOICES = 3
UPGRADE_FIRE_FACTOR = 0.8
UPGRADE_DAMAGE = 1
UPGRADE_SPEED = 30
PLAYER_SPEED_MAX = 360
UPGRADE_PICKUP = 40
UPGRADE_HP = 1

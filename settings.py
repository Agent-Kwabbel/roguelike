# Beeldscherm
W, H = 960, 640
FPS = 60
TILE = 64

# Speler
PLAYER_SPEED = 220
PLAYER_RADIUS = 14

# Enemies
SPAWN_INTERVAL = 1.0
SPAWN_DISTANCE = 600

ENEMY_TYPES = {
    "walker": {"speed": 70, "radius": 16, "color": (200, 50, 50), "hp": 3},
    "runner": {"speed": 140, "radius": 10, "color": (230, 150, 40), "hp": 1},
}

# Schieten
FIRE_INTERVAL = 0.5
FIRE_RANGE = 450
BULLET_SPEED = 500
BULLET_RADIUS = 4
BULLET_DAMAGE = 1
BULLET_LIFETIME = 1.5

# Damage
PLAYER_MAX_HP = 5
INVIS_TIME = 1.0
ENEMY_DAMAGE = 1

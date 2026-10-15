import random

from settings import (
    UPGRADE_CHOICES,
    UPGRADE_FIRE_FACTOR,
    UPGRADE_DAMAGE,
    UPGRADE_SPEED,
    UPGRADE_PICKUP,
    UPGRADE_HP,
)


def faster_fire(player):
    player.fire_interval *= UPGRADE_FIRE_FACTOR


def more_damage(player):
    player.damage += UPGRADE_DAMAGE


def faster_move(player):
    player.speed += UPGRADE_SPEED


def bigger_pickup(player):
    player.pickup_range += UPGRADE_PICKUP


def more_hp(player):
    player.max_hp += UPGRADE_HP
    player.hp += UPGRADE_HP


UPGRADES = [
    {
        "name": "Snellere vuursnelheid",
        "desc": "Schiet 20% sneller",
        "apply": faster_fire,
    },
    {"name": "Meer damage", "desc": "Kogels doen +1 damage", "apply": more_damage},
    {"name": "Sneller lopen", "desc": "+30 beweegsnelheid", "apply": faster_move},
    {
        "name": "Grotere magneet",
        "desc": "XP orbs worden van verder aangetrokken",
        "apply": bigger_pickup,
    },
    {"name": "Extra leven", "desc": "+1 max HP en heel 1 HP", "apply": more_hp},
]


def pick_choices():
    return random.sample(UPGRADES, UPGRADE_CHOICES)

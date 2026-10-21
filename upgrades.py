import random

from settings import (
    UPGRADE_CHOICES,
    UPGRADE_FIRE_FACTOR,
    UPGRADE_DAMAGE,
    UPGRADE_SPEED,
    UPGRADE_PICKUP,
    UPGRADE_HP,
    UPGRADE_CRIT,
    UPGRADE_ARMOR,
    UPGRADE_XP,
    UPGRADE_LUCK,
    FIRE_INTERVAL_MIN,
    PLAYER_SPEED_MAX,
    CRIT_MAX,
    ARMOR_MAX,
    MULTISHOT_MAX,
    PIERCE_MAX,
    REGEN_MAX,
    MAX_WEAPONS,
    WEAPON_MAX_LEVEL,
    WEAPONS,
    UPGRADE_LIFESTEAL,
    LIFESTEAL_MAX,
    UPGRADE_THORNS,
)
from weapons import make_weapon


def faster_fire(player):
    player.fire_interval = max(
        FIRE_INTERVAL_MIN, player.fire_interval * UPGRADE_FIRE_FACTOR
    )


def more_damage(player):
    player.damage += UPGRADE_DAMAGE


def faster_move(player):
    player.speed = min(PLAYER_SPEED_MAX, player.speed + UPGRADE_SPEED)


def bigger_pickup(player):
    player.pickup_range += UPGRADE_PICKUP


def more_hp(player):
    player.max_hp += UPGRADE_HP
    player.hp += UPGRADE_HP


def more_crit(player):
    player.crit_chance = min(CRIT_MAX, player.crit_chance + UPGRADE_CRIT)


def more_armor(player):
    player.armor = min(ARMOR_MAX, player.armor + UPGRADE_ARMOR)


def more_multishot(player):
    player.multishot += 1


def more_pierce(player):
    player.pierce += 1


def more_regen(player):
    player.regen += 1


def more_xp(player):
    player.xp_mult += UPGRADE_XP


def more_luck(player):
    player.luck += UPGRADE_LUCK


def more_lifesteal(player):
    player.lifesteal = min(LIFESTEAL_MAX, player.lifesteal + UPGRADE_LIFESTEAL)


def more_thorns(player):
    player.thorns += UPGRADE_THORNS


def learn_dash(player):
    player.can_dash = True


def add_knives(player):
    if not player.has_weapon("knives"):
        player.weapons.append(make_weapon("knives"))


UPGRADES = [
    {"name": "Snellere vuursnelheid", "desc": "Schiet 20% sneller", "apply": faster_fire, "icon": "icon_fire_rate",
     "can": lambda p: p.fire_interval > FIRE_INTERVAL_MIN},
    {"name": "Meer damage", "desc": "Alle wapens +1 damage", "apply": more_damage, "icon": "icon_damage"},
    {"name": "Sneller lopen", "desc": "+30 beweegsnelheid", "apply": faster_move, "icon": "icon_speed",
     "can": lambda p: p.speed < PLAYER_SPEED_MAX},
    {"name": "Grotere magneet", "desc": "XP van verder aantrekken", "apply": bigger_pickup, "icon": "magnet"},
    {"name": "Extra leven", "desc": "+1 max HP en heel 1 HP", "apply": more_hp, "icon": "heart"},
    {"name": "Kritieke treffer", "desc": "+8% kans op dubbele damage", "apply": more_crit, "icon": "icon_crit",
     "can": lambda p: p.crit_chance < CRIT_MAX},
    {"name": "Harnas", "desc": "+10% kans om een klap te blokken", "apply": more_armor, "icon": "icon_armor",
     "can": lambda p: p.armor < ARMOR_MAX},
    {"name": "Meerdere kogels", "desc": "+1 kogel per schot", "apply": more_multishot, "icon": "icon_multishot",
     "can": lambda p: p.multishot < MULTISHOT_MAX},
    {"name": "Doorboren", "desc": "Kogels gaan door +1 vijand", "apply": more_pierce, "icon": "icon_pierce",
     "can": lambda p: p.pierce < PIERCE_MAX},
    {"name": "Herstel", "desc": "Krijg langzaam HP terug", "apply": more_regen, "icon": "icon_regen",
     "can": lambda p: p.regen < REGEN_MAX},
    {"name": "Wijsheid", "desc": "+20% XP", "apply": more_xp, "icon": "gem_big"},
    {"name": "Geluk", "desc": "Vaker pickups", "apply": more_luck, "icon": "icon_luck"},
    {"name": "Levensroof", "desc": "+3% kans op 1 HP per kill", "apply": more_lifesteal, "icon": "heart",
     "can": lambda p: p.lifesteal < LIFESTEAL_MAX},
    {"name": "Doornen", "desc": "Vijanden die je raken krijgen +3 damage terug", "apply": more_thorns, "icon": "icon_armor"},
    {"name": "Dash", "desc": "Druk op spatie om weg te schieten", "apply": learn_dash, "icon": "boots",
     "can": lambda p: not p.can_dash},
]


def level_up_choice(weapon):
    info = WEAPONS[weapon.key]

    def apply(player):
        weapon.level += 1

    return {
        "name": f"{info['name']} lvl {weapon.level + 1}",
        "desc": "Sterker wapen",
        "apply": apply,
        "icon": info["icon"],
    }


def new_weapon_choice(key):
    info = WEAPONS[key]

    def apply(player):
        player.weapons.append(make_weapon(key))

    return {
        "name": f"Nieuw: {info['name']}",
        "desc": info["desc"],
        "apply": apply,
        "icon": info["icon"],
    }


def pick_choices(player):
    options = []
    for upgrade in UPGRADES:
        if "can" in upgrade and not upgrade["can"](player):
            continue
        options.append(upgrade)
    for weapon in player.weapons:
        if weapon.level < WEAPON_MAX_LEVEL:
            # wapens twee keer in de pot zodat je ze vaker ziet
            options.append(level_up_choice(weapon))
            options.append(level_up_choice(weapon))
    if len(player.weapons) < MAX_WEAPONS:
        for key in WEAPONS:
            if not player.has_weapon(key):
                options.append(new_weapon_choice(key))

    choices = []
    random.shuffle(options)
    for option in options:
        if len(choices) == UPGRADE_CHOICES:
            break
        if option["name"] not in [c["name"] for c in choices]:
            choices.append(option)
    return choices

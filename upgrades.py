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
    XP_MULT_MAX,
    UPGRADE_LUCK,
    FIRE_INTERVAL,
    FIRE_INTERVAL_MIN,
    PLAYER_SPEED,
    PLAYER_SPEED_MAX,
    CRIT_MAX,
    ARMOR_MAX,
    MULTISHOT_MAX,
    PIERCE_MAX,
    REGEN_MAX,
    MAX_WEAPONS,
    WEAPON_MAX_LEVEL,
    WEAPONS,
    EVOLUTIONS,
    LIFESTEAL_STEPS,
    UPGRADE_THORNS,
    UPGRADE_COOLDOWN,
    COOLDOWN_MIN,
    UPGRADE_AREA,
    AREA_MAX,
    FALLBACK_COINS,
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


def extra_life(player):
    player.max_hp += UPGRADE_HP
    player.hp = player.max_hp


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


def next_lifesteal(player):
    if player.lifesteal_kills == 0:
        return LIFESTEAL_STEPS[0]
    for kills in LIFESTEAL_STEPS:
        if kills < player.lifesteal_kills:
            return kills
    return None


def more_lifesteal(player):
    player.lifesteal_kills = next_lifesteal(player)


def more_thorns(player):
    player.thorns += UPGRADE_THORNS


def less_cooldown(player):
    player.cooldown = max(COOLDOWN_MIN, player.cooldown * UPGRADE_COOLDOWN)


def more_area(player):
    player.area = min(AREA_MAX, player.area + UPGRADE_AREA)


def learn_dash(player):
    player.can_dash = True


def add_knives(player):
    if not player.has_weapon("knives"):
        player.weapons.append(make_weapon("knives"))


def learn_medic(player):
    player.medic += 1


def faster_revive(player):
    player.revive_speed = 2


def more_bond(player):
    player.bond += 1


def heal_full(player):
    player.hp = player.max_hp


def bonus_coins(player):
    player.bonus_coins += FALLBACK_COINS


UPGRADES = [
    {"name": "Faster fire rate", "desc": "Shoot 15% faster", "apply": faster_fire, "icon": "icon_fire_rate",
     "can": lambda p: p.fire_interval > FIRE_INTERVAL_MIN},
    {"name": "More damage", "desc": "All weapons +1 damage", "apply": more_damage, "icon": "icon_damage"},
    {"name": "Faster movement", "desc": "+30 move speed", "apply": faster_move, "icon": "icon_speed",
     "can": lambda p: p.speed < PLAYER_SPEED_MAX},
    {"name": "Bigger magnet", "desc": "Pull in XP from further away", "apply": bigger_pickup, "icon": "magnet"},
    {"name": "Extra life", "desc": "+1 max HP and heal to full", "apply": extra_life, "icon": "heart"},
    {"name": "Critical hit", "desc": "+8% chance for double damage", "apply": more_crit, "icon": "icon_crit",
     "can": lambda p: p.crit_chance < CRIT_MAX},
    {"name": "Armor", "desc": "+7% chance to block a hit", "apply": more_armor, "icon": "icon_armor",
     "can": lambda p: p.armor < ARMOR_MAX},
    {"name": "Multishot", "desc": "+1 bullet per shot", "apply": more_multishot, "icon": "icon_multishot",
     "can": lambda p: p.multishot < MULTISHOT_MAX},
    {"name": "Pierce", "desc": "Bullets go through +1 enemy", "apply": more_pierce, "icon": "icon_pierce",
     "can": lambda p: p.pierce < PIERCE_MAX},
    {"name": "Regeneration", "desc": "Slowly get HP back", "apply": more_regen, "icon": "icon_regen",
     "can": lambda p: p.regen < REGEN_MAX},
    {"name": "Wisdom", "desc": "+10% XP", "apply": more_xp, "icon": "gem_big",
     "can": lambda p: p.xp_mult < XP_MULT_MAX - 0.01},
    {"name": "Luck", "desc": "More pickups", "apply": more_luck, "icon": "icon_luck"},
    {"name": "Lifesteal", "desc": "Heal 1 HP every few kills, faster with every pick", "apply": more_lifesteal,
     "icon": "heart", "can": lambda p: next_lifesteal(p) is not None},
    {"name": "Thorns", "desc": "Enemies that hit you take damage back", "apply": more_thorns, "icon": "icon_armor"},
    {"name": "Cooldown", "desc": "All weapons attack 8% faster", "apply": less_cooldown, "icon": "icon_fire_rate",
     "can": lambda p: p.cooldown > COOLDOWN_MIN + 0.01},
    {"name": "Area", "desc": "+12% size for circles, stars, flames and meteors", "apply": more_area,
     "icon": "icon_aura", "can": lambda p: p.area < AREA_MAX - 0.01},
    {"name": "Dash", "desc": "Press space to dash away", "apply": learn_dash, "icon": "boots",
     "can": lambda p: not p.can_dash},
    # only online
    {"name": "Medic", "desc": "Heal teammates close to you every 15 seconds", "apply": learn_medic, "icon": "heart",
     "coop": True, "can": lambda p: p.medic < 2},
    {"name": "Guardian angel", "desc": "Revive teammates twice as fast", "apply": faster_revive,
     "icon": "icon_regen", "coop": True, "can": lambda p: p.revive_speed == 1},
    {"name": "Bond", "desc": "Team spirit reaches further and is stronger", "apply": more_bond, "icon": "icon_aura",
     "coop": True, "can": lambda p: p.bond < 2},
]

# when there is nothing left to pick
FALLBACKS = [
    {"name": "Heal", "desc": "Heal to full HP", "apply": heal_full, "icon": "heart"},
    {"name": "Bag of coins", "desc": f"+{FALLBACK_COINS} coins", "apply": bonus_coins, "icon": "coin"},
]

# the upgrade you need next to a max level weapon to evolve it
EVOLVE_NEEDS = {
    "Faster fire rate": lambda p: p.fire_interval < FIRE_INTERVAL,
    "Multishot": lambda p: p.multishot > 0,
    "Armor": lambda p: p.armor > 0,
    "Regeneration": lambda p: p.regen > 0,
    "Critical hit": lambda p: p.crit_chance > 0.05,
    "Pierce": lambda p: p.pierce > 0,
    "Luck": lambda p: p.luck > 1,
    "Faster movement": lambda p: p.speed > PLAYER_SPEED,
}


def level_up_choice(weapon):
    info = WEAPONS[weapon.key]

    def apply(player):
        weapon.level += 1

    return {
        "name": f"{info['name']} lvl {weapon.level + 1}",
        "desc": "Stronger weapon",
        "apply": apply,
        "icon": info["icon"],
    }


def new_weapon_choice(key):
    info = WEAPONS[key]

    def apply(player):
        player.weapons.append(make_weapon(key))

    return {
        "name": info["name"],
        "desc": info["desc"],
        "apply": apply,
        "icon": info["icon"],
        "new": True,
    }


def evolve_choice(weapon):
    info = EVOLUTIONS[weapon.key]

    def apply(player):
        weapon.evolved = True

    return {
        "name": info["name"],
        "desc": info["desc"],
        "apply": apply,
        "icon": WEAPONS[weapon.key]["icon"],
        "evolve": True,
    }


def can_evolve(player, weapon):
    if weapon.evolved or weapon.level < WEAPON_MAX_LEVEL:
        return False
    return EVOLVE_NEEDS[EVOLUTIONS[weapon.key]["needs"]](player)


def pick_choices(player, chest=False):
    choices = []
    # a chest gives you an evolution first if you can get one
    if chest:
        for weapon in player.weapons:
            if can_evolve(player, weapon) and len(choices) < UPGRADE_CHOICES:
                choices.append(evolve_choice(weapon))

    options = []
    for upgrade in UPGRADES:
        if "can" in upgrade and not upgrade["can"](player):
            continue
        if upgrade.get("coop") and not player.coop:
            continue
        options.append(upgrade)
    for weapon in player.weapons:
        if weapon.level < WEAPON_MAX_LEVEL:
            # weapons go in the pool twice so you see them more often
            options.append(level_up_choice(weapon))
            options.append(level_up_choice(weapon))
    if len(player.weapons) < MAX_WEAPONS:
        for key in WEAPONS:
            if not player.has_weapon(key):
                options.append(new_weapon_choice(key))

    random.shuffle(options)
    for option in options + FALLBACKS:
        if len(choices) == UPGRADE_CHOICES:
            break
        if option["name"] not in [c["name"] for c in choices]:
            choices.append(option)
    return choices

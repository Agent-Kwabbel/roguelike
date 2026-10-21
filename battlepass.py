import json

from settings import (
    BP_SAVE_FILE,
    BP_TIERS,
    BP_XP_PER_TIER,
    BP_XP_PER_SECOND,
    BP_XP_PER_KILL,
    BP_XP_PER_LEVEL,
    PREMIUM_COST,
    PLAYER_SPRITE,
    BULLET_SPRITE,
    TIER_SKIP_COST,
)
from upgrades import (
    more_hp,
    more_damage,
    bigger_pickup,
    faster_move,
    more_crit,
    more_regen,
    more_luck,
    add_knives,
)


def coins(amount):
    return {"type": "coins", "name": f"{amount} coins", "amount": amount}


def skin(name, sprite):
    return {"type": "skin", "name": name, "sprite": sprite}


def bullet(name, sprite):
    return {"type": "bullet", "name": name, "sprite": sprite}


def perk(name, effect):
    return {"type": "perk", "name": name, "effect": effect}


# Index 0 is tier 1. De eerste 20 zijn hetzelfde gebleven zodat oude saves kloppen.
FREE_TIERS = [
    coins(100),
    skin("Groen", "skin_green"),
    coins(100),
    coins(100),
    perk("Grotere start magneet", "pickup"),
    coins(100),
    bullet("Witte kogels", "bullet_white"),
    coins(100),
    coins(100),
    skin("Rood", "skin_red"),
    coins(150),
    coins(150),
    coins(100),
    bullet("Groene kogels", "bullet_green"),
    coins(100),
    coins(100),
    skin("Zilver", "skin_silver"),
    coins(100),
    coins(100),
    skin("Oranje", "skin_orange"),
    # tier 21 - 30
    coins(150),
    coins(100),
    bullet("Pijlen", "bullet_arrow"),
    coins(150),
    skin("Ridder", "skin_knight"),
    coins(100),
    coins(150),
    perk("Meer geluk", "luck"),
    coins(100),
    skin("Piraat", "skin_pirate"),
    # tier 31 - 40
    coins(150),
    coins(150),
    bullet("Sterren", "bullet_star"),
    coins(100),
    skin("Kikker", "skin_frog"),
    coins(150),
    coins(200),
    perk("Start herstel", "regen"),
    coins(150),
    skin("Skelet", "skin_skeleton"),
    # tier 41 - 50
    coins(150),
    coins(200),
    bullet("IJspegels", "bullet_ice"),
    coins(150),
    coins(200),
    coins(150),
    coins(200),
    coins(200),
    coins(250),
    skin("Tovenaar", "skin_wizard"),
]

PREMIUM_TIERS = [
    skin("Goud", "skin_gold"),
    coins(100),
    bullet("Roze kogels", "bullet_pink"),
    perk("Extra start HP", "start_hp"),
    coins(100),
    skin("Paars", "skin_purple"),
    coins(100),
    bullet("Blauwe kogels", "bullet_blue"),
    perk("Extra start damage", "start_damage"),
    coins(150),
    skin("Zwart", "skin_black"),
    coins(100),
    bullet("Rode kogels", "bullet_red"),
    perk("Snellere start", "speed"),
    coins(150),
    skin("Cyaan", "skin_cyan"),
    coins(150),
    bullet("Gouden kogels", "bullet_gold"),
    coins(200),
    skin("Legende", "skin_legend"),
    # tier 21 - 30
    coins(150),
    skin("Robot", "skin_robot"),
    coins(150),
    bullet("Vuurballen", "bullet_fire"),
    coins(150),
    coins(200),
    skin("Astronaut", "skin_astronaut"),
    coins(150),
    coins(200),
    perk("Start met werpmessen", "knives"),
    # tier 31 - 40
    coins(150),
    skin("Ninja", "skin_ninja"),
    coins(200),
    coins(150),
    coins(200),
    bullet("Hartjes", "bullet_heart"),
    coins(200),
    coins(150),
    coins(200),
    perk("Scherpe start", "crit"),
    # tier 41 - 50
    coins(200),
    coins(250),
    coins(200),
    coins(250),
    coins(200),
    coins(250),
    perk("Extra start HP 2", "start_hp"),
    coins(250),
    coins(300),
    skin("Gouden ridder", "skin_gold_knight"),
]

SHOP_ITEMS = [
    {"type": "tier_skip", "name": "Tier overslaan", "price": TIER_SKIP_COST},
    {"type": "skin", "name": "Donkere tovenaar", "sprite": "skin_dark_wizard", "price": 500},
    {"type": "skin", "name": "Vampier", "sprite": "skin_vampire", "price": 600},
    {"type": "bullet", "name": "Leegte kogels", "sprite": "bullet_void", "price": 300},
    {"type": "skin", "name": "Blauwe held", "sprite": "skin_default", "price": 0},
    {"type": "bullet", "name": "Standaard kogels", "sprite": "bullet_default", "price": 0},
]

PERK_EFFECTS = {
    "start_hp": more_hp,
    "start_damage": more_damage,
    "pickup": bigger_pickup,
    "speed": faster_move,
    "crit": more_crit,
    "regen": more_regen,
    "luck": more_luck,
    "knives": add_knives,
}


def new_data():
    return {
        "xp": 0,
        "coins": 0,
        "premium": False,
        "owned": [],
        "skin": None,
        "bullet": None,
        "claimed_free": 0,
        "claimed_premium": 0,
        "challenges": {},
    }


def load():
    data = new_data()
    try:
        with open(BP_SAVE_FILE) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def save(data):
    with open(BP_SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def current_tier(data):
    return min(BP_TIERS, data["xp"] // BP_XP_PER_TIER)


def run_xp(seconds, kills, level):
    return int(seconds * BP_XP_PER_SECOND + kills * BP_XP_PER_KILL + level * BP_XP_PER_LEVEL)


def give(data, reward):
    if reward["type"] == "coins":
        data["coins"] += reward["amount"]
    elif reward["name"] not in data["owned"]:
        data["owned"].append(reward["name"])


def grant_rewards(data):
    tier = current_tier(data)
    while data["claimed_free"] < tier:
        give(data, FREE_TIERS[data["claimed_free"]])
        data["claimed_free"] += 1
    if data["premium"]:
        while data["claimed_premium"] < tier:
            give(data, PREMIUM_TIERS[data["claimed_premium"]])
            data["claimed_premium"] += 1


def add_xp(data, amount):
    old_tier = current_tier(data)
    data["xp"] += amount
    grant_rewards(data)
    return current_tier(data) - old_tier


def buy_premium(data):
    if data["premium"] or data["coins"] < PREMIUM_COST:
        return False
    data["coins"] -= PREMIUM_COST
    data["premium"] = True
    grant_rewards(data)
    return True


def owns(data, item):
    # gratis items uit de winkel heb je altijd
    if item.get("price") == 0:
        return True
    return item["name"] in data["owned"]


def buy_item(data, item):
    """Koop iets uit de winkel, geeft een bericht terug voor op het scherm."""
    if item["type"] == "tier_skip":
        if current_tier(data) >= BP_TIERS:
            return "Battle Pass is al voltooid"
        if data["coins"] < item["price"]:
            return "Niet genoeg coins"
        data["coins"] -= item["price"]
        add_xp(data, BP_XP_PER_TIER - data["xp"] % BP_XP_PER_TIER)
        return f"Tier {current_tier(data)} bereikt!"
    if owns(data, item):
        if equip(data, item):
            return f"{item['name']} uitgerust"
        return "Je hebt dit al"
    if data["coins"] < item["price"]:
        return "Niet genoeg coins"
    data["coins"] -= item["price"]
    data["owned"].append(item["name"])
    equip(data, item)
    return f"{item['name']} gekocht en uitgerust!"


def equip(data, reward):
    if not owns(data, reward):
        return False
    if reward["type"] == "skin":
        data["skin"] = reward["name"]
    elif reward["type"] == "bullet":
        data["bullet"] = reward["name"]
    else:
        return False
    return True


def find_reward(name):
    for reward in FREE_TIERS + PREMIUM_TIERS + SHOP_ITEMS:
        if reward["name"] == name:
            return reward
    return None


def skin_sprite(data):
    reward = find_reward(data["skin"])
    if reward:
        return reward["sprite"]
    return PLAYER_SPRITE


def bullet_sprite(data):
    reward = find_reward(data["bullet"])
    if reward:
        return reward["sprite"]
    return BULLET_SPRITE


def apply_perks(data, player):
    for reward in FREE_TIERS + PREMIUM_TIERS:
        if reward["type"] == "perk" and reward["name"] in data["owned"]:
            PERK_EFFECTS[reward["effect"]](player)

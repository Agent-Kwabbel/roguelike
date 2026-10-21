import saves
from settings import PLAYER_SPRITE, BULLET_SPRITE
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


def skin(name, sprite, price, achievement=None):
    return {"type": "skin", "name": name, "sprite": sprite, "price": price, "achievement": achievement}


def bullet(name, sprite, price, achievement=None):
    return {"type": "bullet", "name": name, "sprite": sprite, "price": price, "achievement": achievement}


def perk(name, effect, price, desc, achievement=None):
    return {"type": "perk", "name": name, "effect": effect, "price": price, "desc": desc,
            "achievement": achievement}


# Everything you can buy. Items with an achievement can only be unlocked by getting that achievement.
SHOP_ITEMS = [
    skin("Blue hero", "skin_default", 0),
    skin("Green", "skin_green", 200),
    skin("Red", "skin_red", 200),
    skin("Orange", "skin_orange", 200),
    skin("Purple", "skin_purple", 250),
    skin("Cyan", "skin_cyan", 250),
    skin("Silver", "skin_silver", 300),
    skin("Black", "skin_black", 300),
    skin("Gold", "skin_gold", 500),
    skin("Knight", "skin_knight", 600),
    skin("Pirate", "skin_pirate", 600),
    skin("Frog", "skin_frog", 600),
    skin("Skeleton", "skin_skeleton", 700),
    skin("Ninja", "skin_ninja", 800),
    skin("Robot", "skin_robot", 800),
    skin("Wizard", "skin_wizard", 900),
    skin("Dark wizard", "skin_dark_wizard", 1000),
    skin("Vampire", "skin_vampire", 1000),
    skin("Astronaut", "skin_astronaut", 1200),
    skin("Cat", "skin_cat", 800),
    skin("Dino", "skin_dino", 900),
    skin("Banana", "skin_banana", 700),
    skin("Clown", "skin_clown", 900),
    skin("Legend", "skin_legend", 0, "genocide"),
    skin("Golden knight", "skin_gold_knight", 0, "marathon"),
    skin("Whale", "skin_whale", 0, "extreme"),
    skin("Team jacket", "skin_team", 0, "together"),
    bullet("Standard bullets", "bullet_default", 0),
    bullet("White bullets", "bullet_white", 150),
    bullet("Green bullets", "bullet_green", 150),
    bullet("Pink bullets", "bullet_pink", 150),
    bullet("Blue bullets", "bullet_blue", 150),
    bullet("Red bullets", "bullet_red", 150),
    bullet("Arrows", "bullet_arrow", 300),
    bullet("Stars", "bullet_star", 400),
    bullet("Icicles", "bullet_ice", 400),
    bullet("Fireballs", "bullet_fire", 500),
    bullet("Hearts", "bullet_heart", 500),
    bullet("Void bullets", "bullet_void", 600),
    bullet("Rainbow bullets", "bullet_rainbow", 700),
    bullet("Coin bullets", "bullet_coin", 0, "rich"),
    bullet("Golden bullets", "bullet_gold", 0, "boss"),
    bullet("Friendship bolts", "bullet_team", 0, "medic"),
    perk("Bigger starting magnet", "pickup", 500, "Pick up XP from further away from the start"),
    perk("More luck", "luck", 700, "Pickups drop more often"),
    perk("Starting regeneration", "regen", 900, "Slowly heal right from the start"),
    perk("Faster start", "speed", 900, "Start every run with +30 move speed"),
    perk("Extra starting HP", "start_hp", 1200, "Start every run with +1 max HP"),
    perk("Extra starting damage", "start_damage", 1200, "All weapons start with +1 damage"),
    perk("Sharp start", "crit", 1200, "Start with +8% critical hit chance"),
    perk("Start with throwing knives", "knives", 1500, "Get throwing knives as a second weapon"),
    perk("Extra starting HP 2", "start_hp", 0, "Another +1 max HP at the start", "level20"),
]

# saves from before the translation still use the Dutch names
OLD_NAMES = {
    "Blauwe held": "Blue hero", "Groen": "Green", "Rood": "Red", "Oranje": "Orange", "Paars": "Purple",
    "Cyaan": "Cyan", "Zilver": "Silver", "Zwart": "Black", "Goud": "Gold", "Ridder": "Knight",
    "Piraat": "Pirate", "Kikker": "Frog", "Skelet": "Skeleton", "Tovenaar": "Wizard",
    "Donkere tovenaar": "Dark wizard", "Vampier": "Vampire", "Kat": "Cat", "Banaan": "Banana",
    "Legende": "Legend", "Gouden ridder": "Golden knight", "Walvis": "Whale",
    "Standaard kogels": "Standard bullets", "Witte kogels": "White bullets", "Groene kogels": "Green bullets",
    "Roze kogels": "Pink bullets", "Blauwe kogels": "Blue bullets", "Rode kogels": "Red bullets",
    "Pijlen": "Arrows", "Sterren": "Stars", "IJspegels": "Icicles", "Vuurballen": "Fireballs",
    "Hartjes": "Hearts", "Leegte kogels": "Void bullets", "Regenboog kogels": "Rainbow bullets",
    "Muntjes kogels": "Coin bullets", "Gouden kogels": "Golden bullets",
    "Grotere start magneet": "Bigger starting magnet", "Meer geluk": "More luck",
    "Start herstel": "Starting regeneration", "Snellere start": "Faster start",
    "Extra start HP": "Extra starting HP", "Extra start damage": "Extra starting damage",
    "Scherpe start": "Sharp start", "Start met werpmessen": "Start with throwing knives",
    "Extra start HP 2": "Extra starting HP 2",
}

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
        "coins": 0,
        "owned": [],
        "skin": None,
        "bullet": None,
        "achievements": [],
        "totals": {"kills": 0, "elites": 0, "runs": 0},
    }


def load():
    data = new_data()
    saved = saves.load_profile()
    if saved:
        data.update(saved)
    data["owned"] = [OLD_NAMES.get(name, name) for name in data["owned"]]
    data["skin"] = OLD_NAMES.get(data["skin"], data["skin"])
    data["bullet"] = OLD_NAMES.get(data["bullet"], data["bullet"])
    # old saves already have the achievement but not the item yet
    for key in data["achievements"]:
        for item in achievement_items(key):
            give(data, item)
    return data


def save(data):
    saves.save_profile(data)


def give(data, item):
    if item["name"] not in data["owned"]:
        data["owned"].append(item["name"])


def owns(data, item):
    # free shop items are always yours
    if item["price"] == 0 and not item["achievement"]:
        return True
    return item["name"] in data["owned"]


def buy_item(data, item):
    """Buy something from the shop, returns a message to show on screen."""
    if owns(data, item):
        if equip(data, item):
            return f"{item['name']} equipped"
        return "You already own this"
    if item["achievement"]:
        return "Get the achievement first"
    if data["coins"] < item["price"]:
        return "Not enough coins"
    data["coins"] -= item["price"]
    give(data, item)
    equip(data, item)
    return f"Bought {item['name']}!"


def equip(data, item):
    if not owns(data, item):
        return False
    if item["type"] == "skin":
        data["skin"] = item["name"]
    elif item["type"] == "bullet":
        data["bullet"] = item["name"]
    else:
        return False
    return True


def find_item(name):
    for item in SHOP_ITEMS:
        if item["name"] == name:
            return item
    return None


def achievement_items(key):
    return [item for item in SHOP_ITEMS if item["achievement"] == key]


def skin_sprite(data):
    item = find_item(data["skin"])
    if item:
        return item["sprite"]
    return PLAYER_SPRITE


def bullet_sprite(data):
    item = find_item(data["bullet"])
    if item:
        return item["sprite"]
    return BULLET_SPRITE


def is_equipped(data, item):
    if item["type"] == "skin":
        return item["sprite"] == skin_sprite(data)
    if item["type"] == "bullet":
        return item["sprite"] == bullet_sprite(data)
    return False


def apply_perks(data, player):
    for item in SHOP_ITEMS:
        if item["type"] == "perk" and item["name"] in data["owned"]:
            PERK_EFFECTS[item["effect"]](player)

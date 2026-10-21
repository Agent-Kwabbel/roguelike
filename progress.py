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


def perk(name, effect, price, achievement=None):
    return {"type": "perk", "name": name, "effect": effect, "price": price, "achievement": achievement}


# Alles wat je kan kopen. Met een achievement erbij krijg je het alleen door die te halen.
SHOP_ITEMS = [
    skin("Blauwe held", "skin_default", 0),
    skin("Groen", "skin_green", 200),
    skin("Rood", "skin_red", 200),
    skin("Oranje", "skin_orange", 200),
    skin("Paars", "skin_purple", 250),
    skin("Cyaan", "skin_cyan", 250),
    skin("Zilver", "skin_silver", 300),
    skin("Zwart", "skin_black", 300),
    skin("Goud", "skin_gold", 500),
    skin("Ridder", "skin_knight", 600),
    skin("Piraat", "skin_pirate", 600),
    skin("Kikker", "skin_frog", 600),
    skin("Skelet", "skin_skeleton", 700),
    skin("Ninja", "skin_ninja", 800),
    skin("Robot", "skin_robot", 800),
    skin("Tovenaar", "skin_wizard", 900),
    skin("Donkere tovenaar", "skin_dark_wizard", 1000),
    skin("Vampier", "skin_vampire", 1000),
    skin("Astronaut", "skin_astronaut", 1200),
    skin("Kat", "skin_cat", 800),
    skin("Dino", "skin_dino", 900),
    skin("Banaan", "skin_banana", 700),
    skin("Clown", "skin_clown", 900),
    skin("Legende", "skin_legend", 0, "genocide"),
    skin("Gouden ridder", "skin_gold_knight", 0, "marathon"),
    skin("Walvis", "skin_whale", 0, "extreme"),
    bullet("Standaard kogels", "bullet_default", 0),
    bullet("Witte kogels", "bullet_white", 150),
    bullet("Groene kogels", "bullet_green", 150),
    bullet("Roze kogels", "bullet_pink", 150),
    bullet("Blauwe kogels", "bullet_blue", 150),
    bullet("Rode kogels", "bullet_red", 150),
    bullet("Pijlen", "bullet_arrow", 300),
    bullet("Sterren", "bullet_star", 400),
    bullet("IJspegels", "bullet_ice", 400),
    bullet("Vuurballen", "bullet_fire", 500),
    bullet("Hartjes", "bullet_heart", 500),
    bullet("Leegte kogels", "bullet_void", 600),
    bullet("Regenboog kogels", "bullet_rainbow", 700),
    bullet("Muntjes kogels", "bullet_coin", 0, "rich"),
    bullet("Gouden kogels", "bullet_gold", 0, "boss"),
    perk("Grotere start magneet", "pickup", 500),
    perk("Meer geluk", "luck", 700),
    perk("Start herstel", "regen", 900),
    perk("Snellere start", "speed", 900),
    perk("Extra start HP", "start_hp", 1200),
    perk("Extra start damage", "start_damage", 1200),
    perk("Scherpe start", "crit", 1200),
    perk("Start met werpmessen", "knives", 1500),
    perk("Extra start HP 2", "start_hp", 0, "level20"),
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
    # oude saves hebben de achievement al maar nog niet het item
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
    # gratis items uit de winkel heb je altijd
    if item["price"] == 0 and not item["achievement"]:
        return True
    return item["name"] in data["owned"]


def buy_item(data, item):
    """Koop iets uit de winkel, geeft een bericht terug voor op het scherm."""
    if owns(data, item):
        if equip(data, item):
            return f"{item['name']} uitgerust"
        return "Je hebt dit al"
    if item["achievement"]:
        return "Haal eerst de achievement"
    if data["coins"] < item["price"]:
        return "Niet genoeg coins"
    data["coins"] -= item["price"]
    give(data, item)
    equip(data, item)
    return f"{item['name']} gekocht!"


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


def apply_perks(data, player):
    for item in SHOP_ITEMS:
        if item["type"] == "perk" and item["name"] in data["owned"]:
            PERK_EFFECTS[item["effect"]](player)

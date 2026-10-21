import json
import os
import shutil
from datetime import date

import pygame

from settings import W, H

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saves")
SETTINGS_FILE = os.path.join(SAVE_DIR, "settings.json")
OLD_SAVE = os.path.join(os.path.dirname(__file__), "battlepass.json")
SLOTS = 3

slot = 1


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_json(path, data):
    # eerst naar een tijdelijk bestand, zo is de save nooit half geschreven
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def slot_dir(n=None):
    if n is None:
        n = slot
    return os.path.join(SAVE_DIR, f"slot_{n}")


def profile_file(n=None):
    return os.path.join(slot_dir(n), "profile.json")


def run_file(n=None):
    return os.path.join(slot_dir(n), "run.json")


def migrate():
    """De oude battlepass.json komt in slot 1 als die nog leeg is."""
    if os.path.exists(OLD_SAVE) and not os.path.exists(profile_file(1)):
        data = read_json(OLD_SAVE)
        if data:
            write_json(profile_file(1), data)


def load_profile():
    return read_json(profile_file())


def save_profile(data):
    data["last_played"] = date.today().isoformat()
    write_json(profile_file(), data)


def slot_info(n):
    data = read_json(profile_file(n))
    if data is None:
        return None
    run = read_json(run_file(n))
    return {
        "xp": data.get("xp", 0),
        "coins": data.get("coins", 0),
        "achievements": len(data.get("achievements", [])),
        "runs": data.get("totals", {}).get("runs", 0),
        "last_played": data.get("last_played", "?"),
        "run": run_summary(run),
    }


def delete_slot(n):
    shutil.rmtree(slot_dir(n), ignore_errors=True)


# ---------- runs ----------

def has_run():
    return os.path.exists(run_file())


def run_summary(run=None):
    if run is None:
        return None
    return {"difficulty": run["difficulty_key"], "time": run["time"], "level": run["player"]["level"]}


def current_run_summary():
    return run_summary(read_json(run_file()))


def delete_run():
    if os.path.exists(run_file()):
        os.remove(run_file())


STATE_KEYS = ("difficulty_key", "time", "spawn_timer", "next_boss", "stats", "freeze", "streak",
              "event", "event_time", "next_event")


def save_run(state):
    player = state["player"]
    data = {}
    for key in STATE_KEYS:
        data[key] = state[key]

    info = {}
    for key, value in vars(player).items():
        if isinstance(value, (int, float, bool, str)):
            info[key] = value
    info["pos"] = list(player.pos)
    info["facing"] = list(player.facing)
    info["weapons"] = [{"key": w.key, "level": w.level} for w in player.weapons]
    # een open upgrade keuze gaat niet verloren
    if state["choices"]:
        info["pending_upgrades"] += 1
    data["player"] = info

    data["enemies"] = []
    for enemy in state["enemies"]:
        if enemy.hp <= 0:
            continue
        data["enemies"].append({"kind": enemy.kind, "pos": list(enemy.pos), "minutes": enemy.minutes,
                                "elite": enemy.elite, "hp": enemy.hp, "max_hp": enemy.max_hp,
                                "speed": enemy.speed})
    data["orbs"] = [{"pos": list(o.pos), "value": o.value} for o in state["orbs"] if o.value > 0]
    data["pickups"] = [{"kind": p.kind, "pos": list(p.pos), "life": p.life} for p in state["pickups"]]
    data["seed"] = state["world"].seed
    data["looted"] = [list(key) for key in state["world"].looted]
    write_json(run_file(), data)


def load_run():
    return read_json(run_file())


def apply_run(state, data):
    """Zet een opgeslagen run terug in een vers gemaakte state."""
    from enemy import Enemy
    from orb import Orb
    from pickup import Pickup
    from weapons import make_weapon

    for key in STATE_KEYS:
        if key in data:
            state[key] = data[key]

    player = state["player"]
    info = data["player"]
    for key, value in info.items():
        # skin en kogels komen van de save, die kan je in de tussentijd veranderd hebben
        if key in ("pos", "facing", "weapons", "sprite", "bullet_sprite"):
            continue
        if hasattr(player, key):
            setattr(player, key, value)
    player.pos = pygame.Vector2(info["pos"])
    player.facing = pygame.Vector2(info["facing"])
    player.weapons = []
    for weapon_info in info["weapons"]:
        weapon = make_weapon(weapon_info["key"])
        weapon.level = weapon_info["level"]
        player.weapons.append(weapon)

    for item in data["enemies"]:
        enemy = Enemy(item["kind"], item["pos"], item["minutes"], elite=item["elite"])
        enemy.hp = item["hp"]
        enemy.max_hp = item["max_hp"]
        enemy.speed = item["speed"]
        state["enemies"].append(enemy)
    for item in data["orbs"]:
        state["orbs"].append(Orb(item["pos"], item["value"]))
    for item in data["pickups"]:
        pickup = Pickup(item["kind"], item["pos"])
        pickup.life = item["life"]
        state["pickups"].append(pickup)
    for key in data["looted"]:
        state["world"].looted.add(tuple(key))
    state["camera"] = player.pos - pygame.Vector2(W / 2, H / 2)

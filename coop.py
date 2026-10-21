import random

import pygame

import achievements
import ambient
import effects
import progress
import sound
from bullet import Bullet
from enemy import Enemy
from orb import Orb
from pickup import Pickup
from player import Player
from upgrades import pick_choices
from weapons import make_weapon
from settings import W, H, SNAPSHOT_RATE, CHOICE_TIME, REVIVE_TIME, REVIVE_RANGE, REVIVE_HP, COOP_COLORS, DASH_DURATION

# these keys hold enemies, those can't be sent
SKIP_KEYS = ("hit", "cooldowns")
SMOOTHING = 15


def pack(value):
    """Turn something into plain json: vectors become lists, floats get rounded."""
    if isinstance(value, pygame.Vector2):
        return [round(value.x, 1), round(value.y, 1)]
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, (list, tuple)):
        return [pack(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key not in SKIP_KEYS:
                result[key] = pack(item)
        return result
    return value


def unpack(value):
    if isinstance(value, list):
        return [unpack(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in ("pos", "dir"):
                result[key] = pygame.Vector2(item)
            else:
                result[key] = unpack(item)
        return result
    return value


def make_player(info, difficulty, index):
    player = Player(difficulty["player_hp"], info["sprite"], info["bullet"])
    progress.apply_perks({"owned": info["perks"]}, player)
    player.id = info["id"]
    player.name = info["name"]
    player.color = COOP_COLORS[index % len(COOP_COLORS)]
    # a bit apart, so you don't all stand on the same spot
    player.pos = pygame.Vector2(index * 50, 0)
    return player


def setup(state, info):
    start = info["start"]
    state["online"] = info["role"]
    state["my_id"] = info["my_id"]
    state["players"] = []
    for i, player_info in enumerate(start["players"]):
        if player_info["id"] == info["my_id"]:
            player = state["player"]
            player.id = player_info["id"]
            player.name = player_info["name"]
            player.color = COOP_COLORS[i % len(COOP_COLORS)]
            player.pos = pygame.Vector2(i * 50, 0)
        else:
            player = make_player(player_info, state["difficulty"], i)
            player.remote = True
        state["players"].append(player)
    state["snapshot_timer"] = 0
    state["choice_ids"] = {}
    if info["role"] == "host":
        state["conns"] = info["conns"]
        state["server"] = info["server"]
        effects.outbox = []
        sound.outbox = []
    else:
        state["conn"] = info["conn"]
        # the host does the healing, otherwise you'd see it twice
        state["player"].regen = 0
        state["enemy_ids"] = {}
        state["picked"] = None
        state["dashed"] = False
        state["pick"] = None
        state["host_left"] = False


def find_player(state, player_id):
    for player in state["players"]:
        if player.id == player_id:
            return player
    return None


def stop(state):
    """Close everything when the online run is over."""
    if state["online"] == "host":
        message = {"type": "end", "stats": state["stats"], "time": state["time"]}
        for conn in state["conns"].values():
            conn.send(message)
            conn.close()
        state["conns"] = {}
        state["server"].close()
    elif state["online"] == "client":
        state["conn"].close()
    effects.outbox = None
    sound.outbox = None


# ---------- host ----------

def read_clients(state):
    for player_id, conn in list(state["conns"].items()):
        player = find_player(state, player_id)
        for message in conn.messages():
            if message["type"] == "disconnect":
                del state["conns"][player_id]
                state["players"].remove(player)
                effects.announce(f"{player.name} left", (240, 110, 110), 40)
                break
            if message["type"] != "input":
                continue
            if not player.downed:
                player.pos = pygame.Vector2(message["pos"])
                player.facing = pygame.Vector2(message["facing"])
                player.move = pygame.Vector2(message["move"])
            if message["dash"]:
                player.invis_timer = max(player.invis_timer, DASH_DURATION + 0.1)
            if message["pick"] is not None and message["pick"][0] == state["choice_ids"].get(player_id):
                pick(player, message["pick"][1])


def pick(player, index):
    if player.choices and 0 <= index < len(player.choices):
        player.choices[index]["apply"](player)
        player.choices = None
        if not player.remote:
            sound.play_local("pick")


def update_choices(state, dt):
    for player in state["players"]:
        if player.choices:
            player.choice_timer -= dt
            if player.choice_timer <= 0:
                pick(player, random.randrange(len(player.choices)))
        elif player.pending_upgrades > 0 and not player.downed:
            player.pending_upgrades -= 1
            player.choices = pick_choices(player)
            player.choice_timer = CHOICE_TIME
            # every new set of cards gets a number, so an old click can't pick from it
            state["choice_ids"][player.id] = state["choice_ids"].get(player.id, 0) + 1
            if player is state["player"]:
                state["choice_selected"] = 0
                sound.play_local("level_up")


def update_revive(state, dt):
    for player in state["players"]:
        if not player.downed:
            continue
        helped = False
        for other in state["players"]:
            if not other.downed and other.pos.distance_to(player.pos) < REVIVE_RANGE:
                helped = True
        if helped:
            player.revive_timer += dt
        else:
            player.revive_timer = max(0, player.revive_timer - dt)
        if player.revive_timer >= REVIVE_TIME:
            player.downed = False
            player.revive_timer = 0
            player.hp = REVIVE_HP
            player.invis_timer = 2
            effects.ring(player.pos, (120, 240, 120), 60)
            effects.add_text(player.pos + (0, -40), "Revived!", (120, 240, 120), 28)
            sound.play("level_up")


def player_info(state, player):
    choices = None
    if player.choices:
        choices = [{"name": c["name"], "desc": c["desc"], "icon": c["icon"], "new": c.get("new", False)}
                   for c in player.choices]
    weapons = []
    for weapon in player.weapons:
        info = pack(vars(weapon))
        info["key"] = weapon.key
        weapons.append(info)
    return {"id": player.id, "name": player.name, "color": player.color, "pos": pack(player.pos),
            "facing": pack(player.facing), "move": pack(player.move), "hp": player.hp,
            "max_hp": player.max_hp, "xp": pack(player.xp), "level": player.level, "sprite": player.sprite,
            "invis": pack(player.invis_timer), "dash": pack(player.dash_timer), "boots": pack(player.boots_timer),
            "potion": pack(player.potion_timer), "speed": pack(player.speed), "can_dash": player.can_dash,
            "downed": player.downed, "revive": pack(player.revive_timer), "choices": choices,
            "choice_id": state["choice_ids"].get(player.id, 0), "choice_timer": pack(player.choice_timer),
            "weapons": weapons, "anim": pack(player.anim_time)}


def bullet_info(bullet):
    return [bullet.sprite, round(bullet.pos.x), round(bullet.pos.y), round(bullet.velocity.x),
            round(bullet.velocity.y), round(bullet.life, 2), bullet.radius]


def make_snapshot(state):
    enemies = []
    for enemy in state["enemies"]:
        enemies.append([enemy.id, enemy.kind, round(enemy.pos.x), round(enemy.pos.y), enemy.hp, enemy.max_hp,
                        enemy.elite, round(enemy.flash, 2), enemy.facing_left, enemy.awake, round(enemy.fuse, 2),
                        enemy.dash_state, round(enemy.heal_flash, 2), enemy.radius])
    return {
        "type": "snap",
        "time": pack(state["time"]),
        "freeze": pack(state["freeze"]),
        "flash": pack(state["flash"]),
        "streak": state["streak"],
        "streak_timer": pack(state["streak_timer"]),
        "stats": state["stats"],
        "event": state["event"],
        "event_time": pack(state["event_time"]),
        "meteors": pack(state["event_meteors"]),
        "players": [player_info(state, p) for p in state["players"]],
        "enemies": enemies,
        "bullets": [bullet_info(b) for b in state["bullets"]],
        "enemy_bullets": [bullet_info(b) for b in state["enemy_bullets"]],
        "orbs": [[round(o.pos.x), round(o.pos.y), o.value] for o in state["orbs"]],
        "pickups": [[p.kind, round(p.pos.x), round(p.pos.y), round(p.life, 1)] for p in state["pickups"]],
        "effects": effects.outbox,
        "sounds": sound.outbox,
    }


def send_snapshot(state, dt):
    state["snapshot_timer"] -= dt
    if state["snapshot_timer"] > 0:
        return
    state["snapshot_timer"] = 1 / SNAPSHOT_RATE
    message = make_snapshot(state)
    for conn in state["conns"].values():
        conn.send(message)
    effects.outbox.clear()
    sound.outbox.clear()


# ---------- client ----------

def send_input(state):
    player = state["player"]
    pick_message = None
    if state["pick"] is not None:
        pick_message = [state["choice_ids"].get(player.id, 0), state["pick"]]
        state["picked"] = pick_message[0]
        state["pick"] = None
    state["conn"].send({"type": "input", "pos": pack(player.pos), "facing": pack(player.facing),
                        "move": pack(player.move), "dash": state["dashed"], "pick": pick_message})
    state["dashed"] = False


def smooth(pos, target, dt):
    # far away means it was a jump (like a new spot), then just go there
    if pos.distance_to(target) > 200:
        pos.update(target)
    else:
        pos += (target - pos) * min(1, dt * SMOOTHING)


def apply_player(state, player, info):
    is_me = player is state["player"]
    if is_me and info["hp"] < player.hp:
        effects.shake(6)
        sound.play("hurt")
    player.hp = info["hp"]
    player.max_hp = info["max_hp"]
    player.xp = info["xp"]
    player.level = info["level"]
    player.invis_timer = info["invis"]
    player.boots_timer = info["boots"]
    player.potion_timer = info["potion"]
    player.speed = info["speed"]
    player.can_dash = info["can_dash"]
    player.downed = info["downed"]
    if is_me and player.downed:
        # lying down where the host says you are, so teammates can find you
        player.pos = pygame.Vector2(info["pos"])
    player.revive_timer = info["revive"]
    player.choice_timer = info["choice_timer"]
    state["choice_ids"][player.id] = info["choice_id"]
    player.choices = info["choices"]
    # after you clicked a card it stays away, even if an older snapshot still has it
    if is_me and state["picked"] == info["choice_id"]:
        player.choices = None
    weapons = []
    for weapon_info in info["weapons"]:
        weapon = make_weapon(weapon_info["key"])
        for key, value in unpack(weapon_info).items():
            if key != "key":
                setattr(weapon, key, value)
        weapons.append(weapon)
    player.weapons = weapons
    if not is_me:
        player.target = pygame.Vector2(info["pos"])
        player.facing = pygame.Vector2(info["facing"])
        player.move = pygame.Vector2(info["move"])
        player.dash_timer = info["dash"]
        player.anim_time = info["anim"]
        player.color = info["color"]


def make_bullet(info):
    bullet = Bullet((info[1], info[2]), pygame.Vector2(info[3], info[4]), 0, info[0], 1, radius=info[6],
                    life=info[5])
    return bullet


def apply_snapshot(state, snap):
    for key in ("time", "freeze", "flash", "streak", "streak_timer", "stats", "event", "event_time"):
        state[key] = snap[key]
    state["event_meteors"] = unpack(snap["meteors"])

    players = []
    for info in snap["players"]:
        player = find_player(state, info["id"])
        if player is None:
            player = Player(info["max_hp"], info["sprite"])
            player.id = info["id"]
            player.name = info["name"]
            player.remote = True
            player.pos = pygame.Vector2(info["pos"])
        apply_player(state, player, info)
        players.append(player)
    if state["player"] not in players:
        players.append(state["player"])
    state["players"] = players

    old = state["enemy_ids"]
    new = {}
    for info in snap["enemies"]:
        enemy_id, kind = info[0], info[1]
        enemy = old.get(enemy_id)
        if enemy is None:
            enemy = Enemy(kind, (info[2], info[3]), elite=info[6])
        enemy.target = pygame.Vector2(info[2], info[3])
        enemy.hp, enemy.max_hp, enemy.elite, enemy.flash = info[4], info[5], info[6], info[7]
        enemy.facing_left, enemy.awake, enemy.fuse, enemy.dash_state = info[8], info[9], info[10], info[11]
        enemy.heal_flash, enemy.radius = info[12], info[13]
        new[enemy_id] = enemy
    state["enemy_ids"] = new
    state["enemies"] = list(new.values())

    state["bullets"] = [make_bullet(b) for b in snap["bullets"]]
    state["enemy_bullets"] = [make_bullet(b) for b in snap["enemy_bullets"]]
    state["orbs"] = [Orb((o[0], o[1]), o[2]) for o in snap["orbs"]]
    pickups = []
    for info in snap["pickups"]:
        pickup = Pickup(info[0], (info[1], info[2]))
        pickup.life = info[3]
        pickups.append(pickup)
    state["pickups"] = pickups
    effects.replay(snap["effects"])
    sound.replay(snap["sounds"])


def client_update(state, dt):
    """Returns True when the run is over."""
    player = state["player"]
    world = state["world"]
    ambient.update(dt)
    if state["paused"] or player.downed:
        player.move = pygame.Vector2(0, 0)
    player.update(dt)
    world.collide(player.pos, player.radius)
    state["camera"] = player.pos - pygame.Vector2(W / 2, H / 2)
    world.update_roofs(dt, player.pos)

    over = False
    newest = None
    for message in state["conn"].messages():
        if message["type"] == "snap":
            newest = message
        elif message["type"] == "end":
            state["stats"] = message["stats"]
            state["time"] = message["time"]
            over = True
        elif message["type"] == "disconnect" and not over:
            state["host_left"] = True
            over = True
    if over:
        return True
    if newest:
        apply_snapshot(state, newest)
    else:
        state["time"] += dt
    send_input(state)

    for other in state["players"]:
        if other is player:
            continue
        smooth(other.pos, getattr(other, "target", other.pos), dt)
        if other.move.length() > 0:
            other.anim_time += dt
    for enemy in state["enemies"]:
        smooth(enemy.pos, getattr(enemy, "target", enemy.pos), dt)
        enemy.anim_time += dt
    for bullet in state["bullets"] + state["enemy_bullets"]:
        bullet.update(dt)
    effects.update(dt)
    events_meteors_tick(state, dt)

    state["achievement_timer"] -= dt
    if state["achievement_timer"] <= 0:
        state["achievement_timer"] = 2
        stats = state["stats"]
        stats["time"] = state["time"]
        stats["level"] = player.level
        stats["weapons"] = len(player.weapons)
        achievements.check(stats, state["bp"])

    if player.choices and state.get("choice_seen") != state["choice_ids"].get(player.id):
        state["choice_seen"] = state["choice_ids"].get(player.id)
        state["choice_selected"] = 0
        sound.play("level_up")
    return False


def events_meteors_tick(state, dt):
    # the falling animation runs between snapshots too
    for meteor in state["event_meteors"]:
        meteor["timer"] -= dt
    for other in state["players"]:
        for weapon in other.weapons:
            if weapon.key == "meteor":
                for meteor in weapon.falling:
                    meteor["timer"] -= dt

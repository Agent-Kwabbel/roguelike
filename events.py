import random

import pygame

import effects
import phases
import sound
from enemy import spawn_kind, spawn_position, random_kind, random_affix
from pickup import Pickup
from settings import W, H, EVENT_FIRST, PUDDLE_RADIUS, PUDDLE_LIFE
from weapons import land, draw_meteor

# start is in effective seconds, so on hard difficulties they show up sooner
EVENTS = {
    "gold": {"name": "Gold rush!", "desc": "Enemies drop coins", "time": 30, "color": (250, 210, 60), "start": 0},
    "meteors": {"name": "Meteor shower!", "desc": "Look up", "time": 20, "color": (255, 120, 50), "start": 0},
    "blood_moon": {"name": "Blood moon", "desc": "Faster enemies, double XP", "time": 40, "color": (230, 40, 50),
                   "start": 0},
    "slime_rain": {"name": "Slime rain", "desc": "Where did they come from?", "time": 3, "color": (90, 200, 80),
                   "start": 0},
    "swarm": {"name": "Swarm!", "desc": "Something is coming...", "time": 4, "color": (150, 90, 200), "start": 240},
    "encircle": {"name": "Surrounded!", "desc": "Break out!", "time": 3, "color": (240, 120, 60), "start": 360},
    "fog": {"name": "Thick fog", "desc": "You can't see far", "time": 35, "color": (170, 180, 200), "start": 480},
    "elite_squad": {"name": "Elite squad", "desc": "Strong enemies are hunting you", "time": 3,
                    "color": (250, 210, 60), "start": 600},
    "cursed_ground": {"name": "Cursed ground", "desc": "Don't stand in the purple", "time": 20,
                      "color": (190, 80, 240), "start": 600},
    # only online with 2 or more players
    "split": {"name": "Split up!", "desc": "Hold both circles at the same time", "time": 45,
              "color": (120, 220, 255), "start": 240, "coop": True},
    "together": {"name": "Stick together!", "desc": "Everyone in the circle", "time": 40,
                 "color": (140, 240, 140), "start": 360, "coop": True},
}
ZONE_NEED = {"split": 12, "together": 10}
CURSE_RADIUS = 70
CURSE_DELAY = 1.0


def init(state):
    state["event"] = None
    state["event_time"] = 0
    state["next_event"] = EVENT_FIRST
    state["event_meteors"] = []
    state["meteor_timer"] = 0
    state["hazards"] = []
    state["zones"] = []


def alive_players(state):
    return [p for p in state["players"] if not p.downed]


def random_player(state):
    alive = [p for p in state["players"] if not p.downed]
    if alive:
        return random.choice(alive)
    return state["player"]


def add_enemy(state, enemy):
    if len(state["enemies"]) < phases.max_enemies(state) + 40:
        state["enemies"].append(enemy)


def add_hazard(state, pos, radius, life, color, delay=0):
    state["hazards"].append({"pos": pygame.Vector2(pos), "radius": radius, "life": life, "color": color,
                             "delay": delay})


def lava_puddle(state, pos):
    add_hazard(state, pos, PUDDLE_RADIUS, PUDDLE_LIFE, (255, 120, 40))


def available(state):
    time = phases.effective_time(state)
    team = len(alive_players(state)) >= 2
    keys = []
    for key, info in EVENTS.items():
        if time < info["start"]:
            continue
        if info.get("coop") and not team:
            continue
        keys.append(key)
    return keys


def team_center(state):
    players = alive_players(state) or state["players"]
    center = pygame.Vector2(0, 0)
    for player in players:
        center += player.pos
    return center / len(players)


def per_player(state, amount):
    # in co-op every player gets a wave, but a smaller one
    return round(amount * 2 / (len(alive_players(state)) + 1))


def start(state, key=None):
    if key is None:
        key = random.choice(available(state))
    info = EVENTS[key]
    state["event"] = key
    state["event_time"] = info["time"]
    effects.announce(info["name"], info["color"], 60)
    sound.play("event")
    player = random_player(state)
    effects.add_text(player.pos + (0, -60), info["desc"], info["color"], 28)
    world = state["world"]
    if key == "slime_rain":
        for _ in range(15):
            add_enemy(state, spawn_kind("walker", spawn_position(state, player.pos), state))
    elif key == "swarm":
        # a big group of bats from one side
        for target in alive_players(state):
            direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            for _ in range(per_player(state, 25)):
                offset = direction * random.uniform(550, 700) + direction.rotate(90) * random.uniform(-200, 200)
                add_enemy(state, spawn_kind("runner", target.pos + offset, state))
    elif key == "encircle":
        kind = random.choice(["walker", "skeleton", "spider"])
        if phases.index(state) >= 3:
            kind = random.choice(["knight", "skeleton", "lava_slime"])
        for target in alive_players(state):
            count = per_player(state, 28)
            for i in range(count):
                pos = target.pos + pygame.Vector2(380, 0).rotate(i * 360 / count)
                if not world.is_blocked(pos):
                    add_enemy(state, spawn_kind(kind, pos, state))
    elif key == "elite_squad":
        elite_squad(state, player)
    elif key == "split":
        center = team_center(state)
        direction = pygame.Vector2(350, 0).rotate(random.uniform(0, 360))
        for pos in (center + direction, center - direction):
            add_zone(state, pos, 90, "split", info["time"])
    elif key == "together":
        center = team_center(state) + pygame.Vector2(150, 0).rotate(random.uniform(0, 360))
        add_zone(state, center, 130, "together", info["time"])
    return info["name"]


def elite_squad(state, player):
    for _ in range(3):
        add_enemy(state, spawn_kind(random_kind(state), spawn_position(state, player.pos), state, True,
                                    random_affix()))


def add_zone(state, pos, radius, mode, life):
    # don't put it in a lake
    pos = pygame.Vector2(pos)
    for _ in range(10):
        if not state["world"].is_blocked(pos):
            break
        pos += pygame.Vector2(80, 0).rotate(random.uniform(0, 360))
    state["zones"].append({"pos": pos, "radius": radius, "mode": mode, "progress": 0,
                           "need": ZONE_NEED[mode], "life": life})


def inside(player, zone):
    return player.pos.distance_to(zone["pos"]) < zone["radius"]


def update_zones(state, dt):
    zones = state["zones"]
    if not zones:
        return
    players = alive_players(state)
    mode = zones[0]["mode"]
    if mode == "split":
        holding = all(any(inside(p, zone) for p in players) for zone in zones)
    else:
        holding = len(players) > 0 and all(inside(p, zones[0]) for p in players)
    for zone in zones:
        zone["life"] -= dt
        if holding:
            zone["progress"] += dt
    if zones[0]["progress"] >= zones[0]["need"]:
        zone_done(state, players)
    elif zones[0]["life"] <= 0:
        effects.announce("Failed...", (240, 90, 90), 50)
        if mode == "split" and players:
            elite_squad(state, random.choice(players))
        state["zones"] = []


def zone_done(state, players):
    effects.announce("Well done, team!", (140, 240, 140), 56)
    sound.play("achievement")
    state["stats"]["coop_events"] = state["stats"].get("coop_events", 0) + 1
    if state["zones"][0]["mode"] == "split":
        for zone in state["zones"]:
            state["pickups"].append(Pickup("chest", zone["pos"]))
    else:
        for player in players:
            player.hp = player.max_hp
            state["pickups"].append(Pickup("chest", player.pos + (0, 40)))
            effects.add_text(player.pos + (0, -40), "Healed!", (120, 240, 120), 26)
    for zone in state["zones"]:
        effects.ring(zone["pos"], (140, 240, 140), zone["radius"])
    state["zones"] = []
    state["event"] = None
    state["event_time"] = 0


def spawn_mult(state):
    # more enemies while you stand together in the circle
    if state["event"] == "together":
        return 0.6
    return 1


def update(state, dt):
    if state["time"] >= state["next_event"]:
        state["next_event"] += phases.current(state)["events"]
        start(state)

    if state["event"]:
        state["event_time"] -= dt
        if state["event_time"] <= 0:
            state["event"] = None

    if state["event"] == "meteors":
        state["meteor_timer"] -= dt
        if state["meteor_timer"] <= 0:
            state["meteor_timer"] = 0.35
            offset = pygame.Vector2(random.uniform(-450, 450), random.uniform(-320, 320))
            state["event_meteors"].append({"pos": random_player(state).pos + offset, "timer": 1.0, "landed": False})
    elif state["event"] == "cursed_ground":
        state["meteor_timer"] -= dt
        if state["meteor_timer"] <= 0:
            state["meteor_timer"] = 0.8
            offset = pygame.Vector2(random.uniform(-200, 200), random.uniform(-160, 160))
            add_hazard(state, random_player(state).pos + offset, CURSE_RADIUS, 5, (190, 80, 240), CURSE_DELAY)

    for meteor in state["event_meteors"]:
        meteor["timer"] -= dt
        if meteor["timer"] <= 0 and not meteor["landed"]:
            meteor["landed"] = True
            land(meteor["pos"], 60, 10, state["player"], state["enemies"])
            for player in state["players"]:
                if player.pos.distance_to(meteor["pos"]) < 60:
                    player.take_damage(1)
    state["event_meteors"] = [m for m in state["event_meteors"] if m["timer"] > -0.2]
    update_hazards(state, dt)
    update_zones(state, dt)


def update_hazards(state, dt):
    damage = phases.enemy_damage(state)
    for hazard in state["hazards"]:
        if hazard["delay"] > 0:
            hazard["delay"] -= dt
            continue
        hazard["life"] -= dt
        for player in state["players"]:
            if not player.downed and player.pos.distance_to(hazard["pos"]) < hazard["radius"]:
                player.take_damage(damage)
    state["hazards"] = [h for h in state["hazards"] if h["life"] > 0]


def enemy_speed(state):
    if state["event"] == "blood_moon":
        return 1.35
    return 1


def xp_mult(state):
    if state["event"] == "blood_moon":
        return 2
    return 1


def coin_drops(state):
    return state["event"] == "gold"


def draw(screen, camera, state):
    for hazard in state["hazards"]:
        draw_hazard(screen, camera, hazard)
    for meteor in state["event_meteors"]:
        draw_meteor(screen, camera, meteor, 60)
    for zone in state["zones"]:
        draw_zone(screen, camera, zone)


def draw_zone(screen, camera, zone):
    pos = zone["pos"] - camera
    radius = zone["radius"]
    color = (120, 220, 255) if zone["mode"] == "split" else (140, 240, 140)
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surface, color + (45,), (radius, radius), radius)
    screen.blit(surface, (pos.x - radius, pos.y - radius))
    pygame.draw.circle(screen, color, pos, radius, 3)
    # progress goes around the circle
    part = min(1, zone["progress"] / zone["need"])
    if part > 0:
        rect = pygame.Rect(pos.x - radius - 8, pos.y - radius - 8, radius * 2 + 16, radius * 2 + 16)
        pygame.draw.arc(screen, (255, 255, 255), rect, 1.571, 1.571 + part * 6.283, 5)


def draw_hazard(screen, camera, hazard):
    radius = hazard["radius"]
    pos = hazard["pos"] - camera
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    r, g, b = hazard["color"]
    if hazard["delay"] > 0:
        # warning first, just an outline
        pygame.draw.circle(surface, (r, g, b, 160), (radius, radius), radius, 2)
    else:
        alpha = min(1, hazard["life"]) * 110
        pygame.draw.circle(surface, (r, g, b, int(alpha)), (radius, radius), radius)
        pygame.draw.circle(surface, (r, g, b, int(alpha * 1.8)), (radius, radius), radius, 3)
    screen.blit(surface, (pos.x - radius, pos.y - radius))


def draw_overlay(screen, state):
    if state["event"] == "blood_moon":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((150, 0, 20, 60))
        screen.blit(overlay, (0, 0))
    elif state["event"] == "fog":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((180, 185, 200, 220))
        center = state["player"].pos - state["camera"]
        for i in range(7):
            pygame.draw.circle(overlay, (180, 185, 200, int(220 * (6 - i) / 7)), center, 260 - i * 30)
        screen.blit(overlay, (0, 0))

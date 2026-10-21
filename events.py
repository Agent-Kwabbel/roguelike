import random

import pygame

import effects
import sound
from enemy import spawn_kind
from settings import W, H, EVENT_FIRST, EVENT_INTERVAL, MAX_ENEMIES
from weapons import land, draw_meteor

EVENTS = {
    "gold": {"name": "Gold rush!", "desc": "Enemies drop coins", "time": 30, "color": (250, 210, 60)},
    "meteors": {"name": "Meteor shower!", "desc": "Look up", "time": 20, "color": (255, 120, 50)},
    "blood_moon": {"name": "Blood moon", "desc": "Faster enemies, double XP", "time": 40, "color": (230, 40, 50)},
    "slime_rain": {"name": "Slime rain", "desc": "Where did they come from?", "time": 3, "color": (90, 200, 80)},
}


def init(state):
    state["event"] = None
    state["event_time"] = 0
    state["next_event"] = EVENT_FIRST
    state["event_meteors"] = []
    state["meteor_timer"] = 0


def random_player(state):
    alive = [p for p in state["players"] if not p.downed]
    if alive:
        return random.choice(alive)
    return state["player"]


def start(state, key=None):
    if key is None:
        key = random.choice(list(EVENTS.keys()))
    info = EVENTS[key]
    state["event"] = key
    state["event_time"] = info["time"]
    effects.announce(info["name"], info["color"], 60)
    sound.play("event")
    player = random_player(state)
    effects.add_text(player.pos + (0, -60), info["desc"], info["color"], 28)
    if key == "slime_rain":
        for _ in range(15):
            if len(state["enemies"]) < MAX_ENEMIES:
                state["enemies"].append(spawn_kind("walker", player.pos, state["time"], state["difficulty"], state["world"]))
    return info["name"]


def update(state, dt):
    if state["time"] >= state["next_event"]:
        state["next_event"] += EVENT_INTERVAL
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

    for meteor in state["event_meteors"]:
        meteor["timer"] -= dt
        if meteor["timer"] <= 0 and not meteor["landed"]:
            meteor["landed"] = True
            land(meteor["pos"], 60, 10, state["player"], state["enemies"])
            for player in state["players"]:
                if player.pos.distance_to(meteor["pos"]) < 60:
                    player.take_damage(1)
    state["event_meteors"] = [m for m in state["event_meteors"] if m["timer"] > -0.2]


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
    for meteor in state["event_meteors"]:
        draw_meteor(screen, camera, meteor, 60)


def draw_overlay(screen, state):
    if state["event"] == "blood_moon":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((150, 0, 20, 60))
        screen.blit(overlay, (0, 0))

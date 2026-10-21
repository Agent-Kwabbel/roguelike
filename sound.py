import os
import random

import pygame

import config

FOLDER = os.path.join(os.path.dirname(__file__), "assets")

# how long a sound has to wait before it can play again, so 30 hits in one frame isn't a wall of noise
COOLDOWNS = {
    "shoot": 0.06,
    "knife": 0.06,
    "hit": 0.035,
    "crit": 0.05,
    "kill": 0.03,
    "enemy_shoot": 0.08,
    "lightning": 0.06,
    "meteor": 0.08,
    "explosion": 0.08,
    "fuse": 0.15,
    "menu_move": 0.03,
    "coin": 0.04,
}
MAX_COPIES = 4
XP_STEPS = 8
XP_COMBO_TIME = 0.6
DUCKED = 0.35

enabled = False
sounds = {}
timers = {}
xp = {"step": 0, "timer": 0}
# in an online game the host writes sounds in here, they get sent to the other players
outbox = None
music_state = {"wanted": None, "playing": None, "fading": False, "ducked": False, "volume": -1}


def init():
    global enabled
    try:
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
    except pygame.error:
        print("no sound device, the game stays quiet")
        return
    folder = os.path.join(FOLDER, "sounds")
    if not os.path.isdir(folder):
        print("no sounds found, run tools/make_sounds.py")
        return
    for file in sorted(os.listdir(folder)):
        if not file.endswith(".wav"):
            continue
        name = file[:-4]
        # hit_0, hit_1, ... are variants of "hit"
        base, _, number = name.rpartition("_")
        if base and number.isdigit():
            name = base
        sounds.setdefault(name, []).append(pygame.mixer.Sound(os.path.join(folder, file)))
    enabled = True


def play(name, volume=1.0):
    if outbox is not None:
        outbox.append([name, volume])
    if not enabled or name not in sounds:
        return
    if timers.get(name, 0) > 0:
        return
    timers[name] = COOLDOWNS.get(name, 0.02)
    sound = random.choice(sounds[name])
    if sound.get_num_channels() >= MAX_COPIES:
        return
    channel = pygame.mixer.find_channel()
    if channel is None:
        return
    channel.set_volume(volume * config.get("sound_volume") / 10)
    channel.play(sound)


def play_xp():
    # every orb picked up quickly after the last one sounds a bit higher
    play(f"xp{xp['step']}")
    xp["step"] = min(XP_STEPS - 1, xp["step"] + 1)
    xp["timer"] = XP_COMBO_TIME


def play_streak(streak):
    if streak >= 100:
        play_local("streak3")
    elif streak >= 25:
        play_local("streak2")
    elif streak >= 10:
        play_local("streak1")
    else:
        play_local("streak0")


def play_local(name, volume=1.0):
    """Only on this computer, not sent to the other players."""
    global outbox
    saved = outbox
    outbox = None
    play(name, volume)
    outbox = saved


def replay(items):
    for name, volume in items:
        play(name, volume)


def music(name):
    music_state["wanted"] = name


def duck(on):
    music_state["ducked"] = on


def update_music():
    state = music_state
    mixer = pygame.mixer.music
    if state["wanted"] != state["playing"]:
        if mixer.get_busy() and not state["fading"]:
            mixer.fadeout(600)
            state["fading"] = True
        elif not mixer.get_busy():
            state["fading"] = False
            state["playing"] = state["wanted"]
            path = os.path.join(FOLDER, "music", f"{state['wanted']}.wav")
            if state["wanted"] and os.path.exists(path):
                mixer.load(path)
                mixer.play(-1, fade_ms=800)

    volume = config.get("music_volume") / 10
    if state["ducked"]:
        volume *= DUCKED
    if volume != state["volume"]:
        state["volume"] = volume
        mixer.set_volume(volume)


def update(dt):
    if not enabled:
        return
    for name in timers:
        timers[name] -= dt
    xp["timer"] -= dt
    if xp["timer"] <= 0:
        xp["step"] = 0
    update_music()

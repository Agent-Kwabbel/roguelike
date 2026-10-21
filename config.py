import pygame

import saves
from settings import W, H

DEFAULTS = {
    "fullscreen": True,
    "screen_shake": True,
    "show_fps": False,
    "effects": True,
    "music_volume": 6,
    "sound_volume": 8,
    "last_slot": None,
    "last_ip": "",
}

values = dict(DEFAULTS)


def load():
    data = saves.read_json(saves.SETTINGS_FILE)
    if data:
        values.update(data)


def save():
    saves.write_json(saves.SETTINGS_FILE, values)


def get(key):
    return values[key]


def set(key, value):
    values[key] = value
    save()


def window_flags():
    flags = pygame.SCALED
    if values["fullscreen"]:
        flags |= pygame.FULLSCREEN
    return flags


def toggle_fullscreen():
    set("fullscreen", not values["fullscreen"])
    pygame.display.set_mode((W, H), window_flags())

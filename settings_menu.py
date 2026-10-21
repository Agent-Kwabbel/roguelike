import pygame

import config
import sound
import ui
from settings import W

OPTIONS = [
    ("Music", "music_volume", "A/D to change"),
    ("Sound effects", "sound_volume", "A/D to change"),
    ("Fullscreen", "fullscreen", "F11 works everywhere too"),
    ("Screen shake", "screen_shake", "Screen shakes on explosions and streaks"),
    ("Show FPS", "show_fps", "In the bottom right corner"),
    ("Extra effects", "effects", "Clouds, fireflies and sparkles"),
]
VOLUMES = ("music_volume", "sound_volume")

selected = 0


def rects():
    result = []
    for i in range(len(OPTIONS)):
        result.append(pygame.Rect(W / 2 - 240, 152 + i * 64, 480, 56))
    result.append(pygame.Rect(W / 2 - 100, 152 + len(OPTIONS) * 64 + 10, 200, 46))
    return result


def change_volume(key, amount, wrap=False):
    value = config.get(key) + amount
    if wrap and value > 10:
        value = 0
    config.set(key, max(0, min(10, value)))
    if key == "sound_volume":
        sound.play("menu_select")


def handle(events):
    """Returns True when you want to go back."""
    global selected
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            selected = 0
            return True
        if event.type == pygame.KEYDOWN and selected < len(OPTIONS) and OPTIONS[selected][1] in VOLUMES:
            key = OPTIONS[selected][1]
            if event.key in (pygame.K_LEFT, pygame.K_a):
                change_volume(key, -1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                change_volume(key, 1)
    if ui.back_clicked(events):
        selected = 0
        return True
    selected, chosen = ui.navigate(events, selected, rects())
    if chosen is None:
        return False
    if chosen == len(OPTIONS):
        selected = 0
        return True
    key = OPTIONS[chosen][1]
    if key in VOLUMES:
        change_volume(key, 1, wrap=True)
    elif key == "fullscreen":
        config.toggle_fullscreen()
    else:
        config.set(key, not config.get(key))
    return False


def draw_switch(screen, rect, on):
    switch = pygame.Rect(rect.right - 84, rect.centery - 14, 60, 28)
    color = ui.GREEN if on else (60, 58, 80)
    pygame.draw.rect(screen, color, switch, border_radius=14)
    knob_x = switch.right - 14 if on else switch.x + 14
    pygame.draw.circle(screen, (20, 18, 30), (knob_x, switch.centery + 2), 11)
    pygame.draw.circle(screen, ui.WHITE, (knob_x, switch.centery), 11)
    label = "ON" if on else "OFF"
    ui.text(screen, label, 18, ui.GREEN if on else ui.DIM, (switch.x - 10, switch.y + 7), "right")


def draw_volume(screen, rect, value):
    # ten little blocks that get taller, like a volume icon
    right = rect.right - 24
    for i in range(10):
        height = 8 + i * 2
        block = pygame.Rect(right - (10 - i) * 12, rect.centery + 11 - height, 8, height)
        color = ui.GREEN if i < value else (60, 58, 80)
        pygame.draw.rect(screen, color, block, border_radius=2)
    label = "OFF" if value == 0 else f"{value * 10}%"
    ui.text(screen, label, 18, ui.GREEN if value else ui.DIM, (right - 130, rect.centery - 8), "right")


def draw(screen):
    ui.title(screen, "Settings", 64, ui.WHITE, 72)
    ui.text(screen, "Saved automatically", 22, ui.GREY, (W / 2, 120), "center")
    all_rects = rects()
    for i, (label, key, desc) in enumerate(OPTIONS):
        rect = ui.button(screen, all_rects[i], label, i == selected, sub=desc)
        if key in VOLUMES:
            draw_volume(screen, rect, config.get(key))
        else:
            draw_switch(screen, rect, config.get(key))
    ui.center_button(screen, all_rects[-1], "Back", selected == len(OPTIONS), ui.GREY)
    ui.back_button(screen)
    ui.footer(screen, [("W/S", "Move"), ("A/D", "Volume"), ("Enter", "Toggle"), ("Esc", "Back")])

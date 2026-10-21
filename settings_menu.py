import pygame

import config
import ui
from settings import W, H

OPTIONS = [
    ("Volledig scherm", "fullscreen", "F11 werkt ook overal"),
    ("Screen shake", "screen_shake", "Beeld schudt bij explosies en streaks"),
    ("FPS tonen", "show_fps", "Linksonder in beeld"),
]

selected = 0


def rects():
    result = []
    for i in range(len(OPTIONS) + 1):
        result.append(pygame.Rect(W / 2 - 220, 200 + i * 78, 440, 64))
    return result


def handle(events):
    """Geeft True terug als je terug wil."""
    global selected
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
    if ui.back_clicked(events):
        return True
    selected, chosen = ui.navigate(events, selected, rects())
    if chosen is None:
        return False
    if chosen == len(OPTIONS):
        selected = 0
        return True
    key = OPTIONS[chosen][1]
    if key == "fullscreen":
        config.toggle_fullscreen()
    else:
        config.set(key, not config.get(key))
    return False


def draw(screen):
    ui.title(screen, "Instellingen", 72, ui.WHITE, 100)
    all_rects = rects()
    for i, (label, key, desc) in enumerate(OPTIONS):
        rect = ui.button(screen, all_rects[i], label, i == selected, sub=desc)
        on = config.get(key)
        # schakelaartje rechts in de knop
        switch = pygame.Rect(rect.right - 84, rect.centery - 14, 60, 28)
        color = (110, 210, 120) if on else (80, 78, 100)
        pygame.draw.rect(screen, color, switch, border_radius=14)
        knob_x = switch.right - 14 if on else switch.x + 14
        pygame.draw.circle(screen, ui.WHITE, (knob_x, switch.centery), 11)
    ui.button(screen, all_rects[-1], "Terug", selected == len(OPTIONS))
    ui.back_button(screen)

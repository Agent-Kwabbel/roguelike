import pygame

import sprites
from menus import draw_background, text_center, panel, YELLOW, GREY
from settings import W

# check krijgt de stats van de run en de save, gems is de beloning
ACHIEVEMENTS = [
    {"key": "first_blood", "name": "Eerste bloed", "desc": "Versla een vijand", "gems": 5,
     "check": lambda s, bp: s.get("kills", 0) >= 1},
    {"key": "butcher", "name": "Slager", "desc": "500 kills in een run", "gems": 20,
     "check": lambda s, bp: s.get("kills", 0) >= 500},
    {"key": "genocide", "name": "Dat zijn er veel", "desc": "5000 kills in totaal", "gems": 50,
     "check": lambda s, bp: bp["totals"].get("kills", 0) >= 5000},
    {"key": "survivor", "name": "Overlever", "desc": "Overleef 5 minuten", "gems": 15,
     "check": lambda s, bp: s.get("time", 0) >= 300},
    {"key": "marathon", "name": "Marathon", "desc": "Overleef 15 minuten", "gems": 50,
     "check": lambda s, bp: s.get("time", 0) >= 900},
    {"key": "boss", "name": "Baasbreker", "desc": "Versla een baas", "gems": 15,
     "check": lambda s, bp: s.get("bosses", 0) >= 1},
    {"key": "elite", "name": "Elite jager", "desc": "Versla 10 elites in totaal", "gems": 15,
     "check": lambda s, bp: bp["totals"].get("elites", 0) >= 10},
    {"key": "level20", "name": "Hoog niveau", "desc": "Haal level 20 in een run", "gems": 20,
     "check": lambda s, bp: s.get("level", 0) >= 20},
    {"key": "extreme", "name": "Masochist", "desc": "Overleef 3 minuten op Extreme", "gems": 30,
     "check": lambda s, bp: s.get("extreme_time", 0) >= 180},
    {"key": "rich", "name": "Rijkaard", "desc": "Heb 5000 coins", "gems": 25,
     "check": lambda s, bp: bp["coins"] >= 5000},
    {"key": "whale", "name": "Walvis", "desc": "Koop het Walvis pakket", "gems": 0,
     "check": lambda s, bp: bp.get("whale", False)},
    {"key": "gambler", "name": "Gokverslaafd", "desc": "Open 10 lootboxen", "gems": 10,
     "check": lambda s, bp: bp.get("boxes_opened", 0) >= 10},
    {"key": "revive", "name": "Betaal om te winnen", "desc": "Koop een extra leven", "gems": 5,
     "check": lambda s, bp: s.get("revived", False)},
    {"key": "streak", "name": "Onstopbaar", "desc": "Kill streak van 50", "gems": 20,
     "check": lambda s, bp: s.get("best_streak", 0) >= 50},
    {"key": "chests", "name": "Schatzoeker", "desc": "Open 5 kisten in een run", "gems": 15,
     "check": lambda s, bp: s.get("chests", 0) >= 5},
    {"key": "arsenal", "name": "Wandelend arsenaal", "desc": "Heb 6 wapens tegelijk", "gems": 25,
     "check": lambda s, bp: s.get("weapons", 0) >= 6},
]

toasts = []


def check(stats, bp):
    """Kijk welke achievements nieuw gehaald zijn en geef de gems."""
    new = []
    for achievement in ACHIEVEMENTS:
        if achievement["key"] in bp["achievements"]:
            continue
        if achievement["check"](stats, bp):
            bp["achievements"].append(achievement["key"])
            bp["gems"] += achievement["gems"]
            toasts.append({"achievement": achievement, "life": 3.5})
            new.append(achievement)
    return new


def unlock_all(bp):
    for achievement in ACHIEVEMENTS:
        if achievement["key"] not in bp["achievements"]:
            bp["achievements"].append(achievement["key"])


def update(dt):
    for toast in toasts:
        toast["life"] -= dt
    toasts[:] = [t for t in toasts if t["life"] > 0]


def draw_toasts(screen):
    # hooguit twee tegelijk laten zien
    for i, toast in enumerate(toasts[:2]):
        achievement = toast["achievement"]
        slide = min(1, (3.5 - toast["life"]) * 4, toast["life"] * 4)
        y = -70 + slide * (90 + i * 74)
        panel(screen, (W / 2 - 180, y, 360, 64), YELLOW)
        text_center(screen, "Achievement: " + achievement["name"], 26, YELLOW, y + 10)
        line = achievement["desc"]
        if achievement["gems"]:
            line += f" (+{achievement['gems']} gems)"
        text_center(screen, line, 22, (230, 230, 230), y + 38)


def handle_input(state, events):
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_a):
            state["screen"] = "menu"


def draw_screen(screen, state):
    bp = state["bp"]
    draw_background(screen, state, 190)
    done = len(bp["achievements"])
    text_center(screen, "Achievements", 64, YELLOW, 20)
    text_center(screen, f"{done} / {len(ACHIEVEMENTS)} gehaald", 26, GREY, 74)
    for i, achievement in enumerate(ACHIEVEMENTS):
        x = 60 + (i % 2) * 430
        y = 104 + (i // 2) * 56
        unlocked = achievement["key"] in bp["achievements"]
        panel(screen, (x, y, 410, 50), YELLOW if unlocked else (70, 70, 90))
        color = (255, 255, 255) if unlocked else (130, 130, 140)
        screen.blit(sprites.font(26).render(achievement["name"], True, color), (x + 12, y + 6))
        screen.blit(sprites.font(20).render(achievement["desc"], True, GREY if unlocked else (110, 110, 120)), (x + 12, y + 28))
        if achievement["gems"]:
            gems = sprites.font(22).render(f"{achievement['gems']}", True, (230, 120, 230))
            screen.blit(gems, (x + 380 - gems.get_width(), y + 16))
            screen.blit(sprites.scaled(sprites.get("gem_premium"), 0.6), (x + 384, y + 16))
    text_center(screen, "Esc: terug", 24, GREY, 560)


SCREENS = {
    "achievements": (handle_input, draw_screen),
}

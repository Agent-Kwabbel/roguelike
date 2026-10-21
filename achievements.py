import pygame

import progress
import sound
import sprites
import ui
from settings import W

# check gets the stats of the run and the save, coins is the reward
ACHIEVEMENTS = [
    {"key": "first_blood", "name": "First blood", "desc": "Defeat an enemy", "coins": 50,
     "check": lambda s, bp: s.get("kills", 0) >= 1},
    {"key": "butcher", "name": "Butcher", "desc": "500 kills in one run", "coins": 200,
     "check": lambda s, bp: s.get("kills", 0) >= 500},
    {"key": "genocide", "name": "That's a lot", "desc": "5000 kills in total", "coins": 500,
     "check": lambda s, bp: bp["totals"].get("kills", 0) >= 5000},
    {"key": "survivor", "name": "Survivor", "desc": "Survive 5 minutes", "coins": 150,
     "check": lambda s, bp: s.get("time", 0) >= 300},
    {"key": "marathon", "name": "Marathon", "desc": "Survive 15 minutes", "coins": 500,
     "check": lambda s, bp: s.get("time", 0) >= 900},
    {"key": "boss", "name": "Boss breaker", "desc": "Defeat a boss", "coins": 150,
     "check": lambda s, bp: s.get("bosses", 0) >= 1},
    {"key": "elite", "name": "Elite hunter", "desc": "Defeat 10 elites in total", "coins": 150,
     "check": lambda s, bp: bp["totals"].get("elites", 0) >= 10},
    {"key": "level20", "name": "High level", "desc": "Reach level 20 in a run", "coins": 200,
     "check": lambda s, bp: s.get("level", 0) >= 20},
    {"key": "extreme", "name": "Masochist", "desc": "Survive 3 minutes on Extreme", "coins": 300,
     "check": lambda s, bp: s.get("extreme_time", 0) >= 180},
    {"key": "rich", "name": "Moneybags", "desc": "Have 5000 coins", "coins": 250,
     "check": lambda s, bp: bp["coins"] >= 5000},
    {"key": "streak", "name": "Unstoppable", "desc": "Kill streak of 50", "coins": 200,
     "check": lambda s, bp: s.get("best_streak", 0) >= 50},
    {"key": "chests", "name": "Treasure hunter", "desc": "Open 5 chests in one run", "coins": 150,
     "check": lambda s, bp: s.get("chests", 0) >= 5},
    {"key": "arsenal", "name": "Walking arsenal", "desc": "Have 6 weapons at once", "coins": 250,
     "check": lambda s, bp: s.get("weapons", 0) >= 6},
    {"key": "cursed", "name": "Cursed", "desc": "Reach the cursed lands", "coins": 200,
     "check": lambda s, bp: s.get("phase", 0) >= 3},
    {"key": "abyss", "name": "Into the abyss", "desc": "Reach the abyss", "coins": 400,
     "check": lambda s, bp: s.get("phase", 0) >= 4},
    {"key": "evolve", "name": "Evolution", "desc": "Evolve a weapon", "coins": 250,
     "check": lambda s, bp: s.get("evolved", 0) >= 1},
    {"key": "bone_lord", "name": "Bone breaker", "desc": "Defeat the Bone Lord", "coins": 250,
     "check": lambda s, bp: s.get("beat_bone_lord", 0) >= 1},
    {"key": "golem_king", "name": "Kingslayer", "desc": "Defeat the Golem King", "coins": 300,
     "check": lambda s, bp: s.get("beat_golem_king", 0) >= 1},
    {"key": "reaper", "name": "Meet the reaper", "desc": "Survive 30 minutes", "coins": 1000,
     "check": lambda s, bp: s.get("won", 0) >= 1},
    {"key": "together", "name": "Better together", "desc": "Reach Dusk in an online game", "coins": 300,
     "check": lambda s, bp: s.get("online", 0) and s.get("phase", 0) >= 2},
    {"key": "medic", "name": "Medic!", "desc": "Revive 10 teammates in total", "coins": 400,
     "check": lambda s, bp: bp["totals"].get("revives", 0) >= 10},
    {"key": "squad", "name": "Squad goals", "desc": "Finish 3 team events in one run", "coins": 400,
     "check": lambda s, bp: s.get("coop_events", 0) >= 3},
    {"key": "ride_or_die", "name": "Ride or die", "desc": "Survive 30 minutes online", "coins": 1500,
     "check": lambda s, bp: s.get("online", 0) and s.get("won", 0)},
    {"key": "reaper_extreme", "name": "Death defier", "desc": "Survive 30 minutes on Extreme or Nightmare",
     "coins": 2500, "check": lambda s, bp: s.get("won_extreme", 0) or s.get("won_nightmare", 0)},
]

COLUMNS = 2
ROWS = 5
TOP = 128

toasts = []


def find(key):
    for achievement in ACHIEVEMENTS:
        if achievement["key"] == key:
            return achievement
    return None


def check(stats, bp):
    """See which achievements were just reached and give the reward."""
    new = []
    for achievement in ACHIEVEMENTS:
        if achievement["key"] in bp["achievements"]:
            continue
        if achievement["check"](stats, bp):
            bp["achievements"].append(achievement["key"])
            bp["coins"] += achievement["coins"]
            for item in progress.achievement_items(achievement["key"]):
                progress.give(bp, item)
            toasts.append({"achievement": achievement, "life": 3.5})
            sound.play("achievement")
            new.append(achievement)
    return new


def update(dt):
    for toast in toasts:
        toast["life"] -= dt
    toasts[:] = [t for t in toasts if t["life"] > 0]


def draw_toasts(screen):
    # at most two at the same time
    for i, toast in enumerate(toasts[:2]):
        achievement = toast["achievement"]
        slide = min(1, (3.5 - toast["life"]) * 4, toast["life"] * 4)
        y = -80 + slide * (96 + i * 80)
        rect = pygame.Rect(W / 2 - 200, y, 400, 68)
        ui.glow(screen, rect, ui.YELLOW, alpha=35)
        ui.card(screen, rect, ui.YELLOW, (26, 24, 40, 240))
        pygame.draw.circle(screen, ui.tint(ui.YELLOW, 0.4, 255)[:3], (rect.x + 36, rect.centery), 20)
        ui.check_mark(screen, (rect.x + 36, rect.centery), ui.YELLOW, 9)
        ui.text(screen, "ACHIEVEMENT UNLOCKED", 18, ui.YELLOW, (rect.x + 68, rect.y + 10))
        ui.text(screen, achievement["name"], 30, ui.WHITE, (rect.x + 68, rect.y + 30))
        ui.text(screen, f"+{achievement['coins']}", 26, ui.COIN, (rect.right - 44, rect.y + 24), "right")
        screen.blit(sprites.scaled(sprites.get("coin"), 0.8), (rect.right - 38, rect.y + 23))


def first_row(selected):
    last_row = (len(ACHIEVEMENTS) - 1) // COLUMNS
    row = selected // COLUMNS
    return min(max(0, row - ROWS + 2), max(0, last_row - ROWS + 1))


def visible_rects(selected):
    """(index, rect) for the cards that fit on screen right now."""
    start = first_row(selected)
    result = []
    for i in range(len(ACHIEVEMENTS)):
        row = i // COLUMNS - start
        if 0 <= row < ROWS:
            rect = pygame.Rect(50 + (i % COLUMNS) * 440, TOP + row * 88, 420, 78)
            result.append((i, rect))
    return result


def handle_input(state, events):
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            state["screen"] = "menu"
            return
    if ui.back_clicked(events):
        state["screen"] = "menu"
        return

    selected = state["achievement_selected"]
    cards = visible_rects(selected)
    count = len(ACHIEVEMENTS)
    for event in events:
        if event.type == pygame.MOUSEMOTION:
            for i, rect in cards:
                if rect.collidepoint(event.pos):
                    selected = i
        elif event.type == pygame.MOUSEWHEEL:
            selected = max(0, min(count - 1, selected - event.y * COLUMNS))
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                selected = max(0, selected - COLUMNS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                selected = min(count - 1, selected + COLUMNS)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                selected = max(0, selected - 1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                selected = min(count - 1, selected + 1)
    state["achievement_selected"] = selected


def draw_card(screen, achievement, rect, unlocked, active):
    if unlocked:
        border = ui.YELLOW
        fill = ui.tint(ui.YELLOW, 0.14)
    else:
        border = ui.BORDER
        fill = (20, 18, 30, 215)
    if active:
        ui.glow(screen, rect, border if unlocked else ui.GREY, alpha=35)
        border = ui.WHITE if not unlocked else border
    ui.card(screen, rect, border, fill)

    center = (rect.x + 38, rect.centery)
    if unlocked:
        pygame.draw.circle(screen, ui.tint(ui.YELLOW, 0.45, 255)[:3], center, 22)
        ui.check_mark(screen, center, ui.YELLOW, 10)
        name_color, desc_color = ui.WHITE, ui.GREY
    else:
        pygame.draw.circle(screen, (40, 38, 56), center, 22)
        ui.lock(screen, (center[0], center[1] + 2), ui.DIM)
        name_color, desc_color = (150, 150, 162), ui.DIM

    ui.text(screen, achievement["name"], 28, name_color, (rect.x + 72, rect.y + 14))
    ui.text(screen, achievement["desc"], 22, desc_color, (rect.x + 72, rect.y + 42))

    coin = sprites.scaled(sprites.get("coin"), 0.7)
    screen.blit(coin, (rect.right - 14 - coin.get_width(), rect.y + 14))
    ui.text(screen, achievement["coins"], 24, ui.COIN, (rect.right - 20 - coin.get_width(), rect.y + 14), "right")
    items = progress.achievement_items(achievement["key"])
    if items:
        ui.badge(screen, items[0]["name"], (rect.right - 12, rect.y + 44), ui.PURPLE,
                 "right", 18)


def draw_screen(screen, state):
    bp = state["bp"]
    ui.draw_background(screen, state, 190)
    done = len([a for a in ACHIEVEMENTS if a["key"] in bp["achievements"]])
    ui.title(screen, "Achievements", 60, ui.WHITE, 22)
    ui.text(screen, f"{done} / {len(ACHIEVEMENTS)} unlocked", 24, ui.GREY, (W / 2 - 150, 82))
    ui.progress_bar(screen, (W / 2 - 150, 104, 300, 10), done / len(ACHIEVEMENTS), ui.YELLOW)
    ui.text(screen, "Purple tags are shop items you unlock", 20, ui.DIM, (W - 50, 98), "right")

    selected = state["achievement_selected"]
    for i, rect in visible_rects(selected):
        achievement = ACHIEVEMENTS[i]
        draw_card(screen, achievement, rect, achievement["key"] in bp["achievements"], i == selected)

    rows = (len(ACHIEVEMENTS) + COLUMNS - 1) // COLUMNS
    ui.scrollbar(screen, (W - 26, TOP, 8, ROWS * 88 - 10), first_row(selected), ROWS, rows)
    ui.back_button(screen)
    ui.footer(screen, [("WASD", "Browse"), ("Wheel", "Scroll"), ("Esc", "Back")])


SCREENS = {
    "achievements": (handle_input, draw_screen),
}

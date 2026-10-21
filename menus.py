import math

import pygame

import achievements
import config
import progress
import saves
import settings_menu
import sound
import sprites
import ui
from settings import W, H, DIFFICULTIES

DIFFICULTY_KEYS = list(DIFFICULTIES.keys())
YELLOW = ui.YELLOW
GREY = ui.GREY
PANEL = (30, 28, 45, 220)

PERK_ICONS = {
    "start_hp": "heart",
    "start_damage": "icon_damage",
    "pickup": "magnet",
    "speed": "icon_speed",
    "crit": "icon_crit",
    "regen": "icon_regen",
    "luck": "icon_luck",
    "knives": "knife",
}


def init_menu(bp, world, last_run=None):
    return {
        "running": True,
        "screen": "menu",
        "selected": 1,
        "last_run": last_run,
        "bp": bp,
        "shop_tab": 0,
        "shop_selected": 0,
        "shop_scroll": 0,
        "achievement_selected": 0,
        "message": "",
        "world": world,
        "menu_time": 0,
        "start": None,
        "start_online": None,
        "menu_page": "main",
        "menu_selected": 0,
        "confirm_selected": 1,
        "results_selected": 0,
        "run_info": saves.current_run_summary(),
        "continue": False,
        "slot_selected": saves.slot - 1,
        "slot_confirm": None,
    }


# ---------- drawing helpers ----------

def text_center(screen, text, size, color, y, x=W / 2):
    font = sprites.font(size)
    shadow = font.render(text, True, (0, 0, 0))
    image = font.render(text, True, color)
    screen.blit(shadow, (x - image.get_width() / 2 + 2, y + 2))
    screen.blit(image, (x - image.get_width() / 2, y))


def wrap_text(text, size, max_width):
    font = sprites.font(size)
    lines = []
    line = ""
    for word in text.split():
        test = (line + " " + word).strip()
        if font.size(test)[0] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    return lines


def panel(screen, rect, border=(90, 90, 120), width=2):
    surface = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(surface, PANEL, (0, 0, rect[2], rect[3]), border_radius=10)
    screen.blit(surface, (rect[0], rect[1]))
    pygame.draw.rect(screen, border, rect, width, border_radius=10)


def draw_coins(screen, amount, y=18):
    """Coin counter in a little pill at the top right."""
    image = sprites.font(32).render(str(amount), True, ui.COIN)
    coin = sprites.get("coin")
    width = image.get_width() + coin.get_width() + 30
    rect = pygame.Rect(W - width - 16, y, width, 38)
    ui.card(screen, rect, ui.tint(ui.COIN, 0.5, 255)[:3], radius=19)
    screen.blit(coin, (rect.x + 10, rect.centery - coin.get_height() / 2))
    screen.blit(image, (rect.right - image.get_width() - 12, rect.y + 9))


def reward_icon(reward, time=0):
    if reward["type"] == "skin":
        return sprites.frame(reward["sprite"], time, 3)
    if reward["type"] == "bullet":
        return sprites.scaled(sprites.get(reward["sprite"]), 2)
    return sprites.scaled(sprites.get(PERK_ICONS.get(reward["effect"], "icon_luck")), 1.5)


def format_time(seconds):
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


# ---------- main menu ----------

DIFFICULTY_COLORS = {"easy": (120, 220, 130), "normal": (120, 190, 250), "hard": (250, 170, 70),
                     "extreme": (240, 80, 90), "nightmare": (190, 90, 240)}
MENU_HOTKEYS = {pygame.K_k: "shop", pygame.K_a: "achievements"}


def open_screen(state, name):
    state["screen"] = name
    state["message"] = ""


def menu_buttons(state):
    """List of (action, label, small text, height)."""
    buttons = []
    run = state["run_info"]
    if run:
        sub = f"{DIFFICULTIES[run['difficulty']]['name']} - {format_time(run['time'])}, level {run['level']}"
        buttons.append(("continue", "Continue", sub, 56))
    buttons.append(("new", "New run", None, 44))
    buttons.append(("multiplayer", "Multiplayer", None, 40))
    buttons.append(("shop", "Shop", None, 40))
    buttons.append(("achievements", "Achievements", None, 40))
    buttons.append(("settings", "Settings", None, 40))
    buttons.append(("slots", "Switch save", None, 40))
    buttons.append(("quit", "Quit", None, 40))
    return buttons


def menu_rects(state):
    rects = []
    y = 160
    for button in menu_buttons(state):
        rects.append(pygame.Rect(40, y, 320, button[3]))
        y += button[3] + 6
    return rects


def difficulty_rects():
    rects = []
    for i in range(len(DIFFICULTY_KEYS)):
        rects.append(pygame.Rect(36 + i * 180, 150, 168, 350))
    rects.append(pygame.Rect(W / 2 - 100, 528, 200, 44))
    return rects


def menu_action(state, action):
    if action == "continue":
        state["continue"] = True
    elif action == "new":
        if state["run_info"]:
            state["menu_page"] = "confirm_new"
            state["confirm_selected"] = 1
        else:
            state["menu_page"] = "difficulty"
    elif action == "settings":
        state["screen"] = "settings"
    elif action == "slots":
        state["screen"] = "slots"
        state["slot_selected"] = saves.slot - 1
    elif action == "quit":
        state["menu_page"] = "confirm_quit"
        state["confirm_selected"] = 1
    else:
        open_screen(state, action)


def handle_menu_input(state, events):
    page = state["menu_page"]
    if page in ("confirm_new", "confirm_quit"):
        state["confirm_selected"], answer = ui.handle_confirm(events, state["confirm_selected"])
        if answer is None:
            return
        if answer and page == "confirm_quit":
            state["running"] = False
        elif answer:
            state["menu_page"] = "difficulty"
        else:
            state["menu_page"] = "main"
        return

    if page == "difficulty":
        handle_difficulty_input(state, events)
        return

    buttons = menu_buttons(state)
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            menu_action(state, "quit")
            return
        if event.key in MENU_HOTKEYS:
            open_screen(state, MENU_HOTKEYS[event.key])
            return
    state["menu_selected"] = min(state["menu_selected"], len(buttons) - 1)
    state["menu_selected"], chosen = ui.navigate(events, state["menu_selected"], menu_rects(state))
    if chosen is not None:
        menu_action(state, buttons[chosen][0])


def draw_menu(screen, state):
    ui.draw_background(screen, state, 110)
    if state["menu_page"] == "difficulty":
        draw_difficulty(screen, state)
        return
    t = state["menu_time"]

    # dark strip on the left behind the buttons
    strip = pygame.Surface((400, H), pygame.SRCALPHA)
    strip.fill((8, 6, 18, 170))
    screen.blit(strip, (0, 0))
    pygame.draw.line(screen, (60, 58, 85), (400, 0), (400, H))

    ui.title(screen, "roguelike", 96, ui.WHITE, 46 + math.sin(t * 2) * 4, 200)
    ui.badge(screen, f"Save {saves.slot}", (200, 118), GREY, "center", 20)

    rects = menu_rects(state)
    for i, (action, label, sub, _) in enumerate(menu_buttons(state)):
        accent = YELLOW
        if action == "continue":
            accent = ui.GREEN
        elif action == "quit":
            accent = ui.RED
        size = 32 if action in ("continue", "new") else 28
        ui.button(screen, rects[i], label, i == state["menu_selected"], accent, sub, size)

    draw_coins(screen, state["bp"]["coins"])
    draw_hero_card(screen, state)
    draw_stats_card(screen, state)
    if state["last_run"]:
        draw_last_run_card(screen, state["last_run"])
    else:
        draw_controls_card(screen)

    ui.footer(screen, [("W/S", "Move"), ("Enter", "Select"), ("K", "Shop"), ("A", "Achievements"),
                       ("F11", "Fullscreen")])

    if state["menu_page"] == "confirm_new":
        ui.draw_confirm(screen, "Start a new run?", "Your saved run will be lost", state["confirm_selected"])
    elif state["menu_page"] == "confirm_quit":
        ui.draw_confirm(screen, "Quit the game?", None, state["confirm_selected"])


def draw_hero_card(screen, state):
    bp = state["bp"]
    t = state["menu_time"]
    rect = pygame.Rect(440, 70, 490, 180)
    ui.card(screen, rect, ui.BORDER, shadow=True)
    center = (rect.x + 110, rect.centery + math.sin(t * 3) * 5)
    sprites.draw_glow(screen, 70, (60, 50, 110), center)
    screen.blit(sprites.shadow(60), (center[0] - 30, rect.centery + 42))
    hero = sprites.scaled(sprites.frame(progress.skin_sprite(bp), t, 4), 3)
    sprites.draw_centered(screen, hero, center)

    x = rect.x + 220
    ui.text(screen, "YOUR HERO", 20, ui.DIM, (x, rect.y + 22))
    ui.text(screen, bp["skin"] or "Blue hero", 38, ui.WHITE, (x, rect.y + 44))
    ui.text(screen, "Bullets", 20, ui.DIM, (x, rect.y + 92))
    bullet = sprites.get(progress.bullet_sprite(bp))
    sprites.draw_centered(screen, sprites.scaled(bullet, 1.5), (x + 12, rect.y + 126))
    ui.text(screen, bp["bullet"] or "Standard bullets", 26, ui.GREY, (x + 30, rect.y + 116))
    ui.text(screen, "Change your look in the shop", 20, ui.DIM, (x, rect.bottom - 30))


def draw_stats_card(screen, state):
    bp = state["bp"]
    totals = bp["totals"]
    rect = pygame.Rect(440, 264, 490, 96)
    ui.card(screen, rect, ui.BORDER)
    columns = [("Runs", totals.get("runs", 0)), ("Kills", totals.get("kills", 0)),
               ("Elites", totals.get("elites", 0))]
    for i, (label, value) in enumerate(columns):
        x = rect.x + 24 + i * 100
        ui.text(screen, label.upper(), 18, ui.DIM, (x, rect.y + 16))
        ui.text(screen, value, 36, YELLOW, (x, rect.y + 36))
    done = len(bp["achievements"])
    total = len(achievements.ACHIEVEMENTS)
    x = rect.x + 330
    ui.text(screen, "ACHIEVEMENTS", 18, ui.DIM, (x, rect.y + 16))
    ui.text(screen, f"{done} / {total}", 30, ui.WHITE, (x, rect.y + 36))
    ui.progress_bar(screen, (x, rect.y + 66, 136, 10), done / total, YELLOW)


def draw_last_run_card(screen, last_run):
    rect = pygame.Rect(440, 374, 490, 170)
    ui.card(screen, rect, ui.BORDER)
    color = DIFFICULTY_COLORS.get(last_run["difficulty_key"], YELLOW)
    pygame.draw.rect(screen, color, (rect.x, rect.y + 14, 4, rect.h - 28), border_radius=2)
    ui.text(screen, "LAST RUN", 20, ui.DIM, (rect.x + 24, rect.y + 16))
    ui.badge(screen, last_run["difficulty"], (rect.right - 20, rect.y + 14), color, "right")
    stats = [("Time", format_time(last_run["time"])), ("Level", last_run["level"]),
             ("Kills", last_run["kills"]), ("Coins", f"+{last_run['coins']}")]
    for i, (label, value) in enumerate(stats):
        x = rect.x + 24 + i * 116
        ui.text(screen, label, 20, ui.GREY, (x, rect.y + 48))
        ui.text(screen, value, 34, ui.COIN if label == "Coins" else ui.WHITE, (x, rect.y + 68))
    y = rect.y + 112
    for name in last_run["achievements"][:2]:
        ui.check_mark(screen, (rect.x + 34, y + 9), ui.GREEN, 6)
        ui.text(screen, name, 22, ui.GREEN, (rect.x + 50, y + 1))
        y += 24


def draw_controls_card(screen):
    rect = pygame.Rect(440, 374, 490, 170)
    ui.card(screen, rect, ui.BORDER)
    ui.text(screen, "HOW TO PLAY", 20, ui.DIM, (rect.x + 24, rect.y + 16))
    rows = [("WASD", "Move around, you shoot automatically"),
            ("Space", "Dash (once you have the upgrade)"),
            ("1 2 3", "Pick an upgrade, or click it"),
            ("Esc", "Pause the game")]
    for i, (key, label) in enumerate(rows):
        y = rect.y + 46 + i * 29
        ui.keycap(screen, key, (rect.x + 24, y))
        ui.text(screen, label, 22, ui.GREY, (rect.x + 96, y + 3))


# ---------- choose difficulty ----------

def handle_difficulty_input(state, events):
    number_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
    count = len(DIFFICULTY_KEYS) + 1
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            state["menu_page"] = "main"
            return
        if event.key in number_keys and number_keys.index(event.key) < len(DIFFICULTY_KEYS):
            state["start"] = DIFFICULTY_KEYS[number_keys.index(event.key)]
            return
        if event.key in (pygame.K_LEFT, pygame.K_a):
            state["selected"] = (state["selected"] - 1) % count
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            state["selected"] = (state["selected"] + 1) % count
        if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            sound.play("menu_move")
    if ui.back_clicked(events):
        state["menu_page"] = "main"
        return
    state["selected"], chosen = ui.navigate(events, state["selected"], difficulty_rects())
    if chosen == len(DIFFICULTY_KEYS):
        state["menu_page"] = "main"
    elif chosen is not None:
        state["start"] = DIFFICULTY_KEYS[chosen]


def draw_difficulty(screen, state):
    ui.darken(screen, 110)
    ui.title(screen, "Choose difficulty", 64, ui.WHITE, 56)
    text_center(screen, "Harder means more enemies, more HP and fewer lives", 24, GREY, 112)
    rects = difficulty_rects()
    heart = sprites.scaled(sprites.get("heart"), 0.6)
    for i, key in enumerate(DIFFICULTY_KEYS):
        info = DIFFICULTIES[key]
        color = DIFFICULTY_COLORS.get(key, YELLOW)
        rect = rects[i].copy()
        active = i == state["selected"]
        if active:
            rect.y -= 8
            ui.glow(screen, rect, color, spread=8)
            ui.card(screen, rect, color, ui.tint(color, 0.22), shadow=True)
        else:
            ui.card(screen, rect, ui.BORDER, shadow=True)
        pygame.draw.rect(screen, color, (rect.x, rect.y, rect.w, 8),
                         border_top_left_radius=12, border_top_right_radius=12)
        ui.keycap(screen, str(i + 1), (rect.x + 12, rect.y + 20))
        ui.text(screen, info["name"], 34, color if active else ui.WHITE, (rect.centerx, rect.y + 58), "center")

        y = rect.y + 110
        ui.text(screen, "Lives", 20, ui.DIM, (rect.x + 14, y))
        for h in range(info["player_hp"]):
            screen.blit(heart, (rect.x + 14 + h * (heart.get_width() + 2), y + 20))
        rows = [("Enemy HP", f"x{info['enemy_hp']}"),
                ("Enemy speed", f"x{info['enemy_speed']}"),
                ("Spawn rate", f"x{1 / info['spawn']:.1f}"),
                ("Damage taken", str(info["enemy_damage"]))]
        y += 58
        for label, value in rows:
            ui.text(screen, label, 20, ui.DIM, (rect.x + 14, y))
            ui.text(screen, value, 24, ui.WHITE, (rect.right - 14, y - 2), "right")
            y += 30
        if active:
            ui.center_button(screen, (rect.x + 14, rect.bottom - 52, rect.w - 28, 38), "Play", True, color, 26)

    ui.center_button(screen, rects[-1], "Back", state["selected"] == len(DIFFICULTY_KEYS), GREY)
    ui.back_button(screen)
    ui.footer(screen, [("A/D", "Choose"), ("Enter", "Play"), ("1-5", "Quick start"), ("Esc", "Back")])


# ---------- choose a save ----------

def init_slots(world):
    return {
        "running": True,
        "screen": "slots",
        "bp": None,
        "world": world,
        "menu_time": 0,
        "start": None,
        "continue": False,
        "slot_selected": 0,
        "slot_confirm": None,
        "confirm_selected": 1,
    }


def slot_rects():
    cards = []
    deletes = []
    for i in range(saves.SLOTS):
        x = 75 + i * 280
        cards.append(pygame.Rect(x, 150, 250, 310))
        deletes.append(pygame.Rect(x + 40, 480, 170, 40))
    return cards, deletes


def pick_slot(state, n):
    saves.slot = n
    config.set("last_slot", n)
    bp = progress.load()
    progress.save(bp)
    state.update(init_menu(bp, state["world"]))


def handle_slots_input(state, events):
    if state["slot_confirm"] is not None:
        state["confirm_selected"], answer = ui.handle_confirm(events, state["confirm_selected"])
        if answer:
            n = state["slot_confirm"]
            saves.delete_slot(n)
            # the save you were in is gone, so pick a new one first
            if state["bp"] is not None and n == saves.slot:
                state["bp"] = None
                config.set("last_slot", None)
        if answer is not None:
            state["slot_confirm"] = None
        return

    cards, deletes = slot_rects()
    if ui.back_clicked(events) and state["bp"] is not None:
        state["screen"] = "menu"
        return
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            if state["bp"] is not None:
                state["screen"] = "menu"
            else:
                state["running"] = False
            return
        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE, pygame.K_x) and saves.slot_info(state["slot_selected"] + 1):
            state["slot_confirm"] = state["slot_selected"] + 1
            state["confirm_selected"] = 1
            return

    delete = ui.clicked(events, deletes)
    if delete is not None and saves.slot_info(delete + 1):
        state["slot_confirm"] = delete + 1
        state["confirm_selected"] = 1
        return
    state["slot_selected"], chosen = ui.navigate(events, state["slot_selected"], cards, columns=saves.SLOTS)
    if chosen is not None:
        pick_slot(state, chosen + 1)


def draw_slots(screen, state):
    ui.draw_background(screen, state, 170)
    ui.title(screen, "Choose a save", 64, ui.WHITE, 50)
    text_center(screen, "Every save has its own coins, unlocks and run", 24, GREY, 104)
    cards, deletes = slot_rects()
    coin = sprites.get("coin")
    for i in range(saves.SLOTS):
        info = saves.slot_info(i + 1)
        rect = cards[i].copy()
        active = i == state["slot_selected"]
        if active:
            rect.y -= 6
            ui.glow(screen, rect, YELLOW)
            ui.card(screen, rect, YELLOW, ui.tint(YELLOW, 0.18), shadow=True)
        else:
            ui.card(screen, rect, ui.BORDER, shadow=True)
        ui.text(screen, f"Save {i + 1}", 44, YELLOW if active else ui.WHITE, (rect.centerx, rect.y + 22), "center")
        if state["bp"] is not None and i + 1 == saves.slot:
            ui.badge(screen, "Current", (rect.centerx, rect.y + 62), ui.GREEN, "center")

        if info is None:
            pygame.draw.circle(screen, ui.BORDER, (rect.centerx, rect.centery + 4), 34, 3)
            pygame.draw.line(screen, GREY, (rect.centerx - 14, rect.centery + 4), (rect.centerx + 14, rect.centery + 4), 4)
            pygame.draw.line(screen, GREY, (rect.centerx, rect.centery - 10), (rect.centerx, rect.centery + 18), 4)
            ui.text(screen, "New game", 28, GREY, (rect.centerx, rect.centery + 54), "center")
            continue

        y = rect.y + 102
        screen.blit(coin, (rect.x + 24, y - 2))
        ui.text(screen, info["coins"], 30, ui.COIN, (rect.x + 30 + coin.get_width(), y))
        lines = [("Runs played", info["runs"]), ("Achievements", info["achievements"]),
                 ("Last played", info["last_played"])]
        y += 42
        for label, value in lines:
            ui.text(screen, label, 20, ui.DIM, (rect.x + 24, y))
            ui.text(screen, value, 22, ui.WHITE, (rect.right - 24, y), "right")
            y += 28
        if info["run"]:
            run = info["run"]
            label = f"Run: {format_time(run['time'])}, lvl {run['level']}"
            ui.badge(screen, label, (rect.centerx, rect.bottom - 40), ui.GREEN, "center", 20)
        hover = deletes[i].collidepoint(pygame.mouse.get_pos())
        ui.center_button(screen, deletes[i], "Delete", hover, ui.RED, 24)

    if state["bp"] is not None:
        ui.back_button(screen)
    hints = [("A/D", "Choose"), ("Enter", "Play"), ("Del", "Delete")]
    hints.append(("Esc", "Back" if state["bp"] is not None else "Quit"))
    ui.footer(screen, hints)
    if state["slot_confirm"] is not None:
        ui.draw_confirm(screen, f"Delete save {state['slot_confirm']}?", "This can't be undone",
                        state["confirm_selected"])


# ---------- settings ----------

def handle_settings_input(state, events):
    if settings_menu.handle(events):
        state["screen"] = "menu"


def draw_settings(screen, state):
    ui.draw_background(screen, state, 170)
    settings_menu.draw(screen)


# ---------- after a run ----------

def results_rects():
    return [pygame.Rect(W / 2 - 230, 486, 220, 52), pygame.Rect(W / 2 + 10, 486, 220, 52)]


def handle_results_input(state, events):
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            state["screen"] = "menu"
            return
        if event.key == pygame.K_r:
            state["start"] = state["last_run"]["difficulty_key"]
            return
        if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            state["results_selected"] = 1 - state["results_selected"]
            sound.play("menu_move")
    state["results_selected"], chosen = ui.navigate(events, state["results_selected"], results_rects())
    if chosen == 0:
        state["start"] = state["last_run"]["difficulty_key"]
    elif chosen == 1:
        state["screen"] = "menu"


def draw_results(screen, state):
    ui.draw_background(screen, state, 170)
    run = state["last_run"]
    t = state["menu_time"]
    if run["died"]:
        ui.title(screen, "GAME OVER", 88, ui.RED, 40 + math.sin(t * 2) * 3)
    else:
        ui.title(screen, "RUN ENDED", 88, YELLOW, 40 + math.sin(t * 2) * 3)
    color = DIFFICULTY_COLORS.get(run["difficulty_key"], YELLOW)
    ui.badge(screen, run["difficulty"], (W / 2, 120), color, "center", 22)
    if run.get("note"):
        ui.text(screen, run["note"], 20, ui.RED, (W / 2, 147), "center", True)

    rect = pygame.Rect(W / 2 - 300, 160, 600, 300)
    ui.card(screen, rect, ui.BORDER, shadow=True)
    stats = [("Survived", format_time(run["time"]), ui.WHITE), ("Level", run["level"], ui.WHITE),
             ("Kills", run["kills"], ui.WHITE), ("Coins earned", f"+{run['coins']}", ui.COIN)]
    for i, (label, value, value_color) in enumerate(stats):
        x = rect.x + 75 + i * 150
        ui.text(screen, label.upper(), 18, ui.DIM, (x, rect.y + 26), "center")
        ui.text(screen, value, 48, value_color, (x, rect.y + 50), "center")
    pygame.draw.line(screen, ui.BORDER, (rect.x + 30, rect.y + 116), (rect.right - 30, rect.y + 116))

    ui.text(screen, "NEW ACHIEVEMENTS", 18, ui.DIM, (rect.x + 30, rect.y + 134))
    if not run["achievements"]:
        ui.text(screen, "None this time", 24, ui.GREY, (rect.x + 30, rect.y + 160))
    for i, name in enumerate(run["achievements"][:4]):
        y = rect.y + 160 + i * 30
        ui.check_mark(screen, (rect.x + 40, y + 9), ui.GREEN, 7)
        ui.text(screen, name, 26, ui.GREEN, (rect.x + 58, y))
    ui.text(screen, f"Total coins: {state['bp']['coins']}", 22, ui.GREY, (rect.right - 30, rect.bottom - 34), "right")

    play, menu = results_rects()
    ui.center_button(screen, play, "Play again", state["results_selected"] == 0, ui.GREEN)
    ui.center_button(screen, menu, "Main menu", state["results_selected"] == 1, GREY)
    ui.footer(screen, [("A/D", "Choose"), ("Enter", "Select"), ("R", "Play again"), ("Esc", "Main menu")])


SCREENS = {
    "menu": (handle_menu_input, draw_menu),
    "slots": (handle_slots_input, draw_slots),
    "settings": (handle_settings_input, draw_settings),
    "results": (handle_results_input, draw_results),
}

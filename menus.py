import math
import random

import pygame

import battlepass
import challenges
import config
import saves
import settings_menu
import sprites
import ui
from settings import W, H, DIFFICULTIES, BP_TIERS, BP_XP_PER_TIER, PREMIUM_COST

DIFFICULTY_KEYS = list(DIFFICULTIES.keys())
YELLOW = (250, 220, 60)
GREY = (180, 180, 190)
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
    challenges.refresh(bp)
    return {
        "running": True,
        "screen": "menu",
        "selected": 1,
        "last_run": last_run,
        "bp": bp,
        "bp_selected": 0,
        "bp_row": 0,
        "shop_selected": 0,
        "message": "",
        "world": world,
        "menu_time": 0,
        "start": None,
        "gem_selected": 0,
        "gem_pay": None,
        "gem_ad": None,
        "gem_box": None,
        # na een run soms een "aanbieding" laten zien
        "popup": last_run is not None and random.random() < 0.35,
        "menu_page": "main",
        "menu_selected": 0,
        "confirm_selected": 1,
        "run_info": saves.current_run_summary(),
        "continue": False,
        "slot_selected": saves.slot - 1,
        "slot_confirm": None,
    }


# ---------- tekenhulpjes ----------

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


def draw_background(screen, state, darkness=150):
    t = state["menu_time"]
    camera = pygame.Vector2(t * 30, t * 12)
    state["world"].draw(screen, camera)
    state["world"].draw_roofs(screen, camera)
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, darkness))
    screen.blit(overlay, (0, 0))


def draw_coins(screen, amount):
    text = sprites.font(36).render(str(amount), True, (240, 200, 60))
    x = W - text.get_width() - 20
    screen.blit(text, (x, 26))
    coin = sprites.get("coin")
    screen.blit(coin, (x - coin.get_width() - 8, 22))


def draw_gems(screen, amount):
    text = sprites.font(36).render(str(amount), True, (230, 120, 230))
    x = W - text.get_width() - 20
    screen.blit(text, (x, 62))
    gem = sprites.get("gem_premium")
    screen.blit(gem, (x - gem.get_width() - 8, 60))


def reward_icon(reward, time=0):
    if reward["type"] == "skin":
        return sprites.frame(reward["sprite"], time, 3)
    if reward["type"] == "bullet":
        return sprites.scaled(sprites.get(reward["sprite"]), 2)
    if reward["type"] == "coins":
        return sprites.scaled(sprites.get("coin"), 1.5)
    if reward["type"] == "tier_skip":
        return sprites.scaled(sprites.get("icon_fire_rate"), 1.5)
    return sprites.scaled(sprites.get(PERK_ICONS.get(reward["effect"], "icon_luck")), 1.5)


def move_selection(event, index, size, columns):
    if event.key in (pygame.K_LEFT, pygame.K_a):
        index -= 1
    elif event.key in (pygame.K_RIGHT, pygame.K_d):
        index += 1
    elif event.key in (pygame.K_UP, pygame.K_w):
        index -= columns
    elif event.key in (pygame.K_DOWN, pygame.K_s):
        index += columns
    return max(0, min(size - 1, index))


# ---------- hoofdmenu ----------

DIFFICULTY_COLORS = {"easy": (120, 220, 130), "normal": (120, 190, 250), "hard": (250, 170, 70),
                     "extreme": (240, 80, 90)}
MENU_HOTKEYS = {pygame.K_b: "battlepass", pygame.K_c: "challenges", pygame.K_k: "shop",
                pygame.K_g: "gemstore", pygame.K_a: "achievements"}


def open_screen(state, name):
    state["screen"] = name
    state["message"] = ""
    if name == "battlepass":
        state["bp_selected"] = max(0, battlepass.current_tier(state["bp"]) - 1)
    elif name == "challenges":
        challenges.refresh(state["bp"])


def menu_buttons(state):
    """Lijst van (actie, tekst, kleine tekst, hoogte)."""
    buttons = []
    run = state["run_info"]
    if run:
        sub = f"{DIFFICULTIES[run['difficulty']]['name']} - {format_time(run['time'])}, level {run['level']}"
        buttons.append(("continue", "Doorgaan", sub, 56))
    buttons.append(("new", "Nieuwe run", None, 44))
    buttons.append(("battlepass", f"Battle Pass (tier {battlepass.current_tier(state['bp'])})", None, 40))
    buttons.append(("challenges", "Challenges", None, 40))
    buttons.append(("shop", "Winkel", None, 40))
    buttons.append(("gemstore", "Gems", None, 40))
    buttons.append(("achievements", "Achievements", None, 40))
    buttons.append(("settings", "Instellingen", None, 40))
    buttons.append(("slots", "Wissel save", None, 40))
    buttons.append(("quit", "Afsluiten", None, 40))
    return buttons


def menu_rects(state):
    rects = []
    y = 150
    for button in menu_buttons(state):
        rects.append(pygame.Rect(50, y, 320, button[3]))
        y += button[3] + 6
    return rects


def difficulty_rects():
    rects = []
    for i in range(len(DIFFICULTY_KEYS)):
        rects.append(pygame.Rect(W / 2 - 280, 150 + i * 86, 560, 74))
    rects.append(pygame.Rect(W / 2 - 280, 150 + len(DIFFICULTY_KEYS) * 86 + 8, 560, 48))
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
        number_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                state["menu_page"] = "main"
                return
            if event.key in number_keys and number_keys.index(event.key) < len(DIFFICULTY_KEYS):
                state["start"] = DIFFICULTY_KEYS[number_keys.index(event.key)]
                return
        if ui.back_clicked(events):
            state["menu_page"] = "main"
            return
        state["selected"], chosen = ui.navigate(events, state["selected"], difficulty_rects())
        if chosen == len(DIFFICULTY_KEYS):
            state["menu_page"] = "main"
        elif chosen is not None:
            state["start"] = DIFFICULTY_KEYS[chosen]
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
    bp = state["bp"]
    draw_background(screen, state, 120)
    t = state["menu_time"]
    if state["menu_page"] == "difficulty":
        draw_difficulty(screen, state)
        return
    # donkere strook links achter de knoppen
    strip = pygame.Surface((420, H), pygame.SRCALPHA)
    strip.fill((8, 6, 18, 150))
    screen.blit(strip, (0, 0))

    bob = math.sin(t * 2) * 4
    ui.title(screen, "roguelike", 104, ui.WHITE, 40 + bob, 210)
    ui.title(screen, f"Save {saves.slot}", 24, GREY, 116, 210)

    rects = menu_rects(state)
    for i, (action, label, sub, _) in enumerate(menu_buttons(state)):
        accent = YELLOW
        if action == "continue":
            accent = (120, 220, 130)
        elif action == "gemstore":
            accent = (230, 120, 230)
        elif action == "quit":
            accent = (240, 110, 110)
        size = 32 if action in ("continue", "new") else 28
        ui.button(screen, rects[i], label, i == state["menu_selected"], accent, sub, size)

    draw_coins(screen, bp["coins"])
    draw_gems(screen, bp["gems"])

    # held in het midden van de rechterkant
    hero = sprites.scaled(sprites.frame(battlepass.skin_sprite(bp), t, 4), 3)
    sprites.draw_centered(screen, hero, (670, 200 + math.sin(t * 3) * 6))
    tier = battlepass.current_tier(bp)
    ui.card(screen, (470, 290, 400, 70), (70, 68, 95))
    screen.blit(sprites.font(28).render(f"Battle Pass tier {tier}", True, YELLOW), (490, 302))
    progress = 1 if tier >= BP_TIERS else (bp["xp"] % BP_XP_PER_TIER) / BP_XP_PER_TIER
    pygame.draw.rect(screen, (40, 40, 60), (490, 332, 360, 12), border_radius=6)
    pygame.draw.rect(screen, (80, 220, 240), (490, 332, 360 * progress, 12), border_radius=6)

    last_run = state["last_run"]
    if last_run:
        ui.card(screen, (470, 376, 400, 150), (240, 130, 130))
        screen.blit(sprites.font(28).render("Laatste run", True, (240, 130, 130)), (490, 388))
        lines = [
            (f"{last_run['difficulty']} - {format_time(last_run['time'])}, level {last_run['level']}", ui.WHITE),
            (f"{last_run['kills']} kills, +{last_run['coins']} coins, +{last_run['bp_xp']} BP XP", YELLOW),
        ]
        if last_run["new_tiers"] > 0:
            lines.append((f"Tier {last_run['tier']} bereikt!", YELLOW))
        for text in last_run["finished"][:2]:
            lines.append((f"Challenge voltooid: {text}", (120, 230, 120)))
        for i, (text, color) in enumerate(lines[:4]):
            screen.blit(sprites.font(22).render(text, True, color), (490, 418 + i * 24))

    hint = "Muis of pijltjes + Enter  -  B C K G A sneltoetsen  -  F11 volledig scherm"
    image = sprites.font(20).render(hint, True, GREY)
    screen.blit(image, (W - image.get_width() - 20, H - 28))

    if state["menu_page"] == "confirm_new":
        ui.draw_confirm(screen, "Nieuwe run?", "Je opgeslagen run gaat verloren", state["confirm_selected"])
    elif state["menu_page"] == "confirm_quit":
        ui.draw_confirm(screen, "Afsluiten?", None, state["confirm_selected"])


def draw_difficulty(screen, state):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((8, 6, 18, 100))
    screen.blit(overlay, (0, 0))
    ui.title(screen, "Kies moeilijkheid", 64, ui.WHITE, 70)
    rects = difficulty_rects()
    for i, key in enumerate(DIFFICULTY_KEYS):
        info = DIFFICULTIES[key]
        sub = f"{info['player_hp']} levens, vijanden x{info['enemy_hp']} HP en x{info['enemy_speed']} snelheid"
        if info["enemy_damage"] > 1:
            sub += f", {info['enemy_damage']} schade"
        ui.button(screen, rects[i], f"{i + 1}. {info['name']}", i == state["selected"],
                  DIFFICULTY_COLORS.get(key, YELLOW), sub, 34)
    ui.button(screen, rects[-1], "Terug", state["selected"] == len(DIFFICULTY_KEYS), size=28)
    ui.back_button(screen)
    text_center(screen, "1-4 start meteen, Esc: terug", 22, GREY, H - 34)


# ---------- saves kiezen ----------

def init_slots(world):
    return {
        "running": True,
        "screen": "slots",
        "bp": None,
        "world": world,
        "menu_time": 0,
        "start": None,
        "continue": False,
        "popup": False,
        "slot_selected": 0,
        "slot_confirm": None,
        "confirm_selected": 1,
    }


def slot_rects():
    cards = []
    deletes = []
    for i in range(saves.SLOTS):
        x = 75 + i * 280
        cards.append(pygame.Rect(x, 160, 250, 300))
        deletes.append(pygame.Rect(x + 40, 474, 170, 40))
    return cards, deletes


def pick_slot(state, n):
    saves.slot = n
    config.set("last_slot", n)
    bp = battlepass.load()
    battlepass.save(bp)
    state.update(init_menu(bp, state["world"]))


def handle_slots_input(state, events):
    if state["slot_confirm"] is not None:
        state["confirm_selected"], answer = ui.handle_confirm(events, state["confirm_selected"])
        if answer:
            n = state["slot_confirm"]
            saves.delete_slot(n)
            # de save waar je in zat is weg, dus eerst een nieuwe kiezen
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
        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and saves.slot_info(state["slot_selected"] + 1):
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
    draw_background(screen, state, 170)
    ui.title(screen, "Kies een save", 72, ui.WHITE, 60)
    cards, deletes = slot_rects()
    for i in range(saves.SLOTS):
        info = saves.slot_info(i + 1)
        rect = cards[i]
        active = i == state["slot_selected"]
        if active:
            ui.card(screen, rect, YELLOW, ui.tint(YELLOW, 0.2))
        else:
            ui.card(screen, rect, (70, 68, 95))
        text_center(screen, f"Save {i + 1}", 44, YELLOW if active else ui.WHITE, rect.y + 20, rect.centerx)
        if state["bp"] is not None and i + 1 == saves.slot:
            text_center(screen, "Huidige save", 20, (120, 220, 130), rect.y + 62, rect.centerx)
        if info is None:
            text_center(screen, "Nieuw spel", 32, GREY, rect.centery - 10, rect.centerx)
            continue
        lines = [
            (f"Tier {min(BP_TIERS, info['xp'] // BP_XP_PER_TIER)}", ui.WHITE),
            (f"{info['coins']} coins", (240, 200, 60)),
            (f"{info['gems']} gems", (230, 120, 230)),
            (f"{info['runs']} runs gespeeld", GREY),
            (f"Gespeeld: {info['last_played']}", GREY),
        ]
        for j, (text, color) in enumerate(lines):
            text_center(screen, text, 26, color, rect.y + 100 + j * 30, rect.centerx)
        if info["run"]:
            run = info["run"]
            text = f"Run bezig: {format_time(run['time'])}, lvl {run['level']}"
            text_center(screen, text, 22, (120, 220, 130), rect.bottom - 34, rect.centerx)
        hover = deletes[i].collidepoint(pygame.mouse.get_pos())
        ui.button(screen, deletes[i], "Verwijderen", hover, (240, 110, 110), size=24)

    if state["bp"] is not None:
        ui.back_button(screen)
    text_center(screen, "Klik of Enter: spelen, Delete: verwijderen, Esc: terug", 22, GREY, H - 40)
    if state["slot_confirm"] is not None:
        ui.draw_confirm(screen, f"Save {state['slot_confirm']} verwijderen?", "Dit kan je niet terugdraaien",
                        state["confirm_selected"])


# ---------- instellingen ----------

def handle_settings_input(state, events):
    if settings_menu.handle(events):
        state["screen"] = "menu"


def draw_settings(screen, state):
    draw_background(screen, state, 170)
    settings_menu.draw(screen)


def format_time(seconds):
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


# ---------- battle pass ----------

def handle_battlepass_input(state, events):
    bp = state["bp"]
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_b):
            state["screen"] = "menu"
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            state["bp_selected"] = max(0, state["bp_selected"] - 1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            state["bp_selected"] = min(BP_TIERS - 1, state["bp_selected"] + 1)
        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            state["bp_row"] = 1 - state["bp_row"]
        elif event.key == pygame.K_PAGEUP:
            state["bp_selected"] = max(0, state["bp_selected"] - 5)
        elif event.key == pygame.K_PAGEDOWN:
            state["bp_selected"] = min(BP_TIERS - 1, state["bp_selected"] + 5)
        elif event.key == pygame.K_p:
            if bp["premium"]:
                state["message"] = "Je hebt premium al"
            elif battlepass.buy_premium(bp):
                battlepass.save(bp)
                state["message"] = "Premium gekocht!"
            else:
                state["message"] = "Niet genoeg coins"
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if state["bp_row"] == 0:
                reward = battlepass.FREE_TIERS[state["bp_selected"]]
            else:
                reward = battlepass.PREMIUM_TIERS[state["bp_selected"]]
            if reward["type"] not in ("skin", "bullet"):
                state["message"] = "Dit kan je niet uitrusten"
            elif battlepass.equip(bp, reward):
                battlepass.save(bp)
                state["message"] = f"{reward['name']} uitgerust"
            else:
                state["message"] = "Nog niet vrijgespeeld"


def draw_reward_box(screen, reward, x, y, tier, unlocked, owned, equipped, selected, time):
    width, height = 150, 140
    if unlocked:
        bg = (55, 52, 80)
    else:
        bg = (28, 26, 38)
    pygame.draw.rect(screen, bg, (x, y, width, height), border_radius=10)
    if selected:
        pygame.draw.rect(screen, YELLOW, (x, y, width, height), 4, border_radius=10)
    elif owned or (reward["type"] == "coins" and unlocked):
        pygame.draw.rect(screen, (120, 200, 120), (x, y, width, height), 2, border_radius=10)
    else:
        pygame.draw.rect(screen, (90, 90, 110), (x, y, width, height), 2, border_radius=10)

    screen.blit(sprites.font(22).render(f"Tier {tier}", True, (200, 200, 200)), (x + 10, y + 8))

    icon = reward_icon(reward, time)
    if not unlocked:
        icon = icon.copy()
        icon.set_alpha(110)
    sprites.draw_centered(screen, icon, (x + width / 2, y + 62))

    text_center(screen, reward["name"], 20, (255, 255, 255), y + 96, x + width / 2)
    if equipped:
        text_center(screen, "Uitgerust", 20, (120, 220, 120), y + 116, x + width / 2)
    elif not unlocked:
        text_center(screen, "Op slot", 20, (150, 150, 150), y + 116, x + width / 2)


def draw_battlepass(screen, state):
    bp = state["bp"]
    draw_background(screen, state, 190)
    text_center(screen, "Battle Pass", 64, YELLOW, 20)
    draw_coins(screen, bp["coins"])

    tier = battlepass.current_tier(bp)
    if tier < BP_TIERS:
        progress = bp["xp"] % BP_XP_PER_TIER
        line = f"Tier {tier} - {progress}/{BP_XP_PER_TIER} XP naar tier {tier + 1}"
    else:
        progress = BP_XP_PER_TIER
        line = f"Tier {tier} - Battle Pass voltooid!"
    text_center(screen, line, 26, (255, 255, 255), 78)
    pygame.draw.rect(screen, (30, 30, 50), (180, 104, 600, 14), border_radius=7)
    pygame.draw.rect(screen, (80, 220, 240), (180, 104, 600 * progress / BP_XP_PER_TIER, 14), border_radius=7)

    start = min(max(0, state["bp_selected"] - 2), BP_TIERS - 5)
    left = 65
    rows = [
        ("GRATIS", battlepass.FREE_TIERS, 140, True),
        ("PREMIUM", battlepass.PREMIUM_TIERS, 320, bp["premium"]),
    ]
    for row, (label, tiers, y, active) in enumerate(rows):
        color = YELLOW if row == 1 else (200, 200, 200)
        screen.blit(sprites.font(26).render(label, True, color), (left, y))
        for i in range(start, start + 5):
            reward = tiers[i]
            x = left + (i - start) * 170
            unlocked = active and i < tier
            owned = reward["name"] in bp["owned"]
            equipped = reward["name"] in (bp["skin"], bp["bullet"])
            selected = i == state["bp_selected"] and row == state["bp_row"]
            draw_reward_box(screen, reward, x, y + 22, i + 1, unlocked, owned, equipped, selected, state["menu_time"])

    # kleine balk met alle tiers
    segment = 830 / BP_TIERS
    for i in range(BP_TIERS):
        if i < tier:
            color = (80, 220, 240)
        else:
            color = (50, 50, 70)
        if start <= i < start + 5:
            pygame.draw.rect(screen, (90, 90, 120), (65 + i * segment, 494, segment - 2, 14))
        pygame.draw.rect(screen, color, (65 + i * segment, 497, segment - 2, 8))

    if bp["premium"]:
        line = "Premium: gekocht"
    else:
        line = f"P: koop premium ({PREMIUM_COST} coins)"
    text_center(screen, line, 26, YELLOW, 520)
    text_center(screen, "Pijltjes: kiezen, PgUp/PgDn: 5 verder, Enter: uitrusten, Esc: terug", 24, GREY, 552)
    if state["message"]:
        text_center(screen, state["message"], 28, (240, 130, 130), 590)


# ---------- challenges ----------

def handle_challenges_input(state, events):
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_c):
            state["screen"] = "menu"


def draw_challenge_list(screen, title, items, xp, y, time):
    panel(screen, (80, y, W - 160, 52 + len(items) * 58))
    screen.blit(sprites.font(34).render(title, True, YELLOW), (100, y + 12))
    reward = sprites.font(24).render(f"+{xp} BP XP per stuk", True, GREY)
    screen.blit(reward, (W - 100 - reward.get_width(), y + 18))
    for i, challenge in enumerate(items):
        row_y = y + 52 + i * 58
        color = (120, 230, 120) if challenge["done"] else (255, 255, 255)
        screen.blit(sprites.font(26).render(challenge["text"], True, color), (100, row_y))
        bar_w = 420
        fill = challenge["progress"] / challenge["goal"]
        pygame.draw.rect(screen, (60, 60, 85), (100, row_y + 26, bar_w, 12), border_radius=6)
        pygame.draw.rect(screen, color if challenge["done"] else (80, 220, 240), (100, row_y + 26, bar_w * fill, 12), border_radius=6)
        progress = sprites.font(24).render(challenges.progress_text(challenge), True, GREY)
        screen.blit(progress, (540, row_y + 22))
        if challenge["done"]:
            screen.blit(sprites.font(26).render("Klaar!", True, color), (W - 170, row_y + 10))


def draw_challenges(screen, state):
    bp = state["bp"]
    draw_background(screen, state, 190)
    text_center(screen, "Challenges", 64, YELLOW, 20)
    draw_challenge_list(screen, "Dagelijks", bp["challenges"]["daily"], challenges.DAILY_XP, 90, state["menu_time"])
    draw_challenge_list(screen, "Wekelijks", bp["challenges"]["weekly"], challenges.WEEKLY_XP, 330, state["menu_time"])
    text_center(screen, "Challenges tellen automatisch na elke run. Esc: terug", 24, GREY, 580)


# ---------- winkel ----------

def handle_shop_input(state, events):
    bp = state["bp"]
    items = battlepass.SHOP_ITEMS
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_k):
            state["screen"] = "menu"
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            state["message"] = battlepass.buy_item(bp, items[state["shop_selected"]])
            battlepass.save(bp)
        else:
            state["shop_selected"] = move_selection(event, state["shop_selected"], len(items), 3)


def draw_shop(screen, state):
    bp = state["bp"]
    draw_background(screen, state, 190)
    text_center(screen, "Winkel", 64, YELLOW, 20)
    draw_coins(screen, bp["coins"])

    for i, item in enumerate(battlepass.SHOP_ITEMS):
        x = 105 + (i % 3) * 260
        y = 100 + (i // 3) * 210
        selected = i == state["shop_selected"]
        panel(screen, (x, y, 230, 190), YELLOW if selected else (90, 90, 120), 4 if selected else 2)
        icon = reward_icon(item, state["menu_time"])
        if item["type"] == "skin":
            icon = sprites.scaled(icon, 1.5)
        sprites.draw_centered(screen, icon, (x + 115, y + 70))
        text_center(screen, item["name"], 26, (255, 255, 255), y + 122, x + 115)

        equipped = item["name"] in (bp["skin"], bp["bullet"])
        if item["type"] == "tier_skip":
            status = f"{item['price']} coins"
            color = (240, 200, 60)
        elif equipped:
            status, color = "Uitgerust", (120, 220, 120)
        elif battlepass.owns(bp, item):
            status, color = "In bezit", (180, 220, 180)
        else:
            status = f"{item['price']} coins"
            color = (240, 200, 60)
        text_center(screen, status, 22, color, y + 154, x + 115)

    text_center(screen, "Pijltjes: kiezen, Enter: kopen of uitrusten, Esc: terug", 24, GREY, 552)
    if state["message"]:
        text_center(screen, state["message"], 28, (240, 130, 130), 590)


SCREENS = {
    "menu": (handle_menu_input, draw_menu),
    "battlepass": (handle_battlepass_input, draw_battlepass),
    "challenges": (handle_challenges_input, draw_challenges),
    "shop": (handle_shop_input, draw_shop),
    "slots": (handle_slots_input, draw_slots),
    "settings": (handle_settings_input, draw_settings),
}

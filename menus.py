import pygame

import battlepass
import challenges
import sprites
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

def handle_menu_input(state, events):
    number_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            state["running"] = False
        elif event.key in (pygame.K_UP, pygame.K_w):
            state["selected"] = (state["selected"] - 1) % len(DIFFICULTY_KEYS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            state["selected"] = (state["selected"] + 1) % len(DIFFICULTY_KEYS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            state["start"] = DIFFICULTY_KEYS[state["selected"]]
        elif event.key == pygame.K_b:
            state["screen"] = "battlepass"
            state["bp_selected"] = max(0, battlepass.current_tier(state["bp"]) - 1)
            state["message"] = ""
        elif event.key == pygame.K_c:
            challenges.refresh(state["bp"])
            state["screen"] = "challenges"
        elif event.key == pygame.K_k:
            state["screen"] = "shop"
            state["message"] = ""
        elif event.key in number_keys:
            index = number_keys.index(event.key)
            if index < len(DIFFICULTY_KEYS):
                state["start"] = DIFFICULTY_KEYS[index]


def draw_menu(screen, state):
    bp = state["bp"]
    draw_background(screen, state)
    draw_coins(screen, bp["coins"])

    text_center(screen, "roguelike", 96, (255, 255, 255), 50)
    hero = sprites.scaled(sprites.frame(battlepass.skin_sprite(bp), state["menu_time"], 4), 2)
    sprites.draw_centered(screen, hero, (W / 2 - 250, 90))
    sprites.draw_centered(screen, sprites.flipped(hero), (W / 2 + 250, 90))

    panel(screen, (W / 2 - 200, 150, 400, 270))
    text_center(screen, "Kies moeilijkheid", 40, (255, 255, 255), 168)
    for i, key in enumerate(DIFFICULTY_KEYS):
        name = DIFFICULTIES[key]["name"]
        y = 220 + i * 48
        if i == state["selected"]:
            pygame.draw.rect(screen, (70, 60, 30), (W / 2 - 170, y - 6, 340, 40), border_radius=8)
            pygame.draw.rect(screen, YELLOW, (W / 2 - 170, y - 6, 340, 40), 2, border_radius=8)
            text_center(screen, f"{i + 1}. {name}", 40, YELLOW, y)
        else:
            text_center(screen, f"{i + 1}. {name}", 40, (200, 200, 200), y)

    tier = battlepass.current_tier(bp)
    buttons = [("B", f"Battle Pass (tier {tier})"), ("C", "Challenges"), ("K", "Winkel")]
    x = W / 2 - 330
    for key, label in buttons:
        panel(screen, (x, 438, 210, 40), YELLOW)
        text_center(screen, f"{key}: {label}", 26, YELLOW, 450, x + 105)
        x += 225
    text_center(screen, "Pijltjes + Enter of 1-4 om te starten, Esc om te stoppen", 24, GREY, 492)

    last_run = state["last_run"]
    if last_run:
        line = f"Laatste run: {last_run['difficulty']} - {format_time(last_run['time'])}, level {last_run['level']}, {last_run['kills']} kills"
        text_center(screen, line, 26, (240, 130, 130), 522)
        line = f"+{last_run['bp_xp']} BP XP, +{last_run['coins']} coins"
        if last_run["new_tiers"] > 0:
            line += f" - tier {last_run['tier']} bereikt!"
        text_center(screen, line, 26, YELLOW, 550)
        for i, text in enumerate(last_run["finished"][:2]):
            text_center(screen, f"Challenge voltooid: {text}", 24, (120, 230, 120), 578 + i * 24)


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
}

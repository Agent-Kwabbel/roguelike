import math
import random

import pygame

import battlepass
import sprites
from menus import draw_background, draw_coins, draw_gems, text_center, panel, wrap_text, move_selection, YELLOW, GREY
from settings import W, H, LOOTBOX_COST, MEGA_LOOTBOX_COST

PINK = (230, 120, 230)

# Alles hier is nep, er wordt nooit echt geld betaald
ITEMS = [
    {"type": "pack", "name": "STARTER PACK", "price": "€0,99", "gems": 600, "icon": "gem_premium", "tag": "99% KORTING"},
    {"type": "pack", "name": "Handje gems", "price": "€4,99", "gems": 80, "icon": "gem_premium"},
    {"type": "pack", "name": "Kist gems", "price": "€49,99", "gems": 1200, "icon": "gem_premium", "tag": "POPULAIR"},
    {"type": "pack", "name": "Berg gems", "price": "€99,99", "gems": 2800, "icon": "gem_premium"},
    {"type": "pack", "name": "Walvis pakket", "price": "€999,99", "gems": 15000, "icon": "skin_whale", "tag": "BESTE DEAL"},
    {"type": "ad", "name": "Reclame kijken", "price": "Gratis", "gems": 5, "icon": "botje"},
    {"type": "box", "name": "Lootbox", "cost": LOOTBOX_COST, "mega": False, "icon": "lootbox"},
    {"type": "box", "name": "Mega lootbox", "cost": MEGA_LOOTBOX_COST, "mega": True, "icon": "lootbox", "tag": "BETERE KANS"},
    {"type": "booster", "name": "Dubbele XP", "cost": 60, "booster": "xp", "icon": "potion"},
    {"type": "booster", "name": "Dubbele coins", "cost": 60, "booster": "coins", "icon": "coin"},
    {"type": "pet", "name": "Huisdier Slijmpje", "cost": 300, "icon": "pet"},
    {"type": "exchange", "name": "1000 coins", "cost": 100, "coins": 1000, "icon": "coin"},
]

RARITIES = [
    ("Gewoon", (200, 200, 200)),
    ("Zeldzaam", (90, 170, 255)),
    ("Episch", (190, 90, 255)),
    ("Legendarisch", (255, 200, 50)),
]
CHANCES = {False: [60, 25, 12, 3], True: [0, 50, 35, 15]}

THANKS = [
    "Bedankt voor je steun!",
    "Je portemonnee huilt, maar je skin is mooi.",
    "Betaling geslaagd! (er is niks betaald, dit is nep)",
    "De ontwikkelaar kan nu een broodje kopen.",
]


def item_icon(item, time):
    if item["icon"].startswith("skin") or item["icon"] in ("botje", "pet"):
        return sprites.frame(item["icon"], time, 4)
    return sprites.get(item["icon"])


def price_text(item):
    if "price" in item:
        return item["price"]
    return f"{item['cost']} gems"


def roll_lootbox(bp, mega):
    rarity = random.choices(range(4), CHANCES[mega])[0]
    options = [r for r in battlepass.GEM_REWARDS if r.get("rarity") == rarity]
    if not options:
        reward = battlepass.coins(150 + 50 * rarity)
    else:
        reward = random.choice(options)
    duplicate = reward["type"] != "coins" and reward["name"] in bp["owned"]
    if duplicate:
        bp["gems"] += 20
    else:
        battlepass.give(bp, reward)
        battlepass.equip(bp, reward)
    bp["boxes_opened"] = bp.get("boxes_opened", 0) + 1
    return {"timer": 2.2, "reward": reward, "rarity": rarity, "duplicate": duplicate}


def buy(state, item):
    bp = state["bp"]
    if item["type"] == "pack":
        state["gem_pay"] = {"timer": 1.8, "item": item}
        return ""
    if item["type"] == "ad":
        state["gem_ad"] = {"timer": 3.0}
        return ""
    if item["type"] == "pet" and bp["pet"]:
        return "Je hebt Slijmpje al. Slijmpje is uniek."
    if bp["gems"] < item["cost"]:
        return "Niet genoeg gems. Koop meer gems!"
    bp["gems"] -= item["cost"]
    if item["type"] == "box":
        state["gem_box"] = roll_lootbox(bp, item["mega"])
        return ""
    if item["type"] == "booster":
        bp["boosters"][item["booster"]] += 1
        return f"{item['name']} geldt voor je volgende run"
    if item["type"] == "pet":
        bp["pet"] = True
        return "Slijmpje loopt nu met je mee!"
    if item["type"] == "exchange":
        bp["coins"] += item["coins"]
        return f"+{item['coins']} coins"
    return ""


def finish_payment(state):
    bp = state["bp"]
    item = state["gem_pay"]["item"]
    bp["gems"] += item["gems"]
    if item["name"] == "Walvis pakket":
        bp["whale"] = True
        whale = battlepass.find_reward("Walvis")
        battlepass.give(bp, whale)
        battlepass.equip(bp, whale)
    state["gem_pay"] = None
    state["message"] = f"+{item['gems']} gems. " + random.choice(THANKS)
    battlepass.save(bp)


def update(state, dt):
    if state.get("gem_pay"):
        state["gem_pay"]["timer"] -= dt
        if state["gem_pay"]["timer"] <= 0:
            finish_payment(state)
    if state.get("gem_ad"):
        state["gem_ad"]["timer"] -= dt
        if state["gem_ad"]["timer"] <= 0:
            state["gem_ad"] = None
            state["bp"]["gems"] += 5
            state["message"] = "+5 gems. Bedankt voor het kijken!"
            battlepass.save(state["bp"])
    if state.get("gem_box"):
        state["gem_box"]["timer"] -= dt


def handle_input(state, events):
    bp = state["bp"]
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        # tijdens betalen en reclame kan je niks
        if state["gem_pay"] or state["gem_ad"]:
            continue
        if state["gem_box"]:
            if state["gem_box"]["timer"] <= 0 and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                state["gem_box"] = None
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_g):
            state["screen"] = "menu"
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            state["message"] = buy(state, ITEMS[state["gem_selected"]])
            battlepass.save(bp)
        else:
            state["gem_selected"] = move_selection(event, state["gem_selected"], len(ITEMS), 4)


def draw_item(screen, item, x, y, selected, time):
    panel(screen, (x, y, 200, 134), PINK if selected else (90, 90, 120), 4 if selected else 2)
    icon = item_icon(item, time)
    factor = 48 / max(icon.get_width(), icon.get_height())
    if selected:
        factor *= 1 + 0.08 * math.sin(time * 6)
    sprites.draw_centered(screen, sprites.scaled(icon, round(factor, 2)), (x + 100, y + 42))
    text_center(screen, item["name"], 24, (255, 255, 255), y + 76, x + 100)
    text_center(screen, price_text(item), 24, YELLOW if "price" in item else PINK, y + 102, x + 100)
    if "tag" in item:
        tag = sprites.font(20).render(item["tag"], True, (255, 255, 255))
        rect = (x + 200 - tag.get_width() - 14, y - 8, tag.get_width() + 10, 20)
        pygame.draw.rect(screen, (220, 40, 60), rect, border_radius=6)
        screen.blit(tag, (rect[0] + 5, rect[1] + 3))


def draw_payment(screen, state):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    item = state["gem_pay"]["item"]
    panel(screen, (W / 2 - 220, 220, 440, 180), PINK)
    text_center(screen, "Betaling verwerken...", 40, (255, 255, 255), 244)
    text_center(screen, f"{item['name']} - {item['price']}", 28, YELLOW, 290)
    for i in range(8):
        angle = state["menu_time"] * 6 + i * math.pi / 4
        alpha = 80 + i * 20
        pos = (W / 2 + math.cos(angle) * 22, 350 + math.sin(angle) * 22)
        pygame.draw.circle(screen, (alpha, alpha, 255), pos, 5)


def draw_ad(screen, state):
    t = state["menu_time"]
    colors = [(255, 60, 120), (60, 200, 255), (255, 220, 50)]
    screen.fill(colors[int(t * 4) % 3])
    text_center(screen, "RECLAME", 40, (0, 0, 0), 40)
    text_center(screen, "KOOP NU HET", 72, (255, 255, 255), 170)
    text_center(screen, "WALVIS PAKKET", 96, (255, 255, 255), 240)
    image = sprites.scaled(sprites.frame("skin_whale", t, 6), 3)
    sprites.draw_centered(screen, image, (W / 2, 400))
    text_center(screen, "Nu slechts €999,99!!!", 40, (0, 0, 0), 470)
    left = math.ceil(state["gem_ad"]["timer"])
    text_center(screen, f"Reclame sluit over {left}...", 28, (0, 0, 0), 580)


def draw_lootbox(screen, state):
    box = state["gem_box"]
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))
    name, color = RARITIES[box["rarity"]]
    if box["timer"] > 0:
        # kist schudt steeds harder
        power = (2.2 - box["timer"]) * 6
        offset = (random.uniform(-power, power), random.uniform(-power, power))
        image = sprites.scaled(sprites.get("lootbox"), 2)
        sprites.draw_centered(screen, image, (W / 2 + offset[0], 300 + offset[1]))
        text_center(screen, "Openen...", 40, (255, 255, 255), 420)
        return
    pygame.draw.circle(screen, color, (W / 2, 280), 110, 6)
    for i in range(12):
        angle = state["menu_time"] * 1.5 + i * math.pi / 6
        start = (W / 2 + math.cos(angle) * 120, 280 + math.sin(angle) * 120)
        end = (W / 2 + math.cos(angle) * 170, 280 + math.sin(angle) * 170)
        pygame.draw.line(screen, color, start, end, 4)
    reward = box["reward"]
    if reward["type"] == "skin":
        icon = sprites.scaled(sprites.frame(reward["sprite"], state["menu_time"], 4), 2)
    elif reward["type"] == "bullet":
        icon = sprites.scaled(sprites.get(reward["sprite"]), 4)
    else:
        icon = sprites.scaled(sprites.get("coin"), 3)
    sprites.draw_centered(screen, icon, (W / 2, 280))
    text_center(screen, name.upper(), 52, color, 120)
    text_center(screen, reward["name"], 40, (255, 255, 255), 420)
    if box["duplicate"]:
        text_center(screen, "Dubbel! Je krijgt 20 gems terug", 28, PINK, 466)
    text_center(screen, "Enter: verder", 24, GREY, 540)


def draw_screen(screen, state):
    bp = state["bp"]
    draw_background(screen, state, 190)
    text_center(screen, "Gem Winkel", 64, PINK, 20)
    draw_coins(screen, bp["coins"])
    draw_gems(screen, bp["gems"])
    for i, item in enumerate(ITEMS):
        x = 50 + (i % 4) * 220
        y = 100 + (i // 4) * 150
        draw_item(screen, item, x, y, i == state["gem_selected"], state["menu_time"])

    boosters = bp["boosters"]
    line = f"Boosters klaar: {boosters['xp']}x dubbele XP, {boosters['coins']}x dubbele coins"
    text_center(screen, line, 22, GREY, 552)
    text_center(screen, "* Alle prijzen zijn nep, er wordt nooit echt geld betaald. Esc: terug", 20, (140, 140, 150), 576)
    if state["message"]:
        text_center(screen, state["message"], 26, (240, 130, 130), 602)

    if state["gem_pay"]:
        draw_payment(screen, state)
    elif state["gem_ad"]:
        draw_ad(screen, state)
    elif state["gem_box"]:
        draw_lootbox(screen, state)


# ---------- starter pack popup in het menu ----------

def handle_popup(state, events):
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            state["popup"] = False
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            state["popup"] = False
            state["screen"] = "gemstore"
            state["gem_selected"] = 0
            state["message"] = ""


def draw_popup(screen, state):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    t = state["menu_time"]
    pulse = 1 + 0.04 * math.sin(t * 8)
    panel(screen, (W / 2 - 260, 130, 520, 360), (255, 60, 90), 5)
    text_center(screen, "STARTER PACK", int(64 * pulse), YELLOW, 150)
    text_center(screen, "99% KORTING!!", int(48 * pulse), (255, 80, 100), 210)
    sprites.draw_centered(screen, sprites.scaled(sprites.get("gem_premium"), 2), (W / 2 - 60, 300))
    text_center(screen, "x600", 48, PINK, 284, W / 2 + 40)
    # de timer begint gewoon opnieuw als hij op 0 staat
    left = 299 - int(t) % 300
    text_center(screen, f"Nog maar {left // 60}:{left % 60:02d} geldig!", 30, (255, 255, 255), 360)
    text_center(screen, "Van €99,99 voor maar €0,99", 26, GREY, 396)
    text_center(screen, "Enter: bekijken, Esc: nee bedankt, ik hou niet van geld besparen", 22, GREY, 446)


SCREENS = {
    "gemstore": (handle_input, draw_screen),
}

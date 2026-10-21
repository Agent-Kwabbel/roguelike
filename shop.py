import pygame

import achievements
import progress
import sound
import sprites
import ui
from menus import draw_coins, reward_icon, wrap_text

TABS = [("skin", "Skins"), ("bullet", "Bullets"), ("perk", "Perks")]
COLUMNS = 4
ROWS = 3
TILE_W = 126
TILE_H = 128
GRID_X = 50
GRID_Y = 132
DETAIL = pygame.Rect(616, 132, 296, 408)
ACTION = pygame.Rect(DETAIL.x + 18, DETAIL.bottom - 62, DETAIL.w - 36, 46)
BAD_MESSAGES = ("Not enough coins", "Get the achievement first")


def tab_items(state):
    kind = TABS[state["shop_tab"]][0]
    return [item for item in progress.SHOP_ITEMS if item["type"] == kind]


def tab_rects():
    return [pygame.Rect(GRID_X + i * 150, 76, 140, 40) for i in range(len(TABS))]


def visible_tiles(state):
    """(index, rect) for the tiles that fit in the grid right now."""
    result = []
    for i in range(len(tab_items(state))):
        row = i // COLUMNS - state["shop_scroll"]
        if 0 <= row < ROWS:
            x = GRID_X + (i % COLUMNS) * (TILE_W + 12)
            result.append((i, pygame.Rect(x, GRID_Y + row * (TILE_H + 12), TILE_W, TILE_H)))
    return result


def max_scroll(state):
    rows = (len(tab_items(state)) + COLUMNS - 1) // COLUMNS
    return max(0, rows - ROWS)


def keep_in_view(state):
    row = state["shop_selected"] // COLUMNS
    if row < state["shop_scroll"]:
        state["shop_scroll"] = row
    elif row >= state["shop_scroll"] + ROWS:
        state["shop_scroll"] = row - ROWS + 1


def switch_tab(state, tab):
    state["shop_tab"] = tab % len(TABS)
    state["shop_selected"] = 0
    state["shop_scroll"] = 0
    state["message"] = ""


def item_status(bp, item):
    """(short text, colour) for the badge on a tile."""
    if progress.is_equipped(bp, item):
        return "Equipped", ui.GREEN
    if progress.owns(bp, item):
        if item["type"] == "perk":
            return "Active", ui.GREEN
        return "Owned", ui.GREY
    if item["achievement"]:
        return "Locked", ui.DIM
    return str(item["price"]), ui.COIN


def buy(state):
    items = tab_items(state)
    coins = state["bp"]["coins"]
    state["message"] = progress.buy_item(state["bp"], items[state["shop_selected"]])
    if state["bp"]["coins"] < coins:
        sound.play("buy")
    elif state["message"].endswith("equipped"):
        sound.play("menu_select")
    else:
        sound.play("error")
    progress.save(state["bp"])


def handle_input(state, events):
    items = tab_items(state)
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_k):
            state["screen"] = "menu"
            sound.play("menu_back")
            return
        if event.key == pygame.K_TAB or event.key == pygame.K_e:
            switch_tab(state, state["shop_tab"] + 1)
            return
        if event.key == pygame.K_q:
            switch_tab(state, state["shop_tab"] - 1)
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            buy(state)
            return

        selected = state["shop_selected"]
        if event.key in (pygame.K_LEFT, pygame.K_a):
            selected -= 1
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            selected += 1
        elif event.key in (pygame.K_UP, pygame.K_w):
            selected -= COLUMNS
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            selected += COLUMNS
        selected = max(0, min(len(items) - 1, selected))
        if selected != state["shop_selected"]:
            sound.play("menu_move")
        state["shop_selected"] = selected
        keep_in_view(state)

    if ui.back_clicked(events):
        state["screen"] = "menu"
        return
    tab = ui.clicked(events, tab_rects())
    if tab is not None:
        switch_tab(state, tab)
        return
    if ui.clicked(events, [ACTION]) is not None:
        buy(state)
        return

    # the mouse only selects on click, otherwise the panel changes while you move to the buy button
    tiles = visible_tiles(state)
    tile = ui.clicked(events, [rect for _, rect in tiles])
    if tile is not None:
        sound.play("menu_move")
        state["shop_selected"] = tiles[tile][0]
        state["message"] = ""

    scroll = state["shop_scroll"] + ui.wheel(events)
    state["shop_scroll"] = max(0, min(max_scroll(state), scroll))


def draw_tile(screen, state, item, rect, selected, hover):
    bp = state["bp"]
    if selected:
        ui.glow(screen, rect, ui.YELLOW, alpha=40)
        ui.card(screen, rect, ui.YELLOW, ui.tint(ui.YELLOW, 0.2))
    elif hover:
        ui.card(screen, rect, ui.GREY, ui.tint(ui.GREY, 0.12))
    else:
        ui.card(screen, rect, ui.BORDER)

    icon = reward_icon(item, state["menu_time"])
    sprites.draw_centered(screen, icon, (rect.centerx, rect.y + 42))

    lines = wrap_text(item["name"], 20, rect.w - 12)[:2]
    y = rect.y + 74 if len(lines) == 1 else rect.y + 66
    for line in lines:
        ui.text(screen, line, 20, ui.WHITE, (rect.centerx, y), "center")
        y += 16

    label, color = item_status(bp, item)
    if color == ui.COIN:
        coin = sprites.scaled(sprites.get("coin"), 0.6)
        width = sprites.font(20).size(label)[0] + coin.get_width() + 4
        x = rect.centerx - width / 2
        screen.blit(coin, (x, rect.bottom - 24))
        ui.text(screen, label, 20, ui.COIN, (x + coin.get_width() + 4, rect.bottom - 22))
    else:
        ui.badge(screen, label, (rect.centerx, rect.bottom - 26), color, "center", 16)


def draw_detail(screen, state, item):
    bp = state["bp"]
    t = state["menu_time"]
    ui.card(screen, DETAIL, ui.BORDER, shadow=True)
    kinds = {"skin": "SKIN", "bullet": "BULLETS", "perk": "PERK"}
    ui.text(screen, kinds[item["type"]], 18, ui.DIM, (DETAIL.x + 20, DETAIL.y + 18))

    center = (DETAIL.centerx, DETAIL.y + 110)
    sprites.draw_glow(screen, 70, (60, 50, 110), center)
    icon = reward_icon(item, t)
    if item["type"] == "skin":
        icon = sprites.scaled(icon, 2.5)
    else:
        icon = sprites.scaled(icon, 2)
    sprites.draw_centered(screen, icon, center)

    y = DETAIL.y + 190
    for line in wrap_text(item["name"], 34, DETAIL.w - 40)[:2]:
        ui.text(screen, line, 34, ui.WHITE, (DETAIL.centerx, y), "center")
        y += 28
    if item["type"] == "skin":
        desc = "A new look for your hero"
    elif item["type"] == "bullet":
        desc = "Changes how your bullets look"
    else:
        desc = item["desc"]
    y += 6
    for line in wrap_text(desc, 22, DETAIL.w - 40):
        ui.text(screen, line, 22, ui.GREY, (DETAIL.centerx, y), "center")
        y += 20

    equipped = progress.is_equipped(bp, item)
    owned = progress.owns(bp, item)
    if equipped:
        label, accent, disabled = "Equipped", ui.GREEN, True
    elif owned and item["type"] == "perk":
        label, accent, disabled = "Active every run", ui.GREEN, True
    elif owned:
        label, accent, disabled = "Equip", ui.GREEN, False
    elif item["achievement"]:
        label, accent, disabled = "Locked", ui.GREY, True
        name = achievements.find(item["achievement"])["name"]
        ui.lock(screen, (DETAIL.centerx, ACTION.y - 34), ui.DIM)
        ui.text(screen, f"Unlock: {name}", 22, ui.PURPLE, (DETAIL.centerx, ACTION.y - 22), "center")
    else:
        enough = bp["coins"] >= item["price"]
        label, accent, disabled = f"Buy for {item['price']}", ui.YELLOW, not enough
        if not enough:
            missing = item["price"] - bp["coins"]
            ui.text(screen, f"{missing} coins short", 22, ui.RED, (DETAIL.centerx, ACTION.y - 22), "center")
    ui.center_button(screen, ACTION, label, not disabled, accent, 28, disabled)


def draw_screen(screen, state):
    bp = state["bp"]
    ui.draw_background(screen, state, 190)
    ui.title(screen, "Shop", 60, ui.YELLOW, 18)
    draw_coins(screen, bp["coins"])
    ui.tabs(screen, tab_rects(), [label for _, label in TABS], state["shop_tab"])

    items = tab_items(state)
    hover = ui.hovered([rect for _, rect in visible_tiles(state)])
    for n, (i, rect) in enumerate(visible_tiles(state)):
        draw_tile(screen, state, items[i], rect, i == state["shop_selected"], n == hover)
    rows = (len(items) + COLUMNS - 1) // COLUMNS
    ui.scrollbar(screen, (GRID_X + COLUMNS * (TILE_W + 12) + 4, GRID_Y, 6, ROWS * (TILE_H + 12) - 12),
                 state["shop_scroll"], ROWS, rows)
    draw_detail(screen, state, items[state["shop_selected"]])

    if state["message"]:
        color = ui.RED if state["message"] in BAD_MESSAGES else ui.GREEN
        ui.text(screen, state["message"], 26, color, (DETAIL.centerx, DETAIL.bottom + 16), "center", True)

    ui.back_button(screen)
    ui.footer(screen, [("WASD", "Browse"), ("Enter", "Buy / equip"), ("Tab", "Category"), ("Esc", "Back")])


SCREENS = {
    "shop": (handle_input, draw_screen),
}

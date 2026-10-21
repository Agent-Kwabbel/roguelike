import pygame

import battlepass
import challenges
from enemy import spawn_boss
from menus import text_center, panel, YELLOW, GREY
from settings import W, H, WEAPONS, MAX_WEAPONS, WEAPON_MAX_LEVEL, BP_XP_PER_TIER
from weapons import make_weapon
import sprites

is_open = False
selected = 0
god = False
message = ""


# ---------- in de run ----------

def toggle_god(state):
    global god
    god = not god
    return "God mode aan" if god else "God mode uit"


def level_up(state):
    player = state["player"]
    player.level += 1
    player.pending_upgrades += 1
    return f"Level {player.level}"


def full_heal(state):
    state["player"].heal(state["player"].max_hp)
    return "Volledig genezen"


def add_boss(state):
    player = state["player"]
    state["enemies"].append(spawn_boss(player.pos, state["time"], state["difficulty"], state["world"]))
    return "Baas gespawnd"


def kill_all(state):
    for enemy in state["enemies"]:
        enemy.hp = 0
    return f"{len(state['enemies'])} vijanden gedood"


def skip_minute(state):
    state["time"] += 60
    return "+1 minuut"


def new_weapon(state):
    player = state["player"]
    if len(player.weapons) >= MAX_WEAPONS:
        return "Maximaal aantal wapens"
    for key in WEAPONS:
        if not player.has_weapon(key):
            player.weapons.append(make_weapon(key))
            return f"{WEAPONS[key]['name']} gekregen"
    return "Je hebt alle wapens al"


def max_weapons(state):
    for weapon in state["player"].weapons:
        weapon.level = WEAPON_MAX_LEVEL
    return "Wapens op max level"


def run_coins(state):
    state["stats"]["coins"] += 100
    return "+100 coins (na de run)"


# ---------- in het menu ----------

def add_coins(state):
    state["bp"]["coins"] += 1000
    battlepass.save(state["bp"])
    return "+1000 coins"


def add_tier(state):
    bp = state["bp"]
    battlepass.add_xp(bp, BP_XP_PER_TIER)
    battlepass.save(bp)
    return f"Tier {battlepass.current_tier(bp)}"


def toggle_premium(state):
    bp = state["bp"]
    bp["premium"] = not bp["premium"]
    battlepass.grant_rewards(bp)
    battlepass.save(bp)
    return "Premium aan" if bp["premium"] else "Premium uit"


def reset_save(state):
    bp = state["bp"]
    bp.clear()
    bp.update(battlepass.new_data())
    challenges.refresh(bp)
    battlepass.save(bp)
    return "Save gereset"


GAME_OPTIONS = [
    ("God mode aan/uit", toggle_god),
    ("+1 level", level_up),
    ("Volledig genezen", full_heal),
    ("Spawn baas", add_boss),
    ("Dood alle vijanden", kill_all),
    ("+1 minuut", skip_minute),
    ("Nieuw wapen", new_weapon),
    ("Wapens max level", max_weapons),
    ("+100 coins", run_coins),
]

MENU_OPTIONS = [
    ("+1000 coins", add_coins),
    ("+1 Battle Pass tier", add_tier),
    ("Premium aan/uit", toggle_premium),
    ("Save resetten", reset_save),
]


def current_options(state):
    if state["screen"] == "game":
        return GAME_OPTIONS
    return MENU_OPTIONS


def handle_input(state, events):
    """Geeft True terug als het dev menu de input heeft gebruikt."""
    global is_open, selected, message
    options = current_options(state)
    selected = min(selected, len(options) - 1)
    used = is_open
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_F1:
            is_open = not is_open
            message = ""
            used = True
        elif not is_open:
            continue
        elif event.key == pygame.K_ESCAPE:
            is_open = False
        elif event.key == pygame.K_UP:
            selected = (selected - 1) % len(options)
        elif event.key == pygame.K_DOWN:
            selected = (selected + 1) % len(options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            message = options[selected][1](state)
    return used


def draw(screen, state):
    if not is_open:
        if god and state["screen"] == "game":
            tag = sprites.font(24).render("GOD", True, YELLOW)
            screen.blit(tag, (W - tag.get_width() - 10, 84))
        return

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    options = current_options(state)
    height = 110 + len(options) * 36
    top = H / 2 - height / 2
    panel(screen, (W / 2 - 180, top, 360, height), YELLOW)
    text_center(screen, "Dev menu", 40, YELLOW, top + 12)
    for i, (label, _) in enumerate(options):
        y = top + 60 + i * 36
        if label.startswith("God") and god:
            label += " (aan)"
        if i == selected:
            pygame.draw.rect(screen, (70, 60, 30), (W / 2 - 160, y - 4, 320, 32), border_radius=8)
            text_center(screen, label, 28, YELLOW, y)
        else:
            text_center(screen, label, 28, (220, 220, 220), y)
    bottom = top + height - 40
    if message:
        text_center(screen, message, 24, (120, 230, 120), bottom - 4)
    else:
        text_center(screen, "Pijltjes, Enter: doen, F1/Esc: sluiten", 22, GREY, bottom)

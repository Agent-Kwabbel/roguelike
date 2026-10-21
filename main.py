import math
import random

import pygame

from settings import (
    W,
    H,
    FPS,
    SPAWN_INTERVAL,
    SPAWN_INTERVAL_MIN,
    SPAWN_INTERVAL_DECAY,
    MAX_ENEMIES,
    DIFFICULTIES,
    BOSS_INTERVAL,
    SPLIT_INTO,
    SPLIT_COUNT,
    BOMB_RANGE,
    BOMB_BOSS_DAMAGE,
    CHEST_COINS,
    LOOT_COIN_VALUE,
    COINS_PER_KILLS,
    WEAPONS,
    EXPLODE_RADIUS,
    FREEZE_TIME,
    BOOTS_TIME,
    POTION_TIME,
    STREAK_TIME,
    STREAK_TEXTS,
    REVIVE_COST,
    DAY_LENGTH,
    NIGHT_DARKNESS,
)
from player import Player
from enemy import spawn_enemy, spawn_boss, split, heal_nearby
from orb import Orb
from pickup import Pickup, random_drop
from upgrades import pick_choices
from world import World
from menus import init_menu, init_slots, format_time, text_center, panel, wrap_text
from pet import Pet
import achievements
import assistant
import battlepass
import challenges
import config
import dev
import effects
import events
import gemstore
import menus
import saves
import settings_menu
import sprites
import ui

SCREENS = {}
SCREENS.update(menus.SCREENS)
SCREENS.update(gemstore.SCREENS)
SCREENS.update(achievements.SCREENS)

# deze vijanden lopen om naar de deur als je binnen bent
PATH_AI = ("chase", "dasher", "zigzag", "exploder", "mimic")
# hier staat linksboven een terug knop
BACK_SCREENS = ("battlepass", "challenges", "shop", "gemstore", "achievements")
PAUSE_BUTTONS = ["Verder spelen", "Instellingen", "Opslaan en naar menu", "Run opgeven"]


def init_game(difficulty_key, bp, world, resume=None):
    """Maak de beginstaat van het spel aan. Met resume gaat een opgeslagen run verder."""
    difficulty = DIFFICULTIES[difficulty_key]
    player = Player(
        difficulty["player_hp"],
        battlepass.skin_sprite(bp),
        battlepass.bullet_sprite(bp),
    )
    battlepass.apply_perks(bp, player)
    effects.clear()
    if resume:
        # de boosters zijn bij het begin van de run al gebruikt
        boost_xp = resume["boost_xp"]
        boost_coins = resume["boost_coins"]
    else:
        boost_xp = bp["boosters"]["xp"] > 0
        boost_coins = bp["boosters"]["coins"] > 0
        if boost_xp:
            bp["boosters"]["xp"] -= 1
            player.xp_mult *= 2
        if boost_coins:
            bp["boosters"]["coins"] -= 1
        battlepass.save(bp)
    assistant.say("start", force=True)
    state = {
        "running": True,
        "screen": "game",
        "difficulty_key": difficulty_key,
        "difficulty": difficulty,
        "player": player,
        "enemies": [],
        "bullets": [],
        "enemy_bullets": [],
        "orbs": [],
        "pickups": [],
        "spawn_timer": 0,
        "time": 0,
        "next_boss": BOSS_INTERVAL,
        "camera": pygame.Vector2(0, 0),
        "choices": None,
        "paused": False,
        "pause_page": "main",
        "pause_selected": 0,
        "confirm_selected": 1,
        "quit_run": False,
        "flash": 0,
        "world": world,
        "bp": bp,
        "stats": {"kills": 0, "bosses": 0, "elites": 0, "pickups": 0, "chests": 0, "coins": 0,
                  "best_streak": 0, "revived": False},
        "pet": Pet(player.pos) if bp["pet"] else None,
        "freeze": 0,
        "streak": 0,
        "streak_timer": 0,
        "revive_prompt": False,
        "boost_xp": boost_xp,
        "boost_coins": boost_coins,
        "achievement_timer": 2,
    }
    events.init(state)
    return state


def continue_run(state):
    data = saves.load_run()
    if data is None:
        state["run_info"] = None
        state["continue"] = False
        return state
    new_state = init_game(data["difficulty_key"], state["bp"], World(data["seed"]), resume=data)
    saves.apply_run(new_state, data)
    return new_state


def quit_game(state):
    # een lopende run wordt bewaard, behalve als je al dood bent
    if state["screen"] == "game":
        if state["revive_prompt"] or state["player"].hp <= 0:
            end_run(state)
        else:
            saves.save_run(state)
    state["running"] = False


def handle_input(state):
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            quit_game(state)
            return state
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            assistant.toggle()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            config.toggle_fullscreen()
        if event.type == pygame.WINDOWFOCUSLOST and state["screen"] == "game":
            if not state["choices"] and not state["revive_prompt"]:
                state["paused"] = True
                state["pause_page"] = "main"

    # zonder save kan het dev menu niks
    if state["bp"] is not None and dev.handle_input(state, events):
        if state["screen"] == "game":
            state["player"].move = pygame.Vector2(0, 0)
        return state

    if state["screen"] == "menu" and state["popup"]:
        gemstore.handle_popup(state, events)
        return state

    if state["screen"] in SCREENS:
        if state["screen"] in BACK_SCREENS and ui.back_clicked(events) and not gem_overlay(state):
            state["screen"] = "menu"
            return state
        handle_screen = SCREENS[state["screen"]][0]
        handle_screen(state, events)
        if state["start"]:
            saves.delete_run()
            return init_game(state["start"], state["bp"], World())
        if state["continue"]:
            return continue_run(state)
        return state

    if state["paused"] and not state["revive_prompt"]:
        state["player"].move = pygame.Vector2(0, 0)
        return handle_pause(state, events)
    if state["choices"]:
        choice = ui.clicked(events, upgrade_rects(state["choices"]))
        if choice is not None:
            state["choices"][choice]["apply"](state["player"])
            state["choices"] = None

    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if state["revive_prompt"]:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                revive(state)
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                state["revive_prompt"] = False
                state["quit_run"] = True
        elif state["choices"]:
            keys = [pygame.K_1, pygame.K_2, pygame.K_3]
            if event.key in keys:
                index = keys.index(event.key)
                if index < len(state["choices"]):
                    state["choices"][index]["apply"](state["player"])
                    state["choices"] = None
        elif event.key in (pygame.K_ESCAPE, pygame.K_p):
            state["paused"] = True
            state["pause_page"] = "main"
            state["pause_selected"] = 0
        elif event.key == pygame.K_SPACE:
            state["player"].dash()
    state["player"].read_input()
    return state


def gem_overlay(state):
    # tijdens betalen, reclame of een lootbox kan je niet weg
    return state.get("gem_pay") or state.get("gem_ad") or state.get("gem_box")


def handle_pause(state, events):
    page = state["pause_page"]
    if page == "settings":
        if settings_menu.handle(events):
            state["pause_page"] = "main"
        return state
    if page == "confirm":
        state["confirm_selected"], answer = ui.handle_confirm(events, state["confirm_selected"])
        if answer:
            state["paused"] = False
            state["quit_run"] = True
        elif answer is not None:
            state["pause_page"] = "main"
        return state

    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            state["paused"] = False
            return state
        if event.key == pygame.K_q:
            state["pause_page"] = "confirm"
            state["confirm_selected"] = 1
            return state
    state["pause_selected"], chosen = ui.navigate(events, state["pause_selected"], pause_rects())
    if chosen == 0:
        state["paused"] = False
    elif chosen == 1:
        state["pause_page"] = "settings"
    elif chosen == 2:
        saves.save_run(state)
        effects.clear()
        return init_menu(state["bp"], state["world"])
    elif chosen == 3:
        state["pause_page"] = "confirm"
        state["confirm_selected"] = 1
    return state


def revive(state):
    bp = state["bp"]
    player = state["player"]
    bp["gems"] -= REVIVE_COST
    battlepass.save(bp)
    state["revive_prompt"] = False
    state["stats"]["revived"] = True
    player.hp = player.max_hp
    player.invis_timer = 3
    # alles in de buurt wegblazen zodat je niet meteen weer dood gaat
    for enemy in state["enemies"]:
        if enemy.kind != "boss" and player.pos.distance_to(enemy.pos) < 300:
            enemy.hurt(enemy.hp)
    state["flash"] = 0.3
    effects.announce("TERUG VAN WEGGEWEEST", (230, 120, 230), 54)


def update(state, dt):
    achievements.update(dt)
    assistant.update(dt)
    if state["screen"] != "game":
        state["menu_time"] += dt
        gemstore.update(state, dt)
        if state["screen"] == "menu":
            assistant.say("menu", chance=0.01)
        return state
    if state["quit_run"]:
        return end_run(state)
    if state["choices"] or state["paused"] or dev.is_open or state["revive_prompt"]:
        return state

    player = state["player"]
    difficulty = state["difficulty"]
    world = state["world"]
    player.update(dt)
    world.collide(player.pos, player.radius)
    state["camera"] = player.pos - pygame.Vector2(W / 2, H / 2)

    state["time"] += dt
    interval = max(
        SPAWN_INTERVAL_MIN, SPAWN_INTERVAL - state["time"] * SPAWN_INTERVAL_DECAY
    )
    interval *= difficulty["spawn"]
    state["spawn_timer"] += dt
    if state["spawn_timer"] >= interval:
        state["spawn_timer"] = 0
        if len(state["enemies"]) < MAX_ENEMIES:
            state["enemies"].append(spawn_enemy(player.pos, state["time"], difficulty, world))

    if state["time"] >= state["next_boss"]:
        state["next_boss"] += BOSS_INTERVAL
        state["enemies"].append(spawn_boss(player.pos, state["time"], difficulty, world))
        effects.add_text(player.pos + (0, -70), "Een baas komt eraan!", (240, 70, 70), 40)
        effects.announce("BAAS!", (240, 70, 70), 80)
        assistant.say("boss", force=True)

    events.update(state, dt)
    state["bullets"] += player.update_weapons(dt, state["enemies"])
    update_enemies(state, dt)
    if state["pet"]:
        state["pet"].update(dt, player, state["orbs"])
    pickups, orbs = world.update(dt, player.pos)
    state["pickups"] += pickups
    state["orbs"] += orbs
    for bullet in state["bullets"] + state["enemy_bullets"]:
        bullet.update(dt)
    for orb in state["orbs"]:
        orb.update(dt, player.pos, player.pickup_range)
    for pickup in state["pickups"]:
        pickup.update(dt)
    effects.update(dt)
    state["flash"] = max(0, state["flash"] - dt)
    state["freeze"] = max(0, state["freeze"] - dt)
    state["streak_timer"] -= dt
    if state["streak_timer"] <= 0:
        state["streak"] = 0

    handle_collisions(state)
    assistant_hints(state)

    state["achievement_timer"] -= dt
    if state["achievement_timer"] <= 0:
        state["achievement_timer"] = 2
        achievements.check(run_stats(state), state["bp"])

    if player.pending_upgrades > 0:
        player.pending_upgrades -= 1
        state["choices"] = pick_choices(player)
        assistant.say("level_up", chance=0.4)

    if player.hp <= 0:
        if not state["stats"]["revived"] and state["bp"]["gems"] >= REVIVE_COST:
            state["revive_prompt"] = True
            return state
        return end_run(state)
    return state


def update_enemies(state, dt):
    player = state["player"]
    world = state["world"]
    # als de speler binnen is lopen vijanden om naar de deur
    home = world.building_at(player.pos)
    enemy_dt = dt * events.enemy_speed(state)
    spawned = []
    for enemy in state["enemies"]:
        if state["freeze"] > 0:
            continue
        target = player.pos
        if home and enemy.ai in PATH_AI:
            target = home.path_target(enemy.pos, player.pos)
        old_pos = enemy.pos.copy()
        state["enemy_bullets"] += enemy.update(enemy_dt, enemy.steer(target))
        # spoken gaan overal doorheen
        if enemy.ai != "ghost":
            world.collide(enemy.pos, enemy.radius)
        enemy.check_stuck(old_pos, target, dt)
        if enemy.spawned:
            spawned += enemy.spawned
            enemy.spawned = []
        if enemy.heal_ready:
            heal_nearby(enemy, state["enemies"])
    room = MAX_ENEMIES - len(state["enemies"])
    state["enemies"] += spawned[:max(0, room)]


def assistant_hints(state):
    player = state["player"]
    if player.hp <= 1:
        assistant.say("low_hp", chance=0.02)
    if len(state["enemies"]) > 80:
        assistant.say("crowd", chance=0.005)
    if player.still_time > 6:
        assistant.say("idle", chance=0.01)


def run_stats(state):
    stats = state["stats"]
    stats["time"] = state["time"]
    stats["level"] = state["player"].level
    stats["weapons"] = len(state["player"].weapons)
    if state["difficulty_key"] == "extreme":
        stats["extreme_time"] = state["time"]
    return stats


def end_run(state):
    bp = state["bp"]
    player = state["player"]
    stats = run_stats(state)
    stats["runs"] = 1
    if state["difficulty_key"] in ("hard", "extreme"):
        stats["hard_time"] = state["time"]

    coins = stats["kills"] // COINS_PER_KILLS + stats["coins"]
    if state["boost_coins"]:
        coins *= 2
    bp["coins"] += coins
    for key in ("kills", "elites", "runs"):
        bp["totals"][key] = bp["totals"].get(key, 0) + stats.get(key, 0)
    achievements.check(stats, bp)
    if player.hp <= 0:
        assistant.say("death", force=True)
    bp_xp = battlepass.run_xp(state["time"], stats["kills"], player.level)
    challenge_xp, finished = challenges.update(bp, stats)
    new_tiers = battlepass.add_xp(bp, bp_xp + challenge_xp)
    battlepass.save(bp)
    saves.delete_run()
    last_run = {
        "difficulty": state["difficulty"]["name"],
        "time": state["time"],
        "level": player.level,
        "kills": stats["kills"],
        "coins": coins,
        "bp_xp": bp_xp + challenge_xp,
        "new_tiers": new_tiers,
        "tier": battlepass.current_tier(bp),
        "finished": finished,
    }
    return init_menu(bp, state["world"], last_run)


def bullet_hits(state):
    for bullet in state["bullets"]:
        for enemy in state["enemies"]:
            if enemy.hp <= 0:
                continue
            if bullet.pos.distance_to(enemy.pos) < bullet.radius + enemy.radius:
                if bullet.hit_enemy(enemy):
                    enemy.hurt(bullet.damage, bullet.crit)
                    if bullet.life <= 0:
                        break


def enemy_hits(state):
    if dev.god:
        return
    player = state["player"]
    damage = state["difficulty"]["enemy_damage"]
    for enemy in state["enemies"]:
        if enemy.hp <= 0 or not enemy.awake:
            continue
        if player.pos.distance_to(enemy.pos) < player.radius + enemy.radius:
            if player.take_damage(damage) and player.thorns > 0:
                enemy.hurt(player.thorns)
    for bullet in state["enemy_bullets"]:
        if player.pos.distance_to(bullet.pos) < player.radius + bullet.radius:
            player.take_damage(damage)
            bullet.life = 0


def use_pickup(state, kind):
    player = state["player"]
    state["stats"]["pickups"] += 1
    if kind == "heart":
        player.heal(1)
        effects.add_text(player.pos + (0, -30), "+1 HP", (240, 90, 90), 28)
    elif kind == "magnet":
        for orb in state["orbs"]:
            orb.magnet = True
        effects.add_text(player.pos + (0, -30), "Magneet!", (120, 200, 255), 28)
    elif kind == "bomb":
        state["flash"] = 0.25
        for enemy in state["enemies"]:
            if player.pos.distance_to(enemy.pos) > BOMB_RANGE:
                continue
            if enemy.kind == "boss":
                enemy.hurt(BOMB_BOSS_DAMAGE)
            else:
                enemy.hurt(enemy.hp)
    elif kind == "chest":
        state["stats"]["chests"] += 1
        state["stats"]["coins"] += CHEST_COINS
        player.pending_upgrades += 1
        effects.add_text(player.pos + (0, -30), f"+{CHEST_COINS} coins", (240, 200, 60), 28)
    elif kind == "coin":
        state["stats"]["coins"] += LOOT_COIN_VALUE
        effects.add_text(player.pos + (0, -30), f"+{LOOT_COIN_VALUE} coins", (240, 200, 60), 24)
    elif kind == "freeze":
        state["freeze"] = FREEZE_TIME
        effects.add_text(player.pos + (0, -30), "Bevroren!", (150, 210, 255), 28)
    elif kind == "boots":
        player.boots_timer = BOOTS_TIME
        effects.add_text(player.pos + (0, -30), "Snelle schoenen!", (255, 220, 80), 28)
    elif kind == "potion":
        player.potion_timer = POTION_TIME
        effects.add_text(player.pos + (0, -30), "Dubbele XP!", (120, 230, 120), 28)
    if kind != "coin":
        assistant.say("pickup", chance=0.3)


def collect(state):
    player = state["player"]
    for orb in state["orbs"]:
        if player.pos.distance_to(orb.pos) < player.radius + orb.radius:
            player.add_xp(orb.value * events.xp_mult(state))
            orb.value = 0
    for pickup in state["pickups"]:
        if player.pos.distance_to(pickup.pos) < player.radius + pickup.radius:
            use_pickup(state, pickup.kind)
            pickup.life = 0


def explode(state, enemy):
    effects.burst(enemy.pos, (255, 140, 40), 20)
    effects.burst(enemy.pos, (80, 80, 80), 10)
    effects.shake(10)
    state["flash"] = max(state["flash"], 0.1)
    player = state["player"]
    if not dev.god and player.pos.distance_to(enemy.pos) < EXPLODE_RADIUS:
        player.take_damage(state["difficulty"]["enemy_damage"])
    # andere vijanden krijgen ook wat
    for other in state["enemies"]:
        if other is not enemy and other.hp > 0 and other.pos.distance_to(enemy.pos) < EXPLODE_RADIUS:
            other.hurt(5)


def add_streak(state):
    state["streak"] += 1
    state["streak_timer"] = STREAK_TIME
    stats = state["stats"]
    stats["best_streak"] = max(stats["best_streak"], state["streak"])
    if state["streak"] in STREAK_TEXTS:
        effects.announce(STREAK_TEXTS[state["streak"]])
        effects.shake(min(12, 2 + state["streak"] / 10))
        if state["streak"] >= 25:
            assistant.say("streak", chance=0.5)


def enemy_deaths(state):
    stats = state["stats"]
    player = state["player"]
    spawned = []
    for enemy in state["enemies"]:
        if enemy.hp > 0:
            continue
        if enemy.exploded:
            # zelf ontploft telt niet als kill
            explode(state, enemy)
            continue
        state["orbs"].append(Orb(enemy.pos, enemy.xp))
        stats["kills"] += 1
        add_streak(state)
        effects.burst(enemy.pos, enemy.color)
        if player.lifesteal > 0 and random.random() < player.lifesteal and player.hp < player.max_hp:
            player.heal(1)
            effects.add_text(player.pos + (0, -30), "+1", (240, 90, 90), 22)
        if events.coin_drops(state) and random.random() < 0.3:
            state["pickups"].append(Pickup("coin", enemy.pos))
        if enemy.kind in ("boss", "mimic", "king_slime"):
            if enemy.kind == "boss":
                stats["bosses"] += 1
            state["pickups"].append(Pickup("chest", enemy.pos))
        elif enemy.elite:
            stats["elites"] += 1
            state["pickups"].append(Pickup("chest", enemy.pos))
        else:
            drop = random_drop(enemy.pos, state["player"].luck)
            if drop:
                state["pickups"].append(drop)
        if enemy.kind in SPLIT_INTO:
            spawned += split(enemy, SPLIT_INTO[enemy.kind], SPLIT_COUNT[enemy.kind])
    state["enemies"] = [e for e in state["enemies"] if e.hp > 0] + spawned


def handle_collisions(state):
    bullet_hits(state)
    enemy_hits(state)
    collect(state)
    enemy_deaths(state)
    state["orbs"] = [o for o in state["orbs"] if o.value > 0]
    state["bullets"] = [b for b in state["bullets"] if b.life > 0]
    state["enemy_bullets"] = [b for b in state["enemy_bullets"] if b.life > 0]
    state["pickups"] = [p for p in state["pickups"] if p.life > 0]


def draw_hp(screen, player):
    for i in range(player.max_hp):
        name = "heart" if i < player.hp else "heart_empty"
        screen.blit(sprites.get(name), (10 + i * 30, 10))


def draw_weapons(screen, player):
    for i, weapon in enumerate(player.weapons):
        x = 10 + i * 46
        pygame.draw.rect(screen, (30, 28, 45), (x, 44, 40, 40), border_radius=6)
        pygame.draw.rect(screen, (90, 90, 120), (x, 44, 40, 40), 2, border_radius=6)
        icon = sprites.get(WEAPONS[weapon.key]["icon"])
        factor = 28 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), (x + 20, 64))
        level = sprites.font(20).render(str(weapon.level), True, (250, 220, 60))
        screen.blit(level, (x + 40 - level.get_width() - 3, 44 + 40 - 15))


def draw_xp(screen, player):
    pygame.draw.rect(screen, (30, 30, 50), (0, H - 12, W, 12))
    width = W * player.xp / player.xp_needed()
    pygame.draw.rect(screen, (80, 220, 240), (0, H - 12, width, 12))
    text = sprites.font(26).render(f"Level {player.level}", True, (255, 255, 255))
    screen.blit(text, (10, H - 38))


def draw_time(screen, state):
    text = sprites.font(36).render(format_time(state["time"]), True, (255, 255, 255))
    screen.blit(text, (W - text.get_width() - 10, 10))
    label = sprites.font(24).render(state["difficulty"]["name"], True, (200, 200, 200))
    screen.blit(label, (W - label.get_width() - 10, 40))
    kills = sprites.font(24).render(f"{state['stats']['kills']} kills", True, (200, 200, 200))
    screen.blit(kills, (W - kills.get_width() - 10, 62))


def draw_boss_bar(screen, enemies):
    for enemy in enemies:
        if enemy.kind == "boss":
            pygame.draw.rect(screen, (40, 15, 20), (W / 2 - 200, 14, 400, 16), border_radius=8)
            pygame.draw.rect(screen, (220, 40, 50), (W / 2 - 200, 14, 400 * enemy.hp / enemy.max_hp, 16), border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), (W / 2 - 200, 14, 400, 16), 2, border_radius=8)
            text_center(screen, "Baas", 22, (255, 255, 255), 34)
            return


def upgrade_rects(choices):
    left = W / 2 - (len(choices) * 270 - 20) / 2
    return [pygame.Rect(left + i * 270, 210, 250, 250) for i in range(len(choices))]


def draw_upgrade_menu(screen, choices):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    text_center(screen, "Kies een upgrade", 52, (255, 255, 255), 130)

    left = W / 2 - (len(choices) * 270 - 20) / 2
    hover = ui.hovered(upgrade_rects(choices))
    for i, upgrade in enumerate(choices):
        x = left + i * 270
        if i == hover:
            panel(screen, (x, 205, 250, 250), (255, 255, 255), 4)
        else:
            panel(screen, (x, 210, 250, 250), (250, 220, 60))
        text_center(screen, str(i + 1), 32, (250, 220, 60), 222, x + 125)
        icon = sprites.get(upgrade["icon"])
        factor = 64 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), (x + 125, 300))
        lines = wrap_text(upgrade["name"], 28, 230)
        y = 350
        for line in lines:
            text_center(screen, line, 28, (255, 255, 255), y, x + 125)
            y += 24
        for line in wrap_text(upgrade["desc"], 22, 230):
            text_center(screen, line, 22, (190, 190, 200), y + 6, x + 125)
            y += 20
    text_center(screen, "Klik of druk op 1, 2 of 3", 26, (190, 190, 200), 490)


def draw_status(screen, state):
    player = state["player"]
    lines = []
    if state["event"]:
        info = events.EVENTS[state["event"]]
        lines.append((f"{info['name']} {int(state['event_time'])}s", info["color"]))
    if state["freeze"] > 0:
        lines.append((f"Bevroren {state['freeze']:.0f}s", (150, 210, 255)))
    if player.boots_timer > 0:
        lines.append((f"Snelle schoenen {player.boots_timer:.0f}s", (255, 220, 80)))
    if player.potion_timer > 0:
        lines.append((f"Dubbele XP {player.potion_timer:.0f}s", (120, 230, 120)))
    if state["boost_xp"]:
        lines.append(("Booster: dubbele XP", (230, 120, 230)))
    if state["boost_coins"]:
        lines.append(("Booster: dubbele coins", (230, 120, 230)))
    if player.can_dash:
        if player.dash_cooldown > 0:
            lines.append((f"Dash {player.dash_cooldown:.1f}s", GREY_TEXT))
        else:
            lines.append(("Dash klaar (spatie)", (200, 220, 255)))
    if state["streak"] >= 2:
        lines.append((f"Streak x{state['streak']}", (255, 200, 60)))
    for i, (text, color) in enumerate(lines):
        image = sprites.font(22).render(text, True, color)
        screen.blit(image, (10, 92 + i * 20))


GREY_TEXT = (170, 170, 180)


def draw_night(screen, state, camera):
    phase = (state["time"] % DAY_LENGTH) / DAY_LENGTH
    darkness = max(0, -math.cos(phase * 2 * math.pi))
    alpha = int(darkness * NIGHT_DARKNESS)
    if alpha < 5:
        return
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((10, 10, 40, alpha))
    # een licht cirkeltje rond de speler
    center = state["player"].pos - camera
    for i in range(6):
        pygame.draw.circle(overlay, (10, 10, 40, int(alpha * (5 - i) / 6)), center, 190 - i * 25)
    screen.blit(overlay, (0, 0))


def draw_revive(screen, state):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((40, 0, 0, 190))
    screen.blit(overlay, (0, 0))
    text_center(screen, "Je bent dood!", 72, (240, 80, 80), 170)
    text_center(screen, f"Doorgaan voor {REVIVE_COST} gems?", 44, (230, 120, 230), 260)
    text_center(screen, f"Je hebt {state['bp']['gems']} gems", 28, (200, 200, 200), 310)
    text_center(screen, "Enter: ja graag, Esc: nee, laat me maar dood", 28, (200, 200, 200), 380)


def pause_rects():
    return [pygame.Rect(W / 2 - 180, 250 + i * 62, 360, 52) for i in range(len(PAUSE_BUTTONS))]


def draw_pause(screen, state):
    ui.blur(screen)
    if state["pause_page"] == "settings":
        settings_menu.draw(screen)
        return
    ui.card(screen, (W / 2 - 220, 110, 440, 420), (90, 90, 120))
    ui.title(screen, "Pauze", 72, ui.WHITE, 130)
    line = f"{format_time(state['time'])}  -  level {state['player'].level}  -  {state['stats']['kills']} kills"
    text_center(screen, line, 26, ui.GREY, 200)
    accents = [(120, 220, 130), ui.YELLOW, ui.YELLOW, (240, 110, 110)]
    for i, rect in enumerate(pause_rects()):
        ui.button(screen, rect, PAUSE_BUTTONS[i], i == state["pause_selected"], accents[i])
    text_center(screen, "Esc: verder spelen", 22, ui.GREY, 545)
    if state["pause_page"] == "confirm":
        ui.draw_confirm(screen, "Run opgeven?", "Je krijgt wel je coins en BP XP", state["confirm_selected"])


def draw_game(screen, state):
    camera = state["camera"] + effects.shake_offset()
    state["world"].draw(screen, camera)
    for pickup in state["pickups"]:
        pickup.draw(screen, camera, state["time"])
    for orb in state["orbs"]:
        orb.draw(screen, camera, state["time"])
    frozen = state["freeze"] > 0
    for enemy in sorted(state["enemies"], key=lambda e: e.pos.y):
        enemy.draw(screen, camera, frozen)
    for bullet in state["bullets"]:
        bullet.draw(screen, camera)
    if state["pet"]:
        state["pet"].draw(screen, camera)
    state["player"].draw(screen, camera)
    for bullet in state["enemy_bullets"]:
        bullet.draw(screen, camera)
    events.draw(screen, camera, state)
    state["world"].draw_roofs(screen, camera)
    effects.draw(screen, camera)
    draw_night(screen, state, camera)
    events.draw_overlay(screen, state)
    effects.draw_banners(screen)

    if state["flash"] > 0:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, int(state["flash"] * 600)))
        screen.blit(overlay, (0, 0))

    draw_hp(screen, state["player"])
    draw_weapons(screen, state["player"])
    draw_xp(screen, state["player"])
    draw_time(screen, state)
    draw_boss_bar(screen, state["enemies"])
    draw_status(screen, state)
    if state["revive_prompt"]:
        draw_revive(screen, state)
    elif state["choices"]:
        draw_upgrade_menu(screen, state["choices"])
    elif state["paused"]:
        draw_pause(screen, state)


def draw(screen, state):
    if state["screen"] in SCREENS:
        draw_screen = SCREENS[state["screen"]][1]
        draw_screen(screen, state)
        if state["screen"] == "menu" and state["popup"]:
            gemstore.draw_popup(screen, state)
        if state["screen"] in BACK_SCREENS and not gem_overlay(state):
            ui.back_button(screen)
    else:
        draw_game(screen, state)
    # in de andere menus staat hij in de weg
    if state["screen"] in ("menu", "game"):
        assistant.draw(screen)
    achievements.draw_toasts(screen)
    if state["bp"] is not None:
        dev.draw(screen, state)
    if config.get("show_fps"):
        text = sprites.font(22).render(f"{fps:.0f} FPS", True, (200, 255, 200))
        screen.blit(text, (W - text.get_width() - 10, H - 34))
    pygame.display.flip()


fps = 0


def main():
    global fps
    pygame.init()
    saves.migrate()
    config.load()
    pygame.display.set_mode((W, H), config.window_flags())
    pygame.display.set_caption("roguelike")
    sprites.load_all()
    clock = pygame.time.Clock()

    last_slot = config.get("last_slot")
    if last_slot and saves.slot_info(last_slot):
        saves.slot = last_slot
        state = init_menu(battlepass.load(), World())
    else:
        state = init_slots(World())
    while state["running"]:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        fps = clock.get_fps()
        state = handle_input(state)
        state = update(state, dt)
        # na F11 kan het scherm een nieuw surface zijn
        draw(pygame.display.get_surface(), state)
    pygame.quit()


if __name__ == "__main__":
    main()

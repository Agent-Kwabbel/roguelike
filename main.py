import math
import random

import pygame

from settings import (
    W,
    H,
    FPS,
    DIFFICULTIES,
    BOSS_INTERVAL,
    BOSS_ORDER,
    BOSS_NAMES,
    PHASES,
    REAPER_TIME,
    REAPER_DAMAGE,
    WIN_COINS,
    PHASE_COINS,
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
    NIGHT_DARKNESS,
    DASH_COOLDOWN_PLAYER,
    COOP_SPAWN_BONUS,
    COOP_COIN_BONUS,
    SHARED_XP,
    SHARED_XP_RANGE,
    TEAM_RANGE,
    BOSS_FOCUS_TIME,
    COOP_COLORS,
    CHOICE_TIME,
    REVIVE_TIME,
)
from player import Player
from enemy import Enemy, spawn_enemy, spawn_boss, spawn_position, split, heal_nearby, vampire_bite
from orb import Orb
from pickup import Pickup, random_drop
from upgrades import pick_choices
from world import World
from menus import init_menu, init_slots, format_time, text_center, wrap_text
import achievements
import ambient
import config
import coop
import effects
import events
import lobby
import menus
import phases
import progress
import saves
import settings_menu
import shop
import sound
import sprites
import ui

SCREENS = {}
SCREENS.update(menus.SCREENS)
SCREENS.update(achievements.SCREENS)
SCREENS.update(shop.SCREENS)
SCREENS.update(lobby.SCREENS)

# these enemies walk around to the door when you're inside
PATH_AI = ("chase", "dasher", "zigzag", "exploder", "mimic")
# and these go straight through walls and mountains
FLYING_AI = ("ghost", "blinker", "reaper")
BOSS_AI = ("boss", "reaper")
PAUSE_BUTTONS = ["Resume", "Settings", "Save and quit to menu", "Give up run"]
ONLINE_PAUSE_BUTTONS = ["Resume", "Settings", "Leave game"]


def init_game(difficulty_key, bp, world):
    """Create the starting state of the game."""
    difficulty = DIFFICULTIES[difficulty_key]
    player = Player(
        difficulty["player_hp"],
        progress.skin_sprite(bp),
        progress.bullet_sprite(bp),
    )
    progress.apply_perks(bp, player)
    player.color = COOP_COLORS[0]
    effects.clear()
    state = {
        "running": True,
        "screen": "game",
        "difficulty_key": difficulty_key,
        "difficulty": difficulty,
        "player": player,
        "players": [player],
        "online": None,
        "enemies": [],
        "bullets": [],
        "enemy_bullets": [],
        "orbs": [],
        "pickups": [],
        "spawn_timer": 0,
        "time": 0,
        "next_boss": BOSS_INTERVAL,
        "boss_count": 0,
        "phase": 0,
        "reaper": False,
        "camera": pygame.Vector2(0, 0),
        "choices": None,
        "choice_selected": 0,
        "paused": False,
        "pause_page": "main",
        "pause_selected": 0,
        "confirm_selected": 1,
        "quit_run": False,
        "flash": 0,
        "world": world,
        "bp": bp,
        "stats": {"kills": 0, "bosses": 0, "elites": 0, "pickups": 0, "chests": 0, "coins": 0,
                  "best_streak": 0},
        "freeze": 0,
        "spawn_turn": 0,
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
    new_state = init_game(data["difficulty_key"], state["bp"], World(data["seed"]))
    saves.apply_run(new_state, data)
    return new_state


def quit_game(state):
    # a running run gets saved, unless you're already dead
    if state["screen"] == "game":
        if state["online"] or state["player"].hp <= 0:
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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            config.toggle_fullscreen()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if state["screen"] == "game" and not state["paused"] and not state["choices"]:
                sound.play("menu_select")
            else:
                sound.play("menu_back")
        if event.type == pygame.WINDOWFOCUSLOST and state["screen"] == "game":
            if not state["choices"] and not state["online"]:
                state["paused"] = True
                state["pause_page"] = "main"

    if state["screen"] in SCREENS:
        handle_screen = SCREENS[state["screen"]][0]
        handle_screen(state, events)
        if state["start"]:
            saves.delete_run()
            return init_game(state["start"], state["bp"], World())
        if state["continue"]:
            return continue_run(state)
        if state.get("start_online"):
            return start_online(state, state["start_online"])
        return state

    if state["paused"]:
        state["player"].move = pygame.Vector2(0, 0)
        return handle_pause(state, events)
    if state["choices"]:
        handle_choices(state, events)
        return state

    if state["player"].choices:
        handle_online_choices(state, events)
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            state["paused"] = True
            state["pause_page"] = "main"
            state["pause_selected"] = 0
        elif event.key == pygame.K_SPACE and not state["player"].downed:
            if state["player"].dash() and state["online"] == "client":
                state["dashed"] = True
    state["player"].read_input()
    return state


def start_online(state, info):
    start = info["start"]
    new_state = init_game(start["difficulty"], state["bp"], World(start["seed"]))
    coop.setup(new_state, info)
    return new_state


def handle_online_choices(state, events):
    # no A/D here, you still walk around with those
    player = state["player"]
    keys = [pygame.K_1, pygame.K_2, pygame.K_3]
    chosen = None
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in keys and keys.index(event.key) < len(player.choices):
            chosen = keys.index(event.key)
    rects = upgrade_rects(player.choices, True)
    for event in events:
        if event.type == pygame.MOUSEMOTION:
            index = ui.hovered(rects, event.pos)
            if index is not None:
                state["choice_selected"] = index
    if chosen is None:
        chosen = ui.clicked(events, rects)
    if chosen is None:
        return
    sound.play("pick")
    if state["online"] == "host":
        coop.pick(player, chosen)
    else:
        state["pick"] = chosen
        player.choices = None


def handle_choices(state, events):
    choices = state["choices"]
    state["player"].move = pygame.Vector2(0, 0)
    keys = [pygame.K_1, pygame.K_2, pygame.K_3]
    chosen = None
    for event in events:
        if event.type == pygame.KEYDOWN and event.key in keys and keys.index(event.key) < len(choices):
            chosen = keys.index(event.key)
    if chosen is None:
        state["choice_selected"], chosen = ui.navigate(events, state["choice_selected"], upgrade_rects(choices),
                                                       columns=len(choices))
    if chosen is not None:
        choices[chosen]["apply"](state["player"])
        state["choices"] = None
        sound.play("pick")


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
    buttons = pause_buttons(state)
    state["pause_selected"], chosen = ui.navigate(events, state["pause_selected"], pause_rects(buttons))
    if chosen is None:
        return state
    label = buttons[chosen]
    if label == "Resume":
        state["paused"] = False
    elif label == "Settings":
        state["pause_page"] = "settings"
    elif label == "Save and quit to menu":
        saves.save_run(state)
        effects.clear()
        return init_menu(state["bp"], state["world"])
    else:
        state["pause_page"] = "confirm"
        state["confirm_selected"] = 1
    return state


def pause_buttons(state):
    if state["online"]:
        return ONLINE_PAUSE_BUTTONS
    return PAUSE_BUTTONS


def update(state, dt):
    achievements.update(dt)
    sound.update(dt)
    if state["screen"] != "game":
        sound.music("menu")
        sound.duck(False)
        state["menu_time"] += dt
        ambient.update(dt)
        return state
    if any(enemy.ai in BOSS_AI for enemy in state["enemies"]):
        sound.music("boss")
    else:
        sound.music("run")
    sound.duck(state["choices"] or state["paused"])
    if state["quit_run"]:
        return end_run(state)
    if state["online"] == "client":
        if coop.client_update(state, dt):
            return end_run(state)
        return state
    if state["choices"] or (state["paused"] and not state["online"]):
        return state

    if state["online"]:
        coop.read_clients(state)
    player = state["player"]
    players = state["players"]
    world = state["world"]
    ambient.update(dt)
    for p in players:
        p.update(dt)
        if not p.remote:
            world.collide(p.pos, p.radius)
    state["camera"] = player.pos - pygame.Vector2(W / 2, H / 2)

    state["time"] += dt
    update_spawns(state, dt)
    events.update(state, dt)
    for p in alive_players(state):
        bullets = p.update_weapons(dt, state["enemies"])
        for bullet in bullets:
            bullet.owner = p
        state["bullets"] += bullets
    update_enemies(state, dt)
    for p in players:
        p.hunted = any(e.focus is p for e in state["enemies"] if e.ai == "boss")
    for p in players:
        pickups, orbs = world.loot_near(p.pos)
        state["pickups"] += pickups
        state["orbs"] += orbs
    world.update_roofs(dt, player.pos)
    for bullet in state["bullets"] + state["enemy_bullets"]:
        bullet.update(dt)
    for orb in state["orbs"]:
        target = nearest_player(state, orb.pos)
        orb.update(dt, target.pos, target.pickup_range)
    for pickup in state["pickups"]:
        pickup.update(dt)
    effects.update(dt)
    state["flash"] = max(0, state["flash"] - dt)
    state["freeze"] = max(0, state["freeze"] - dt)
    for p in players:
        p.streak_timer -= dt
        if p.streak_timer <= 0:
            p.streak = 0

    handle_collisions(state)

    state["achievement_timer"] -= dt
    if state["achievement_timer"] <= 0:
        state["achievement_timer"] = 2
        achievements.check(run_stats(state), state["bp"])

    if state["online"]:
        coop.update_choices(state, dt)
        coop.update_revive(state, dt)
        coop.update_team(state, dt)
    elif player.pending_upgrades > 0:
        player.pending_upgrades -= 1
        chest = player.chest_upgrades > 0
        if chest:
            player.chest_upgrades -= 1
        state["choices"] = pick_choices(player, chest)
        state["choice_selected"] = 0
        sound.play("level_up")

    for p in players:
        if p.hp <= 0 and not p.downed:
            p.downed = True
            p.choices = None
            if state["online"]:
                effects.burst(p.pos, (240, 80, 80), 20)
                effects.announce(f"{p.name} is down!", (240, 80, 80), 40)
    if not alive_players(state):
        return end_run(state)
    if state["online"]:
        coop.send_snapshot(state, dt)
    return state


def update_spawns(state, dt):
    index = phases.index(state)
    if index > state["phase"]:
        state["phase"] = index
        phase = PHASES[index]
        effects.announce(phase["name"], phase["color"], 70)
        effects.add_text(state["player"].pos + (0, -70), "It gets harder...", phase["color"], 30)
        sound.play("event")

    interval = phases.blend(state, "spawn") * state["difficulty"]["spawn"] * events.spawn_mult(state)
    # more players, more enemies
    interval /= 1 + COOP_SPAWN_BONUS * (len(state["players"]) - 1)
    state["spawn_timer"] += dt
    if state["spawn_timer"] >= interval:
        state["spawn_timer"] = 0
        center = next_player(state).pos
        for _ in range(phases.current(state)["pack"]):
            if len(state["enemies"]) < phases.max_enemies(state):
                state["enemies"].append(spawn_enemy(state, center))

    if state["time"] >= state["next_boss"]:
        state["next_boss"] += BOSS_INTERVAL
        center = random_player(state).pos
        count = 1
        if phases.current(state).get("double_boss"):
            count = 2
        names = []
        for _ in range(count):
            kind = BOSS_ORDER[state["boss_count"] % len(BOSS_ORDER)]
            # with two bosses in co-op they come from different players
            state["enemies"].append(spawn_boss(state, next_player(state).pos, kind))
            state["boss_count"] += 1
            names.append(BOSS_NAMES[kind])
        effects.add_text(center + (0, -70), " and ".join(names) + "!", (240, 70, 70), 40)
        effects.announce("BOSS!", (240, 70, 70), 80)
        sound.play("boss")

    if state["time"] >= REAPER_TIME and not state["reaper"]:
        state["reaper"] = True
        for p in alive_players(state):
            state["enemies"].append(Enemy("reaper", spawn_position(state, p.pos)))
        effects.announce(BOSS_NAMES["reaper"], (200, 30, 40), 100)
        effects.add_text(state["player"].pos + (0, -70), "You survived! Now it's over...", (240, 70, 70), 34)
        sound.play("boss")


def alive_players(state):
    return [p for p in state["players"] if not p.downed]


def next_player(state):
    """Takes turns, so every player gets the same amount of enemies."""
    alive = alive_players(state)
    if not alive:
        return state["player"]
    state["spawn_turn"] = (state["spawn_turn"] + 1) % len(alive)
    return alive[state["spawn_turn"]]


def random_player(state):
    alive = alive_players(state)
    if alive:
        return random.choice(alive)
    return state["player"]


def nearest_player(state, pos):
    best = None
    for p in alive_players(state):
        if best is None or p.pos.distance_to(pos) < best.pos.distance_to(pos):
            best = p
    if best is None:
        return state["player"]
    return best


def enemy_target(state, enemy, dt):
    alive = alive_players(state)
    if enemy.ai != "boss" or len(alive) < 2:
        return nearest_player(state, enemy.pos)
    # in co-op a boss goes after one player at a time
    enemy.focus_timer -= dt
    if enemy.focus not in alive or enemy.focus_timer <= 0:
        enemy.focus_timer = BOSS_FOCUS_TIME
        enemy.focus = random.choice(alive)
        name = BOSS_NAMES.get(enemy.kind, "The boss")
        effects.add_text(enemy.focus.pos + (0, -60), f"{name} is after {enemy.focus.name}!", (240, 80, 80), 26)
    return enemy.focus


def update_enemies(state, dt):
    world = state["world"]
    enemy_dt = dt * events.enemy_speed(state)
    spawned = []
    for enemy in state["enemies"]:
        if state["freeze"] > 0:
            continue
        target_player = enemy_target(state, enemy, dt)
        target = target_player.pos
        # when the player is inside, enemies walk around to the door
        home = world.building_at(target)
        if home and enemy.ai in PATH_AI:
            target = home.path_target(enemy.pos, target)
        old_pos = enemy.pos.copy()
        state["enemy_bullets"] += enemy.update(enemy_dt, enemy.steer(target))
        # ghosts go through everything
        if enemy.ai not in FLYING_AI:
            world.collide(enemy.pos, enemy.radius)
        enemy.check_stuck(old_pos, target, dt)
        if enemy.spawned:
            spawned += enemy.spawned
            enemy.spawned = []
        for pos in enemy.puddles:
            events.lava_puddle(state, pos)
        enemy.puddles = []
        if enemy.heal_ready:
            heal_nearby(enemy, state["enemies"])
    room = phases.max_enemies(state) - len(state["enemies"])
    state["enemies"] += spawned[:max(0, room)]


def run_stats(state):
    stats = state["stats"]
    stats["time"] = state["time"]
    stats["level"] = state["player"].level
    stats["weapons"] = len(state["player"].weapons)
    stats["best_streak"] = state["player"].best_streak
    stats["revives"] = state["player"].revives
    if state["online"]:
        stats["online"] = 1
    stats["phase"] = state["phase"]
    stats["evolved"] = len([w for w in state["player"].weapons if w.evolved])
    if state["difficulty_key"] in ("extreme", "nightmare"):
        stats["extreme_time"] = state["time"]
    return stats


def end_run(state):
    bp = state["bp"]
    player = state["player"]
    stats = run_stats(state)
    stats["runs"] = 1
    if state["difficulty_key"] in ("hard", "extreme", "nightmare"):
        stats["hard_time"] = state["time"]
    won = state["time"] >= REAPER_TIME
    if won:
        stats["won"] = 1
        stats["won_" + state["difficulty_key"]] = 1

    if state["online"]:
        coop.stop(state)
    coins = stats["kills"] // COINS_PER_KILLS + stats["coins"] + player.bonus_coins
    coins += PHASE_COINS * state["phase"]
    if won:
        coins += WIN_COINS
    if state["online"]:
        coins = round(coins * (1 + COOP_COIN_BONUS * (len(state["players"]) - 1)))
    bp["coins"] += coins
    for key in ("kills", "elites", "runs", "revives"):
        bp["totals"][key] = bp["totals"].get(key, 0) + stats.get(key, 0)
    new = achievements.check(stats, bp)
    progress.save(bp)
    # an online run never touches your saved run
    if not state["online"]:
        saves.delete_run()
    last_run = {
        "difficulty": state["difficulty"]["name"],
        "difficulty_key": state["difficulty_key"],
        "died": player.hp <= 0,
        "won": won,
        "time": state["time"],
        "level": player.level,
        "kills": stats["kills"],
        "coins": coins,
        "achievements": [a["name"] for a in new],
    }
    if state.get("host_left"):
        last_run["note"] = "The host left the game"
    if player.hp <= 0:
        sound.play("game_over")
    menu = init_menu(bp, state["world"], last_run)
    menu["screen"] = "results"
    return menu


def bullet_hits(state):
    for bullet in state["bullets"]:
        for enemy in state["enemies"]:
            if enemy.hp <= 0:
                continue
            if bullet.pos.distance_to(enemy.pos) < bullet.radius + enemy.radius:
                if bullet.hit_enemy(enemy):
                    enemy.hurt(bullet.damage, bullet.crit)
                    enemy.last_hit = bullet.owner
                    if bullet.life <= 0:
                        break


def enemy_hits(state):
    damage = phases.enemy_damage(state)
    for player in alive_players(state):
        for enemy in state["enemies"]:
            if enemy.hp <= 0 or not enemy.awake or enemy.spawn_time > 0:
                continue
            if player.pos.distance_to(enemy.pos) < player.radius + enemy.radius:
                if enemy.ai == "reaper":
                    player.take_damage(REAPER_DAMAGE, True)
                    continue
                if not player.take_damage(damage):
                    continue
                if player.thorns > 0:
                    enemy.hurt(player.thorns + player.damage)
                    enemy.last_hit = player
                if enemy.affix == "vampiric":
                    vampire_bite(enemy, state["enemies"])
        for bullet in state["enemy_bullets"]:
            if bullet.life > 0 and player.pos.distance_to(bullet.pos) < player.radius + bullet.radius:
                player.take_damage(damage)
                bullet.life = 0


def use_pickup(state, kind, player):
    state["stats"]["pickups"] += 1
    sound.play(kind)
    if kind == "heart":
        player.heal(1)
        effects.add_text(player.pos + (0, -30), "+1 HP", (240, 90, 90), 28)
    elif kind == "magnet":
        for orb in state["orbs"]:
            orb.magnet = True
        effects.add_text(player.pos + (0, -30), "Magnet!", (120, 200, 255), 28)
    elif kind == "bomb":
        state["flash"] = 0.25
        for enemy in state["enemies"]:
            if player.pos.distance_to(enemy.pos) > BOMB_RANGE:
                continue
            if enemy.ai in BOSS_AI:
                enemy.hurt(BOMB_BOSS_DAMAGE)
            else:
                enemy.hurt(enemy.hp, true_damage=True)
    elif kind == "chest":
        state["stats"]["chests"] += 1
        state["stats"]["coins"] += CHEST_COINS
        player.pending_upgrades += 1
        player.chest_upgrades += 1
        effects.add_text(player.pos + (0, -30), f"+{CHEST_COINS} coins", (240, 200, 60), 28)
    elif kind == "coin":
        state["stats"]["coins"] += LOOT_COIN_VALUE
        effects.add_text(player.pos + (0, -30), f"+{LOOT_COIN_VALUE} coins", (240, 200, 60), 24)
    elif kind == "freeze":
        state["freeze"] = FREEZE_TIME
        effects.add_text(player.pos + (0, -30), "Frozen!", (150, 210, 255), 28)
    elif kind == "boots":
        player.boots_timer = BOOTS_TIME
        effects.add_text(player.pos + (0, -30), "Speed boots!", (255, 220, 80), 28)
    elif kind == "potion":
        player.potion_timer = POTION_TIME
        effects.add_text(player.pos + (0, -30), "Double XP!", (120, 230, 120), 28)


def share_xp(state, player, amount):
    for other in alive_players(state):
        if other is not player and other.pos.distance_to(player.pos) < SHARED_XP_RANGE:
            other.add_xp(amount * SHARED_XP)


def collect(state):
    for player in alive_players(state):
        for orb in state["orbs"]:
            if orb.value > 0 and player.pos.distance_to(orb.pos) < player.radius + orb.radius:
                player.add_xp(orb.value * events.xp_mult(state))
                share_xp(state, player, orb.value * events.xp_mult(state))
                orb.value = 0
                if player.remote:
                    sound.play("xp0")
                else:
                    sound.play_xp()
        for pickup in state["pickups"]:
            if pickup.life > 0 and player.pos.distance_to(pickup.pos) < player.radius + pickup.radius:
                use_pickup(state, pickup.kind, player)
                pickup.life = 0


def explode(state, enemy):
    effects.burst(enemy.pos, (255, 140, 40), 20)
    effects.burst(enemy.pos, (80, 80, 80), 10)
    effects.shake(10)
    sound.play("explosion")
    state["flash"] = max(state["flash"], 0.1)
    for player in alive_players(state):
        if player.pos.distance_to(enemy.pos) < EXPLODE_RADIUS:
            player.take_damage(phases.enemy_damage(state))
    # other enemies get hit too
    for other in state["enemies"]:
        if other is not enemy and other.hp > 0 and other.pos.distance_to(enemy.pos) < EXPLODE_RADIUS:
            other.hurt(5)


def add_streak(state, player):
    player.streak += 1
    player.streak_timer = STREAK_TIME
    player.best_streak = max(player.best_streak, player.streak)
    # every player has their own streak, online players see theirs on their own computer
    if player is state["player"] and player.streak in STREAK_TEXTS:
        effects.announce(STREAK_TEXTS[player.streak], local=True)
        sound.play_streak(player.streak)
        effects.shake(min(12, 2 + player.streak / 10), local=True)


def enemy_deaths(state):
    stats = state["stats"]
    spawned = []
    for enemy in state["enemies"]:
        if enemy.hp > 0:
            continue
        if enemy.exploded:
            # blowing yourself up doesn't count as a kill
            explode(state, enemy)
            continue
        state["orbs"].append(Orb(enemy.pos, enemy.xp))
        stats["kills"] += 1
        effects.burst(enemy.pos, enemy.color, 12)
        effects.ring(enemy.pos, (255, 255, 255), enemy.radius * 2)
        if enemy.ai == "boss":
            sound.play("boss_dead")
        else:
            sound.play("kill")
        player = enemy.last_hit
        if player is None or player not in state["players"]:
            player = nearest_player(state, enemy.pos)
        add_streak(state, player)
        if player.lifesteal_kills and not player.downed:
            player.kill_counter += 1
            if player.kill_counter >= player.lifesteal_kills:
                player.kill_counter = 0
                if player.hp < player.max_hp:
                    player.heal(1)
                    effects.add_text(player.pos + (0, -30), "+1", (240, 90, 90), 22)
        if events.coin_drops(state) and random.random() < 0.3:
            state["pickups"].append(Pickup("coin", enemy.pos))
        if enemy.affix == "volatile":
            # a warning ring first, then it blows up
            events.add_hazard(state, enemy.pos, EXPLODE_RADIUS, 0.3, (255, 140, 40), 0.8)
        if enemy.ai == "boss" or enemy.kind in ("mimic", "king_slime"):
            if enemy.ai == "boss":
                stats["bosses"] += 1
                stats["beat_" + enemy.kind] = 1
            state["pickups"].append(Pickup("chest", enemy.pos))
        elif enemy.elite:
            stats["elites"] += 1
            state["pickups"].append(Pickup("chest", enemy.pos))
        else:
            drop = random_drop(enemy.pos, player.luck)
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


def hud_panel(screen, rect):
    ui.card(screen, rect, (60, 58, 85), (14, 12, 24, 170), radius=10)


def draw_player_panel(screen, player):
    hearts_width = player.max_hp * 28
    weapons_width = len(player.weapons) * 42
    hud_panel(screen, (8, 8, max(hearts_width, weapons_width) + 16, 88))
    for i in range(player.max_hp):
        name = "heart" if i < player.hp else "heart_empty"
        screen.blit(sprites.get(name), (16 + i * 28, 16))

    for i, weapon in enumerate(player.weapons):
        x = 16 + i * 42
        pygame.draw.rect(screen, (30, 28, 45), (x, 48, 38, 38), border_radius=6)
        pygame.draw.rect(screen, (90, 90, 120), (x, 48, 38, 38), 2, border_radius=6)
        icon = sprites.get(WEAPONS[weapon.key]["icon"])
        factor = 26 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), (x + 19, 67))
        if weapon.evolved:
            pygame.draw.rect(screen, ui.YELLOW, (x, 48, 38, 38), 2, border_radius=6)
            level = sprites.font(18).render("*", True, ui.YELLOW)
        else:
            level = sprites.font(18).render(str(weapon.level), True, ui.YELLOW)
        screen.blit(level, (x + 38 - level.get_width() - 3, 48 + 38 - 13))


def draw_xp(screen, player):
    fraction = player.xp / player.xp_needed()
    pygame.draw.rect(screen, (14, 12, 24), (0, H - 14, W, 14))
    pygame.draw.rect(screen, (40, 120, 150), (0, H - 14, W * fraction, 14))
    pygame.draw.rect(screen, (110, 230, 250), (0, H - 14, W * fraction, 4))
    rect = pygame.Rect(W / 2 - 50, H - 40, 100, 30)
    ui.card(screen, rect, (110, 230, 250), (14, 12, 24, 220), radius=15)
    ui.text(screen, f"Level {player.level}", 24, ui.WHITE, (rect.centerx, rect.y + 8), "center")


def draw_time(screen, state):
    rect = pygame.Rect(W - 168, 8, 160, 88)
    hud_panel(screen, rect)
    ui.text(screen, format_time(state["time"]), 44, ui.WHITE, (rect.right - 12, rect.y + 10), "right")
    color = menus.DIFFICULTY_COLORS.get(state["difficulty_key"], ui.YELLOW)
    ui.badge(screen, state["difficulty"]["name"], (rect.x + 12, rect.y + 60), color, size=16)
    ui.text(screen, f"{state['stats']['kills']} kills", 22, ui.GREY, (rect.right - 12, rect.y + 62), "right")


def draw_boss_bar(screen, enemies):
    bosses = [e for e in enemies if e.ai == "boss"]
    y = 12
    for enemy in bosses[:3]:
        rect = pygame.Rect(W / 2 - 200, y + 22, 400, 16)
        name = BOSS_NAMES.get(enemy.kind, "BOSS")
        if enemy.enraged:
            name += " (enraged)"
        ui.text(screen, name, 24, (240, 90, 90), (W / 2, y), "center", True)
        ui.progress_bar(screen, rect, enemy.hp / enemy.max_hp, (220, 40, 50), (40, 15, 20))
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        y += 48


def upgrade_rects(choices, online=False):
    if online:
        # smaller and lower, the game keeps going behind it
        left = W / 2 - (len(choices) * 236 - 16) / 2
        return [pygame.Rect(left + i * 236, H - 226, 220, 170) for i in range(len(choices))]
    left = W / 2 - (len(choices) * 270 - 20) / 2
    return [pygame.Rect(left + i * 270, 200, 250, 300) for i in range(len(choices))]


def draw_upgrade_menu(screen, state):
    choices = state["choices"]
    ui.darken(screen, 170)
    ui.title(screen, "LEVEL UP!", 72, ui.YELLOW, 84)
    text_center(screen, "Choose an upgrade", 28, ui.GREY, 150)

    for i, upgrade in enumerate(choices):
        rect = upgrade_rects(choices)[i]
        active = i == state["choice_selected"]
        if active:
            rect.y -= 10
            ui.glow(screen, rect, ui.YELLOW, spread=8)
            ui.card(screen, rect, ui.YELLOW, ui.tint(ui.YELLOW, 0.22), shadow=True)
        else:
            ui.card(screen, rect, ui.BORDER, shadow=True)
        ui.keycap(screen, str(i + 1), (rect.x + 12, rect.y + 12))
        if upgrade.get("new"):
            ui.badge(screen, "NEW WEAPON", (rect.right - 12, rect.y + 12), ui.GREEN, "right", 18)

        center = (rect.centerx, rect.y + 96)
        pygame.draw.circle(screen, (36, 34, 54), center, 46)
        pygame.draw.circle(screen, ui.YELLOW if active else ui.BORDER, center, 46, 2)
        icon = sprites.get(upgrade["icon"])
        factor = 56 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), center)

        y = rect.y + 158
        for line in wrap_text(upgrade["name"], 30, rect.w - 24):
            ui.text(screen, line, 30, ui.YELLOW if active else ui.WHITE, (rect.centerx, y), "center")
            y += 26
        y += 8
        for line in wrap_text(upgrade["desc"], 24, rect.w - 32):
            ui.text(screen, line, 24, ui.GREY, (rect.centerx, y), "center")
            y += 22
    ui.footer(screen, [("A/D", "Choose"), ("Enter", "Pick"), ("1-3", "Quick pick"), ("Mouse", "Click a card")])


def draw_online_choices(screen, state):
    player = state["player"]
    choices = player.choices
    rects = upgrade_rects(choices, True)
    top = rects[0].y
    ui.text(screen, "LEVEL UP! Pick with 1 2 3 or click", 28, ui.YELLOW, (W / 2, top - 44), "center", True)
    bar = pygame.Rect(W / 2 - 160, top - 14, 320, 6)
    ui.progress_bar(screen, bar, max(0, player.choice_timer) / CHOICE_TIME, ui.YELLOW)
    for i, upgrade in enumerate(choices):
        rect = rects[i]
        active = i == state["choice_selected"]
        if active:
            ui.card(screen, rect, ui.YELLOW, ui.tint(ui.YELLOW, 0.22))
        else:
            ui.card(screen, rect, ui.BORDER, (22, 20, 34, 220))
        ui.keycap(screen, str(i + 1), (rect.x + 10, rect.y + 10))
        if upgrade.get("new"):
            ui.badge(screen, "NEW", (rect.right - 10, rect.y + 10), ui.GREEN, "right", 16)
        center = (rect.centerx, rect.y + 48)
        pygame.draw.circle(screen, (36, 34, 54), center, 30)
        icon = sprites.get(upgrade["icon"])
        factor = 38 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), center)
        y = rect.y + 88
        for line in wrap_text(upgrade["name"], 26, rect.w - 20):
            ui.text(screen, line, 26, ui.YELLOW if active else ui.WHITE, (rect.centerx, y), "center")
            y += 22
        y += 4
        for line in wrap_text(upgrade["desc"], 20, rect.w - 24):
            ui.text(screen, line, 20, ui.GREY, (rect.centerx, y), "center")
            y += 18


def draw_teammate_arrows(screen, state, camera):
    """An arrow at the edge of the screen for every teammate you can't see."""
    center = pygame.Vector2(W / 2, H / 2)
    for p in state["players"]:
        if p is state["player"]:
            continue
        pos = p.pos - camera
        if 0 <= pos.x <= W and 0 <= pos.y <= H:
            continue
        direction = pos - center
        if direction.length() == 0:
            continue
        direction = direction.normalize()
        # walk from the middle until we hit the edge (with some room)
        scale = min((W / 2 - 70) / max(abs(direction.x), 0.001), (H / 2 - 80) / max(abs(direction.y), 0.001))
        tip = center + direction * scale
        color = (240, 80, 80) if p.downed else p.color
        side = direction.rotate(90)
        points = [tip + direction * 14, tip - direction * 10 + side * 11, tip - direction * 10 - side * 11]
        pygame.draw.polygon(screen, (0, 0, 0), [pt + (2, 2) for pt in points])
        pygame.draw.polygon(screen, color, points)
        label = p.name + (" - revive!" if p.downed else "")
        ui.text(screen, label, 18, color, tip - direction * 30 + (0, -8), "center", True)


def status_chips(state):
    """List of (text, colour, fraction of time left or None)."""
    player = state["player"]
    chips = []
    index = phases.index(state)
    phase = PHASES[index]
    if index + 1 < len(PHASES):
        part = (phases.effective_time(state) - phase["start"]) / (PHASES[index + 1]["start"] - phase["start"])
        chips.append((phase["name"], phase["color"], 1 - part))
    else:
        left = max(0, phases.reaper_time_left(state))
        chips.append((f"{phase['name']} - reaper in {format_time(left)}", phase["color"], None))
    if player.downed:
        chips.append(("You are down! A teammate can revive you", (240, 80, 80), player.revive_timer / REVIVE_TIME))
    if state["event"]:
        info = events.EVENTS[state["event"]]
        chips.append((f"{info['name']} {int(state['event_time'])}s", info["color"], state["event_time"] / info["time"]))
    if state["freeze"] > 0:
        chips.append((f"Frozen {state['freeze']:.0f}s", (150, 210, 255), state["freeze"] / FREEZE_TIME))
    if player.boots_timer > 0:
        chips.append((f"Speed boots {player.boots_timer:.0f}s", (255, 220, 80), player.boots_timer / BOOTS_TIME))
    if player.potion_timer > 0:
        chips.append((f"Double XP {player.potion_timer:.0f}s", (120, 230, 120), player.potion_timer / POTION_TIME))
    if player.can_dash:
        if player.dash_cooldown > 0:
            chips.append(("Dash", ui.GREY, 1 - player.dash_cooldown / DASH_COOLDOWN_PLAYER))
        else:
            chips.append(("Dash ready (space)", (200, 220, 255), None))
    if player.streak >= 2:
        chips.append((f"Streak x{player.streak}", (255, 200, 60), max(0, player.streak_timer) / STREAK_TIME))
    if player.team_bonus:
        chips.append(("Team spirit: faster weapons", (140, 230, 255), None))
    return chips


def draw_status(screen, state):
    y = 104
    for label, color, fraction in status_chips(state):
        image = sprites.font(22).render(label, True, color)
        rect = pygame.Rect(8, y, image.get_width() + 20, 30)
        hud_panel(screen, rect)
        screen.blit(image, (rect.x + 10, rect.y + 6))
        if fraction is not None:
            ui.progress_bar(screen, (rect.x + 8, rect.bottom - 6, rect.w - 16, 3), fraction, color)
        y += 36


def draw_night(screen, state, camera):
    darkness = ambient.darkness(state["time"])
    # a warm orange glow around sunrise and sunset
    sunset = max(0, 1 - abs(darkness - 0.15) / 0.2)
    if sunset > 0:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((255, 120, 40, int(sunset * 45)))
        screen.blit(overlay, (0, 0))
    alpha = int(darkness * NIGHT_DARKNESS)
    if alpha < 5:
        return
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((10, 10, 40, alpha))
    # a circle of light around every player
    for p in state["players"]:
        center = p.pos - camera
        for i in range(6):
            pygame.draw.circle(overlay, (10, 10, 40, int(alpha * (5 - i) / 6)), center, 190 - i * 25)
    screen.blit(overlay, (0, 0))


def pause_rects(buttons):
    return [pygame.Rect(W / 2 - 330, 230 + i * 62, 340, 52) for i in range(len(buttons))]


def draw_pause(screen, state):
    ui.blur(screen)
    if state["pause_page"] == "settings":
        settings_menu.draw(screen)
        return
    player = state["player"]
    ui.card(screen, (W / 2 - 350, 90, 380, 410), ui.BORDER, (22, 20, 34, 235), shadow=True)
    ui.title(screen, "Menu" if state["online"] else "Paused", 72, ui.WHITE, 112, W / 2 - 160)
    text_center(screen, f"{state['difficulty']['name']} run", 24, ui.GREY, 176, W / 2 - 160)
    buttons = pause_buttons(state)
    accents = [ui.GREEN, ui.YELLOW, ui.YELLOW, ui.RED]
    if state["online"]:
        accents = [ui.GREEN, ui.YELLOW, ui.RED]
    for i, rect in enumerate(pause_rects(buttons)):
        ui.button(screen, rect, buttons[i], i == state["pause_selected"], accents[i])

    rect = pygame.Rect(W / 2 + 50, 90, 300, 410)
    ui.card(screen, rect, ui.BORDER, (22, 20, 34, 235), shadow=True)
    ui.text(screen, "THIS RUN", 18, ui.DIM, (rect.x + 20, rect.y + 20))
    stats = [("Time", format_time(state["time"])), ("Level", player.level),
             ("Kills", state["stats"]["kills"]), ("Coins found", state["stats"]["coins"]),
             ("Best streak", player.best_streak)]
    y = rect.y + 46
    for label, value in stats:
        ui.text(screen, label, 22, ui.GREY, (rect.x + 20, y))
        ui.text(screen, value, 24, ui.WHITE, (rect.right - 20, y - 1), "right")
        y += 28
    y += 10
    ui.text(screen, "WEAPONS", 18, ui.DIM, (rect.x + 20, y))
    y += 24
    for weapon in player.weapons:
        info = WEAPONS[weapon.key]
        icon = sprites.get(info["icon"])
        factor = 24 / max(icon.get_width(), icon.get_height())
        sprites.draw_centered(screen, sprites.scaled(icon, factor), (rect.x + 34, y + 10))
        ui.text(screen, info["name"], 22, ui.WHITE, (rect.x + 56, y + 2))
        if weapon.evolved:
            ui.text(screen, "EVOLVED", 18, ui.YELLOW, (rect.right - 20, y + 4), "right")
        else:
            ui.text(screen, f"lvl {weapon.level}", 22, ui.YELLOW, (rect.right - 20, y + 2), "right")
        y += 30

    ui.footer(screen, [("W/S", "Move"), ("Enter", "Select"), ("Esc", "Resume"), ("Q", "Give up")])
    if state["pause_page"] == "confirm" and state["online"]:
        ui.draw_confirm(screen, "Leave this game?", "You still keep your coins", state["confirm_selected"])
    elif state["pause_page"] == "confirm":
        ui.draw_confirm(screen, "Give up this run?", "You still keep your coins", state["confirm_selected"])


def draw_team_links(screen, state, camera):
    """A soft line between teammates that have team spirit."""
    players = [p for p in state["players"] if p.team_bonus and not p.downed]
    for i, a in enumerate(players):
        for b in players[i + 1:]:
            reach = TEAM_RANGE * (1 + 0.5 * max(a.bond, b.bond))
            if a.pos.distance_to(b.pos) > reach:
                continue
            start = a.pos - camera + (0, 16)
            end = b.pos - camera + (0, 16)
            pulse = 0.5 + 0.5 * math.sin(state["time"] * 4)
            color = (int(100 + 80 * pulse), int(200 + 40 * pulse), 255)
            pygame.draw.line(screen, (30, 60, 90), start, end, 5)
            pygame.draw.line(screen, color, start, end, 2)


def draw_hunted(screen, state, camera):
    # a red arrow above the player a boss is chasing
    for p in state["players"]:
        if not p.hunted or p.downed:
            continue
        pos = p.pos - camera + (0, -58 + math.sin(state["time"] * 6) * 4)
        points = [pos + (0, 10), pos + (-9, -4), pos + (9, -4)]
        pygame.draw.polygon(screen, (0, 0, 0), [pt + (2, 2) for pt in points])
        pygame.draw.polygon(screen, (240, 60, 60), points)


def draw_game(screen, state):
    camera = state["camera"] + effects.shake_offset()
    state["world"].draw(screen, camera)
    for pickup in state["pickups"]:
        pickup.draw(screen, camera, state["time"])
    for orb in state["orbs"]:
        orb.draw(screen, camera, state["time"])
    draw_team_links(screen, state, camera)
    frozen = state["freeze"] > 0
    for enemy in sorted(state["enemies"], key=lambda e: e.pos.y):
        enemy.draw(screen, camera, frozen)
    for bullet in state["bullets"]:
        bullet.draw(screen, camera)
    online = state["online"] is not None
    for p in state["players"]:
        if p is not state["player"]:
            p.draw(screen, camera, online)
    state["player"].draw(screen, camera)
    for bullet in state["enemy_bullets"]:
        bullet.draw(screen, camera)
    events.draw(screen, camera, state)
    draw_hunted(screen, state, camera)
    state["world"].draw_roofs(screen, camera)
    effects.draw(screen, camera)
    dark = ambient.darkness(state["time"])
    ambient.draw(screen, camera, state["world"], dark)
    draw_night(screen, state, camera)
    if dark > 0.45:
        # fireflies have to glow through the night
        ambient.draw(screen, camera, state["world"], dark, only_lights=True)
    events.draw_overlay(screen, state)
    ambient.draw_vignette(screen)
    effects.draw_banners(screen)

    if state["flash"] > 0:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, int(state["flash"] * 600)))
        screen.blit(overlay, (0, 0))

    draw_player_panel(screen, state["player"])
    draw_xp(screen, state["player"])
    draw_time(screen, state)
    draw_boss_bar(screen, state["enemies"])
    draw_status(screen, state)
    if online:
        draw_teammate_arrows(screen, state, camera)
    if state["player"].choices and not state["paused"]:
        draw_online_choices(screen, state)
    if state["choices"]:
        draw_upgrade_menu(screen, state)
    elif state["paused"]:
        draw_pause(screen, state)


def draw(screen, state):
    if state["screen"] in SCREENS:
        draw_screen = SCREENS[state["screen"]][1]
        draw_screen(screen, state)
    else:
        draw_game(screen, state)
    achievements.draw_toasts(screen)
    if config.get("show_fps"):
        ui.text(screen, f"{fps:.0f} FPS", 22, (200, 255, 200), (W - 10, H - 62), "right")
    pygame.display.flip()


fps = 0


def main():
    global fps
    # small buffer so the sounds come right on time
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    saves.migrate()
    config.load()
    sound.init()
    pygame.display.set_mode((W, H), config.window_flags())
    pygame.display.set_caption("roguelike")
    sprites.load_all()
    ambient.init()
    clock = pygame.time.Clock()

    last_slot = config.get("last_slot")
    if last_slot and saves.slot_info(last_slot):
        saves.slot = last_slot
        state = init_menu(progress.load(), World())
    else:
        state = init_slots(World())
    while state["running"]:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        fps = clock.get_fps()
        state = handle_input(state)
        state = update(state, dt)
        # after F11 the screen can be a new surface
        draw(pygame.display.get_surface(), state)
    pygame.quit()


if __name__ == "__main__":
    main()

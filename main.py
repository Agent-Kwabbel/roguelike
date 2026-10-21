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
)
from player import Player
from enemy import spawn_enemy, spawn_boss, split
from orb import Orb
from pickup import Pickup, random_drop
from upgrades import pick_choices
from world import World
from menus import init_menu, format_time, text_center, panel, wrap_text
import battlepass
import challenges
import dev
import effects
import menus
import sprites


def init_game(difficulty_key, bp, world):
    """Maak de beginstaat van het spel aan."""
    difficulty = DIFFICULTIES[difficulty_key]
    player = Player(
        difficulty["player_hp"],
        battlepass.skin_sprite(bp),
        battlepass.bullet_sprite(bp),
    )
    battlepass.apply_perks(bp, player)
    effects.clear()
    return {
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
        "quit_run": False,
        "flash": 0,
        "world": world,
        "bp": bp,
        "stats": {"kills": 0, "bosses": 0, "elites": 0, "pickups": 0, "chests": 0, "coins": 0},
    }


def handle_input(state):
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            state["running"] = False

    if dev.handle_input(state, events):
        if state["screen"] == "game":
            state["player"].move = pygame.Vector2(0, 0)
        return state

    if state["screen"] in menus.SCREENS:
        handle_screen = menus.SCREENS[state["screen"]][0]
        handle_screen(state, events)
        if state["start"]:
            return init_game(state["start"], state["bp"], World())
        return state

    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if state["choices"]:
            keys = [pygame.K_1, pygame.K_2, pygame.K_3]
            if event.key in keys:
                index = keys.index(event.key)
                if index < len(state["choices"]):
                    state["choices"][index]["apply"](state["player"])
                    state["choices"] = None
        elif event.key in (pygame.K_ESCAPE, pygame.K_p):
            state["paused"] = not state["paused"]
        elif state["paused"] and event.key == pygame.K_q:
            state["quit_run"] = True
    state["player"].read_input()
    return state


def update(state, dt):
    if state["screen"] != "game":
        state["menu_time"] += dt
        return state
    if state["quit_run"]:
        return end_run(state)
    if state["choices"] or state["paused"] or dev.is_open:
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

    state["bullets"] += player.update_weapons(dt, state["enemies"])
    # als de speler binnen is lopen vijanden om naar de deur
    home = world.building_at(player.pos)
    for enemy in state["enemies"]:
        target = player.pos
        if home and enemy.ai in ("chase", "dasher"):
            target = home.path_target(enemy.pos, player.pos)
        old_pos = enemy.pos.copy()
        state["enemy_bullets"] += enemy.update(dt, enemy.steer(target))
        world.collide(enemy.pos, enemy.radius)
        enemy.check_stuck(old_pos, target, dt)
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

    handle_collisions(state)

    if player.pending_upgrades > 0:
        player.pending_upgrades -= 1
        state["choices"] = pick_choices(player)

    if player.hp <= 0:
        return end_run(state)
    return state


def end_run(state):
    bp = state["bp"]
    player = state["player"]
    stats = state["stats"]
    stats["time"] = state["time"]
    stats["level"] = player.level
    stats["runs"] = 1
    if state["difficulty_key"] in ("hard", "extreme"):
        stats["hard_time"] = state["time"]

    coins = stats["kills"] // COINS_PER_KILLS + stats["coins"]
    bp["coins"] += coins
    bp_xp = battlepass.run_xp(state["time"], stats["kills"], player.level)
    challenge_xp, finished = challenges.update(bp, stats)
    new_tiers = battlepass.add_xp(bp, bp_xp + challenge_xp)
    battlepass.save(bp)
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
        if player.pos.distance_to(enemy.pos) < player.radius + enemy.radius:
            player.take_damage(damage)
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


def collect(state):
    player = state["player"]
    for orb in state["orbs"]:
        if player.pos.distance_to(orb.pos) < player.radius + orb.radius:
            player.add_xp(orb.value)
            orb.value = 0
    for pickup in state["pickups"]:
        if player.pos.distance_to(pickup.pos) < player.radius + pickup.radius:
            use_pickup(state, pickup.kind)
            pickup.life = 0


def enemy_deaths(state):
    stats = state["stats"]
    spawned = []
    for enemy in state["enemies"]:
        if enemy.hp > 0:
            continue
        state["orbs"].append(Orb(enemy.pos, enemy.xp))
        stats["kills"] += 1
        effects.burst(enemy.pos, enemy.color)
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
            spawned += split(enemy, SPLIT_INTO[enemy.kind], SPLIT_COUNT)
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


def draw_upgrade_menu(screen, choices):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    text_center(screen, "Kies een upgrade", 52, (255, 255, 255), 130)

    left = W / 2 - (len(choices) * 270 - 20) / 2
    for i, upgrade in enumerate(choices):
        x = left + i * 270
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
    text_center(screen, "Druk op 1, 2 of 3", 26, (190, 190, 200), 490)


def draw_pause(screen):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    text_center(screen, "Pauze", 72, (255, 255, 255), 220)
    text_center(screen, "Esc: verder spelen, Q: run stoppen", 30, (200, 200, 200), 300)


def draw_game(screen, state):
    camera = state["camera"]
    state["world"].draw(screen, camera)
    for pickup in state["pickups"]:
        pickup.draw(screen, camera, state["time"])
    for orb in state["orbs"]:
        orb.draw(screen, camera, state["time"])
    for enemy in sorted(state["enemies"], key=lambda e: e.pos.y):
        enemy.draw(screen, camera)
    for bullet in state["bullets"]:
        bullet.draw(screen, camera)
    state["player"].draw(screen, camera)
    for bullet in state["enemy_bullets"]:
        bullet.draw(screen, camera)
    state["world"].draw_roofs(screen, camera)
    effects.draw(screen, camera)

    if state["flash"] > 0:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, int(state["flash"] * 600)))
        screen.blit(overlay, (0, 0))

    draw_hp(screen, state["player"])
    draw_weapons(screen, state["player"])
    draw_xp(screen, state["player"])
    draw_time(screen, state)
    draw_boss_bar(screen, state["enemies"])
    if state["choices"]:
        draw_upgrade_menu(screen, state["choices"])
    elif state["paused"]:
        draw_pause(screen)


def draw(screen, state):
    if state["screen"] in menus.SCREENS:
        draw_screen = menus.SCREENS[state["screen"]][1]
        draw_screen(screen, state)
    else:
        draw_game(screen, state)
    dev.draw(screen, state)
    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("roguelike")
    sprites.load_all()
    clock = pygame.time.Clock()

    state = init_menu(battlepass.load(), World())
    while state["running"]:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        state = handle_input(state)
        state = update(state, dt)
        draw(screen, state)
    pygame.quit()


if __name__ == "__main__":
    main()

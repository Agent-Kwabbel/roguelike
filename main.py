import pygame

from settings import (
    W,
    H,
    FPS,
    TILE,
    SPAWN_INTERVAL,
    ENEMY_DAMAGE,
)
from player import Player
from enemy import spawn_enemy
from orb import Orb
from upgrades import pick_choices


def init_game():
    """Maak de beginstaat van het spel aan."""
    return {
        "running": True,
        "player": Player(),
        "enemies": [],
        "bullets": [],
        "orbs": [],
        "spawn_timer": 0,
        "camera": pygame.Vector2(0, 0),
        "choices": None,
    }


def handle_input(state):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False
        if event.type == pygame.KEYDOWN and state["choices"]:
            keys = [pygame.K_1, pygame.K_2, pygame.K_3]
            if event.key in keys:
                index = keys.index(event.key)
                if index < len(state["choices"]):
                    state["choices"][index]["apply"](state["player"])
                    state["choices"] = None
    state["player"].read_input()
    return state


def update(state, dt):
    player = state["player"]
    if state["choices"]:
        return state

    player.update(dt)
    state["camera"] = player.pos - pygame.Vector2(W / 2, H / 2)

    state["spawn_timer"] += dt
    if state["spawn_timer"] >= SPAWN_INTERVAL:
        state["spawn_timer"] = 0
        state["enemies"].append(spawn_enemy(player.pos))

    bullet = player.shoot(state["enemies"])
    if bullet:
        state["bullets"].append(bullet)

    for enemy in state["enemies"]:
        enemy.update(dt, player.pos)
    for bullet in state["bullets"]:
        bullet.update(dt)

    for orb in state["orbs"]:
        orb.update(dt, player.pos, player.pickup_range)

    handle_collisions(state)

    if player.pending_upgrades > 0:
        player.pending_upgrades -= 1
        state["choices"] = pick_choices()

    if player.hp <= 0:
        return init_game()
    return state


def handle_collisions(state):
    player = state["player"]

    for bullet in state["bullets"]:
        for enemy in state["enemies"]:
            if bullet.pos.distance_to(enemy.pos) < bullet.radius + enemy.radius:
                enemy.hp -= bullet.damage
                bullet.life = 0
                break

    for enemy in state["enemies"]:
        if player.pos.distance_to(enemy.pos) < player.radius + enemy.radius:
            player.take_damage(ENEMY_DAMAGE)

    for enemy in state["enemies"]:
        if enemy.hp <= 0:
            state["orbs"].append(Orb(enemy.pos, enemy.xp))

    for orb in state["orbs"]:
        if player.pos.distance_to(orb.pos) < player.radius + orb.radius:
            player.add_xp(orb.value)
            orb.value = 0

    state["enemies"] = [e for e in state["enemies"] if e.hp > 0]
    state["orbs"] = [o for o in state["orbs"] if o.value > 0]
    state["bullets"] = [b for b in state["bullets"] if b.life > 0]


def draw_floor(screen, camera):
    screen.fill((40, 90, 50))
    start_x = -int(camera.x) % TILE
    start_y = -int(camera.y) % TILE
    for x in range(start_x - TILE, W + TILE, TILE):
        pygame.draw.line(screen, (50, 105, 60), (x, 0), (x, H))
    for y in range(start_y - TILE, H + TILE, TILE):
        pygame.draw.line(screen, (50, 105, 60), (0, y), (W, y))


def draw_hp(screen, player):
    for i in range(player.max_hp):
        color = (220, 40, 40) if i < player.hp else (70, 30, 30)
        pygame.draw.rect(screen, color, (10 + i * 26, 10, 20, 20))


def draw_xp(screen, player):
    pygame.draw.rect(screen, (30, 30, 50), (0, H - 12, W, 12))
    width = W * player.xp / player.xp_needed()
    pygame.draw.rect(screen, (80, 220, 240), (0, H - 12, width, 12))
    font = pygame.font.Font(None, 24)
    text = font.render(f"Level {player.level}", True, (255, 255, 255))
    screen.blit(text, (10, H - 36))


def draw_upgrade_menu(screen, choices):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    big = pygame.font.Font(None, 48)
    small = pygame.font.Font(None, 32)

    title = big.render("Kies een upgrade", True, (255, 255, 255))
    screen.blit(title, (W / 2 - title.get_width() / 2, 150))

    for i, upgrade in enumerate(choices):
        line = f"{i + 1}. {upgrade['name']} - {upgrade['desc']}"
        text = small.render(line, True, (255, 255, 255))
        screen.blit(text, (W / 2 - text.get_width() / 2, 250 + i * 50))


def draw(screen, state):
    camera = state["camera"]
    draw_floor(screen, camera)
    for enemy in state["enemies"]:
        enemy.draw(screen, camera)
    for orb in state["orbs"]:
        orb.draw(screen, camera)
    for bullet in state["bullets"]:
        bullet.draw(screen, camera)
    state["player"].draw(screen, camera)
    draw_hp(screen, state["player"])
    draw_xp(screen, state["player"])
    if state["choices"]:
        draw_upgrade_menu(screen, state["choices"])
    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("roguelike")
    clock = pygame.time.Clock()

    state = init_game()
    while state["running"]:
        dt = clock.tick(FPS) / 1000
        state = handle_input(state)
        state = update(state, dt)
        draw(screen, state)
    pygame.quit()


if __name__ == "__main__":
    main()

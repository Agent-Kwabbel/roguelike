import pygame

from settings import W, H, FPS, TILE, SPAWN_INTERVAL, ENEMY_DAMAGE, PLAYER_MAX_HP
from player import Player
from enemy import spawn_enemy


def init_game():
    """Maak de beginstaat van het spel aan."""
    return {
        "running": True,
        "player": Player(),
        "enemies": [],
        "bullets": [],
        "spawn_timer": 0,
        "camera": pygame.Vector2(0, 0),
    }


def handle_input(state):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False
    state["player"].read_input()
    return state


def update(state, dt):
    player = state["player"]
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

    handle_collisions(state)

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

    state["enemies"] = [e for e in state["enemies"] if e.hp > 0]
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
    for i in range(PLAYER_MAX_HP):
        color = (220, 40, 40) if i < player.hp else (70, 30, 30)
        pygame.draw.rect(screen, color, (10 + i * 26, 10, 20, 20))


def draw(screen, state):
    camera = state["camera"]
    draw_floor(screen, camera)
    for enemy in state["enemies"]:
        enemy.draw(screen, camera)
    for bullet in state["bullets"]:
        bullet.draw(screen, camera)
    state["player"].draw(screen, camera)
    draw_hp(screen, state["player"])
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

import pygame

from settings import W, H, FPS, TILE, SPAWN_INTERVAL
from player import Player
from enemy import spawn_enemy


def init_game():
    """Maak de beginstaat van het spel aan."""
    return {
        "running": True,
        "player": Player(),
        "enemies": [],
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

    for enemy in state["enemies"]:
        enemy.update(dt, player.pos)
    return state


def draw_floor(screen, camera):
    screen.fill((40, 90, 50))
    start_x = -int(camera.x) % TILE
    start_y = -int(camera.y) % TILE
    for x in range(start_x - TILE, W + TILE, TILE):
        pygame.draw.line(screen, (50, 105, 60), (x, 0), (x, H))
    for y in range(start_y - TILE, H + TILE, TILE):
        pygame.draw.line(screen, (50, 105, 60), (0, y), (W, y))


def draw(screen, state):
    camera = state["camera"]
    draw_floor(screen, camera)
    for enemy in state["enemies"]:
        enemy.draw(screen, camera)
    state["player"].draw(screen, camera)
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

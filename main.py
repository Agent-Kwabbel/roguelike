import pygame


W, H = 960, 640
FPS = 60
TILE = 64
PLAYER_SPEED = 220
PLAYER_RADIUS = 14


def init_game():
    """Maak de beginstaat van het spel aan."""
    return {
        "running": True,
        "player": pygame.Vector2(0, 0),
        "camera": pygame.Vector2(0, 0),
    }


def handle_input(state):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False

    keys = pygame.key.get_pressed()
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        move.y -= 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        move.y += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        move.x -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        move.x += 1

    if move.length() > 0:
        move = move.normalize()
    state["move"] = move
    return state


def update(state, dt):
    state["player"] += state["move"] * PLAYER_SPEED * dt
    state["camera"] = state["player"] - pygame.Vector2(W / 2, H / 2)
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
    draw_floor(screen, state["camera"])
    pos = state["player"] - state["camera"]
    pygame.draw.circle(screen, (60, 120, 220), pos, PLAYER_RADIUS)
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

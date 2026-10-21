import random

import pygame

import config
import net
import progress
import sound
import ui
from menus import DIFFICULTY_KEYS, DIFFICULTY_COLORS, text_center
from settings import W, H, NET_PORT, MAX_PLAYERS, DIFFICULTIES, COOP_COLORS

CHOOSE_BUTTONS = ["Host game", "Join game", "Back"]
IP_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz.-:"
PLAYER_LIST = pygame.Rect(W / 2 + 10, 150, 340, 300)


def new_lobby():
    return {"page": "choose", "selected": 0, "ip": config.get("last_ip"), "error": "", "server": None,
            "conn": None, "players": [], "difficulty": 1, "my_id": 0, "next_id": 1,
            "host_ip": ""}


def my_info(state, player_id):
    bp = state["bp"]
    return {"id": player_id, "name": f"Player {player_id + 1}", "sprite": progress.skin_sprite(bp),
            "bullet": progress.bullet_sprite(bp), "perks": list(bp["owned"])}


def lobby_state(state):
    if "lobby" not in state:
        state["lobby"] = new_lobby()
    return state["lobby"]


def leave(state):
    lobby = state["lobby"]
    if lobby["server"]:
        lobby["server"].close()
        for player in lobby["players"]:
            if player.get("conn"):
                player["conn"].close()
    if lobby["conn"]:
        lobby["conn"].close()
    state["lobby"] = new_lobby()


def back_to_menu(state):
    leave(state)
    state["screen"] = "menu"


def button_rects(count, y=200):
    return [pygame.Rect(W / 2 - 350, y + i * 62, 320, 52) for i in range(count)]


# ---------- choose ----------

def handle_choose(state, events):
    lobby = state["lobby"]
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            back_to_menu(state)
            return
    lobby["selected"], chosen = ui.navigate(events, lobby["selected"], button_rects(3))
    if chosen == 0:
        start_hosting(state)
    elif chosen == 1:
        lobby["page"] = "join"
        lobby["selected"] = 0
        lobby["error"] = ""
    elif chosen == 2:
        back_to_menu(state)


def start_hosting(state):
    lobby = state["lobby"]
    try:
        lobby["server"] = net.Server()
    except OSError as error:
        lobby["error"] = f"Could not host: {error}"
        return
    lobby["page"] = "host"
    lobby["host_ip"] = net.local_ip()
    lobby["selected"] = 1
    lobby["error"] = ""
    lobby["players"] = [my_info(state, 0)]


# ---------- host ----------

def send_lobby(lobby):
    names = [p["name"] for p in lobby["players"]]
    for player in lobby["players"]:
        if player.get("conn"):
            player["conn"].send({"type": "lobby", "players": names, "difficulty": DIFFICULTY_KEYS[lobby["difficulty"]]})


def host_network(lobby):
    changed = False
    for conn in lobby["server"].new_players():
        lobby["players"].append({"id": lobby["next_id"], "conn": conn, "name": "...", "ready": False})
        conn.send({"type": "welcome", "id": lobby["next_id"]})
        lobby["next_id"] += 1
    for player in lobby["players"][1:]:
        for message in player["conn"].messages():
            if message["type"] == "hello":
                player.update(message["info"])
                player["name"] = f"Player {len(lobby['players'])}"
                player["ready"] = True
                sound.play("pick")
                changed = True
            elif message["type"] == "disconnect":
                player["gone"] = True
    gone = [p for p in lobby["players"] if p.get("gone")]
    if gone:
        lobby["players"] = [p for p in lobby["players"] if not p.get("gone")]
        lobby["server"].count -= len(gone)
        changed = True
    if changed:
        # names follow the order in the list
        for i, player in enumerate(lobby["players"]):
            player["name"] = f"Player {i + 1}"
        send_lobby(lobby)


def handle_host(state, events):
    lobby = state["lobby"]
    host_network(lobby)
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            leave(state)
            return
        if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            step = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
            lobby["difficulty"] = (lobby["difficulty"] + step) % len(DIFFICULTY_KEYS)
            sound.play("menu_move")
            send_lobby(lobby)
    lobby["selected"], chosen = ui.navigate(events, lobby["selected"], button_rects(3))
    if chosen == 0:
        lobby["difficulty"] = (lobby["difficulty"] + 1) % len(DIFFICULTY_KEYS)
        send_lobby(lobby)
    elif chosen == 1:
        start_game(state)
    elif chosen == 2:
        leave(state)


def start_game(state):
    lobby = state["lobby"]
    if any(not p.get("ready", True) for p in lobby["players"]):
        lobby["error"] = "Someone is still joining"
        return
    lobby["server"].stop_accepting()
    players = []
    conns = {}
    for player in lobby["players"]:
        players.append({"id": player["id"], "name": player["name"], "sprite": player["sprite"],
                        "bullet": player["bullet"], "perks": player["perks"]})
        if player.get("conn"):
            conns[player["id"]] = player["conn"]
    message = {"type": "start", "seed": random.randrange(1000000),
               "difficulty": DIFFICULTY_KEYS[lobby["difficulty"]], "players": players}
    for conn in conns.values():
        conn.send(message)
    state["start_online"] = {"role": "host", "start": message, "conns": conns, "my_id": 0,
                             "server": lobby["server"]}
    state["lobby"] = new_lobby()


# ---------- join ----------

def handle_join(state, events):
    lobby = state["lobby"]
    for event in events:
        if event.type == pygame.TEXTINPUT:
            for char in event.text.lower():
                if char in IP_CHARS and len(lobby["ip"]) < 40:
                    lobby["ip"] += char
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                lobby["page"] = "choose"
                lobby["selected"] = 1
                return
            if event.key == pygame.K_BACKSPACE:
                lobby["ip"] = lobby["ip"][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                join(state)
                return
    # only the mouse here, the keyboard is for typing
    chosen = ui.clicked(events, join_rects())
    if chosen == 0:
        join(state)
    elif chosen == 1:
        lobby["page"] = "choose"
        lobby["selected"] = 1


def join_rects():
    return [pygame.Rect(W / 2 - 350, 320, 155, 52), pygame.Rect(W / 2 - 185, 320, 155, 52)]


def join(state):
    lobby = state["lobby"]
    ip = lobby["ip"].strip() or "127.0.0.1"
    port = NET_PORT
    if ":" in ip:
        ip, port_text = ip.rsplit(":", 1)
        if port_text.isdigit():
            port = int(port_text)
    sound.play("menu_select")
    conn, error = net.connect(ip, port)
    if conn is None:
        lobby["error"] = f"Could not connect: {error}"
        sound.play("menu_back")
        return
    config.set("last_ip", lobby["ip"])
    lobby["conn"] = conn
    lobby["page"] = "wait"
    lobby["error"] = ""
    lobby["players"] = []


def handle_wait(state, events):
    lobby = state["lobby"]
    for message in lobby["conn"].messages():
        if message["type"] == "welcome":
            lobby["my_id"] = message["id"]
            lobby["conn"].send({"type": "hello", "info": my_info(state, message["id"])})
        elif message["type"] == "lobby":
            lobby["players"] = message["players"]
            lobby["difficulty"] = DIFFICULTY_KEYS.index(message["difficulty"])
        elif message["type"] == "start":
            state["start_online"] = {"role": "client", "start": message, "conn": lobby["conn"],
                                     "my_id": lobby["my_id"]}
            lobby["conn"] = None
            state["lobby"] = new_lobby()
            return
        elif message["type"] == "disconnect":
            leave(state)
            state["lobby"]["page"] = "join"
            state["lobby"]["error"] = "The host closed the game (or it is full)"
            return
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            leave(state)
            return
    if ui.clicked(events, button_rects(1, 380)) == 0:
        leave(state)


def handle_input(state, events):
    lobby = lobby_state(state)
    pages = {"choose": handle_choose, "host": handle_host, "join": handle_join, "wait": handle_wait}
    pages[lobby["page"]](state, events)


# ---------- drawing ----------

def draw_players(screen, names, difficulty, host_ip=None):
    rect = PLAYER_LIST
    ui.card(screen, rect, ui.BORDER, (22, 20, 34, 235), shadow=True)
    ui.text(screen, f"PLAYERS {len(names)}/{MAX_PLAYERS}", 18, ui.DIM, (rect.x + 20, rect.y + 20))
    for i, name in enumerate(names):
        y = rect.y + 52 + i * 44
        pygame.draw.circle(screen, COOP_COLORS[i % len(COOP_COLORS)], (rect.x + 34, y + 12), 9)
        label = name + ("  (host)" if i == 0 else "")
        ui.text(screen, label, 26, ui.WHITE, (rect.x + 54, y))
    key = DIFFICULTY_KEYS[difficulty]
    ui.text(screen, "DIFFICULTY", 18, ui.DIM, (rect.x + 20, rect.bottom - 70))
    ui.badge(screen, DIFFICULTIES[key]["name"], (rect.x + 20, rect.bottom - 44), DIFFICULTY_COLORS.get(key, ui.YELLOW), size=22)
    if host_ip:
        ui.text(screen, f"Others join with: {host_ip}", 24, ui.YELLOW, (W / 2, rect.bottom + 18), "center", True)


def draw_screen(screen, state):
    lobby = lobby_state(state)
    ui.draw_background(screen, state, 190)
    ui.title(screen, "Multiplayer", 60, ui.YELLOW, 40)
    text_center(screen, "Co-op with up to 4 players", 24, ui.GREY, 110)
    page = lobby["page"]

    if page == "choose":
        accents = [ui.GREEN, ui.YELLOW, ui.GREY]
        for i, rect in enumerate(button_rects(3)):
            ui.button(screen, rect, CHOOSE_BUTTONS[i], i == lobby["selected"], accents[i])
        rect = PLAYER_LIST
        ui.card(screen, rect, ui.BORDER, (22, 20, 34, 235), shadow=True)
        ui.text(screen, "HOW IT WORKS", 18, ui.DIM, (rect.x + 20, rect.y + 20))
        lines = ["One player hosts, the others", "join with the host's IP address.",
                 "", "Same network: just use the IP.", "Over the internet: the host",
                 f"forwards port {NET_PORT}, or use", "something like Tailscale."]
        for i, line in enumerate(lines):
            ui.text(screen, line, 22, ui.GREY, (rect.x + 20, rect.y + 50 + i * 26))
        ui.footer(screen, [("W/S", "Move"), ("Enter", "Select"), ("Esc", "Back")])

    elif page == "host":
        key = DIFFICULTY_KEYS[lobby["difficulty"]]
        labels = [f"< {DIFFICULTIES[key]['name']} >", "Start", "Back"]
        accents = [DIFFICULTY_COLORS.get(key, ui.YELLOW), ui.GREEN, ui.GREY]
        for i, rect in enumerate(button_rects(3)):
            sub = "Difficulty" if i == 0 else None
            ui.button(screen, rect, labels[i], i == lobby["selected"], accents[i], sub)
        names = [p["name"] if p.get("ready", True) else "joining..." for p in lobby["players"]]
        draw_players(screen, names, lobby["difficulty"], lobby["host_ip"])
        ui.footer(screen, [("W/S", "Move"), ("A/D", "Difficulty"), ("Enter", "Select"), ("Esc", "Back")])

    elif page == "join":
        ui.text(screen, "Host IP address", 24, ui.GREY, (W / 2 - 350, 196))
        box = pygame.Rect(W / 2 - 350, 226, 320, 56)
        ui.card(screen, box, ui.YELLOW, (22, 20, 34, 235))
        caret = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
        ui.text(screen, lobby["ip"] + caret, 32, ui.WHITE, (box.x + 16, box.y + 14))
        if not lobby["ip"]:
            ui.text(screen, "127.0.0.1", 32, ui.DIM, (box.x + 16, box.y + 14))
        hover = ui.hovered(join_rects())
        ui.center_button(screen, join_rects()[0], "Join", hover == 0, ui.GREEN)
        ui.center_button(screen, join_rects()[1], "Back", hover == 1, ui.GREY)
        ui.footer(screen, [("Type", "IP address"), ("Enter", "Join"), ("Esc", "Back")])

    elif page == "wait":
        text = "Waiting for the host to start..."
        ui.text(screen, text, 28, ui.WHITE, (W / 2 - 350, 220))
        dots = "." * (pygame.time.get_ticks() // 400 % 4)
        ui.text(screen, "Connected" + dots, 24, ui.GREEN, (W / 2 - 350, 260))
        rect = button_rects(1, 380)[0]
        ui.button(screen, rect, "Leave", rect.collidepoint(pygame.mouse.get_pos()), ui.GREY)
        draw_players(screen, lobby["players"], lobby["difficulty"])
        ui.footer(screen, [("Esc", "Leave")])

    if lobby["error"]:
        ui.text(screen, lobby["error"], 24, ui.RED, (W / 2, H - 80), "center", True)


SCREENS = {
    "multiplayer": (handle_input, draw_screen),
}

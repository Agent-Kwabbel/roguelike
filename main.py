"""Startpunt van je game. Pas dit bestand aan en breid het uit."""


def init_game():
    """Maak de beginstaat van het spel aan."""
    # TODO: bepaal welke gegevens je bijhoudt (score, positie, levens, ...)
    return {"score": 0, "running": True}


def handle_input(state):
    """Lees de invoer van de speler en werk de staat bij."""
    # TODO: vervang dit door de echte spelbesturing
    command = input("> ").strip().lower()
    if command == "stop":
        state["running"] = False
    return state


def update(state):
    """Werk de spelstaat bij (regels, botsingen, score, ...)."""
    # TODO
    return state


def draw(state):
    """Toon de huidige spelstaat aan de speler."""
    # TODO
    print(f"Score: {state['score']}")


def main():
    state = init_game()
    while state["running"]:
        draw(state)
        state = handle_input(state)
        state = update(state)
    print("Einde spel.")


if __name__ == "__main__":
    main()

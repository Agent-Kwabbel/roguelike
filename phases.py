from settings import PHASES, REAPER_TIME


def effective_time(state):
    # harder difficulties go through the phases faster
    return state["time"] * state["difficulty"]["ramp"]


def effective_minutes(state):
    return effective_time(state) / 60


def index(state):
    time = effective_time(state)
    current = 0
    for i, phase in enumerate(PHASES):
        if time >= phase["start"]:
            current = i
    return current


def current(state):
    return PHASES[index(state)]


def blend(state, key):
    """Slides a number smoothly from this phase to the next one."""
    i = index(state)
    if i == len(PHASES) - 1:
        return PHASES[i][key]
    start = PHASES[i]["start"]
    end = PHASES[i + 1]["start"]
    part = (effective_time(state) - start) / (end - start)
    return PHASES[i][key] + (PHASES[i + 1][key] - PHASES[i][key]) * part


def enemy_damage(state):
    return state["difficulty"]["enemy_damage"] + current(state)["damage"]


def max_enemies(state):
    return current(state)["max_enemies"]


def elite_chance(state):
    return current(state)["elite"] * state["difficulty"]["elite"]


def affixes_on(state):
    return current(state).get("affixes", False) or state["difficulty"].get("elite_affix", False)


def reaper_time_left(state):
    return REAPER_TIME - state["time"]

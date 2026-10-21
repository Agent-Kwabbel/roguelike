import datetime
import random

from settings import DAILY_CHALLENGES, WEEKLY_CHALLENGES

# mode "total" telt op over meerdere runs, "best" moet in een run gehaald worden
TEMPLATES = [
    {"stat": "kills", "mode": "total", "text": "Versla {goal} vijanden", "daily": 150, "weekly": 1000},
    {"stat": "time", "mode": "best", "text": "Overleef {minutes} minuten in een run", "daily": 180, "weekly": 480},
    {"stat": "level", "mode": "best", "text": "Haal level {goal} in een run", "daily": 8, "weekly": 18},
    {"stat": "bosses", "mode": "total", "text": "Versla {goal} keer een baas", "daily": 1, "weekly": 5},
    {"stat": "elites", "mode": "total", "text": "Versla {goal} elite vijanden", "daily": 2, "weekly": 12},
    {"stat": "pickups", "mode": "total", "text": "Pak {goal} pickups op", "daily": 4, "weekly": 25},
    {"stat": "runs", "mode": "total", "text": "Speel {goal} runs", "daily": 3, "weekly": 15},
    {"stat": "hard_time", "mode": "best", "text": "Overleef {minutes} minuten op Hard of Extreme", "daily": 120, "weekly": 300},
    {"stat": "chests", "mode": "total", "text": "Open {goal} kisten", "daily": 1, "weekly": 6},
]

DAILY_XP = 60
WEEKLY_XP = 200


def day_key():
    return datetime.date.today().isoformat()


def week_key():
    year, week, _ = datetime.date.today().isocalendar()
    return f"{year}-W{week}"


def make_list(key, kind, count):
    # zelfde seed per dag/week zodat iedereen dezelfde challenges krijgt
    rng = random.Random(kind + key)
    templates = rng.sample(TEMPLATES, count)
    result = []
    for template in templates:
        goal = template[kind]
        text = template["text"].format(goal=goal, minutes=goal // 60)
        result.append({
            "stat": template["stat"],
            "mode": template["mode"],
            "goal": goal,
            "text": text,
            "progress": 0,
            "done": False,
        })
    return result


def refresh(bp):
    data = bp["challenges"]
    if data.get("day") != day_key():
        data["day"] = day_key()
        data["daily"] = make_list(day_key(), "daily", DAILY_CHALLENGES)
    if data.get("week") != week_key():
        data["week"] = week_key()
        data["weekly"] = make_list(week_key(), "weekly", WEEKLY_CHALLENGES)


def update(bp, stats):
    """Verwerk een gespeelde run. Geeft (BP XP, lijst met voltooide challenges) terug."""
    refresh(bp)
    xp = 0
    finished = []
    for kind, reward in [("daily", DAILY_XP), ("weekly", WEEKLY_XP)]:
        for challenge in bp["challenges"][kind]:
            if challenge["done"]:
                continue
            value = stats.get(challenge["stat"], 0)
            if challenge["mode"] == "total":
                challenge["progress"] += value
            else:
                challenge["progress"] = max(challenge["progress"], value)
            if challenge["progress"] >= challenge["goal"]:
                challenge["progress"] = challenge["goal"]
                challenge["done"] = True
                xp += reward
                finished.append(challenge["text"])
    return xp, finished


def progress_text(challenge):
    if challenge["stat"] in ("time", "hard_time"):
        return f"{int(challenge['progress']) // 60}:{int(challenge['progress']) % 60:02d} / {challenge['goal'] // 60}:00"
    return f"{int(challenge['progress'])} / {challenge['goal']}"

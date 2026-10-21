# Makes all sound effects and music in assets/. Run with: uv run tools/make_sounds.py
import array
import math
import os
import random
import wave

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
SFX_RATE = 44100
MUSIC_RATE = 22050

rate = SFX_RATE

NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name):
    """'A4' -> 440.0, also works with sharps and flats like 'F#5' and 'Bb4'."""
    semitone = NOTE_NAMES[name[0]]
    rest = name[1:]
    if rest[0] == "#":
        semitone += 1
        rest = rest[1:]
    elif rest[0] == "b":
        semitone -= 1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + semitone
    return 440 * 2 ** ((midi - 69) / 12)


# ---------- building blocks ----------

def silence(length):
    return [0.0] * int(length * rate)


def tone(freq, length, wave_type="square", end_freq=None, duty=0.5, vibrato=0, vibrato_delay=0.1):
    samples = []
    phase = 0.0
    count = int(length * rate)
    if end_freq is None:
        end_freq = freq
    for i in range(count):
        t = i / rate
        f = freq * (end_freq / freq) ** (i / count)
        if vibrato and t > vibrato_delay:
            f *= 1 + vibrato * math.sin(2 * math.pi * 5.5 * t)
        phase = (phase + f / rate) % 1
        if wave_type == "square":
            # shifted so thin pulses stay centered around zero
            value = (1.0 if phase < duty else -1.0) + 1 - 2 * duty
        elif wave_type == "triangle":
            value = 4 * abs(phase - 0.5) - 1
        elif wave_type == "saw":
            value = 2 * phase - 1
        else:
            value = math.sin(2 * math.pi * phase)
        samples.append(value)
    return samples


def noise(length):
    return [random.uniform(-1, 1) for _ in range(int(length * rate))]


def crunchy_noise(length, freq):
    # noise that holds each value for a while, like old consoles
    samples = []
    hold = max(1, int(rate / freq))
    value = 0
    for i in range(int(length * rate)):
        if i % hold == 0:
            value = random.uniform(-1, 1)
        samples.append(value)
    return samples


def envelope(samples, attack=0.005, decay=0.1, release=0.005):
    """Quick rise, then dies out. Also fades the end so it doesn't click."""
    count = len(samples)
    attack_n = max(1, int(attack * rate))
    release_n = max(1, int(release * rate))
    result = []
    for i, value in enumerate(samples):
        amp = min(1, i / attack_n)
        if i >= attack_n:
            amp = math.exp(-(i - attack_n) / rate / decay)
        if i > count - release_n:
            amp *= (count - i) / release_n
        result.append(value * amp)
    return result


def sustain(samples, attack=0.01, release=0.05, level=0.7, drop=0.08):
    """For notes that keep sounding: rise, drop a bit to 'level' and fade out at the end."""
    count = len(samples)
    attack_n = max(1, int(attack * rate))
    release_n = max(1, min(count // 2, int(release * rate)))
    result = []
    for i, value in enumerate(samples):
        if i < attack_n:
            amp = i / attack_n
        else:
            t = (i - attack_n) / rate
            amp = level + (1 - level) * math.exp(-t / drop)
        if i > count - release_n:
            amp *= (count - i) / release_n
        result.append(value * amp)
    return result


def lowpass(samples, cutoff, end_cutoff=None):
    if end_cutoff is None:
        end_cutoff = cutoff
    result = []
    last = 0.0
    count = max(1, len(samples))
    for i, value in enumerate(samples):
        c = cutoff * (end_cutoff / cutoff) ** (i / count)
        a = 1 - math.exp(-2 * math.pi * c / rate)
        last += a * (value - last)
        result.append(last)
    return result


def highpass(samples, cutoff):
    low = lowpass(samples, cutoff)
    return [s - l for s, l in zip(samples, low)]


def tremolo(samples, speed, depth):
    return [v * (1 - depth + depth * math.sin(2 * math.pi * speed * i / rate)) for i, v in enumerate(samples)]


def scale(samples, volume):
    return [v * volume for v in samples]


def add(target, samples, start=0.0, volume=1.0):
    """Mix samples into target starting at 'start' seconds, makes target longer if needed."""
    offset = int(start * rate)
    needed = offset + len(samples)
    if needed > len(target):
        target.extend([0.0] * (needed - len(target)))
    for i, value in enumerate(samples):
        target[offset + i] += value * volume
    return target


def mix(*layers):
    result = []
    for layer in layers:
        add(result, layer)
    return result


def echo(samples, delay=0.12, feedback=0.35, repeats=3):
    result = list(samples) + [0.0] * int(delay * rate * repeats)
    volume = 1.0
    for n in range(1, repeats + 1):
        volume *= feedback
        add(result, samples, delay * n, volume)
    return result


def finish(samples, peak):
    # soft clip so stacked layers don't crackle, then set the loudness
    clipped = [math.tanh(v * 1.2) for v in samples]
    top = max(abs(v) for v in clipped) or 1
    return [v / top * peak for v in clipped]


def save(samples, folder, name):
    path = os.path.join(ASSETS, folder)
    os.makedirs(path, exist_ok=True)
    data = array.array("h", [int(max(-1, min(1, v)) * 32767) for v in samples])
    with wave.open(os.path.join(path, name + ".wav"), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(rate)
        file.writeframes(data.tobytes())


# ---------- small instruments for the effects ----------

def bell(freq, length=0.3, decay=0.12):
    # a few out of tune overtones sound like metal or glass
    body = mix(
        tone(freq, length, "sine"),
        scale(tone(freq * 2, length, "sine"), 0.35),
        scale(tone(freq * 3.01, length, "sine"), 0.12),
    )
    return envelope(body, 0.002, decay)


def chip(freq, length, duty=0.5, decay=0.1, cutoff=4000):
    return lowpass(envelope(tone(freq, length, "square", duty=duty), 0.003, decay), cutoff)


def thump(start_freq=150, end_freq=40, length=0.3, decay=0.12):
    return envelope(tone(start_freq, length, "sine", end_freq), 0.002, decay)


def boom(length, decay, start_cutoff=3000, end_cutoff=200):
    rumble = lowpass(noise(length), start_cutoff, end_cutoff)
    return envelope(rumble, 0.003, decay)


def whoosh(length, start_cutoff, end_cutoff, attack=0.04, decay=0.08):
    air = lowpass(noise(length), start_cutoff, end_cutoff)
    air = highpass(air, 300)
    return envelope(air, attack, decay)


def arpeggio(notes, gap, instrument):
    result = []
    for i, name in enumerate(notes):
        add(result, instrument(note(name)), i * gap)
    return result


# ---------- sound effects ----------

def make_shoot(pitch):
    pew = lowpass(envelope(tone(900 * pitch, 0.08, "square", 420 * pitch, duty=0.25), 0.002, 0.03), 3200)
    click = envelope(highpass(noise(0.015), 2000), 0.001, 0.004)
    return finish(mix(pew, scale(click, 0.4)), 0.32)


def make_knife(pitch):
    air = whoosh(0.13, 4500 * pitch, 1500 * pitch, 0.02, 0.04)
    swish = envelope(tone(1400 * pitch, 0.1, "sine", 700 * pitch), 0.01, 0.03)
    return finish(mix(air, scale(swish, 0.2)), 0.32)


def make_hit(pitch):
    knock = envelope(tone(320 * pitch, 0.06, "triangle", 140 * pitch), 0.001, 0.025)
    snap = lowpass(envelope(noise(0.02), 0.001, 0.006), 5000)
    return finish(mix(knock, scale(snap, 0.6)), 0.3)


def make_crit(pitch):
    clink = mix(bell(1900 * pitch, 0.18, 0.06), scale(bell(2870 * pitch, 0.18, 0.04), 0.5))
    return finish(mix(make_hit(pitch), clink), 0.45)


def make_kill(pitch):
    # a juicy bubble pop with a little puff of dust
    pop = envelope(tone(720 * pitch, 0.14, "sine", 110 * pitch), 0.001, 0.06)
    blip = lowpass(envelope(tone(1500 * pitch, 0.05, "square", 500 * pitch, duty=0.25), 0.001, 0.015), 4000)
    puff = lowpass(envelope(noise(0.12), 0.002, 0.035), 1800)
    return finish(mix(pop, scale(blip, 0.3), scale(puff, 0.5)), 0.55)


def make_xp(freq):
    plink = mix(bell(freq, 0.25, 0.07), scale(envelope(tone(freq * 2, 0.05, "triangle"), 0.001, 0.015), 0.3))
    return finish(echo(plink, 0.07, 0.2, 2), 0.3)


def make_level_up():
    def voice(freq):
        return mix(chip(freq, 0.2, 0.5, 0.08, 3500), scale(bell(freq, 0.2, 0.08), 0.5))
    result = arpeggio(["C5", "E5", "G5", "C6"], 0.065, voice)
    chord = []
    for name in ("C6", "E6", "G6"):
        held = sustain(tone(note(name), 0.6, "square", duty=0.25, vibrato=0.006), 0.01, 0.3, 0.5, 0.1)
        add(chord, lowpass(held, 3000), 0, 0.5)
    add(result, chord, 0.26)
    return finish(echo(result, 0.11, 0.25, 3), 0.7)


def make_pick():
    result = arpeggio(["G5", "C6"], 0.06, lambda f: bell(f, 0.3, 0.1))
    add(result, chip(note("C6"), 0.15, 0.25, 0.06, 3000), 0.06, 0.4)
    return finish(echo(result, 0.09, 0.2, 2), 0.55)


def make_hurt():
    buzz = lowpass(envelope(tone(230, 0.22, "square", 85), 0.002, 0.08), 1400)
    crunch = lowpass(envelope(noise(0.12), 0.001, 0.04), 900)
    return finish(mix(buzz, crunch, thump(120, 45, 0.25, 0.08)), 0.7)


def make_blocked():
    clank = mix(bell(1250, 0.3, 0.09), scale(bell(1870, 0.3, 0.07), 0.6), scale(bell(2610, 0.3, 0.05), 0.4))
    tick = envelope(highpass(noise(0.02), 2500), 0.001, 0.005)
    return finish(mix(clank, tick), 0.5)


def make_dash():
    air = whoosh(0.28, 800, 5000, 0.05, 0.09)
    rise = envelope(tone(280, 0.2, "sine", 900), 0.02, 0.07)
    return finish(mix(air, scale(rise, 0.25)), 0.5)


def make_explosion(length, decay, peak):
    crackle = []
    for _ in range(int(length * 40)):
        spark = envelope(noise(0.01), 0.001, 0.002)
        add(crackle, spark, random.uniform(0, length * 0.6), random.uniform(0.2, 0.6))
    crackle = highpass(crackle, 1500)
    crackle = envelope(crackle + [0.0] * int(length * rate), 0.001, decay * 1.2)
    rumble = boom(length, decay, 3500, 180)
    low = thump(110, 32, length, decay * 0.9)
    return finish(mix(rumble, scale(low, 1.1), scale(crackle, 0.4)), peak)


def make_lightning():
    zap = envelope(crunchy_noise(0.35, random.uniform(2000, 4000)), 0.001, 0.08)
    zap = tremolo(zap, 37, 0.6)
    hum = lowpass(envelope(tone(60, 0.35, "square"), 0.001, 0.1), 1200)
    sting = envelope(tone(2200, 0.12, "sine", 300), 0.001, 0.04)
    return finish(mix(zap, scale(hum, 0.4), scale(sting, 0.4)), 0.5)


def make_heart():
    def voice(freq):
        return mix(envelope(tone(freq, 0.35, "triangle"), 0.004, 0.14), scale(bell(freq * 2, 0.3, 0.08), 0.25))
    return finish(echo(arpeggio(["E5", "A5"], 0.08, voice), 0.1, 0.2, 2), 0.55)


def make_coin():
    result = chip(note("B5"), 0.07, 0.5, 1, 6000)
    add(result, chip(note("E6"), 0.35, 0.5, 0.12, 6000), 0.07)
    return finish(result, 0.42)


def make_chest():
    result = arpeggio(["C6", "E6", "G6", "C7", "E7"], 0.045, lambda f: bell(f, 0.4, 0.15))
    shimmer = envelope(highpass(noise(0.5), 5000), 0.05, 0.15)
    add(result, scale(shimmer, 0.15))
    low = mix(*[scale(sustain(tone(note(n), 0.5, "triangle"), 0.01, 0.2, 0.6), 0.4) for n in ("C4", "G4")])
    add(result, low)
    return finish(echo(result, 0.09, 0.25, 3), 0.65)


def make_magnet():
    rise = envelope(tone(300, 0.4, "sine", 1500, vibrato=0.04, vibrato_delay=0), 0.02, 0.18)
    edge = lowpass(envelope(tone(150, 0.4, "square", 750, duty=0.25), 0.02, 0.15), 2000)
    return finish(mix(rise, scale(edge, 0.25)), 0.5)


def make_freeze():
    result = arpeggio(["G7", "E7", "C7", "G6", "E6"], 0.04, lambda f: bell(f, 0.4, 0.12))
    frost = envelope(highpass(noise(0.6), 6000), 0.1, 0.2)
    add(result, scale(frost, 0.25))
    return finish(echo(result, 0.08, 0.3, 3), 0.5)


def make_boots():
    result = lowpass(envelope(tone(400, 0.15, "square", 1500, duty=0.25), 0.003, 0.06), 3000)
    add(result, lowpass(envelope(tone(600, 0.15, "square", 2200, duty=0.25), 0.003, 0.06), 3000), 0.09)
    return finish(result, 0.45)


def make_potion():
    result = []
    for i in range(7):
        freq = random.uniform(400, 900)
        bubble = envelope(tone(freq, 0.06, "sine", freq * 1.8), 0.002, 0.02)
        add(result, bubble, i * 0.045 + random.uniform(0, 0.015), random.uniform(0.6, 1))
    return finish(result, 0.45)


def make_streak(root):
    base = note(root)
    result = []
    for i, step in enumerate([0, 4, 7]):
        add(result, chip(base * 2 ** (step / 12), 0.08, 0.25, 0.04, 4000), i * 0.05)
    held = sustain(tone(base * 2, 0.4, "square", duty=0.25, vibrato=0.008, vibrato_delay=0.05), 0.005, 0.2, 0.5)
    add(result, lowpass(held, 3500), 0.15, 0.8)
    add(result, scale(bell(base * 4, 0.3, 0.1), 0.3), 0.15)
    return finish(echo(result, 0.1, 0.25, 2), 0.55)


def make_boss():
    horn = []
    for freq, volume in ((55, 1), (55.6, 0.8), (82.5, 0.6), (110, 0.3)):
        add(horn, tone(freq, 1.8, "saw"), 0, volume)
    horn = lowpass(horn, 300, 900)
    horn = sustain(horn, 0.25, 0.6, 0.8, 0.5)
    horn = tremolo(horn, 4, 0.2)
    result = mix(horn, thump(90, 35, 0.6, 0.2))
    add(result, thump(90, 35, 0.6, 0.2), 0.45)
    return finish(result, 0.8)


def make_boss_dead():
    result = make_explosion(1.0, 0.3, 1)
    fanfare = []
    for name in ("C5", "E5", "G5", "C6"):
        voice = sustain(tone(note(name), 1.1, "square", duty=0.25, vibrato=0.006), 0.02, 0.5, 0.6, 0.2)
        add(fanfare, lowpass(voice, 2500), 0, 0.35)
    add(result, echo(fanfare, 0.13, 0.3, 3), 0.25, 0.8)
    return finish(result, 0.85)


def make_event():
    def horn(name, length):
        body = mix(tone(note(name), length, "square", duty=0.5, vibrato=0.006),
                   scale(tone(note(name) / 2, length, "triangle"), 0.6))
        return lowpass(sustain(body, 0.01, 0.15, 0.6), 2200)
    result = horn("G4", 0.14)
    add(result, horn("C5", 0.5), 0.15)
    return finish(echo(result, 0.12, 0.25, 2), 0.55)


def make_enemy_shoot():
    thwip = envelope(tone(650, 0.07, "triangle", 280), 0.002, 0.025)
    air = whoosh(0.07, 3000, 1500, 0.005, 0.02)
    return finish(mix(thwip, scale(air, 0.5)), 0.3)


def make_summon():
    rise = envelope(tone(200, 0.7, "sine", 520, vibrato=0.03, vibrato_delay=0), 0.15, 0.3)
    odd = envelope(tone(283, 0.7, "sine", 735, vibrato=0.03, vibrato_delay=0), 0.15, 0.3)
    return finish(echo(mix(rise, scale(odd, 0.5)), 0.13, 0.3, 3), 0.45)


def make_mimic():
    growl = lowpass(tremolo(tone(75, 0.55, "saw", 60), 23, 0.7), 900)
    growl = sustain(growl, 0.03, 0.2, 0.7)
    grit = lowpass(envelope(noise(0.5), 0.02, 0.2), 600)
    return finish(mix(growl, scale(grit, 0.4)), 0.6)


def make_fuse():
    result = chip(1050, 0.05, 0.5, 0.02, 5000)
    add(result, chip(1050, 0.05, 0.5, 0.02, 5000), 0.11)
    return finish(result, 0.3)


def make_achievement():
    def voice(freq):
        return mix(bell(freq, 0.4, 0.12), scale(chip(freq, 0.12, 0.25, 0.05, 3500), 0.5))
    result = arpeggio(["G5", "C6", "E6", "G6"], 0.08, voice)
    chord = []
    for name in ("C6", "E6", "G6"):
        add(chord, lowpass(sustain(tone(note(name), 0.5, "triangle", vibrato=0.005), 0.01, 0.25, 0.5), 3000), 0, 0.4)
    add(result, chord, 0.32)
    return finish(echo(result, 0.1, 0.25, 3), 0.55)


def make_menu_move():
    return finish(lowpass(envelope(tone(1300, 0.03, "square", 1100, duty=0.25), 0.001, 0.01), 3500), 0.22)


def make_menu_select():
    click = lowpass(envelope(tone(800, 0.06, "square", 1300, duty=0.25), 0.001, 0.025), 3500)
    return finish(mix(click, scale(bell(1600, 0.1, 0.03), 0.4)), 0.38)


def make_menu_back():
    return finish(lowpass(envelope(tone(700, 0.06, "square", 420, duty=0.25), 0.001, 0.025), 3000), 0.32)


def make_buy():
    result = make_coin()
    add(result, scale(bell(note("G6"), 0.4, 0.12), 0.6), 0.17)
    add(result, scale(bell(note("B6"), 0.4, 0.12), 0.4), 0.22)
    return finish(echo(result, 0.09, 0.2, 2), 0.55)


def make_error():
    result = lowpass(envelope(tone(150, 0.09, "square"), 0.002, 0.08), 1200)
    add(result, lowpass(envelope(tone(140, 0.12, "square"), 0.002, 0.1), 1200), 0.11)
    return finish(result, 0.4)


def make_game_over():
    result = []
    names = ["G4", "F#4", "F4", "E4"]
    for i, name in enumerate(names):
        length = 0.9 if i == 3 else 0.28
        body = mix(tone(note(name), length, "triangle", vibrato=0.01 if i == 3 else 0, vibrato_delay=0.15),
                   scale(tone(note(name), length, "square", duty=0.25), 0.3))
        add(result, lowpass(sustain(body, 0.01, 0.15 if i < 3 else 0.6, 0.6), 1800), i * 0.3)
    return finish(echo(result, 0.15, 0.3, 3), 0.55)


def make_effects():
    global rate
    rate = SFX_RATE
    random.seed(7)
    pitches = [0.92, 1.0, 1.07, 1.14]
    for i, pitch in enumerate(pitches):
        save(make_shoot(pitch), "sounds", f"shoot_{i}")
        save(make_hit(pitch), "sounds", f"hit_{i}")
        save(make_kill(pitch), "sounds", f"kill_{i}")
    for i, pitch in enumerate(pitches[:3]):
        save(make_knife(pitch), "sounds", f"knife_{i}")
        save(make_crit(pitch), "sounds", f"crit_{i}")
    # a pentatonic scale, every orb in a row goes one step higher
    for i, name in enumerate(["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6"]):
        save(make_xp(note(name)), "sounds", f"xp{i}")
    for i, root in enumerate(["C5", "D5", "E5", "G5"]):
        save(make_streak(root), "sounds", f"streak{i}")
    for i in range(2):
        save(make_explosion(0.5, 0.12, 0.7), "sounds", f"meteor_{i}")
        save(make_lightning(), "sounds", f"lightning_{i}")

    effects = {
        "level_up": make_level_up,
        "pick": make_pick,
        "hurt": make_hurt,
        "blocked": make_blocked,
        "dash": make_dash,
        "explosion": lambda: make_explosion(0.9, 0.22, 0.9),
        "bomb": lambda: make_explosion(1.3, 0.35, 1),
        "heart": make_heart,
        "coin": make_coin,
        "chest": make_chest,
        "magnet": make_magnet,
        "freeze": make_freeze,
        "boots": make_boots,
        "potion": make_potion,
        "boss": make_boss,
        "boss_dead": make_boss_dead,
        "event": make_event,
        "enemy_shoot": make_enemy_shoot,
        "summon": make_summon,
        "mimic": make_mimic,
        "fuse": make_fuse,
        "achievement": make_achievement,
        "menu_move": make_menu_move,
        "menu_select": make_menu_select,
        "menu_back": make_menu_back,
        "buy": make_buy,
        "error": make_error,
        "game_over": make_game_over,
    }
    for name, make in effects.items():
        save(make(), "sounds", name)


# ---------- music ----------

CHORDS = {
    "Am": ["A", "C", "E"],
    "F": ["F", "A", "C"],
    "C": ["C", "E", "G"],
    "G": ["G", "B", "D"],
    "E": ["E", "G#", "B"],
    "Em": ["E", "G", "B"],
    "D": ["D", "F#", "A"],
    "B": ["B", "D#", "F#"],
    "Bm": ["B", "D", "F#"],
    "Bb": ["Bb", "D", "F"],
}


def parse_melody(text):
    """'E5:3 B4:1 -:2' -> list of (note name or None, length in steps)."""
    result = []
    for token in text.split():
        name, steps = token.split(":")
        result.append((None if name == "-" else name, int(steps)))
    return result


def place(track, samples, start, loop_length):
    # whatever sticks out past the end wraps around to the start, so the loop is seamless
    offset = int(start * rate)
    for i, value in enumerate(samples):
        track[(offset + i) % loop_length] += value


def loop_echo(track, delay, feedback):
    shift = int(delay * rate)
    count = len(track)
    result = list(track)
    for i in range(count):
        result[i] += track[(i - shift) % count] * feedback + track[(i - 2 * shift) % count] * feedback * feedback
    return result


def lead_voice(freq, length):
    body = mix(tone(freq, length, "square", duty=0.25, vibrato=0.005, vibrato_delay=0.15),
               scale(tone(freq * 1.004, length, "square", duty=0.5), 0.4))
    return lowpass(sustain(body, 0.008, 0.04, 0.55, 0.1), 3200)


def soft_lead_voice(freq, length):
    body = mix(tone(freq, length, "triangle", vibrato=0.006, vibrato_delay=0.2),
               scale(tone(freq * 2, length, "sine"), 0.15),
               scale(tone(freq * 1.003, length, "square", duty=0.125), 0.12))
    return lowpass(sustain(body, 0.03, 0.12, 0.6, 0.25), 2400)


def bass_voice(freq, length):
    body = mix(tone(freq, length, "triangle"), scale(tone(freq, length, "square"), 0.25))
    return lowpass(sustain(body, 0.004, 0.03, 0.75, 0.08), 700)


def pluck_voice(freq, length):
    return lowpass(envelope(tone(freq, length, "square", duty=0.125), 0.002, 0.07), 2600)


def pad_voice(freq, length):
    body = mix(tone(freq, length, "saw"), tone(freq * 1.006, length, "saw"), tone(freq * 0.995, length, "triangle"))
    return lowpass(sustain(body, 0.4, 0.5, 0.8, 1), 900)


def kick():
    return mix(thump(160, 45, 0.25, 0.08), scale(envelope(noise(0.01), 0.001, 0.003), 0.3))


def snare():
    rattle = lowpass(highpass(noise(0.2), 1200), 7000)
    return mix(envelope(rattle, 0.001, 0.06), scale(envelope(tone(190, 0.1, "triangle", 150), 0.001, 0.04), 0.7))


def hat(length=0.04):
    return envelope(highpass(noise(length + 0.02), 6000), 0.001, length / 3)


def make_song(bpm, bars, melody_bars, parts):
    """bars: list of chord names, melody_bars: list of melody strings (or None) per bar.
    parts says which layers play, returns the mixed samples."""
    step = 60 / bpm / 4
    bar_steps = 16
    loop_length = int(len(bars) * bar_steps * step * rate)
    lead = [0.0] * loop_length
    back = [0.0] * loop_length
    drums = [0.0] * loop_length
    instruments = {"kick": kick(), "snare": snare(), "hat": hat(), "open_hat": hat(0.12)}

    for b, chord_name in enumerate(bars):
        bar_start = b * bar_steps * step
        chord = CHORDS[chord_name]
        root = note(chord[0] + "2")
        if root < note("E2"):
            root *= 2
        part = parts[b]

        # bass
        if "bass" in part:
            for s in range(0, 16, 2):
                freq = root
                if part["bass"] == "octaves" and s % 4 == 2:
                    freq = root * 2
                if part["bass"] == "drive":
                    freq = root * (2 if s in (6, 14) else 1)
                place(back, scale(bass_voice(freq, step * 2), 0.36), bar_start + s * step, loop_length)
            if part["bass"] == "drive":
                # sixteenths in between for the boss
                for s in range(1, 16, 2):
                    place(back, scale(bass_voice(root, step), 0.2), bar_start + s * step, loop_length)
        if "long_bass" in part:
            place(back, scale(bass_voice(root, step * 8), 0.36), bar_start, loop_length)
            place(back, scale(bass_voice(root * 1.5, step * 8), 0.28), bar_start + 8 * step, loop_length)

        # chord tones going up and down
        if "arp" in part:
            octave = part["arp"]
            tones = [note(n + str(octave)) for n in chord]
            tones += [tones[0] * 2, tones[1] * 2]
            pattern = [0, 1, 2, 3, 4, 3, 2, 1]
            for s in range(16):
                freq = tones[pattern[s % 8]]
                place(back, scale(pluck_voice(freq, step * 1.5), 0.13), bar_start + s * step, loop_length)
        if "pad" in part:
            for n in chord:
                place(back, scale(pad_voice(note(n + "3"), 16 * step + 0.3), 0.09), bar_start, loop_length)

        # drums
        beat = part.get("drums")
        if beat == "soft":
            for s in (0, 8):
                place(drums, scale(instruments["kick"], 0.45), bar_start + s * step, loop_length)
            for s in range(2, 16, 4):
                place(drums, scale(instruments["hat"], 0.12), bar_start + s * step, loop_length)
        elif beat == "rock":
            for s in (0, 6, 8, 10):
                place(drums, scale(instruments["kick"], 0.8), bar_start + s * step, loop_length)
            for s in (4, 12):
                place(drums, scale(instruments["snare"], 0.45), bar_start + s * step, loop_length)
            for s in range(0, 16, 2):
                name = "open_hat" if s == 14 else "hat"
                place(drums, scale(instruments[name], 0.18), bar_start + s * step, loop_length)
        elif beat == "fill":
            for s in (0, 8):
                place(drums, scale(instruments["kick"], 0.8), bar_start + s * step, loop_length)
            for s in (10, 12, 13, 14, 15):
                place(drums, scale(instruments["snare"], 0.25 + s * 0.015), bar_start + s * step, loop_length)
        elif beat == "boss":
            for s in range(0, 16, 4):
                place(drums, scale(instruments["kick"], 0.85), bar_start + s * step, loop_length)
            for s in (4, 12):
                place(drums, scale(instruments["snare"], 0.5), bar_start + s * step, loop_length)
            for s in range(16):
                place(drums, scale(instruments["hat"], 0.15 if s % 2 else 0.08), bar_start + s * step, loop_length)

        # melody
        text = melody_bars[b]
        if text:
            voice = lead_voice
            volume = 0.38
            if part.get("soft"):
                voice = soft_lead_voice
                volume = 0.55
            s = 0
            for name, steps in parse_melody(text):
                if name:
                    freq = note(name)
                    place(lead, scale(voice(freq, steps * step), volume), bar_start + s * step, loop_length)
                    if part.get("double"):
                        place(lead, scale(voice(freq * 2, steps * step), volume / 3), bar_start + s * step, loop_length)
                s += steps
            if s != 16:
                print("waarschuwing: maat", b, "heeft", s, "stappen")

    lead = loop_echo(lead, step * 3, 0.3)
    back = loop_echo(back, step * 3, 0.2)
    song = [a + b + c for a, b, c in zip(lead, back, drums)]
    top = max(abs(v) for v in song) or 1
    return [math.tanh(v / top * 1.4) * 0.8 for v in song]


def make_menu_music():
    chords = ["Am", "F", "C", "G", "Am", "F", "C", "E"]
    melody_a = [
        "E5:6 D5:2 C5:4 B4:2 C5:2", "A4:8 C5:4 F5:4", "E5:6 D5:2 E5:4 G5:4", "D5:12 -:4",
        "E5:6 D5:2 C5:4 E5:4", "F5:6 E5:2 C5:4 A4:4", "G4:4 C5:4 E5:4 D5:4", "B4:12 -:4",
    ]
    melody_b = [
        "A5:4 G5:2 E5:2 C5:4 E5:4", "F5:8 E5:4 C5:4", "G5:4 E5:2 C5:2 E5:4 G5:4", "B4:4 D5:4 G5:8",
        "A5:6 G5:2 E5:4 A4:4", "C5:4 F5:4 A5:4 G5:4", "E5:6 D5:2 C5:4 E5:4", "G#5:8 B5:4 E5:4",
    ]
    quiet = {"pad": True, "arp": 4, "long_bass": True, "soft": True}
    full = {"pad": True, "arp": 4, "long_bass": True, "soft": True, "drums": "soft"}
    bars = chords * 3
    melody = [None] * 8 + melody_a + melody_b
    parts = [quiet] * 8 + [full] * 16
    return make_song(88, bars, melody, parts)


def make_run_music():
    chords_a = ["Em", "C", "G", "D", "Em", "C", "D", "B"]
    chords_b = ["C", "D", "Bm", "Em", "Am", "C", "D", "B"]
    melody_a = [
        "E5:3 B4:1 E5:2 G5:2 F#5:2 E5:2 D5:2 E5:2", "G5:6 E5:2 C5:2 D5:2 E5:4",
        "D5:3 B4:1 D5:2 G5:2 B5:4 A5:2 G5:2", "F#5:6 E5:2 D5:4 A4:4",
        "E5:3 B4:1 E5:2 G5:2 B5:4 A5:2 G5:2", "A5:4 G5:2 E5:2 G5:4 C6:4",
        "B5:4 A5:2 F#5:2 D5:4 F#5:4", "D#5:4 F#5:4 B5:6 -:2",
    ]
    melody_b = [
        "E5:4 G5:4 C6:4 B5:2 A5:2", "A5:6 F#5:2 D5:4 E5:2 F#5:2",
        "D5:4 F#5:4 B5:4 A5:2 F#5:2", "G5:8 E5:4 -:4",
        "A4:2 C5:2 E5:2 A5:2 G5:2 E5:2 C5:2 E5:2", "G5:6 E5:2 C5:4 E5:4",
        "F#5:4 A5:4 D6:4 C6:2 A5:2", "B5:8 D#5:4 F#5:4",
    ]
    intro = {"bass": "octaves", "arp": 4, "drums": "soft"}
    play = {"bass": "octaves", "arp": 4, "drums": "rock"}
    loud = {"bass": "octaves", "arp": 4, "drums": "rock", "double": True}
    bars = chords_a[:4] + chords_a + chords_b + chords_a + ["Em", "C", "D", "B"]
    melody = [None] * 4 + melody_a + melody_b + melody_a + [None] * 4
    parts = [intro] * 4 + [play] * 16 + [loud] * 8 + [play] * 3 + [dict(play, drums="fill")]
    return make_song(132, bars, melody, parts)


def make_boss_music():
    chords = ["Am", "Am", "Bb", "Am", "F", "E", "Am", "E"]
    riff = [
        "A4:2 A4:1 A5:1 G5:2 E5:2 A4:2 C5:2 E5:2 D#5:2", "E5:4 D5:2 C5:2 B4:4 C5:4",
        "Bb4:2 Bb4:1 Bb5:1 A5:2 F5:2 D5:2 F5:2 Bb5:4", "A5:8 G#5:4 E5:4",
        "F5:4 E5:2 F5:2 A5:4 C6:4", "B5:4 G#5:4 E5:4 D5:4",
        "C5:2 E5:2 A5:2 C6:2 B5:2 A5:2 E5:2 C5:2", "G#5:8 E5:4 B4:4",
    ]
    intro = {"bass": "drive", "drums": "boss"}
    play = {"bass": "drive", "drums": "boss", "arp": 4}
    loud = {"bass": "drive", "drums": "boss", "arp": 4, "double": True}
    bars = chords[:4] + chords + chords + chords + ["Am", "Am", "Bb", "E"]
    melody = [None] * 4 + riff + riff + riff + [None] * 4
    parts = [intro] * 4 + [play] * 8 + [loud] * 8 + [play] * 8 + [intro] * 3 + [dict(intro, drums="fill")]
    return make_song(150, bars, melody, parts)


def make_music():
    global rate
    rate = MUSIC_RATE
    random.seed(11)
    save(make_menu_music(), "music", "menu")
    save(make_run_music(), "music", "run")
    save(make_boss_music(), "music", "boss")


if __name__ == "__main__":
    make_effects()
    print("effecten klaar")
    make_music()
    print("muziek klaar")

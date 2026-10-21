import random

import pygame

import sprites
from menus import wrap_text, panel
from settings import W, H

# Botje, je behulpzame (nep) AI assistent
LINES = {
    "start": [
        "Hoi! Ik ben Botje, je AI assistent. Druk op H als ik irritant ben.",
        "Nieuwe run! Mijn neurale netwerk voorspelt: je gaat dood.",
        "Tip: vijanden doodmaken is goed. Doodgaan is slecht.",
        "Ik heb deze run 14 miljoen keer gesimuleerd. Je wint er 1.",
    ],
    "low_hp": [
        "Je HP is laag! Heb je overwogen om niet geraakt te worden?",
        "Waarschuwing: je bent bijna dood. Zal ik alvast een grafsteen bestellen?",
        "Lage HP gedetecteerd. Een Walvis pakket helpt hier echt bij.",
        "Rennen! Of niet. Ik ben maar een taalmodel.",
    ],
    "boss": [
        "Een baas! Volgens mijn data is die groot en boos.",
        "Baas gedetecteerd. Heb je al aan je testament gedacht?",
        "Geen paniek. Ik paniek wel voor je.",
    ],
    "level_up": [
        "Level omhoog! Kies iets goeds. Of iets slechts, ik oordeel niet.",
        "Gefeliciteerd! Je bent nu 0,3% minder slecht.",
        "Mijn advies: kies de middelste. Altijd de middelste.",
    ],
    "crowd": [
        "Dat zijn veel vijanden. Ik tel er... ja, heel veel.",
        "Ben je populair of word je omsingeld? Beide eigenlijk.",
        "Probeer eens de andere kant op te lopen.",
    ],
    "idle": [
        "Hallo? Ben je er nog? Stilstaan is een keuze.",
        "Je staat stil. De vijanden niet.",
        "Zal ik even voor je spelen? Grapje, ik heb geen handen.",
    ],
    "streak": [
        "Wauw! Zelfs ik ben onder de indruk. En ik ben een computer.",
        "Kill streak! Mag ik dit op social media zetten?",
        "Indrukwekkend. Ik pas mijn voorspelling aan naar: iets later dood.",
    ],
    "pickup": [
        "Ooh, iets glimmends!",
        "Goed opgepakt. Ik had het zelf ook gezien hoor.",
    ],
    "event": [
        "Er gebeurt iets raars. Ik doe alsof ik het had voorspeld.",
        "Random event! Mijn favoriet. Behalve als je doodgaat.",
    ],
    "upsell": [
        "Wist je dat Walvis pakket spelers 73% vaker winnen? Bron: ik.",
        "Psst. De gem winkel heeft een aanbieding. Hij heeft altijd een aanbieding.",
        "Een lootbox per dag houdt de dokter weg.",
        "Ik krijg geen commissie op gems. Echt niet. Druk op G in het menu.",
    ],
    "death": [
        "Zoals voorspeld. Volgende keer beter!",
        "RIP. Ik heb je statistieken naar je moeder gestuurd.",
        "Je bent dood. Wil je daar met mij over praten?",
    ],
    "menu": [
        "Tip: Druk op Enter om te spelen. Dat is eigenlijk het hele spel.",
        "Tip: Bliksem en meteoren samen is heel sterk. Denk ik.",
        "Tip: De mimic ziet eruit als een kist. Dat is het hele punt.",
        "Tip: Spoken lopen door muren. Wees niet zoals een spook.",
        "Tip: Je kan met dash (spatie) door vijanden heen.",
        "Tip: Bommenwerpers knipperen voordat ze ontploffen. Ren!",
        "Tip: De sjamaan heelt andere vijanden. Pak hem eerst.",
        "Tip: Druk op A voor achievements. Iedereen houdt van achievements.",
        "Tip: Ik ben geen echte AI. Of toch wel? Nee.",
        "Tip: 's Nachts is het donker. Dat is wetenschap.",
        "Fun fact: ik heb 0 parameters.",
        "Tip: In de gem winkel (G) zit een STARTER PACK met 99% korting!!",
    ],
}

enabled = True
line = ""
timer = 0
cooldown = 0
talk_time = 0
times_spoken = 0


def say(event, force=False, chance=1.0):
    global line, timer, cooldown, times_spoken
    if not enabled or event not in LINES:
        return
    if cooldown > 0 and not force:
        return
    if random.random() > chance:
        return
    # af en toe gewoon reclame maken
    if event not in ("death", "start") and random.random() < 0.15:
        event = "upsell"
    line = random.choice(LINES[event])
    timer = 4.5
    cooldown = 8
    times_spoken += 1


def toggle():
    global enabled, line, timer
    enabled = not enabled
    if enabled:
        line = "Ik ben terug! Heb je me gemist?"
        timer = 3
    else:
        line = ""
        timer = 0


def update(dt):
    global timer, cooldown, talk_time
    timer = max(0, timer - dt)
    cooldown = max(0, cooldown - dt)
    talk_time += dt


def draw(screen):
    if not enabled:
        return
    x = W - 60
    y = H - 80
    bob = 3 if int(talk_time * 2) % 2 == 0 else 0
    speed = 6 if timer > 0 else 1
    image = sprites.frame("botje", talk_time, speed)
    sprites.draw_centered(screen, image, (x, y + bob))
    if timer <= 0 or not line:
        return
    lines = wrap_text(line, 22, 260)
    height = 16 + len(lines) * 20
    left = x - 300
    top = y - height - 10
    panel(screen, (left, top, 280, height), (100, 240, 255))
    pygame.draw.polygon(screen, (100, 240, 255), [(left + 270, top + height - 12), (x - 20, y - 10), (left + 250, top + height)])
    for i, text in enumerate(lines):
        image = sprites.font(22).render(text, True, (255, 255, 255))
        screen.blit(image, (left + 10, top + 8 + i * 20))

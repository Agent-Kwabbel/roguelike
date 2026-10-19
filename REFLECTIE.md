# Reflectie op mijn leerdoelen

## Leerdoel 1: Pygame gebruiken (game loop, input, drawing, bewegen)

- **Heb ik dit leerdoel bereikt?** Ja
- **Waaruit blijkt dat?** main() in main.py heeft een game loop. clock.tick(FPS) geeft dt, en daarna handle_input, update en draw. Input staat in Player.read_input(). Alles beweegt met dt. De camera en de bewegende vloer heb ik zelf gemaakt.
- **Wat ging goed en wat vond je lastig?** Bewegen met dt en pygame.Vector2 ging snel. De camera was lastig. Bij het tekenen moet je de camera eraf trekken.
- **Wat zou je een volgende keer anders doen?** Sprites gebruiken in plaats van cirkels, en lettertypes een keer aanmaken in plaats van elk frame.

## Leerdoel 2: Code opdelen in aparte bestanden en classes

- **Heb ik dit leerdoel bereikt?** Grotendeels
- **Waaruit blijkt dat?** Elk onderdeel heeft een eigen bestand en alle constanten staan in settings.py. Een nieuwe enemy is een regel in ENEMY_TYPES en SPAWN_TABLE, en een nieuwe upgrade is een functie plus een regel in UPGRADES.
- **Wat ging goed en wat vond je lastig?** settings.py maakte balancing vrij makkelijk. Lastig was dat main.py groot is geworden.
- **Wat zou je een volgende keer anders doen?** Een Game class maken, handle_collisions() opsplitsen, en alle getallen in settings.py zetten.

## Leerdoel 3: Basis van game-logica (botsingen, spawnen, upgrades)

- **Heb ik dit leerdoel bereikt?** Ja.
- **Waaruit blijkt dat?** handle_collisions() in main.py checkt bullets, enemies  en orbs, spawn_enemy() kiest een plek rondom de speler en een type op basis van gewichten. Het levelsysteem en upgradesysteem is er ook nog.
- **Wat ging goed en wat vond je lastig?** Het upgradesysteem werkte goed doordat elke upgrade een eigen functie is. Lastig was de balans.
- **Wat zou je een volgende keer anders doen?** Botsingen checken is O(n^2), dus bij veel vijanden is een grid of spatial hash beter zoals ik in een vorige project had gemaakt. Ook meer testen voor de balans en meer wapens en upgrades toevoegen.

## Algemene reflectie

Ik heb geleerd hoe een game is opgebouwd: een loop die input leest, de staat bijwerkt en tekent, met alles op dt. Data los van logica houden (settings.py, ENEMY_TYPES, UPGRADES) maakt nieuwe content maken makkelijk. Het volgende wat ik wil verbeteren is main.py, met een Game class.

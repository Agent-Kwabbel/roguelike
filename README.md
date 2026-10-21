# Verdiepende opdracht: Game

Persoonlijke repository voor je game-project (WB1641 T2B). Hier werk je
aan je eigen game, houd je je voortgang bij en leg je aan het eind vast
wat je hebt geleerd.

## Wat moet je doen?

1. Vul hieronder je **beschrijving** en **persoonlijke leerdoelen** in en push dit als eerste commit.
2. Bouw je game in Python, vanuit `main.py`. Je mag extra bestanden en modules toevoegen.
3. Commit en push regelmatig (zie [Werkwijze](#werkwijze)).
4. Schrijf aan het einde je **reflectie** in `REFLECTIE.md`.

## Opzet

Dit project gebruikt [uv](https://docs.astral.sh/uv/) voor Python en
pakketbeheer. uv installeert zelf een recente Python-versie (3.14).
Wil je een extern pakket toevoegen, dan kan dat met `uv add <pakket>`.

```bash
uv run main.py      # start het spel
```

## Korte beschrijving van je game

Vul hier een korte beschrijving van je game aan (max. ongeveer 10 regels):

- **Idee:** De game is een top-down roguelike shooter geinspireerd door Vampire Survivors. De basis is dat je rondloopt als de karakter en de vijanden die rondlopen dood en hun xp verzamelt om levels te verzamelen en up te graden.
- **Functionaliteiten:** ik wil de speler implementeren met standard top-down bewegingen en automatisch schieten op de dichtsbijzijnde vijand. Daarnaast wil ik minstens twee soorten vijanden implementeren die spawnen rondom de speler, waarvan een een tragere maar sterkere vijand is en een kleinere, snellere, maar zwakkere vijand. Als laatst is belangrijk dat het level systeem wordt geimplementeerd. Dus dat je levels kan verzeamelen en dan als je een level omhoog gaat dat je een upgrade kan kiezen.
- **Gebouwen:** In de wereld spawnen willekeurig huizen, schuren, torens en ruines. Je loopt er via de deur in, het dak verdwijnt als je binnen bent en er ligt loot (kisten, hartjes, coins, gems). Muren houden jou en de vijanden tegen, vijanden lopen om naar de deur.
- **Terrein:** De wereld wordt gemaakt met een hoogtekaart (noise): meren, stranden, heuvels met terrassen en bergen met rotswanden en sneeuw. Diep water en bergen houden jou en de vijanden tegen, gebouwen staan alleen op vlak gras.
- **Besturing:** Je gebruikt WASD of pijltjes, er wordt automatisch geschoten op de dichtsbijzijnde vijand, en je kan je upgrade kiezen met 1, 2, of 3. Esc pauzeert (Q geeft de run op). In het menu open je met B de Battle Pass (P koopt premium met coins, Enter rust een skin of kogels uit), met C de dagelijkse en wekelijkse challenges en met K de winkel. F1 opent overal een dev menu (god mode, levels, baas spawnen, coins, tiers, save resetten). Met G open je de Gem Winkel (nep microtransacties, lootboxen, boosters, een huisdier), met A de achievements, H zet Botje de AI assistent aan of uit, en spatie is dash als je die upgrade hebt.
- **Menu en saves:** Het spel start volledig scherm (F11 wisselt, ook in Instellingen). Het hoofd- en pauzemenu werken met muis en toetsenbord. Er zijn 3 save slots in `saves/`, elk met een eigen voortgang en een opgeslagen run: in het pauzemenu kies je "Opslaan en naar menu" en daarna "Doorgaan". Als je het venster sluit tijdens een run wordt hij ook bewaard. De oude `battlepass.json` komt automatisch in slot 1.
- **Random troep:** nieuwe vijanden (spook, bommenwerper, necromancer met skeletten, spin, sjamaan, mimic, Koning Slijm), nieuwe wapens (boemerang, meteoor, vuurspoor), random events (goudkoorts, meteorenregen, bloedmaan, slijmregen, gem regen), dag en nacht, kill streaks met screen shake, nieuwe pickups (bevriezing, snelle schoenen, XP drankje) en een revive voor gems.

De sprites in `assets/` worden gemaakt door `uv run tools/make_sprites.py`.

## Persoonlijke leerdoelen

Bij het aanmelden voor deze opdracht heb je je eigen leerdoelen bepaald.
Vul ze hieronder in. Formuleer ze concreet, zodat je er aan het einde
op kunt terugkijken: wat wil je leren of kunnen, en hoe merk je dat het gelukt is?

- Ik leer Pygame gebruiken, zoals de game loop, input, drawing, en objecten laten bewegen.
- Ik leer mijn code netjes op te delen in aparte bestanden en classes, zodat mijn game makkelijk uit te breiden blijft.
- Ik leer de basis van game-logica bouwen, zoals botsingen, vijanden laten spawnen en een upgrade-systeem.

## Werkwijze

Commit en push regelmatig (`git add .`, `git commit -m "..."`, `git push`).
Commit bij voorkeur elke keer dat je een werkend tussenstapje hebt.
Alleen gepushte commits tellen mee als zichtbare voortgang.

## Reflectie op de leerdoelen

Aan het einde van het project reflecteer je op de vastgestelde leerdoelen.
Doe dit in het bestand `REFLECTIE.md`, dat al in deze repository staat.

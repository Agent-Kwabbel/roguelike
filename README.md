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
- **Besturing:** Je gebruikt WASD of pijltjes, er wordt automatisch geschoten op de dichtsbijzijnde vijand, en je kiest je upgrade met 1, 2 of 3, met A/D + Enter of met de muis. Esc pauzeert (Q geeft de run op) en spatie is dash als je die upgrade hebt. In het menu open je met K de winkel en met A de achievements.
- **Winkel en achievements:** Na een run krijg je coins. Daarmee koop je in de winkel skins, kogels en start perks (Tab wisselt van categorie, Enter of de knop koopt of rust uit). Achievements geven coins en een paar speciale items krijg je alleen door een achievement te halen.
- **Menu en saves:** Het spel start volledig scherm (F11 wisselt, ook in Instellingen). Alle menu's werken met muis en toetsenbord en de hele game is in het Engels. Er zijn 3 save slots in `saves/`, elk met een eigen voortgang en een opgeslagen run: in het pauzemenu kies je "Save and quit to menu" en daarna "Continue". Als je het venster sluit tijdens een run wordt hij ook bewaard. De oude `battlepass.json` komt automatisch in slot 1.
- **Extra's:** meer vijanden (spook, bommenwerper, necromancer met skeletten, spin, sjamaan, mimic, Koning Slijm), meer wapens (boemerang, meteoor, vuurspoor), random events (goudkoorts, meteorenregen, bloedmaan, slijmregen), dag en nacht, kill streaks met screen shake en nieuwe pickups (bevriezing, snelle schoenen, XP drankje).
- **Moeilijkheid en sfeer:** 5 moeilijkheidsgraden (Easy t/m Nachtmerrie). Huizen hebben een zichtbare deur met een paadje en het dak wordt doorzichtig als je dichtbij komt. Wolkenschaduwen, pluisjes, vuurvliegjes 's nachts, glinsterend water, vonken bij treffers en kogelsporen; "Extra effects" in Settings zet het meeste uit voor langzame computers.
- **Fases en eindspel:** een run gaat door fases (Meadow, Woods, Dusk, Cursed lands, The abyss, Last stand). Elke fase brengt nieuwe vijanden (ridder met harnas, magier, lavaslijm die plassen achterlaat, wraith die naast je teleporteert, kristalgolem), meer elites met extra krachten (snel, schild, vampier, ontploffend), nieuwe events (zwerm, omsingeling, mist, elite squad, vervloekte grond) en vijanden die harder slaan. Er zijn drie bazen die om de beurt komen (The Butcher, Bone Lord, Golem King), vanaf The abyss twee tegelijk. Na 30 minuten komt de Reaper en is de run voorbij: wie dat haalt heeft gewonnen. Hogere moeilijkheden beginnen bijna als Normal maar gaan sneller door de fases.
- **Evoluties en balans:** een wapen op max level met de juiste upgrade (bv. Magic wand + Faster fire rate) kan uit een kist evolueren naar een sterkere versie. Wisdom, Armor en Lifesteal hebben nu een maximum, en hoge levels kosten meer XP. Nieuwe upgrades: Cooldown en Area.
- **Geluid en muziek:** chiptune muziek in het menu, tijdens een run en een eigen nummer als er een baas is (de muziek wordt zachter in het pauzemenu). Elke actie heeft een geluidje: schieten, treffers, een ploppend geluid bij kills, XP bolletjes die steeds hoger klinken als je ze snel achter elkaar pakt, pickups, explosies, level up en klikjes in de menu's. Volume van muziek en effecten stel je in bij Settings.
- **Multiplayer (online co-op):** met "Multiplayer" in het menu speel je met maximaal 4 spelers samen, elk op een eigen computer. Eén speler kiest "Host game" (en de moeilijkheid), de anderen kiezen "Join game" en typen het IP-adres van de host. Op hetzelfde netwerk werkt dat meteen; via internet moet de host poort 50555 (TCP) doorsturen of iets als Tailscale gebruiken. De host rekent het spel uit, de anderen krijgen ~30 keer per seconde een update. Elke speler heeft een eigen camera met pijltjes naar teamgenoten buiten beeld, eigen XP en upgrades (het spel loopt door, je hebt 8 seconden om te kiezen met 1/2/3 of de muis). Ga je neer, dan kan een teamgenoot je weer oprapen door 3 seconden naast je te staan; de run is voorbij als iedereen neer is. Iedereen krijgt de coins van de run in zijn eigen save, een online run wordt niet opgeslagen. Samen spelen loont: sta je dicht bij een teamgenoot dan krijg je "team spirit" (snellere wapens en wat regeneratie, te zien aan een lijntje tussen jullie), je krijgt een deel van de XP die teamgenoten oppakken, en er zijn upgrades die alleen online bestaan (Medic, Guardian angel, Bond). Er zijn team events ("Split up!": houd twee cirkels tegelijk vast, "Stick together!": iedereen in een cirkel) die kisten opleveren, bazen kiezen om de beurt wie ze achterna zitten (rode pijl), opgeraakte spelers komen terug met de helft van hun HP en een online run geeft 25% meer coins per extra speler. Elke speler heeft zijn eigen kill streak. Vijanden verschijnen nu met een portaaltje buiten beeld van alle spelers in plaats van ineens op je scherm. Online achievements geven de skin "Team jacket" en de "Friendship bolts".
- **Chaos versie:** de versie met battle pass, gem winkel, lootboxen, Botje en het dev menu staat nog op de branch `chaos-arc` (`git checkout chaos-arc`).

De sprites in `assets/` worden gemaakt door `uv run tools/make_sprites.py`. De geluiden en muziek in `assets/sounds/` en `assets/music/` worden gemaakt door `uv run tools/make_sounds.py` (alles wordt in code gesynthetiseerd, geen externe bestanden).

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

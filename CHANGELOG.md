# Changelog

## PGS v0.0.2 (candidata — testes físicos pendentes)

- Identidade PGS aplicada aos controles Java, notificações, feeds e catálogos traduzidos sem alterar dados salvos ou a logo e joystick do jogo.
- Ferramenta de anúncios Discord isolada dos canais e credenciais PGS; não há doações PGS direcionadas ao projeto original.
- Atualização incremental do APK completo com assinatura permanente, package `com.nianticlabs.pokemongo` e `versionCode=2026111605`; histórico do projeto-base preservado.

## Unreleased — PGS (versão 0.3)

### New features

- **PGS languages:** Added a global interface-language selector with System, German, English, Spanish, French, Brazilian Portuguese, Russian, Italian, Traditional Chinese, Dutch, Thai and Korean. Menus, fixed choices, accessibility labels and dialogs use bundled offline catalogs. The selection is included in explicit backups and takes effect after restarting the game. Settings search matches both translated and English names.
- **Joystick direction lock:** Hold the centre for 1.5 seconds, drag and release to keep moving. Hold the padlock for half a second to stop. Hiding the joystick, leaving the map or losing its camera releases the lock.
- **Gift shortcut:** Open Send & Open Gifts directly from the quick menu. The shortcut can be hidden independently and opening it does not start a batch.
- **LivePokeMap refresh:** Choose a Shundo Sniper refresh interval from 30 seconds to 10 minutes, with a five-minute default. Global feed browsing refreshes manually.

### Improvements & fixes

- **VGP+ IV rules:** Wild catches use the encounter's populated IVs when selecting premium balls and berries.
- **Owned IV display:** The line stays above the details screen when opened over the Pokédex, and CP/level refresh after power-up without reopening the screen.
- **Real location:** VGP+ can receive a valid real GPS fix through the active game provider when spoofing is off, including devices where the framework getter hook is not called.
- **LivePokeMap limits:** Server refresh floors and Retry-After survive timing variation, interval changes, settings imports and stopping/restarting the sniper. Cancelled requests do not publish stale results.
- **Settings backup:** Global radius and the new refresh/menu options export and import correctly.
- **Buddy feeding:** A missing response no longer leaves feeding stuck after the same buddy is observed fed. Uncertain requests are not repeated or counted as confirmed successes.
- **Silver Pinap:** Corrected its item selection and migrated legacy manual-catch and buddy preferences while preserving berry priority.

## v0.2.5

[Full release notes](docs/releases/v0.2.5.md)

### Improvements & fixes

- More useful diagnostics for failed hooks, account readiness waits and VGP+ readiness, with clearer startup failure reasons and background/resume tracking.
- Logs include phone manufacturer/model, Android version
- Reduced repetitive logging and retained key startup diagnostics when logs rotate.

## v0.2.4

[Full release notes](docs/releases/v0.2.4.md)

### New features

- **Local time:** optional draggable clock in General Settings showing the time at your spoofed location.
- **Gym battles:** new "Battle until defeated" toggle to repeat full rounds from the same gym screen, with Smart healing between rounds when enabled for after battle. Uses your existing battle settings; off by default.
- **Evolve before transferring:** evolve new catches once or through all available stages before transferring. Use your current transfer rules or a separate species list; keep protections still apply.
- **Smart battling:** picks counters for the Pokémon you are fighting. It builds your team before gym, raid, and Rocket grunt battles, and swaps to your best counter during gym and Rocket battles. Off by default.

### Improvements & fixes

- Auto incubate dismisses the Eggs page opened after a hatch.
- Adventure Sync prompts are dismissed...hopefully.
- Skip cutscenes fixes
- During Dyndmax battles, Max energy orbs are automatically grabbed.
- Updated to latest game version (0.435.2)
- UI and performance updates

## v0.2.3

[Full release notes](docs/releases/v0.2.3.md)

### New features

- **Battery usage:** lower resolution, 20 FPS cap, or fewer effects (General Settings).
- **Throw variety:** random throw ratings from the ones you pick, under Throws and in VGP+. Off by default.
- **VGP+ catch-only list:** VGP+ catches only the species you choose.
- **Shundo Sniper black screen:** tap Dark on its card; tap the screen to return.

### Improvements & fixes

- Smart healing: new "Always heal fully" item choice.
- Shundo Sniper: starts sooner, moves on faster when its target doesn't appear, and shows missed checks.
- Transfer on catch: new "Keep 0% IV (0/0/0)" option.
- Gym Slotter and Berry Feeder: placing a defender now comes before feeding.
- World map tiles load faster.
- More cutscene skips.

## v0.2.2

[Full release notes](docs/releases/v0.2.2.md)

### New features

- **Skip cutscenes:** Off by default; turn it on under Settings > General Settings.
- **Smart healing:** Heals damaged Pokémon after battles, periodically, or both, choosing the mix of potions (and optionally revives) that wastes the least, so a Pokémon missing 5 HP gets a Potion, not a Max Potion. Choose the HP threshold (below 25%, 50% or 75%, or any HP missing) under Settings > Team Rocket, Gyms, Raids & Dynamax.
- **Shundo Sniper (experimental):** Teleports to 100% IV Pokémon from the PGS 100% IV feed (no sign-in needed, you're welcome you greedy bastards), LivePokeMap and PoGoCoordinates, checks each one in the background for shiny and catches only shinies. A shiny found during a cooldown is held until the cooldown ends, then caught. Open it from Automation. Its constant teleporting raises the risk of an account warning or ban, so use an alt account.

### Improvements & fixes

- Team GO Rocket battles: while any Rocket automation option is on, the next Pokémon is picked automatically when one faints.
- Location & overlays is renamed General Settings.
- Team Rocket settings now sit with gyms, raids and Dynamax under Team Rocket, Gyms, Raids & Dynamax.
- World map: PokéStops invaded by Team GO Rocket show darkened with a red R.
- Skip cutscenes also closes the "You're going too fast" warning.
- Teleports and walking could stop moving you on the map until the game was restarted, after the game switched between its location services; your position now keeps updating.
- Research: a selected task whose deletion fails is tried again after 30 seconds and then after 2 minutes, instead of staying in your task list until the game restarts.

## v0.2.1

[Full release notes](docs/releases/v0.2.1.md)

- **Catch chance:** Manual encounters show each ball's chance to catch, from the server's catch rate for that encounter with your berry, throw rating and curveball applied. The server's rate already includes your type medal bonus. Turn it off under Settings > Throws.
- **Auto ball:** Optionally picks the cheapest Poké, Great or Ultra Ball that reaches your target chance when a manual encounter opens and after each escape. A ball you pick by hand is kept until the next escape, and it never uses a Master Ball. Turn it on under Settings > Throws.
- **VGP+ auto ball:** VGP+ can also pick the cheapest Poké, Great or Ultra Ball that reaches your target chance for each throw, using the server's catch rate with your VGP+ berry, throw rating and curveball. It replaces the standard ball; the shiny, IV and CP/level Ultra Ball rules still apply, and it never uses a Master Ball. Turn it on under Virtual Go Plus > VGP+.
- **IV display:** Encounter and Pokémon stats screen IVs show on a light panel like the storage list. On the Pokémon stats screen the panel sits just above the name, in front of the Pokémon. Under Settings > Location & overlays > IV Display, each screen (Encounter, Pokémon stats screen, Pokémon storage list) has one button that cycles Off, Lv · IV · 15/14/12, Lv · IV and Lv · 15/14/12, and the storage list can now show the level too.
- **PvP keep:** Auto-transfer can keep catches with good PvP IVs, with a separate rank for Great League (default top 50), Ultra League (default top 10) and Master League (off by default), counting the Pokémon and anything it evolves into when that species is in PvPoke's top 150 for the league. Set it under Transfer on catch.
- **PvP IV display:** A new PvP format for the encounter, Pokémon stats screen and storage list IVs adds a second row with each league's crest and rank: the IV rank in Great and Ultra League, and the species' PvPoke rank in Master League.
- **PoGoCoordinates feed:** Feeds now asks which service to open: LivePokeMap or PoGoCoordinates. PoGoCoordinates searches Pokémon, raids, quests, weather, Rocket and power spots by IV, level, PvP rank and more, with Discord sign-in for higher result limits or guest use. Each service keeps its own sign-in.
- **VGP incense catches:** Virtual GO Plus and VGP+ now catch Pokémon attracted by your incense, not only wild spawns, with the same VGP+ rules, auto ball and transfer settings.
- **LivePokeMap PvP search:** A new PvP only filter lists just Pokémon ranked within your max rank in the leagues you tick, for example Great League top 50, ignoring the IV, level and size filters. Feed rows show any top-100 Great, Ultra or Little Cup rank.
- LivePokeMap's My Shinies tab and its filter are removed, since LivePokeMap no longer offers My Shinies.
- The quick menu and draggable overlays stay inside the screen, clear of the notch and navigation bar.

## v0.2.0

[Full release notes](docs/releases/v0.2.0.md)

- **Research:** Auto-claims completed field research, auto-deletes the field research tasks you select from a list grouped into Item, Encounter and Event, and can catch waiting field research encounters without the encounter screen, applying your transfer rules. Open it from the quick menu.
- **Hide overlay:** A new quick menu entry makes the game look stock after a confirmation: it hides every PGS button, status bar and message, plus the in-game IV text. Tap the screen with three fingers at once to show them again.
- **Storage list IVs:** Shows each Pokémon's IVs under its CP in the Pokémon storage list, as attack/defense/HP, a percentage, or both, colored like the encounter IV overlay. All IV display settings (inventory, encounter and storage list) are now together under Settings > Location & overlays > IV Display.
- **Encounter IVs:** The encounter IV overlay now also shows on field research reward encounters, not only wild spawns.
- **Always Hit:** Now also works when catching after a Max Battle.
- **AR+ throw bonus:** Wild catches now get the AR+ catch bonus.
- **GPX routes:** Starting a GPX route in Autowalk now asks where to begin: from the closest point on the route, from the beginning, or by teleporting to the beginning.
- **Copy coordinates:** The World map has Copy my location and Copy pin location buttons, which center the map on that spot and copy its coordinates. The quick menu Teleport dialog shows your current coordinates with Copy and Favorite buttons; Favorite saves the spot to Favorites under a name you choose.
- Menu options and buttons now look like buttons, with an outline and space between neighbouring buttons.

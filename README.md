# Slay the Spire 2 — Run Tracker

A client-side dashboard for analyzing your Slay the Spire 2 runs. Everything runs in your browser. Just point it at your `.run` files and go.

## Getting Started

1. Open `index.html` (or any page) in **Chrome** or **Edge**. No Firefox right now, sorry.
2. Click **Load Folder** and select your run history folder, which is typically here:
   ```
   %appdata%\SlayTheSpire2\steam\<SteamID>\profile1\saves\history\
   ```
3. Data persists for the session until you close the tab.
4. You can load files while a game is in progress. The active run file is automatically skipped.

---

## Pages

### Runs (`index.html`)

The main run viewer for browsing individual runs.

**Run List Sidebar**
- All loaded runs sorted newest-first
- Character names color-coded by class
- Win/loss badge, ascension level, date, and duration for each run
- "YOU" tag on your character in co-op runs
- Mode tag on runs played in a non-standard game mode (e.g. Blitz)
- Filter by Solo / Co-op / All, by character, by game mode (shown once more than one mode is loaded), and by game version (dropdown)

**Run Summary**
- Character names
- Win/loss result, killed-by encounter for losses, game-mode badge for non-standard modes
- Ascension, run time, seed, date, acts path, floor count, player count, version
- Active modifiers displayed as tags
- End-of-run badges (bronze / silver / gold) for the selected player
- Co-op player tabs tagged You / Partner (or P2, P3…) so same-character teams stay distinguishable

**HP & Gold Charts**
- Canvas-drawn line charts tracking HP (with max HP dashed line) and gold across all floors
- Blitz runs have no gold economy, so the gold chart is replaced by a summary of the Blitz merchant picks

**Final Deck**
- Card chips with thumbnail images, upgrade indicators (+N), enchantment badges, and duplicate counts
- Sort by deck order, card type, or cost; decks of 60+ cards group by card type by default
- Total / upgraded / enchanted card stats

**Damage per Floor**
- Average damage taken per floor broken down by act (Underdocks, Hive, Glory, etc.), plus a Full Run total
- Shows damage per floor value and raw total damage for each act

**Room Types**
- Count of each room type visited per act: Hallway fights, Elites, Events, Shops, Campfires

**Relics & Potions**
- End-of-run display with icons, names, and floor-acquired info
- Potion slots shown

**Floor-by-Floor Timeline**
- Every node visited, organized by act with act headers (acts sit side by side on very wide screens)
- Blitz merchant options with picked vs skipped display
- Color-coded node type icons (combat, elite, boss, rest, shop, treasure, unknown, ancient)
- Encounter name, monster list, turn count
- Tags for: damage, healing, max HP changes, gold changes, cards gained/removed/transformed/upgraded/enchanted, relics bought, potions used/bought/discarded, rest site choices, event choices
- Card reward groups with picked (highlighted) vs skipped (dimmed) options, split into visual groups when relics like Prayer Wheel double rewards
- Relic and potion reward groups with same picked/skipped display
- "Skipped all" indicator when entire reward groups were passed on
- HP bar and gold display at each floor
- Inline icons on all card/relic/potion references

**Tooltips**
- Hover any card, relic, or potion icon to see a popup with the item's name, type, rarity, cost, keywords (Exhaust, Ethereal, etc.), and full description

**Player Tabs**
- In multiplayer runs, tabs for each player's character to switch between their data

---

### Stats (`analytics.html`)

Aggregate analytics across all loaded runs, scoped to your character in multiplayer. The page is split into four tabs, with a filter bar that stays visible while you scroll.

**Filters (apply to every number on the page)**
- All runs / Solo / Co-op
- Game mode (Standard / Blitz / All modes), shown once more than one mode is loaded; defaults to Standard. Custom runs count as Standard
- Character chips (auto-detected, color-coded)
- Ascension dropdown
- Patch dropdown: "vX.Y and later", to leave out runs from older versions of the game
- Count abandoned runs as losses (off by default: abandoned runs are left out of every number, and the count is shown next to the tabs)

**How win rates are shown**
- Colour means better or worse than your own average for the runs being counted, not a fixed grading scale
- Small samples are pulled toward that average before colouring, and anything from fewer than 5 runs is faded
- Relics and "in deck" card rates are judged against an expected rate: what runs that reached the same act usually win. A late pickup was found by a run already doing well, so it has a higher bar

**Performance**
- Win rate with a community reference mark (Mega Crit's published figures, dated), last-20-runs form, streaks, highest ascension won, time played
- Results over time: win/loss dots, rolling 10-run win rate, and ascension as a stepped line
- How far runs get: started → cleared Act 1 → cleared Act 2 → won, with the number of runs that ended at each stage
- Solo vs co-op, by player count, and by partner character
- Characters table, Ascension table, starting-act table
- Records: fastest/longest win, smallest/largest winning deck, most relics, bosses beaten without damage, cards and relics seen

**Threats**
- Deadliest act, most lethal fight, most frequent killer, deaths by fight type
- Floor where runs died (histogram) and death rate by act (deaths ÷ runs that entered the act)
- Encounter record: fights, deaths, death rate, average damage taken and turns for every boss, elite and hallway fight
- Average HP by floor (wins vs losses), HP going into each act's boss, damage taken per floor, and where healing comes from

**Drafting**
- Cards table: offers, pick rate, win rate when you took it vs when you skipped it, lift (the gap between those two), runs in deck, deck win rate split by the act you picked it up in, and how often it ends up upgraded
- Relics table: source, win rate vs expected, win rate by act acquired; click a relic to limit the Cards table to runs that had it
- Ancient boons (Neow and the act-start ancients) and event choices with their win rates
- Card reward skip rate (overall, wins vs losses, by act) and most upgraded cards
- Blitz merchant options and how often you take each (when Blitz runs are included)

**Playstyle**
- Pace: seconds per floor, run length and floors climbed, wins vs losses
- Campfire choices per act, elites fought per act
- Final deck size distribution (as shares, so wins and losses are comparable), deck growth per act, removals per 10 floors
- Gold earned and spent per floor, peak gold and unspent gold; potions used per 10 floors and most-used potions
- Turns per fight by fight type, and badges earned

---

### Relics Encyclopedia (`relics.html`)

- Grid of all 315 relics with images, names, rarity/pool badges (color-coded), and descriptions
- Search by name or description
- Filter by rarity (Common, Uncommon, Rare, Shop, Event, Ancient, Starter)
- Filter by character pool (Shared, Ironclad, Silent, Defect, Necrobinder, Regent, Fool)

### Potions Encyclopedia (`potions.html`)

- Grid of all 67 potions with images, names, rarity/pool badges, and descriptions
- Search by name or description
- Filter by rarity (Common, Uncommon, Rare, Event, Token)
- Filter by character pool (Shared, Ironclad, Silent, Defect, Necrobinder, Regent, Fool)

### Cards Encyclopedia (`cards.html`)

- Grid of all 716 cards with images, names, energy cost (+ star cost for Regent), type/rarity/character badges, descriptions, and keyword badges
- Search by name or description
- Filter by type (Attack, Skill, Power, Status, Curse)
- Filter by rarity (Basic, Common, Uncommon, Rare, Ancient, Event)
- Filter by character (Ironclad, Silent, Defect, Necrobinder, Regent, Fool, Colorless, Event, Token, Curse, Status)

---

## Multiplayer Support

- Automatically detects your Steam ID (the ID appearing most frequently across co-op runs)
- All stats are scoped to your character only, even in multiplayer
- Filter by Solo / Co-op / All on both Runs and Stats pages
- "YOU" tag marks your character in co-op run displays and player tabs; other players are tagged Partner (or P2, P3…)

## Browser Support

- **Chrome / Edge / Opera** — Full support (folder loading + all features)
- **Firefox / Safari** — The "Load Folder" button does not work due to lack of `webkitdirectory` support. No current workaround.

## Privacy

All data stays in your browser. Run files are read locally via the File API and never uploaded anywhere. Session data is stored in IndexedDB and automatically cleared when you close your browser tabs.

## Known Issues

- **Deaths by Act — Event classification** is not fully accurate. Some deaths during event-triggered combat may be miscategorized. Working on a fix.
- **Regent card star costs** are not included in the card encyclopedia data. The energy cost displays correctly but the secondary star cost is missing.
- **Abandoned runs** do not count toward your win rate (they are excluded from the W/L calculation) but they do interrupt win streaks. Not an issue but worth noting.
- **Card descriptions** were scraped from [spire-codex.com](https://spire-codex.com) and may contain minor paraphrasing or become outdated as the game updates during early access.
- **Energy/star icons** in card descriptions display as `[E]` and `[S]` respectively, since the originals were inline images on the source site.
- **Upgraded card costs** are not reflected when sorting by cost in the Final Deck view. Some cards have reduced energy costs when upgraded (e.g. Body Slam goes from 1 to 0), but the sort uses base cost only. Fix TBD.

## Data Sources

- **Run files** — `.run` JSON files generated by Slay the Spire 2 (schema version 8, game builds v0.98-v0.99+)
- **Card/Relic/Potion data and images** — Scraped from [spire-codex.com](https://spire-codex.com)

Card, relic, and potion data is current through game version **v0.113.0** (beta branch — see [scripts/update_cards.py](scripts/update_cards.py)). When the game patches, regenerate it with:

```
py -X utf8 scripts/update_cards.py --fetch
```

This refreshes `cards_parsed.json`, the card/relic/potion constants in `index.html`/`analytics.html`/`cards.html`/`relics.html`/`potions.html`, and downloads art for any new items. Items removed from the game are kept in the lookup constants (and their art retained) so historical runs still render; they are dropped from the gallery pages. Run with `--check` first to preview changes without writing.

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
- Filter by Solo / Co-op / All as well as character

**Run Summary**
- Character names
- Win/loss result, killed-by encounter for losses
- Ascension, run time, seed, date, acts path, floor count, player count, version
- Active modifiers displayed as tags

**HP & Gold Charts**
- Canvas-drawn line charts tracking HP (with max HP dashed line) and gold across all floors

**Final Deck**
- Card chips with thumbnail images, upgrade indicators (+N), enchantment badges, and duplicate counts
- Total / upgraded / enchanted card stats

**Relics & Potions**
- End-of-run display with icons, names, and floor-acquired info
- Potion slots shown

**Floor-by-Floor Timeline**
- Every node visited, organized by act with act headers
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

Aggregate analytics across all loaded runs, scoped to your character in multiplayer.

**Filters**
- Solo / Co-op / All mode buttons with icons
- Character filter buttons (auto-detected from loaded runs, color-coded)
- Both filters combine (e.g., Solo + Ironclad)

**Overview Stat Cards (14 cards, 2 rows of 7)**
- Total Runs
- Win Rate (with W/L/abandoned breakdown)
- Total Play Time
- Avg Run Time
- Max Ascension Won (with highest attempted)
- Most Played Character (color-coded)
- Least Played Character (color-coded)
- Fastest Win
- Slowest Win
- Current Win Streak
- Best Win Streak
- Cards Seen (unique count / 576 with percentage)
- Relics Seen (unique count / 288 with percentage)
- Most Skipped Card (card offered most times but never picked, color-coded by character)

**Results Over Time**
- Canvas chart with green dots (wins), red dots (losses), orange dots (abandoned)
- Blue rolling win rate line (auto-scaled window size based on run count)

**Character Performance**
- Table: Character (color-coded), Runs, Wins, Losses, Win Rate (A-F graded), Avg Time, Avg Ascension, Avg Deck Size
- Mini bar visualization for win rate

**Win Rate by Ascension**
- Bar chart with A-F color grading
- Companion table with runs/wins/win rate per ascension level

**Causes of Death**
- Top Killers: scrollable table with encounter type classification (Boss/Elite/Normal/Weak/Event), color-coded bars
- Deaths by Act: stacked bar chart (Boss/Elite/Hallway/Event segments), acts in canonical order (Overgrowth, Underdocks, Hive, Glory), with legend

**HP & Deck Analysis**
- Avg HP % by Floor: line chart comparing wins (green) vs losses (red), with 0-100% Y-axis at 20% intervals
- Final Deck Size: overlaid histogram comparing wins vs losses

**Relics Table**
- Single sortable table: Relic (with icon), Runs, Win Rate (A-F graded), Avg Floor, Early WR (win rate when acquired in Act 1, with sample size)
- Search box for filtering by name
- Hide Starter Relics checkbox (checked by default, covers all 10 starter/upgraded relics)
- Min Runs filter
- *Click any relic row to filter the Cards table to runs containing that relic (synergy analysis)*
- Hover relic icon for tooltip with rarity and description

**Cards Table**
- Single sortable table: Card, Type (color-coded: Attack=red, Skill=blue, Power=yellow), Runs, Win Rate (A-F graded), Avg Floor, Early WR, Offered, Picked, Pick Rate
- Synergy filter banner when a relic is selected (shows relic icon, name, run count, clear button)
- Search box for filtering by name or type
- Hide Starter Cards checkbox (checked by default, covers all 19 basic cards)
- Min Runs filter
- Colorless shop purchases counted in Offered/Picked stats
- Hover card icon for tooltip with type, rarity, cost, keywords, and description

---

### Relics Encyclopedia (`relics.html`)

- Grid of all 288 relics with images, names, rarity/pool badges (color-coded), and descriptions
- Search by name or description
- Filter by rarity (Common, Uncommon, Rare, Shop, Event, Ancient, Starter)
- Filter by character pool (Shared, Ironclad, Silent, Defect, Necrobinder, Regent)

### Potions Encyclopedia (`potions.html`)

- Grid of all 63 potions with images, names, rarity/pool badges, and descriptions
- Search by name or description
- Filter by rarity (Common, Uncommon, Rare, Event, Token)
- Filter by character pool (Shared, Ironclad, Silent, Defect, Necrobinder, Regent)

### Cards Encyclopedia (`cards.html`)

- Grid of all 576 cards with images, names, energy cost (+ star cost for Regent), type/rarity/character badges, descriptions, and keyword badges
- Search by name or description
- Filter by type (Attack, Skill, Power, Status, Curse)
- Filter by rarity (Basic, Common, Uncommon, Rare, Ancient, Event)
- Filter by character (Ironclad, Silent, Defect, Necrobinder, Regent, Colorless, Event, Token, Curse, Status)

---

## Multiplayer Support

- Automatically detects your Steam ID (the ID appearing most frequently across co-op runs)
- All stats are scoped to your character only, even in multiplayer
- Filter by Solo / Co-op / All on both Runs and Stats pages
- "YOU" tag marks your character in co-op run displays and player tabs

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

## Data Sources

- **Run files** — `.run` JSON files generated by Slay the Spire 2 (schema version 8, game builds v0.98-v0.99+)
- **Card/Relic/Potion data and images** — Scraped from [spire-codex.com](https://spire-codex.com)

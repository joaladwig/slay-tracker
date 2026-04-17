# STS2 `.run` File Schema Documentation

All run files are JSON. Filenames are Unix timestamps (the `start_time` value). `.run.backup` files are copies of the previous save and can be ignored.

Observed across 57 solo + 25 two-player + 3 three-player + 2 four-player runs, all `schema_version: 8`, `game_mode: "standard"`, `platform_type: "steam"`.

---

## Top-Level Fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Always `8` in this dataset |
| `build_id` | string | Game version, e.g. `"v0.98.3"` |
| `game_mode` | string | Always `"standard"` so far |
| `platform_type` | string | `"steam"` |
| `seed` | string | Run seed, e.g. `"7MCCA23V5Y"` |
| `start_time` | int | Unix timestamp; also the filename |
| `run_time` | int | Total run duration in seconds |
| `ascension` | int | Ascension level (0 = no ascension) |
| `acts` | string[] | Ordered list of acts played, e.g. `["ACT.UNDERDOCKS", "ACT.HIVE", "ACT.GLORY"]` |
| `win` | bool | Whether the run was won |
| `was_abandoned` | bool | True if the player quit mid-run (can overlap with `win: false`) |
| `killed_by_encounter` | string | Encounter ID that killed the player, or `"NONE.NONE"` |
| `killed_by_event` | string | Event ID that killed the player, or `"NONE.NONE"`. Only observed: `"EVENT.NEOW"` |
| `modifiers` | array | Run modifiers (e.g. challenge modes). Empty in all observed runs |
| `players` | Player[] | One entry per player (1–4 in co-op) |
| `map_point_history` | Act[][] | Outer array = acts; inner array = map nodes visited in order |

### Acts Observed
- `ACT.UNDERDOCKS`
- `ACT.OVERGROWTH`
- `ACT.HIVE`
- `ACT.GLORY`

Runs always have 3 acts. Two Act 1 variants observed: Underdocks (50 runs) and Overgrowth (37 runs).

---

## `players[]` — Player Object

One object per player. In solo runs, `id` is always `1` (int). In co-op runs, `id` is the Steam ID (int).

| Field | Type | Notes |
|---|---|---|
| `id` | int | Player identifier (1 in solo; Steam ID in co-op) |
| `character` | string | See characters below |
| `deck` | Card[] | Final deck state at run end |
| `relics` | RelicEntry[] | All relics held at run end, in acquisition order |
| `potions` | PotionSlot[] | Potions remaining at run end |
| `max_potion_slot_count` | int | Potion belt capacity |

### Characters Observed
- `CHARACTER.IRONCLAD`
- `CHARACTER.SILENT`
- `CHARACTER.DEFECT`
- `CHARACTER.NECROBINDER`
- `CHARACTER.REGENT`

### Card Entry (in `deck[]`)
| Field | Type | Notes |
|---|---|---|
| `id` | string | Card ID, e.g. `"CARD.IRON_WAVE"` |
| `floor_added_to_deck` | int | Map point index when added |
| `current_upgrade_level` | int? | Present only if card is upgraded (value = upgrade level, e.g. `1`) |
| `enchantment` | object? | Present if enchanted: `{ "id": "ENCHANTMENT.STEADY", "amount": 1 }` |
| `props` | object? | Dynamic card state: `{ "ints": [{ "name": "...", "value": N }] }`. Used for cards with variable values (e.g. scaling damage, TinkerTime riders) |

### Relic Entry (in `relics[]`)
| Field | Type | Notes |
|---|---|---|
| `id` | string | Relic ID, e.g. `"RELIC.BURNING_BLOOD"` |
| `floor_added_to_deck` | int | Map point index when acquired |

### Potion Slot (in `potions[]`)
| Field | Type | Notes |
|---|---|---|
| `id` | string | Potion ID, e.g. `"POTION.ASHWATER"` |
| `slot_index` | int | Slot position (0-based) |

---

## `map_point_history[][]` — The Route

Outer array indexes acts (0, 1, 2). Inner array is ordered map nodes visited. Each node:

| Field | Type | Notes |
|---|---|---|
| `map_point_type` | string | See types below |
| `rooms` | Room[] | Usually one room; the encounter/event that happened here |
| `player_stats` | PlayerStats[] | One entry per player; state deltas at this node |

### Map Point Types
`ancient`, `boss`, `elite`, `monster`, `rest_site`, `shop`, `treasure`, `unknown`

- `ancient` — Start-of-run Neow bonus selection
- `unknown` — Random event room (can be combat or event)
- `treasure` — Chest room
- `rest_site` — Campfire

### Room Object
| Field | Type | Notes |
|---|---|---|
| `room_type` | string | `boss`, `elite`, `event`, `monster`, `rest_site`, `shop`, `treasure` |
| `model_id` | string? | Encounter or event ID. Absent for generic rooms (shops, campfires, chests) |
| `monster_ids` | string[]? | Present for combat rooms; list of monster IDs |
| `turns_taken` | int | Turns in combat (0 for non-combat rooms) |

---

## `player_stats` — Per-Node State Delta

Tracks what happened to each player at each map node. All fields below may be absent if zero/not applicable.

### Always Present
| Field | Type | Notes |
|---|---|---|
| `player_id` | int | Matches `players[].id` |
| `current_hp` | int | HP after this node |
| `max_hp` | int | Max HP after this node |
| `damage_taken` | int | |
| `hp_healed` | int | |
| `max_hp_gained` | int | |
| `max_hp_lost` | int | |
| `current_gold` | int | Gold after this node |
| `gold_gained` | int | |
| `gold_lost` | int | |
| `gold_spent` | int | Spent at shop or similar |
| `gold_stolen` | int | |

### Conditional Fields
| Field | Type | Notes |
|---|---|---|
| `card_choices` | CardChoice[]? | Cards offered; each has `card.id`, `card.floor_added_to_deck` (if picked), `was_picked` bool |
| `cards_gained` | CardRef[]? | Cards added to deck (from reward, event, shop, etc.) |
| `cards_removed` | CardRef[]? | Cards removed (shop purge, event) |
| `cards_transformed` | CardRef[]? | Cards transformed |
| `cards_enchanted` | CardRef[]? | Cards that received an enchantment |
| `upgraded_cards` | string[]? | Card IDs upgraded at campfire (`SMITH`) |
| `downgraded_cards` | string[]? | Card IDs downgraded |
| `relic_choices` | RelicChoice[]? | Relics offered; each has `choice` (ID) and `was_picked` bool. Normally appears on `ancient`, `elite`, `treasure`, and `shop` nodes. Rarely appears on `boss` nodes — observed once on a Regent player after the Act 1 boss; likely triggered by `RELIC.DIVINE_RIGHT` rather than a standard boss reward. Can have multiple `was_picked: true` entries in that case. |
| `relics_removed` | string[]? | Relic IDs removed |
| `potion_choices` | PotionChoice[]? | Potions offered; each has `choice` (ID) and `was_picked` bool |
| `potion_used` | string[]? | Potion IDs used during combat |
| `potion_discarded` | string[]? | Potion IDs discarded |
| `bought_colorless` | ?  | Purchased colorless cards |
| `bought_potions` | ? | Purchased potions |
| `bought_relics` | ? | Purchased relics |
| `event_choices` | EventChoice[]? | Choices made at events; each has `title.key`, `title.table`, and optional `variables` |
| `ancient_choice` | AncientChoice[]? | Neow bonus options; each has `TextKey`, `title`, `was_chosen` bool |
| `rest_site_choices` | string[]? | Campfire action taken |
| `completed_quests` | ?  | Quest completions |

### Rest Site Choices Observed
`HEAL`, `SMITH`, `DIG`, `COOK`, `HATCH`, `LIFT`

---

## Notes & Quirks

- **Floor numbering**: `floor_added_to_deck` on cards/relics is the index into the flattened `map_point_history` (0-based across all acts combined), not a per-act floor number.
- **Co-op player IDs**: In solo runs `player_id` is always `1`. In co-op it's the full Steam ID integer (matches `players[].id`).
- **`was_abandoned: true`** can appear alongside `win: false` — these are runs the player quit; killed_by fields will be `NONE.NONE`.
- **Death at Neow**: `killed_by_event: "EVENT.NEOW"` is possible (observed in data).
- **`props` on cards**: Used for cards with mutable state. The `ints` array contains named integer values. Examples seen: `SpoilsActIndex`, `TinkerTimeType`, `TinkerTimeRider`, `CurrentDamage`, `IncreasedDamage`.
- **Shop `card_choices`**: At shops, `card_choices` lists all cards for sale (none have `floor_added_to_deck`), while `cards_gained` reflects what was actually purchased.
- **`map_point_type` vs `room_type`**: These overlap but differ — e.g. `map_point_type: "unknown"` can contain `room_type: "event"` or `room_type: "monster"`.

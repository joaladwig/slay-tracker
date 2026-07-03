#!/usr/bin/env python3
"""Regenerate card/relic/potion data from the spire-codex API.

Usage:
    py -X utf8 scripts/update_cards.py --fetch [--check]
    py -X utf8 scripts/update_cards.py path/to/dir-with-api-json [--check]

The directory form expects api_cards.json / api_relics.json /
api_potions.json saved from the corresponding API endpoints.

Updates, in repo root:
    cards_parsed.json                                   (current cards, name-sorted)
    index.html      CARD_TYPES / CARD_COSTS / CARD_TIPS / CARD_TIPS_UPGRADED /
                    RELIC_TIPS / POTION_TIPS
    analytics.html  CARD_TYPES / CARD_CHARS / CARD_TIPS / RELIC_TIPS /
                    TOTAL_CARD_COUNT / TOTAL_RELIC_COUNT
    cards.html      allCards
    relics.html     allRelics
    potions.html    allPotions
    assets/{cards,relics,potions}/<slug>.png            (downloads missing art)

Items removed from the game are dropped from the gallery pages but their
entries in the lookup constants (and their art) are preserved so historical
runs that contain them still render.

--check: regenerate and report differences without writing anything.
"""
import json
import re
import sys
import io
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://spire-codex.com/api/cards"
SITE = "https://spire-codex.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ---------------------------------------------------------------- rendering

def _split_top(s, sep="|"):
    """Split on sep at brace depth 0."""
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _find_colon(s):
    depth = 0
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ":" and depth == 0:
            return i
    return -1


BUILTIN_VARS = {"singleStarIcon": "[star:1]", "singleEnergyIcon": "[energy:1]"}


def _lookup(varname, vars):
    if varname in vars:
        return vars[varname]
    for k, v in vars.items():
        if k.lower() == varname.lower():
            return v
    if varname in BUILTIN_VARS:
        return BUILTIN_VARS[varname]
    # calculated-in-combat values are unknown outside combat
    return "X" if varname.startswith("Calculated") else 0


def render(template, vars):
    """Render a description_raw template with the given vars."""
    out, i = [], 0
    while i < len(template):
        ch = template[i]
        if ch != "{":
            out.append(ch)
            i += 1
            continue
        depth, j = 1, i + 1
        while j < len(template) and depth:
            if template[j] == "{":
                depth += 1
            elif template[j] == "}":
                depth -= 1
            j += 1
        out.append(_render_expr(template[i + 1:j - 1], vars))
        i = j
    return "".join(out)


def _render_expr(expr, vars):
    c = _find_colon(expr)
    if c < 0:
        return str(_lookup(expr, vars))
    name, spec = expr[:c], expr[c + 1:]
    val = _lookup(name, vars)
    if spec in ("diff()", "inverseDiff()"):
        return str(val)
    if spec.startswith("energyIcons("):
        arg = spec[len("energyIcons("):spec.index(")")]
        return "[energy:%s]" % (arg or val)
    if spec.startswith("starIcons("):
        arg = spec[len("starIcons("):spec.index(")")]
        return "[star:%s]" % (arg or val)
    if spec.startswith("plural:"):
        branches = _split_top(spec[len("plural:"):])
        chosen = branches[0] if val == 1 else branches[-1]
        return render(chosen, vars)
    if spec.startswith("cond:"):
        branches = _split_top(spec[len("cond:"):])
        chosen = branches[0] if val else (branches[1] if len(branches) > 1 else "")
        return render(chosen, vars)
    if spec.startswith("choose("):
        close = spec.index(")")
        options = spec[len("choose("):close].split("|")
        branches = _split_top(spec[close + 2:])  # skip "):"
        idx = options.index(str(val)) if str(val) in options else len(branches) - 1
        return render(branches[min(idx, len(branches) - 1)], vars)
    # bare conditional: {Var:then|else} / {Var:then}
    branches = _split_top(spec)
    chosen = branches[0] if val else (branches[1] if len(branches) > 1 else "")
    return render(chosen, vars)


def finalize(text):
    """Markup-tagged template output -> plain single-line description."""
    if not text:
        return ""
    text = re.sub(r"\[energy:(\d+)\]", lambda m: "[E]" * int(m.group(1)), text)
    text = re.sub(r"\[star:(\d+)\]", lambda m: "[S]" * int(m.group(1)), text)
    text = re.sub(r"\[/?[a-z_]+\]", "", text)  # [gold] etc.; keeps [E]/[S]
    return re.sub(r"\s+", " ", text).strip()

# ---------------------------------------------------------------- upgrades

FLAG_PREFIX = {"add_innate": "Innate.", "add_retain": "Retain."}
FLAG_REMOVE = {"remove_exhaust": "Exhaust.", "remove_ethereal": "Ethereal."}


def upgraded_vars(card):
    """Apply upgrade diffs to vars; returns (vars, flags, upgraded_cost)."""
    vars = dict(card.get("vars") or {})
    flags, cost = [], None
    for k, dv in (card.get("upgrade") or {}).items():
        if k == "cost":
            cost = dv
            continue
        if k in FLAG_PREFIX or k in FLAG_REMOVE:
            flags.append(k)
            continue
        key = next((vk for vk in vars if vk.lower() == k.lower()), k)
        if isinstance(dv, str):
            vars[key] = vars.get(key, 0) + int(dv)
        else:
            vars[key] = dv
    return vars, flags, cost


def upgraded_description(card, base_final):
    """Final upgraded text, or None if identical to the base text."""
    upvars, flags, _ = upgraded_vars(card)
    if card.get("upgrade_description"):
        # pre-rendered by the API; flags are not spelled out in text
        text = finalize(card["upgrade_description"])
    else:
        has_var_diffs = upvars != (card.get("vars") or {})
        if has_var_diffs:
            text = finalize(render(card.get("description_raw") or "", upvars))
        else:
            text = base_final  # flag/cost-only upgrade: base text unchanged
        for f in flags:
            if f in FLAG_PREFIX:
                text = (FLAG_PREFIX[f] + " " + text).strip()
            else:
                text = re.sub(r"\s+", " ",
                              text.replace(FLAG_REMOVE[f], "")).strip()
    return text if text != base_final else None

# ---------------------------------------------------------------- build

def card_entry(c):
    """API card -> cards_parsed.json entry (key order matters)."""
    e = {
        "name": c["name"],
        "slug": c["id"].lower(),
        "cost": "X" if c.get("is_x_cost") else str(c["cost"]),
        "type": c["type_key"].lower(),
        "rarity": c["rarity_key"].lower(),
        "character": c["color"],
        "description": finalize(c["description"]),
        "keywords": c.get("keywords") or [],
    }
    if c.get("star_cost") is not None:
        e["starCost"] = c["star_cost"]
    _, _, upcost = upgraded_vars(c)
    if upcost is not None:
        e["upgradedCost"] = str(upcost)
    upd = upgraded_description(c, e["description"])
    if upd is not None:
        e["upgradedDescription"] = upd
    return e


def tip(entry, upgraded=False):
    kw = " · ".join(entry["keywords"])
    cost = entry.get("upgradedCost", entry["cost"]) if upgraded else entry["cost"]
    desc = entry.get("upgradedDescription", entry["description"]) if upgraded \
        else entry["description"]
    plus = "+1 · " if upgraded else ""
    return "%s · %s · Cost %s · %s%s— %s" % (
        entry["type"], entry["rarity"], cost, plus, kw + " " if kw else "", desc)


def is_upgradeable(c):
    return bool(c.get("upgrade") or c.get("upgrade_description"))


def build_constants(cards_api):
    entries = {("CARD." + c["id"]): card_entry(c) for c in cards_api}
    consts = {"CARD_TYPES": {}, "CARD_COSTS": {}, "CARD_CHARS": {},
              "CARD_TIPS": {}, "CARD_TIPS_UPGRADED": {}}
    for key in sorted(entries):
        e = entries[key]
        consts["CARD_TYPES"][key] = e["type"]
        consts["CARD_COSTS"][key] = e["cost"]
        consts["CARD_CHARS"][key] = e["character"]
        consts["CARD_TIPS"][key] = tip(e)
    api_by_key = {("CARD." + c["id"]): c for c in cards_api}
    for key in sorted(entries):
        if is_upgradeable(api_by_key[key]):
            consts["CARD_TIPS_UPGRADED"][key] = tip(entries[key], upgraded=True)
    return entries, consts


def relic_entry(r):
    return {
        "name": r["name"],
        "slug": r["id"].lower(),
        "rarity_pool": r["rarity"] + "·" + r["pool"],
        "description": finalize(r["description"]),
    }


def potion_entry(p):
    return {
        "name": p["name"],
        "slug": p["id"].lower(),
        "rarity": p["rarity_key"].lower(),
        "pool": p["pool"],
        "description": finalize(p["description"]),
    }


def relic_tips(relics_api):
    return {("RELIC." + r["id"]): "%s — %s" % (r["rarity"],
                                               finalize(r["description"]))
            for r in sorted(relics_api, key=lambda r: r["id"])}


def potion_tips(potions_api):
    return {("POTION." + p["id"]): "%s · %s — %s" % (
                p["rarity_key"].lower(), p["pool"], finalize(p["description"]))
            for p in sorted(potions_api, key=lambda p: p["id"])}

# ---------------------------------------------------------------- splicing

def splice_const(src, name, value, keep_legacy=True):
    """Replace `const <name> = {...};` (single line) preserving removed ids."""
    m = re.search(r"const %s = (\{.*?\}|\[.*?\]);" % re.escape(name), src)
    if not m:
        raise SystemExit("const %s not found" % name)
    if keep_legacy and m.group(1).startswith("{"):
        old = json.loads(m.group(1))
        merged = dict(value)
        for k, v in old.items():
            if k not in merged:
                merged[k] = v
        value = {k: merged[k] for k in sorted(merged)}
    dumped = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return src[:m.start(1)] + dumped + src[m.end(1):], m.group(1)

# ---------------------------------------------------------------- art

def download_art(slugs, kind, check=False):
    """kind is 'cards', 'relics', or 'potions' (repo dir == site dir)."""
    art_dir = ROOT / "assets" / kind
    missing = [s for s in slugs if not (art_dir / (s + ".png")).exists()]
    for slug in missing:
        if check:
            print("  %s art missing: %s.png" % (kind, slug))
            continue
        from PIL import Image
        url = "%s/static/images/%s/%s.webp" % (SITE, kind, slug)
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=60).read()
        img = Image.open(io.BytesIO(data))
        img.save(art_dir / (slug + ".png"))
        print("  downloaded %s/%s.png (%dx%d)"
              % (kind, slug, img.width, img.height))
    return missing

# ---------------------------------------------------------------- main

def load_api(args):
    data = {}
    for kind in ("cards", "relics", "potions"):
        if "--fetch" in sys.argv:
            req = urllib.request.Request("%s/api/%s" % (SITE, kind), headers=UA)
            data[kind] = json.loads(urllib.request.urlopen(req, timeout=90).read())
        elif args:
            data[kind] = json.loads(
                (Path(args[0]) / ("api_%s.json" % kind)).read_text(encoding="utf-8"))
        else:
            raise SystemExit(__doc__)
    return data


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    api = load_api(args)
    cards_api = api["cards"]

    # renderer sanity check against the API's own pre-rendered descriptions
    bad = [c["name"] for c in cards_api if c.get("description_raw") and
           finalize(render(c["description_raw"], c.get("vars") or {}))
           != finalize(c["description"])]
    print("renderer oracle: %d/%d base descriptions reproduced"
          % (len(cards_api) - len(bad), len(cards_api)))
    if bad:
        print("  mismatches:", ", ".join(bad[:20]))
    derived_bad = [n for n in bad for c in [next(c for c in cards_api if c["name"] == n)]
                   if is_upgradeable(c) and not c.get("upgrade_description")
                   and upgraded_vars(c)[0] != (c.get("vars") or {})]
    if derived_bad:
        print("  WARNING: renderer mismatch on cards needing derived upgrades:",
              ", ".join(derived_bad))

    entries, consts = build_constants(cards_api)
    consts["RELIC_TIPS"] = relic_tips(api["relics"])
    consts["POTION_TIPS"] = potion_tips(api["potions"])
    parsed = sorted(entries.values(), key=lambda e: e["name"])
    parsed_json = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    counts = {"TOTAL_CARD_COUNT": len(entries),
              "TOTAL_RELIC_COUNT": len(api["relics"])}

    plan = [
        ("index.html", ["CARD_TYPES", "CARD_COSTS", "CARD_TIPS",
                        "CARD_TIPS_UPGRADED", "RELIC_TIPS", "POTION_TIPS"]),
        ("analytics.html", ["CARD_TYPES", "CARD_CHARS", "CARD_TIPS",
                            "RELIC_TIPS"]),
    ]
    for fname, names in plan:
        path = ROOT / fname
        src = orig = path.read_text(encoding="utf-8")
        for name in names:
            src, old_raw = splice_const(src, name, consts[name])
            if check:
                new_raw = re.search(
                    r"const %s = (\{.*?\});" % name, src).group(1)
                o, n = json.loads(old_raw), json.loads(new_raw)
                diff = [k for k in set(o) | set(n) if o.get(k) != n.get(k)]
                print("%s %s: %d entries differ" % (fname, name, len(diff)))
        for cname, cval in counts.items():
            src = re.sub(r"const %s = \d+;" % cname,
                         "const %s = %d;" % (cname, cval), src)
        if not check and src != orig:
            path.write_text(src, encoding="utf-8", newline="")
            print("updated %s" % fname)

    galleries = [
        ("cards.html", "allCards", parsed),
        ("relics.html", "allRelics",
         sorted((relic_entry(r) for r in api["relics"]),
                key=lambda e: e["name"])),
        ("potions.html", "allPotions",
         sorted((potion_entry(p) for p in api["potions"]),
                key=lambda e: e["name"])),
    ]
    for fname, name, value in galleries:
        path = ROOT / fname
        src, old_raw = splice_const(path.read_text(encoding="utf-8"),
                                    name, value, keep_legacy=False)
        if check:
            old_list = {e["name"]: e for e in json.loads(old_raw)}
            new_list = {e["name"]: e for e in value}
            changed = [n for n in set(old_list) & set(new_list)
                       if old_list[n] != new_list[n]]
            print("%s %s: %d changed, %d added, %d removed"
                  % (fname, name, len(changed),
                     len(set(new_list) - set(old_list)),
                     len(set(old_list) - set(new_list))))
        else:
            path.write_text(src, encoding="utf-8", newline="")
            print("updated %s (%d %s)" % (fname, len(value), name))

    if not check:
        (ROOT / "cards_parsed.json").write_text(parsed_json, encoding="utf-8",
                                                newline="")
        print("updated cards_parsed.json (%d cards)" % len(parsed))

    download_art([e["slug"] for e in entries.values()], "cards", check=check)
    download_art([r["id"].lower() for r in api["relics"]], "relics", check=check)
    download_art([p["id"].lower() for p in api["potions"]], "potions", check=check)


if __name__ == "__main__":
    main()

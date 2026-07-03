#!/usr/bin/env python3
"""Regenerate card data from the spire-codex API.

Usage:
    py -X utf8 scripts/update_cards.py path/to/api_cards.json [--check]
    py -X utf8 scripts/update_cards.py --fetch [--check]

Updates, in repo root:
    cards_parsed.json                                   (current cards, name-sorted)
    index.html      CARD_TYPES / CARD_COSTS / CARD_TIPS / CARD_TIPS_UPGRADED
    analytics.html  CARD_TYPES / CARD_CHARS / CARD_TIPS
    cards.html      allCards
    assets/cards/<slug>.png                             (downloads missing art)

Cards removed from the game are dropped from cards_parsed.json / cards.html
but their entries in the lookup constants (and their art) are preserved so
historical runs that contain them still render.

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

def download_art(entries, check=False):
    art_dir = ROOT / "assets" / "cards"
    missing = [e for e in entries.values()
               if not (art_dir / (e["slug"] + ".png")).exists()]
    for e in missing:
        if check:
            print("  art missing: %s.png" % e["slug"])
            continue
        from PIL import Image
        url = "%s/static/images/cards/%s.webp" % (SITE, e["slug"])
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=60).read()
        img = Image.open(io.BytesIO(data))
        img.save(art_dir / (e["slug"] + ".png"))
        print("  downloaded %s.png (%dx%d)" % (e["slug"], img.width, img.height))
    return missing

# ---------------------------------------------------------------- main

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    if "--fetch" in sys.argv:
        req = urllib.request.Request(API_URL, headers=UA)
        cards_api = json.loads(urllib.request.urlopen(req, timeout=90).read())
    elif args:
        cards_api = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    else:
        raise SystemExit(__doc__)

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
    parsed = sorted(entries.values(), key=lambda e: e["name"])
    parsed_json = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))

    plan = [
        ("index.html", ["CARD_TYPES", "CARD_COSTS", "CARD_TIPS",
                        "CARD_TIPS_UPGRADED"]),
        ("analytics.html", ["CARD_TYPES", "CARD_CHARS", "CARD_TIPS"]),
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
        src = re.sub(r"const TOTAL_CARD_COUNT = \d+;",
                     "const TOTAL_CARD_COUNT = %d;" % len(entries), src)
        if not check and src != orig:
            path.write_text(src, encoding="utf-8", newline="")
            print("updated %s" % fname)

    cards_html = ROOT / "cards.html"
    src, old_raw = splice_const(cards_html.read_text(encoding="utf-8"),
                                "allCards", parsed, keep_legacy=False)
    if check:
        print("cards.html allCards: %d -> %d cards"
              % (len(json.loads(old_raw)), len(parsed)))
        old_parsed = json.loads((ROOT / "cards_parsed.json")
                                .read_text(encoding="utf-8"))
        ob = {c["name"]: c for c in old_parsed}
        nb = {c["name"]: c for c in parsed}
        changed = [n for n in set(ob) & set(nb) if ob[n] != nb[n]]
        print("cards_parsed.json: %d changed, %d added, %d removed"
              % (len(changed), len(set(nb) - set(ob)), len(set(ob) - set(nb))))
    else:
        cards_html.write_text(src, encoding="utf-8", newline="")
        (ROOT / "cards_parsed.json").write_text(parsed_json, encoding="utf-8",
                                                newline="")
        print("updated cards.html, cards_parsed.json (%d cards)" % len(parsed))

    download_art(entries, check=check)


if __name__ == "__main__":
    main()

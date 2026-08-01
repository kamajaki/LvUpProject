# -*- coding: utf-8 -*-
"""클라 Dead_Reward × Table_Reward × Table_Item → 드랍표 JSON + HTML 주입"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(r"c:\workspace\romc-data-extractor\src")))

from romc_data_extractor.config import GamePaths
from romc_data_extractor.lua_table import LuaTableSource
from romc_data_extractor.translation import TranslationLookup

ROOT = Path(r"c:\workspace\LvUpProject")
GAME = Path(r"C:\Program Files (x86)\XD\ROM Classic")
OUT_DIR = ROOT / "extracted_romc"
HTML_FILES = [
  ROOT / "index.html",
  ROOT / "leveling-helper.html",
  ROOT / "레벨링_도우미.html",
]

# Skip obvious non-field / test names when building the public list.
SKIP_NAME_SUB = ("테스트", "Test", "dummy", "Dummy")

_HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# 클라 복제몹: 포링1~포링10, 고스트링★ 처럼 표기만 다른 경우
_TRAILING_DIGITS_RE = re.compile(r"^(.*\D)\d+$")
_TRAILING_MARK_RE = re.compile(r"[★☆＊*]+$")


def canonical_monster_name(name: str) -> str:
  """복제 표기를 기본 이름으로 합친다.

  - 포링1 → 포링
  - 포링 10 → 포링
  - 고스트링★ → 고스트링
  """
  s = (name or "").strip()
  s = _TRAILING_MARK_RE.sub("", s).strip()
  s = re.sub(r"\s+\d+$", "", s).strip()
  m = _TRAILING_DIGITS_RE.match(s)
  if m:
    return m.group(1).strip()
  return s


def is_displayable_monster_name(name: str) -> bool:
  """Keep only names that look Korean (have Hangul, no Chinese ideographs)."""
  if not name or not str(name).strip():
    return False
  s = str(name).strip()
  if s.startswith("##"):
    return False
  if _CJK_RE.search(s):
    return False
  if not _HANGUL_RE.search(s):
    return False
  if any(x in s for x in SKIP_NAME_SUB):
    return False
  return True

ZONE_KO = {
  "Field": "필드",
  "EndlessTower": "엔들리스 타워",
  "Dojo": "도장",
  "Storm": "폭풍",
  "Repair": "수리",
  "CommonRaid": "공용 레이드",
  "AbyssDragon": "심연의 용",
}

# Zone prefer order when picking the "primary" id for a merged row.
ZONE_PRIORITY = {
  "Field": 0,
  "EndlessTower": 1,
  "Dojo": 2,
  "Storm": 3,
  "Repair": 4,
  "CommonRaid": 5,
  "AbyssDragon": 6,
  "": 9,
}

_LUA_DEC_ESC = re.compile(r"\\([0-9]{1,3})")


def decode_lua_decimal_escapes(text: str) -> str:
  """Decode Lua ``\\ddd`` (decimal byte) sequences into UTF-8 text.

  Table_Monster NameZh often arrives as literal ``\\230\\179\\162...`` when the
  encrypted blob is only partially parsed; those are UTF-8 bytes (e.g. 波利).
  """
  if not text or "\\" not in text:
    return text
  if not _LUA_DEC_ESC.search(text):
    return text

  out: list[str] = []
  buf = bytearray()
  i = 0
  n = len(text)
  while i < n:
    if text[i] == "\\" and i + 1 < n and text[i + 1].isdigit():
      j = i + 1
      while j < n and j < i + 4 and text[j].isdigit():
        j += 1
      buf.append(int(text[i + 1 : j]) & 0xFF)
      i = j
      continue
    if buf:
      out.append(buf.decode("utf-8", errors="replace"))
      buf.clear()
    out.append(text[i])
    i += 1
  if buf:
    out.append(buf.decode("utf-8", errors="replace"))
  return "".join(out)


def load_site_names() -> dict[int, str]:
  """Prefer already-known Korean names from the leveling DB when present."""
  path = ROOT / "leveling_monsters_client_full.json"
  if not path.exists():
    return {}
  rows = json.loads(path.read_text(encoding="utf-8"))
  out: dict[int, str] = {}
  for row in rows:
    mid = row.get("id")
    name = (row.get("clientKo") or row.get("ko") or "").strip()
    if mid is not None and name:
      out[int(mid)] = name
  return out


def load_map_labels() -> dict[int, str]:
  path = OUT_DIR / "maps.json"
  if not path.exists():
    return {}
  data = json.loads(path.read_text(encoding="utf-8"))
  out: dict[int, str] = {}
  for row in data.get("maps") or []:
    mid = row.get("id")
    if mid is None:
      continue
    label = (row.get("label") or row.get("ko") or "").strip()
    if label:
      out[int(mid)] = label
  return out


def load_site_locations() -> dict[int, list[str]]:
  """Monster id → map names from leveling hybrid DB."""
  path = ROOT / "leveling_monsters_client_full.json"
  if not path.exists():
    return {}
  rows = json.loads(path.read_text(encoding="utf-8"))
  out: dict[int, list[str]] = {}
  for row in rows:
    mid = row.get("id")
    if mid is None:
      continue
    locs: list[str] = []
    for mp in row.get("maps") or []:
      label = (mp.get("mapKo") or mp.get("ko") or mp.get("parentKo") or "").strip()
      if label and label not in locs:
        locs.append(label)
    if locs:
      out[int(mid)] = locs
  return out


def zone_label(zone: str) -> str:
  zone = zone or ""
  return ZONE_KO.get(zone, zone or "미확인")


def rate_value(rate) -> float:
  try:
    return float(rate)
  except (TypeError, ValueError):
    return 0.0


def merge_drops(rows: list[list[dict]]) -> list[dict]:
  best: dict[int, dict] = {}
  for drops in rows:
    for d in drops:
      iid = int(d["itemId"])
      prev = best.get(iid)
      if prev is None or rate_value(d.get("rate")) > rate_value(prev.get("rate")):
        best[iid] = d
  merged = list(best.values())
  merged.sort(key=lambda d: rate_value(d.get("rate")), reverse=True)
  return merged


def merge_duplicate_names(records: list[dict]) -> list[dict]:
  """Same Korean name + level → one row, locations as array.

  Also merges clones like 포링1~포링10 into 포링.
  """
  groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
  for rec in records:
    ko = canonical_monster_name(rec["ko"])
    groups[(ko, rec["lv"])].append(rec)

  generic_zones = set(ZONE_KO.values())

  merged: list[dict] = []
  for (ko, lv), group in groups.items():
    group.sort(
      key=lambda r: (
        # Prefer the real base name (no trailing digits) as primary.
        0 if canonical_monster_name(r["ko"]) == r["ko"] else 1,
        ZONE_PRIORITY.get(r.get("zone") or "", 8),
        r["id"],
      )
    )
    primary = group[0]
    locations: list[str] = []
    ids: list[int] = []
    for r in group:
      ids.append(r["id"])
      for loc in r.get("locations") or []:
        if loc and loc not in locations:
          locations.append(loc)
    # If we have concrete map names, drop generic "필드" label.
    has_concrete = any(loc not in generic_zones for loc in locations)
    if has_concrete:
      locations = [loc for loc in locations if loc != "필드"]
    merged.append(
      {
        "id": primary["id"],
        "ids": ids,
        "lv": lv,
        "ko": ko,
        "zone": primary.get("zone") or "",
        "locations": locations or [zone_label(primary.get("zone") or "")],
        "drops": merge_drops([r["drops"] for r in group]),
      }
    )
  merged.sort(key=lambda r: (r["lv"], r["ko"], r["id"]))
  return merged


def translate_name(tr: TranslationLookup, token: str) -> str:
  if not token:
    return ""
  token = decode_lua_decimal_escapes(token)
  name = tr.translate(token)
  if name.startswith("##"):
    return token
  return name or token


def load_packs() -> dict[int, list[dict]]:
  path = OUT_DIR / "rewards.json"
  if not path.exists():
    raise SystemExit(f"missing {path} — run rewards extract first")
  data = json.loads(path.read_text(encoding="utf-8"))
  packs: dict[int, list[dict]] = {}
  for k, rows in (data.get("packs") or {}).items():
    packs[int(k)] = rows
  return packs


def build_records() -> tuple[list[dict], list[dict]]:
  paths = GamePaths(GAME)
  packs = load_packs()
  tr = TranslationLookup(paths.translate_dir, language="korean")
  site_names = load_site_names()
  map_labels = load_map_labels()
  site_locations = load_site_locations()

  monsters = LuaTableSource(paths.monster_bundle, "Table_Monster").load_entries()
  items = LuaTableSource(paths.item_bundle, "Table_Item").load_entries()
  item_by_id = {int(e["id"]): e for e in items if e.get("id") is not None}

  item_name_cache: dict[int, str] = {}

  def item_name(iid: int) -> str:
    if iid in item_name_cache:
      return item_name_cache[iid]
    it = item_by_id.get(iid)
    if not it:
      name = f"#{iid}"
    else:
      name = translate_name(tr, it.get("NameZh") or "")
      if not name or name.startswith("##"):
        name = f"#{iid}"
    item_name_cache[iid] = name
    return name

  raw_rows: list[dict] = []

  for m in monsters:
    reward_ids = m.get("Dead_Reward") or []
    if not reward_ids:
      continue
    mid = int(m["id"])
    lv = int(m.get("Level") or 0)
    ko = site_names.get(mid) or translate_name(tr, m.get("NameZh") or "")
    if not is_displayable_monster_name(ko):
      continue
    zone = m.get("Zone") or ""

    drops: list[dict] = []
    seen_items: set[int] = set()
    for rid in reward_ids:
      rid = int(rid)
      for row in packs.get(rid, []):
        iid = int(row["itemId"])
        if iid in seen_items:
          continue
        seen_items.add(iid)
        drops.append(
          {
            "itemId": iid,
            "name": item_name(iid),
            "rate": row.get("rate"),
            "num": row.get("num"),
            "type": row.get("type"),
            "packId": rid,
          }
        )

    if not drops:
      continue

    drops.sort(key=lambda d: rate_value(d.get("rate")), reverse=True)

    locations: list[str] = []
    manual = m.get("ManualMap")
    if manual is not None and int(manual) in map_labels:
      locations.append(map_labels[int(manual)])
    for loc in site_locations.get(mid, []):
      if loc not in locations:
        locations.append(loc)
    # Always keep zone label so EndlessTower/Dojo etc. are visible.
    zlab = zone_label(zone)
    if zlab not in locations:
      # If we already have a concrete map, still add zone for non-Field instances.
      if not locations or zone not in ("", "Field"):
        locations.append(zlab)
    if not locations:
      locations = [zlab]

    raw_rows.append(
      {
        "id": mid,
        "lv": lv,
        "ko": ko,
        "zone": zone,
        "locations": locations,
        "drops": drops,
      }
    )

  monsters_out = merge_duplicate_names(raw_rows)

  item_to_monsters: dict[int, list[dict]] = defaultdict(list)
  for rec in monsters_out:
    for d in rec["drops"]:
      item_to_monsters[d["itemId"]].append(
        {
          "id": rec["id"],
          "lv": rec["lv"],
          "ko": rec["ko"],
          "rate": d.get("rate"),
          "num": d.get("num"),
          "locations": rec.get("locations") or [],
        }
      )

  items_out: list[dict] = []
  for iid, mlist in item_to_monsters.items():
    mlist.sort(key=lambda x: (x["lv"], x["ko"], x["id"]))
    items_out.append(
      {
        "itemId": iid,
        "name": item_name(iid),
        "monsterCount": len(mlist),
      }
    )
  items_out.sort(key=lambda x: x["name"])

  return monsters_out, items_out


def inject_html(monsters: list[dict], items: list[dict]) -> None:
  monsters_js = json.dumps(monsters, ensure_ascii=False, separators=(",", ":"))
  items_js = json.dumps(items, ensure_ascii=False, separators=(",", ":"))

  marker_start = "/* __DROP_DATA_START__ */"
  marker_end = "/* __DROP_DATA_END__ */"
  block = (
    f"{marker_start}\n"
    f"  const DROP_MONSTERS = {monsters_js};\n"
    f"  const DROP_ITEMS = {items_js};\n"
    f"  {marker_end}"
  )

  re_block = re.compile(
    re.escape(marker_start) + r".*?" + re.escape(marker_end),
    re.DOTALL,
  )

  for html_path in HTML_FILES:
    if not html_path.exists():
      print("skip missing", html_path)
      continue
    text = html_path.read_text(encoding="utf-8")
    if marker_start in text:
      text, n = re_block.subn(block, text, count=1)
      if n != 1:
        raise SystemExit(f"drop data replace failed: {html_path}")
    else:
      # Insert before first large const MONSTERS if present, else before </script> of main
      needle = "  const MONSTERS = "
      idx = text.find(needle)
      if idx < 0:
        raise SystemExit(f"cannot find insert point in {html_path}")
      text = text[:idx] + block + "\n\n" + text[idx:]
    html_path.write_text(text, encoding="utf-8")
    print("injected", html_path.name, "monsters", len(monsters), "items", len(items))


def main() -> None:
  monsters, items = build_records()
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  payload = {
    "monsterCount": len(monsters),
    "itemCount": len(items),
    "monsters": monsters,
    "items": items,
    "note": "rate는 클라 Table_Reward 원값(절대 % 환산 전)",
  }
  out_path = OUT_DIR / "drops.json"
  out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  print("wrote", out_path, "monsters", len(monsters), "items", len(items))

  # Sample poring
  poring = next((m for m in monsters if m["ko"] == "포링" and m["lv"] == 1), None)
  print("poring sample", json.dumps(poring, ensure_ascii=False)[:700] if poring else None)
  dojo = [m for m in monsters if "도장" in (m.get("locations") or [])]
  print("dojo rows", len(dojo), [(m["ko"], m["locations"]) for m in dojo[:5]])

  inject_html(monsters, items)


if __name__ == "__main__":
  main()

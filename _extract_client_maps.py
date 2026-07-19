# -*- coding: utf-8 -*-
"""클라 Monster.ManualMap → Table_Map 한글명 추출

Table_Map은 「명시 id + 순번 이어가기」 구조:
- 일부 엔트리만 id가 명시되고, 나머지는 직전 id+1
- 명시 id 사이의 엔트리 수가 id 간격과 정확히 일치하는 구간만 '검증됨'으로 채택
  (일치하지 않는 구간은 오매핑 위험이 있어 제외)
"""
from __future__ import annotations

import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(r"c:\workspace\romc-data-extractor\src")))

from romc_data_extractor.config import GamePaths
from romc_data_extractor.lua_decoder import _build_luac_payload
from romc_data_extractor.translation import TranslationLookup
from romc_data_extractor.unity_utils import load_bundle

ROOT = Path(r"c:\workspace\LvUpProject")
GAME = Path(r"C:\Program Files (x86)\XD\ROM Classic")
BUNDLE = GAME / "ro_win_Data/Persistent/Windows/resources/script2/config_map_fuben.unity3d"


def get_script(env, name: str) -> bytes:
  for obj in env.objects:
    if obj.type.name != "TextAsset":
      continue
    a = obj.read()
    if a.m_Name == name:
      s = a.m_Script
      return s if isinstance(s, bytes) else s.encode("utf-8", "surrogatepass")
  raise KeyError(name)


def iter_tokens(data: bytes):
  i = 0
  n = len(data)
  while i < n:
    if data[i] == 0x04 and i + 1 < n:
      ln = data[i + 1]
      clen = ln - 1
      if 0 <= clen < 300 and i + 2 + clen <= n:
        try:
          yield ("s", data[i + 2 : i + 2 + clen].decode("utf-8"))
          i += 2 + clen
          continue
        except Exception:
          pass
    if data[i] == 0x13 and i + 9 <= n:
      yield ("n", struct.unpack_from("<q", data, i + 1)[0])
      i += 9
      continue
    i += 1


def is_code(s: str) -> bool:
  # room_prt_1F처럼 대문자가 섞인 코드도 허용 (첫 글자는 소문자)
  if not re.fullmatch(r"[a-z][a-zA-Z0-9_]{1,40}", s or ""):
    return False
  return s.lower() not in {
    "id", "namezh", "nameen", "callzh", "desc", "type", "mode", "map",
    "lvrange", "cameralock", "indexrange", "nocat", "buffid", "monster", "ratio",
    "moneytype", "money", "maptips", "mapscale", "showinlist", "adventurevalue",
    "sceneanimation", "pvpmap", "position", "camera", "maparea", "mapui",
    "iscommonline", "teleportmaptype", "isafk", "areatips", "isdangerous",
    "mapnavigation", "monsterratio", "range",
  }


def translate(tr: TranslationLookup, raw: str) -> str:
  ko = tr.translate(raw)
  return raw if ko.startswith("##") else ko


def extract_chain(toks, tr) -> dict[int, dict]:
  """앵커(##NameZh + 맵코드) 나열 순서 + 명시 id로 ID 체인 해석.

  - 명시 id 후보는 검증 후에만 신뢰 (prt_maze1 앞의 15처럼 가짜 값 존재)
  - 신뢰 규칙: 직전 신뢰 id와 「id 간격 == 앵커 간격」, 또는
    다음 명시 id와 간격이 맞으면 새 구간 시작(재앵커)
  - 신뢰 구간 사이는 순번 부여(chain-verified), 구간 끝 직후 최대 3개만
    부여(chain-partial), 그 외는 오매핑 위험으로 제외
  """
  anchors = []
  for i in range(1, len(toks)):
    if toks[i][0] != "s" or not is_code(toks[i][1]):
      continue
    if toks[i - 1][0] != "s" or not toks[i - 1][1].startswith("##"):
      continue
    cand = None
    if i >= 2 and toks[i - 2][0] == "n" and 1 <= toks[i - 2][1] <= 500:
      cand = int(toks[i - 2][1])
    anchors.append({"en": toks[i][1], "zh": toks[i - 1][1], "cand": cand})

  n = len(anchors)
  ids: list[tuple[int, str] | None] = [None] * n
  explicit = [(k, a["cand"]) for k, a in enumerate(anchors) if a["cand"] is not None]
  if not explicit:
    return {}

  # 신뢰 명시 id 선별 (greedy + 재앵커)
  trusted: list[tuple[int, int]] = []
  ei = 0
  # 시드: 연속 명시 쌍 중 간격이 맞는 첫 쌍
  while ei + 1 < len(explicit):
    (k1, id1), (k2, id2) = explicit[ei], explicit[ei + 1]
    if 0 < id2 - id1 == k2 - k1:
      trusted.append((k1, id1))
      break
    ei += 1
  if not trusted:
    return {}

  for k, mid in explicit:
    kt, idt = trusted[-1]
    if k <= kt:
      continue
    if mid - idt == k - kt and mid > idt:
      trusted.append((k, mid))
      continue
    # 재앵커: 다음 명시 id와 간격이 맞으면 새 구간 시작
    for k2, id2 in explicit:
      if k2 > k:
        if 0 < id2 - mid == k2 - k and mid > idt:
          trusted.append((k, mid))
        break

  # id 부여
  for k, mid in trusted:
    ids[k] = (mid, "direct")
  for (k1, id1), (k2, id2) in zip(trusted, trusted[1:]):
    if id2 - id1 == k2 - k1:
      for off in range(1, k2 - k1):
        ids[k1 + off] = (id1 + off, "chain-verified")
    else:
      # 재앵커 구간: 앞쪽 최대 3개만 부분 부여
      for off in range(1, min(4, k2 - k1)):
        nid = id1 + off
        if nid >= id2:
          break
        ids[k1 + off] = (nid, "chain-partial")

  # 첫 신뢰 id 이전 역채움, 마지막 신뢰 id 이후 최대 3개
  k0, id0 = trusted[0]
  for off in range(1, k0 + 1):
    nid = id0 - off
    if nid < 1:
      break
    ids[k0 - off] = (nid, "chain-verified")
  kl, idl = trusted[-1]
  for off in range(1, 4):
    if kl + off >= n:
      break
    if ids[kl + off] is None:
      ids[kl + off] = (idl + off, "chain-partial")

  by: dict[int, dict] = {}
  for a, resolved in zip(anchors, ids):
    if resolved is None:
      continue
    mid, via = resolved
    if mid in by:
      continue
    by[mid] = {
      "id": mid,
      "en": a["en"],
      "zh": a["zh"],
      "ko": translate(tr, a["zh"]),
      "via": via,
    }
  return by


def extract_map_monster_lists(toks, tr):
  """맵코드 뒤에 나오는 몬스터 ID 묶음."""
  # anchors: ##NameZh, code
  anchors = []
  for i in range(1, len(toks)):
    if toks[i][0] != "s" or not is_code(toks[i][1]):
      continue
    if toks[i - 1][0] == "s" and toks[i - 1][1].startswith("##"):
      zh = toks[i - 1][1]
      anchors.append((i, toks[i][1], zh, translate(tr, zh)))

  out = []
  for ai, (idx, en, zh, ko) in enumerate(anchors):
    end = anchors[ai + 1][0] if ai + 1 < len(anchors) else min(len(toks), idx + 40)
    mids = []
    for j in range(idx + 1, end):
      if toks[j][0] == "n" and 10000 <= toks[j][1] < 20000:
        mids.append(int(toks[j][1]))
    if mids:
      out.append({"en": en, "zh": zh, "ko": ko, "monsters": mids})
  return out


def fill_by_spawn_votes(by: dict[int, dict], spawn_maps: list[dict], monsters: list[dict]):
  mm_of = {
    m["id"]: (m.get("raw") or {}).get("ManualMap")
    for m in monsters
    if isinstance(m.get("id"), int)
  }
  for sm in spawn_maps:
    votes = Counter()
    for mid in sm["monsters"]:
      mm = mm_of.get(mid)
      if isinstance(mm, int):
        votes[mm] += 1
    if not votes:
      continue
    mm, cnt = votes.most_common(1)[0]
    if cnt < 1:
      continue
    if mm in by:
      continue
    by[mm] = {
      "id": mm,
      "en": sm["en"],
      "zh": sm["zh"],
      "ko": sm["ko"],
      "via": "spawn-vote",
      "votes": dict(votes),
    }


# 노비스 구역 중국어 → 한글 (번역 테이블에 없을 때)
ZONE_CN_KO = {
  "普隆德拉区域": "프론테라",
  "依斯鲁得岛区域": "이즈루드",
  "吉芬区域": "게펜",
  "梦罗克区域": "모로크",
  "斐扬区域": "페이욘",
  "古城区域": "글래스트 헤임",
  "艾尔帕兰区域": "알데바란",
  "姜饼城区域": "루티에",
  "天津町区域": "아마쯔",
  "朱诺区域": "유노",
  "尼夫海姆区域": "니플헤임",
  "汶巴拉区域": "움발라",
  "里希塔乐镇区域": "리히타르젠",
  "拉赫区域": "라헬",
  "洛阳区域": "뤄양",
  "艾卡拉奇区域": "아인브로크",
  "深渊之湖": "심연의 호수",
  "伊斯加尔特": "이슈가르드",
}


def normalize_zone_parent(name: str) -> str:
  """'프론테라 구역/필드' / '普隆德拉区域' → '프론테라'"""
  s = (name or "").strip()
  if s in ZONE_CN_KO:
    return ZONE_CN_KO[s]
  s = ZONE_CN_KO.get(s, s)
  s = re.sub(r"(구역|지역|필드|던전|外|区域|地區)$", "", s).strip()
  s = re.sub(r"\s+", " ", s).strip()
  return s


def extract_zone_parents(env, tr: TranslationLookup) -> dict[int, str]:
  """Table_MapTransport: ZoneName → MapID들 → 부모 지역명."""
  toks = list(iter_tokens(_build_luac_payload(get_script(env, "Table_MapTransport"))))
  # 보조: 노비스 서버 중국어 구역명 (번역 실패 시)
  toks_nv = list(
    iter_tokens(_build_luac_payload(get_script(env, "Table_MapTransport_NoviceServer")))
  )

  def parse_zones(tok_list):
    zones = []  # (zone_raw, [map_ids])
    i = 0
    while i < len(tok_list):
      t, v = tok_list[i]
      if t == "s" and (v.startswith("##") or re.search(r"[\u4e00-\u9fff]", v)):
        # zone name candidate if followed by map ids
        j = i + 1
        # skip MapID key
        if j < len(tok_list) and tok_list[j] == ("s", "MapID"):
          j += 1
        ids = []
        while j < len(tok_list) and tok_list[j][0] == "n":
          n = int(tok_list[j][1])
          if 1 <= n <= 500:
            ids.append(n)
          j += 1
          if j < len(tok_list) and tok_list[j][0] == "s":
            break
        if ids and len(ids) >= 1:
          zones.append((v, ids))
          i = j
          continue
      i += 1
    return zones

  # Prefer korean ## tokens from main table; merge novice chinese as fallback labels
  zones_main = parse_zones(toks)
  zones_nv = parse_zones(toks_nv)

  parent_by_id: dict[int, str] = {}
  # use novice for clearer pairing of consecutive zone blocks (same order)
  # MapTransport main has ## for zone then ## for next zone interleaved with ids
  # Novice is clearer: 普隆德拉区域, ids..., 依斯鲁得岛区域, ids...
  for raw, ids in zones_nv:
    ko = translate(tr, raw)
    if ko == raw and raw.startswith("##"):
      ko = raw
    parent = normalize_zone_parent(ko)
    # Chinese fallback normalize common cities if still CJK zone suffix stripped
    parent = normalize_zone_parent(parent)
    for mid in ids:
      parent_by_id.setdefault(mid, parent)

  # overlay with korean translations from main table where available
  for raw, ids in zones_main:
    if not raw.startswith("##"):
      continue
    ko = translate(tr, raw)
    parent = normalize_zone_parent(ko)
    if not parent or parent.startswith("##"):
      continue
    for mid in ids:
      parent_by_id[mid] = parent

  return parent_by_id


# 맵 코드 접두로 부모 보정 (Transport 구역이 어긋날 때)
CODE_PARENT_PREFIX = (
  ("prt_", "프론테라"),
  ("ant_", "모로크"),
  ("moc_", "모로크"),
  ("pay_", "페이욘"),
  ("gef_", "게펜"),
  ("glt_", "글래스트 헤임"),
  ("glas", "글래스트 헤임"),
  ("lhz_", "리히타르젠"),
  ("yuno", "유노"),
  ("lava_", "유노"),
  ("clock", "알데바란"),
  ("xmas_", "루티에"),
  ("nif_", "니플헤임"),
  ("ice_", "라헬"),
  ("ra_", "라헬"),
  ("rachel", "라헬"),
  ("ecl", "이카라기"),
  ("may_", "이카라기"),
  ("dp_", "이카라기"),
  ("ac_", "이카라기"),
  ("beach", "코모도"),
  ("thana", "타나토스 타워"),
  ("luo_", "용지성"),
)


def parent_from_code(code: str) -> str:
  c = (code or "").lower()
  for pref, parent in CODE_PARENT_PREFIX:
    if c.startswith(pref):
      return parent
  return ""


def attach_parents(by: dict[int, dict], parent_by_id: dict[int, str]) -> None:
  for mid, info in by.items():
    parent = normalize_zone_parent(parent_by_id.get(mid) or "")
    # prt_maze1이 모로크 구역에 묶인 경우 등 — 맵코드로 보정
    code_parent = parent_from_code(info.get("en") or "")
    if code_parent:
      parent = code_parent
    if not parent:
      continue
    info["parentKo"] = parent
    child = info.get("ko") or ""
    # 자식 이름에 부모가 이미 포함되면 그대로 (페이욘 동굴2F)
    if not child or parent == child or child.startswith(parent):
      info["label"] = child or parent
    else:
      info["label"] = f"{parent} - {child}"


def collect_anchors(toks, tr) -> list[dict]:
  anchors = []
  for i in range(1, len(toks)):
    if toks[i][0] != "s" or not is_code(toks[i][1]):
      continue
    if toks[i - 1][0] != "s" or not toks[i - 1][1].startswith("##"):
      continue
    cand = None
    if i >= 2 and toks[i - 2][0] == "n" and 1 <= toks[i - 2][1] <= 500:
      cand = int(toks[i - 2][1])
    anchors.append({
      "en": toks[i][1],
      "zh": toks[i - 1][1],
      "cand": cand,
      "ko": translate(tr, toks[i - 1][1]),
    })
  return anchors


def extract_bgm_map_ids(env) -> dict[int, str]:
  """Table_MapBgm: (code_or_bgm, mapId) 쌍. bgm_ 접두 제외."""
  toks = list(iter_tokens(_build_luac_payload(get_script(env, "Table_MapBgm"))))
  out: dict[int, str] = {}
  i = 0
  while i < len(toks) - 1:
    if toks[i][0] == "s" and is_code(toks[i][1]) and toks[i + 1][0] == "n":
      mid = int(toks[i + 1][1])
      code = toks[i][1]
      if 1 <= mid <= 500 and not code.startswith("bgm_"):
        out.setdefault(mid, code)
      i += 2
      continue
    i += 1
  return out


def fill_transport_validated_cands(
  by: dict[int, dict], anchors: list[dict], parents: dict[int, str]
) -> int:
  """MapTransport에 존재하는 명시 cand는 체인 점프여도 채택."""
  used_codes = {v["en"] for v in by.values()}
  n = 0
  for a in anchors:
    cand = a.get("cand")
    if cand is None or cand in by:
      continue
    if cand not in parents:
      continue
    if a["en"] in used_codes:
      continue
    by[cand] = {
      "id": cand,
      "en": a["en"],
      "zh": a["zh"],
      "ko": a["ko"],
      "via": "transport-cand",
    }
    used_codes.add(a["en"])
    n += 1
  return n


def fill_from_bgm_unique(
  by: dict[int, dict],
  bgm: dict[int, str],
  anchors: list[dict],
  parents: dict[int, str],
  needed: set[int],
) -> int:
  """Bgm 문자열이 유일 맵코드이고 필요/Transport ID일 때만 채움."""
  code_info = {a["en"]: a for a in anchors}
  used_codes = {v["en"] for v in by.values()}
  code_owners: dict[str, list[int]] = defaultdict(list)
  for mid, code in bgm.items():
    if code in code_info:
      code_owners[code].append(mid)

  n = 0
  for mid, code in sorted(bgm.items()):
    if mid in by:
      continue
    if mid not in needed and mid not in parents:
      continue
    if code not in code_info or code in used_codes:
      continue
    if len(code_owners.get(code) or []) != 1:
      continue
    a = code_info[code]
    by[mid] = {
      "id": mid,
      "en": code,
      "zh": a["zh"],
      "ko": a["ko"],
      "via": "bgm-unique",
    }
    used_codes.add(code)
    n += 1
  return n


def fill_parent_stubs(by: dict[int, dict], parents: dict[int, str], needed: set[int]) -> int:
  """이름은 못 구했지만 Transport 구역은 아는 ManualMap."""
  n = 0
  for mid in sorted(needed):
    if mid in by:
      continue
    parent = normalize_zone_parent(parents.get(mid) or "")
    if not parent:
      continue
    by[mid] = {
      "id": mid,
      "en": f"map_{mid}",
      "zh": "",
      "ko": parent,
      "label": parent,
      "parentKo": parent,
      "via": "transport-parent",
    }
    n += 1
  return n


def main() -> None:
  tr = TranslationLookup(GamePaths(GAME).translate_dir, "korean")
  env = load_bundle(BUNDLE)
  toks = list(iter_tokens(_build_luac_payload(get_script(env, "Table_Map"))))
  monsters = json.loads((ROOT / "extracted_romc" / "monsters.json").read_text(encoding="utf-8"))[
    "monsters"
  ]
  anchors = collect_anchors(toks, tr)
  parents = extract_zone_parents(env, tr)
  bgm = extract_bgm_map_ids(env)

  pool = json.loads((ROOT / "leveling_monsters_client_full.json").read_text(encoding="utf-8"))
  pool_ids = {p["id"] for p in pool}
  needed: set[int] = set()
  for m in monsters:
    if m["id"] in pool_ids:
      mm = (m.get("raw") or {}).get("ManualMap")
      if isinstance(mm, int):
        needed.add(mm)

  by = extract_chain(toks, tr)
  n_cand = fill_transport_validated_cands(by, anchors, parents)
  # MapBgm은 id↔코드가 Table_Map과 어긋나는 경우가 많아 자동 채움에 쓰지 않음
  _ = bgm
  spawns = extract_map_monster_lists(toks, tr)
  fill_by_spawn_votes(by, spawns, monsters)
  n_stub = fill_parent_stubs(by, parents, needed)

  attach_parents(by, parents)
  print(
    "zone parents", len(parents),
    "maps with parent", sum(1 for m in by.values() if m.get("parentKo")),
    f"+cand={n_cand} +stub={n_stub}",
  )

  print("maps", len(by), "needed", len(needed), "covered", len(needed & set(by)))
  miss = sorted(needed - set(by))
  if miss:
    print("still missing", miss)

  raw_by = {m["id"]: m for m in monsters}
  for mid, label in [(10001, "포링"), (10062, "마이너우로스"), (10067, "구미호"), (10004, "타로우")]:
    mm = (raw_by[mid].get("raw") or {}).get("ManualMap")
    info = by.get(mm)
    print(label, "ManualMap", mm, "->", info.get("label") if info else None, info)

  out = {
    "note": "ROM Classic KR PC — ManualMap≈Table_Map.id, parent=Table_MapTransport ZoneName",
    "count": len(by),
    "maps": [by[i] for i in sorted(by)],
  }
  path = ROOT / "extracted_romc" / "maps.json"
  path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
  print("wrote", path)


if __name__ == "__main__":
  main()

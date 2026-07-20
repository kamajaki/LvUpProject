# -*- coding: utf-8 -*-
"""완전 PC클라 기반 사냥 추천 탭 생성/주입"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NATURE = {
  "Water": "물",
  "Fire": "불",
  "Earth": "땅",
  "Wind": "바람",
  "Poison": "독",
  "Holy": "성",
  "Shadow": "암흑",
  "Ghost": "염",
  "Undead": "언데드",
  "Neutral": "무속성",
}
RACE = {
  "Plant": "식물형",
  "Insect": "곤충형",
  "Fish": "어패형",
  "Demon": "악마형",
  "DemiHuman": "인간형",
  "Human": "인간형",
  "Angel": "천사형",
  "Dragon": "용족",
  "Undead": "언데드",
  "Formless": "무형",
  "Brute": "동물형",
}
ZONE_KO = {"Field": "필드", "Dungeon": "던전"}
SKIP_NAME = ("알", "달걀", "부활절", "테스트", "Test", "MVP", "미니")

# 이벤트/스킨 변형 — 본체로 잘못 붙지 않게 사이트 매칭 제외
VARIANT_PREFIXES = (
  "토끼귀", "리프", "와일드 ", "공중", "황야", "메이플", "초록 ", "빨강 ",
  "빨간꼬리", "호수 ",
)

# 클라 표기 → 기존(사이트) 표기 (같은 몬스터만, 변형몹 제외)
NAME_ALIASES = {
  "메카 하운드": "메커니컬 하운드",
  "메카하운드": "메커니컬 하운드",
  "판다포링": "팬더 포링",
  "지퍼베어": "지퍼 베어",
  "구미호": "나인테일",
  "스포아": "스포어",
  "포이즌 스포아": "포이즌 스포어",
  "퍼밀리어": "패밀리어",
  "울프": "늑대",
  "파이어럿 스켈": "해적 스켈레톤",
  "오본느": "오베아운",
  "휀": "펜",
  "고블린(단검)": "고블린 (단검)",
  "고블린(도끼)": "고블린 (도끼)",
  "고블린(해머)": "고블린 (망치)",
  "고블린(모닝스타)": "고블린 (방패)",
  "고블린(스피어)": "고블린 (창)",
  "고블린 아쳐": "고블린 아처",
  "고블린 스팀라이더": "스팀 고블린",
  "아르지오프": "아르지오페",
  "맨블릿": "멘블라트",
  "가이아스": "기아스",
  "백련옥": "매그놀리아",
  "솔져 스켈레톤": "병사 스켈레톤",
  "마타": "마티르",
  "미이라": "미라",
  "메틀러": "메탈러",
  "천하대장군": "그레이티스트 제너럴",
  "에기라": "애기라",
  "더스티네스": "더스티니스",
  "마이너우로스": "마이너러스",
  "아쳐 스켈레톤": "스켈레톤 아처",
  "오크 아쳐": "오크 아처",
  "코볼트(도끼)": "코볼트 (도끼)",
  # 클라/기존 DB 무기 이름이 서로 다름 → 레벨·HP 기준으로 대응
  "코볼트(해머)": "코볼트 (방패)",
  "코볼트(모닝스타)": "코볼트 (망치)",
  "코볼트 아쳐": "코볼트 아처",
  "미스트케이스": "미스트 케이스",
  "공중쁘띠": "스카이 쁘띠",
  "쁘띠": "그린 쁘띠",
  "곰인형": "테디베어",
  "레이드릭 아쳐": "레이드릭 아처",
  "크루이저": "크루저",
  "페러스": "페루스",
  "레이쓰": "레이스",
  "배회하는 자": "원더러",
  "메탈링": "메탈 포링",
  "브릴라이트": "브리라이트",
  "스템웜": "스템 웜",
  "산들바람": "허리케인 데몬",
  "마르틴 광부": "마틴 스캐빈저",
  "변이 퇴적물": "배리언트 디포짓",
  "마르틴": "마틴 (마멋)",
  "타락한 소드맨": "다크 소드맨",
  "타락한 어콜라이트": "다크 어콜라이트",
  "타락한 매지션": "다크 메이지",
  "타락한 머천트": "다크 머천트",
  "타락한 아처": "다크 아처",
  "타락한 씨프": "다크 시프",
  "플레임 머스탱": "불타는 갈기",
  "큐브": "쿠베",
  "고원 패러사이트": "하이랜드 파라사이트",
  "하이로조이스트": "하일로조이스트",
  "블레이저": "파이어 엘프",
  "지벳트": "지벳",
  "듀라한": "둘라한",
  "어린 몰트레스": "불타는 새끼새",
  "등룡": "랜턴 피셔맨",
  "툼스톤": "툼 좀비",
  "더 페이퍼": "악마인쇄 종이",
  "룡룡": "피시맨",
  "그렘린": "호드렘린",
  "스태포": "스톤 포링",
  "시로마": "작은 시로마",
  "머스키퓰라": "식인 풀",
  "스노이어": "시로마",
  "로우윈": "로윈",
  "비홀더": "악마의 눈",
  "시커": "빨간 악마의 눈",
  "도나": "블랙 위치",
  "클락": "고대의 시계",
  "빨강 쿠키": "크리스마스 쿠키",
}


def shape_to_size(shape) -> tuple[str, str]:
  if shape == "S":
    return "소형", "Small"
  if shape == "L":
    return "대형", "Large"
  if shape == "M":
    return "중형", "Medium"
  return "중형", "Medium"


def norm_name(s: str) -> str:
  return re.sub(r"[\s_\-·\.()（）]+", "", s or "")


def is_variant_name(ko: str) -> bool:
  return any(ko.startswith(p) for p in VARIANT_PREFIXES)


def site_name_for_client(ko_cli: str) -> str:
  """클라 이름 → 비교용 사이트 이름 (별칭 적용)."""
  if ko_cli in NAME_ALIASES:
    return NAME_ALIASES[ko_cli]
  return ko_cli


def find_site_match(
  site_by_key: dict[tuple[str, int], dict],
  used_site: set[tuple[str, int]],
  ko_cli: str,
  lv: int,
) -> dict | None:
  """이름(별칭)+레벨만으로 1:1 매칭. HP/유사도 매칭은 오탐이 많아 사용 안 함."""
  if is_variant_name(ko_cli):
    return None
  want = norm_name(site_name_for_client(ko_cli))
  key = (want, lv)
  # 직접 키
  hit = site_by_key.get(key)
  if hit:
    sk = (norm_name(hit["ko"]), hit["lv"])
    if sk not in used_site:
      return hit
  # 사이트 쪽 정규화 키가 다를 수 있어 선형 검색 (동일 레벨·동일 정규화 이름)
  for sk, s in site_by_key.items():
    if sk[1] != lv:
      continue
    if norm_name(s["ko"]) != want:
      continue
    if sk in used_site:
      return None
    return s
  return None


def maps_from_locations(en: str) -> list[dict]:
  path = ROOT / "monster_locations_raw.json"
  if not en or not path.exists():
    return []
  data = json.loads(path.read_text(encoding="utf-8"))
  by = data.get("byMonster") or {}
  key = en.strip().lower()
  if key in by:
    return list(by[key])
  for k, v in by.items():
    if k.replace(" ", "") == key.replace(" ", ""):
      return list(v)
  return []


def load_client_maps() -> dict[int, dict]:
  path = ROOT / "extracted_romc" / "maps.json"
  if not path.exists():
    return {}
  data = json.loads(path.read_text(encoding="utf-8"))
  return {int(m["id"]): m for m in data.get("maps") or [] if m.get("id") is not None}


def client_maps_for(manual_map, client_maps: dict[int, dict]) -> list[dict]:
  if manual_map is None:
    return []
  try:
    mm = int(manual_map)
  except (TypeError, ValueError):
    return []
  info = client_maps.get(mm)
  if not info:
    return []
  label = info.get("label") or info.get("ko") or info.get("en") or f"맵 {mm}"
  return [{
    "ko": label,
    "en": info.get("en") or f"ManualMap {mm}",
    "parentKo": info.get("parentKo") or "",
    "mapKo": info.get("ko") or "",
    "mapCode": info.get("en") or "",
  }]


def maps_blob(maps: list[dict]) -> str:
  parts = []
  for m in maps or []:
    parts.append(m.get("ko") or "")
    parts.append(m.get("en") or "")
    parts.append(m.get("mapCode") or "")
    parts.append(m.get("mapKo") or "")
  return " ".join(parts)


def client_map_conflicts_site(cli_maps: list[dict], site_maps: list[dict]) -> bool:
  """클라 ManualMap이 실제 출현지와 어긋나는 알려진 패턴."""
  if not cli_maps or not site_maps:
    return False
  cli = maps_blob(cli_maps)
  site = maps_blob(site_maps)
  # 개미지옥 몹인데 ManualMap이 미로숲(prt_maze)으로 잡힌 경우
  if re.search(r"(?i)ant hell|개미지옥|ant_dun", site) and re.search(
    r"(?i)prt_maze|미로숲|미궁의 숲|labyrinth", cli
  ):
    return True
  return False


# ManualMap 미해석 시 몬스터 계열로 출현지 추정 (클라 맵코드/정설 기준)
FAMILY_MAP_FALLBACKS: list[tuple[tuple[str, ...], dict]] = [
  (
    ("어시더스", "페러스", "노버스", "에이션트 미믹"),
    {"ko": "타나토스 타워", "en": "thana", "parentKo": "타나토스 타워"},
  ),
  (
    ("고대 퍼머터", "솔리더", "프리저", "어절터", "힛터", "리퍼", "스프리터",
     "나이터", "소울러", "스팅거"),
    {"ko": "코모도·고대 시대", "en": "beach_dun", "parentKo": "코모도"},
  ),
  (
    ("르간", "깔라마링"),
    {"ko": "타나토스 타워", "en": "thana", "parentKo": "타나토스 타워"},
  ),
  (
    ("텐드릴리온", "파툼"),
    {"ko": "이카라기", "en": "eclage", "parentKo": "이카라기"},
  ),
  (
    ("신나는 점프 버섯", "만드라 학자"),
    {"ko": "개화 시작의 땅", "en": "may_iz", "parentKo": "이카라기"},
  ),
]


def family_map_fallback(ko_cli: str) -> list[dict]:
  for keys, info in FAMILY_MAP_FALLBACKS:
    if any(k in (ko_cli or "") for k in keys):
      label = info["ko"]
      parent = info.get("parentKo") or ""
      if parent and parent not in label and not label.startswith(parent):
        label = f"{parent} - {info['ko']}" if parent != info["ko"] else info["ko"]
      return [{
        "ko": label,
        "en": info.get("en") or "",
        "parentKo": parent,
        "mapKo": info["ko"],
      }]
  return []


def user_maps_note(note: str) -> str:
  """UI에 노출할 출현지 메모 — 내부/클라 용어 제거."""
  return {
    "PC 클라 ManualMap → Table_Map": "",
    "PC 클라 ManualMap → 구역만 확인": "",
    "기존 DB 출현지 (클라 ManualMap 불일치 보정)": "",
    "기존 DB 출현지 (클라 맵ID 미해석)": "",
    "계열 추정 출현지 (클라 맵ID 미해석)": "계열 추정",
    "출현지 미확인": "출현지 미확인",
  }.get(note or "", "")


def with_parent_label(maps: list[dict]) -> list[dict]:
  """기존 DB 맵에도 흔한 부모 접두를 붙여 표시 (가능하면)."""
  # 더 구체적인 패턴을 앞에 — 글래스트 지하수로가 프론테라로 붙지 않게
  hints = [
    (r"(?i)glast|글래스트|고성", "글래스트 헤임"),
    (r"(?i)pyramid|피라미드", "모로크"),
    (r"(?i)ant hell|개미지옥", "모로크"),
    (r"(?i)payon cave|페이욘 동굴", "페이욘"),
    (r"(?i)geffen (dungeon|지하)|게펜 (지하|탑)", "게펜"),
    (r"(?i)capital sewer|수도 하수도", "프론테라"),
    (r"(?i)prontera|프론테라", "프론테라"),
    (r"(?i)toy factory|장난감 공장", "루티에"),
    (r"(?i)clock tower|시계탑", "알데바란"),
    (r"(?i)orc (dungeon|village|던전|마을)", "게펜"),
    (r"(?i)underwater|해저", "이즈루드"),
    (r"(?i)sunken|ghost ship|침몰|유령선", "이즈루드"),
    (r"(?i)lighthalzen|biolab|생체|리히타", "리히타르젠"),
    (r"(?i)magma|nogroad|노그로드|마그마", "유노"),
  ]
  out = []
  for m in maps:
    row = dict(m)
    ko = row.get("ko") or row.get("en") or ""
    en = row.get("en") or ""
    if row.get("parentKo") or " - " in ko:
      out.append(row)
      continue
    parent = ""
    blob = f"{ko} {en}"
    for pat, p in hints:
      if re.search(pat, blob):
        parent = p
        break
    if parent and parent not in ko:
      row["parentKo"] = parent
      row["mapKo"] = ko
      row["ko"] = f"{parent} - {ko}"
    out.append(row)
  return out


def build_pool() -> list[dict]:
  raw = json.loads((ROOT / "extracted_romc" / "monsters.json").read_text(encoding="utf-8"))
  site_list = json.loads((ROOT / "leveling_monsters.json").read_text(encoding="utf-8"))
  client_maps = load_client_maps()
  site_by_key: dict[tuple[str, int], dict] = {}
  for s in site_list:
    site_by_key[(norm_name(s.get("ko") or ""), int(s.get("lv") or 0))] = s

  out: list[dict] = []
  seen = set()
  used_site: set[tuple[str, int]] = set()
  matched_n = 0
  client_map_n = 0
  for m in raw["monsters"]:
    mid = m.get("id")
    if not isinstance(mid, int) or not (10000 <= mid < 12000):
      continue
    r = m.get("raw") or {}
    be_cli = r.get("BaseExp") or 0
    je_cli = r.get("JobExp") or 0
    lv = m.get("level") or 0
    ko_cli = (m.get("name") or {}).get("korean") or ""
    if be_cli < 8 or not ko_cli or not (1 <= lv <= 130):
      continue
    if m.get("class_type") not in (1, "1"):
      continue
    zone = m.get("zone")
    if zone not in ("Field", "Dungeon"):
      continue
    if any(s in ko_cli for s in SKIP_NAME):
      continue
    # 이벤트/스킨 변형은 레벨링 추천에서 제외 (이름 중복·오매칭 유발)
    if is_variant_name(ko_cli):
      continue
    hp_cli = (m.get("stats") or {}).get("hp") or 0
    if hp_cli <= 0 or hp_cli >= 5_000_000:
      continue
    key = (ko_cli, lv)
    if key in seen:
      continue
    seen.add(key)
    size, size_en = shape_to_size(r.get("Shape"))
    hp = hp_cli
    manual = r.get("ManualMap")

    site = find_site_match(site_by_key, used_site, ko_cli, lv)
    # 표시 이름은 항상 클라 이름 유지
    ko = ko_cli
    if site:
      matched_n += 1
      used_site.add((norm_name(site["ko"]), int(site["lv"])))
      be = site.get("base") or be_cli
      je = site.get("job") or je_cli
      en = site.get("en") or ""
      site_ko = site.get("ko") or ""
      site_maps = list(site.get("maps") or [])
      if not site_maps and en:
        site_maps = maps_from_locations(en)
      drop = site.get("drop") or ""
      card = site.get("card") or ""
      card_star = site.get("cardStar") or ""
      card_type = site.get("cardType") or ""
      if site.get("size"):
        size = site["size"]
      if site.get("sizeEn"):
        size_en = site["sizeEn"]
      if site.get("hp"):
        hp = site["hp"]
      exp_note = "Base/Job = 기존 DB"
      source = "hybrid: site EXP + client maps/name"
    else:
      be, je = be_cli, je_cli
      en, site_ko = "", ""
      site_maps = []
      drop = card = card_star = card_type = ""
      exp_note = "Base/Job = PC클라 (기존 DB 없음)"
      source = "ROM Classic KR PC client"

    # 출현맵: 클라 ManualMap 우선 → 기존 DB → 계열 추정
    # ManualMap이 미로숲 등으로 어긋나면 기존 DB 출현지 사용 (예: 데니로→개미지옥)
    cli_maps = client_maps_for(manual, client_maps)
    # Transport 구역명만 있는 stub는 계열 추정이 더 구체하면 후순위로
    cli_is_stub = bool(cli_maps) and (cli_maps[0].get("en") or "").startswith("map_")
    if cli_maps and not cli_is_stub and not client_map_conflicts_site(cli_maps, site_maps):
      maps = cli_maps
      maps_note = "PC 클라 ManualMap → Table_Map"
      client_map_n += 1
    elif site_maps:
      maps = with_parent_label(site_maps)
      if cli_maps and not cli_is_stub:
        maps_note = "기존 DB 출현지 (클라 ManualMap 불일치 보정)"
      else:
        maps_note = "기존 DB 출현지 (클라 맵ID 미해석)"
    else:
      fam = family_map_fallback(ko_cli)
      if fam:
        maps = fam
        maps_note = "계열 추정 출현지 (클라 맵ID 미해석)"
      elif cli_maps:
        maps = cli_maps
        maps_note = (
          "PC 클라 ManualMap → 구역만 확인"
          if cli_is_stub else
          "PC 클라 ManualMap → Table_Map"
        )
        client_map_n += 1
      else:
        maps = []
        maps_note = "출현지 미확인"

    maps_note = user_maps_note(maps_note)

    out.append({
      "id": mid,
      "lv": lv,
      "ko": ko,
      "en": en,
      "siteKo": site_ko,
      "clientKo": ko_cli,
      "hp": hp,
      "flee": (m.get("stats") or {}).get("flee") or 0,
      "def": (m.get("stats") or {}).get("def") or 0,
      "mdef": (m.get("stats") or {}).get("mdef") or 0,
      "atk": (m.get("stats") or {}).get("atk") or 0,
      "elem": NATURE.get(m.get("nature") or "", m.get("nature") or "-"),
      "race": RACE.get(m.get("race") or "", m.get("race") or "-"),
      "base": be,
      "job": je,
      "total": be + je,
      "baseClient": be_cli,
      "jobClient": je_cli,
      "drop": drop,
      "card": card,
      "cardStar": card_star,
      "cardType": card_type,
      "maps": maps,
      "mapsNote": maps_note,
      "size": size,
      "sizeEn": size_en,
      "sizeNote": "PC 클라 Shape 기준 (미기입=중형 추정)" if not site else (site.get("sizeNote") or "기존 DB 크기"),
      "zone": zone,
      "manualMap": manual,
      "expNote": exp_note,
      "source": source,
    })
  out.sort(key=lambda x: (x["lv"], x["id"]))
  print("site-matched", matched_n, "/", len(out), "client-maps", client_map_n)
  return out


CSS = """
  .client-note {
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(47, 107, 79, 0.1);
    border: 1px solid rgba(47, 107, 79, 0.35);
    font-size: 0.92rem;
    line-height: 1.45;
  }
"""


def strip_hybrid_toggle(text: str) -> str:
  # remove data-source toggle UI if present
  text = re.sub(
    r'\s*<div class="data-source" id="dataSource"[\s\S]*?</div>\s*<div class="test-banner" id="testBanner"[\s\S]*?</div>\s*',
    "\n",
    text,
    count=1,
  )
  # restore hunt tab to always use MONSTERS (remove hybrid EXP toggle logic)
  text = text.replace(
    "return dataSource === \"client\" ? MONSTERS_CLIENT : MONSTERS",
    "return MONSTERS",
  )
  text = text.replace(
    "return [...monsterPool()].sort((a, b) => {",
    "return [...MONSTERS].sort((a, b) => {",
  )
  text = text.replace(
    "return monsterPool()\n      .filter((m) => m.lv >= lo && m.lv <= hi)",
    "return MONSTERS\n      .filter((m) => m.lv >= lo && m.lv <= hi)",
  )
  # simplify hints that mention hybrid mode
  text = re.sub(
    r'hint\.innerHTML = dataSource === "client"\s*\?[\s\S]*?: "지금은 <strong>전체 몬스터</strong>를 보고 있어요\. 위에 레벨을 넣으면 추천 3마리가 자세히 나옵니다\."',
    'hint.innerHTML = "지금은 <strong>전체 몬스터</strong>를 보고 있어요. 위에 레벨을 넣으면 추천 3마리가 자세히 나옵니다."',
    text,
    count=1,
  )
  text = text.replace(
    ' + (dataSource === "client" ? " / <strong>PC클라 EXP</strong>" : "")',
    "",
  )
  text = text.replace(
    'const srcTag = dataSource === "client" ? " · PC클라" : ""\n      recoTitle.textContent = getWeaponId() === "none"\n        ? `추천 몬스터 3종 (${modeLabel(mode)}${srcTag})`\n        : `추천 몬스터 3종 (${modeLabel(mode)} · ${wName}${srcTag})`',
    'recoTitle.textContent = getWeaponId() === "none"\n        ? `추천 몬스터 3종 (${modeLabel(mode)})`\n        : `추천 몬스터 3종 (${modeLabel(mode)} · ${wName})`',
  )
  # remove hybrid exp-diff in cards
  text = re.sub(
    r'\s*\$\{m\.baseOld != null \? `<div class="exp-diff">[\s\S]*?</div>` : ""\}\s*',
    "\n        ",
    text,
    count=1,
  )
  # simplify table cells
  text = text.replace(
    '<td title="${m.baseOld != null ? "기존 "+m.baseOld : ""}">${m.base.toLocaleString()}${m.baseOld != null && dataSource === "client" ? ` <small style="color:#8a5a1e">(旧${m.baseOld})</small>` : ""}</td>\n'
    '          <td title="${m.jobOld != null ? "기존 "+m.jobOld : ""}">${m.job.toLocaleString()}${m.jobOld != null && dataSource === "client" ? ` <small style="color:#8a5a1e">(旧${m.jobOld})</small>` : ""}</td>',
    "<td>${m.base.toLocaleString()}</td>\n          <td>${m.job.toLocaleString()}</td>",
  )
  # remove dataSource listeners / sync calls if still present
  text = re.sub(
    r'\s*document\.querySelectorAll\("#dataSource button"\)\.forEach\(\(btn\) => \{[\s\S]*?\}\)\s*',
    "\n  ",
    text,
    count=1,
  )
  text = text.replace("  syncDataSourceUi()\n", "")
  text = text.replace('  let dataSource = "site"\n', "")
  # drop unused hybrid client-exp array (keep MONSTERS_CLIENT_FULL)
  text = re.sub(
    r"\n  const MONSTERS_CLIENT = \[.*?\];\n",
    "\n",
    text,
    count=1,
    flags=re.S,
  )
  # drop unused monsterPool/syncDataSourceUi functions if orphaned
  text = re.sub(
    r"\n  function monsterPool\(\) \{[\s\S]*?\n  \}\n\n  function syncDataSourceUi\(\) \{[\s\S]*?\n  \}\n",
    "\n",
    text,
    count=1,
  )
  return text


def ensure_tab_button(text: str) -> str:
  if 'data-tab="huntClient"' in text:
    return text
  return text.replace(
    '<button type="button" role="tab" data-tab="cards" aria-selected="false">카드 정보</button>',
    '<button type="button" role="tab" data-tab="huntClient" aria-selected="false">사냥 추천 (클라)</button>\n'
    '      <button type="button" role="tab" data-tab="cards" aria-selected="false">카드 정보</button>',
    1,
  )


def ensure_tab_panel(text: str) -> str:
  if 'id="tabHuntClient"' in text:
    return text
  panel = """
    <div id="tabHuntClient" class="tab-panel" role="tabpanel" hidden>
    <section class="panel">
      <div class="client-note">
        <strong>사냥 추천 (클라) 탭</strong> — 이름·목록은 PC 클라, Base/Job은 기존 DB,
        출현맵은 <em>클라 ManualMap 우선</em>(없으면 기존 DB → 계열 추정)입니다.
      </div>
      <div class="controls">
        <div class="control-level">
          <label for="levelC">Base 레벨</label>
          <div class="input-clear-wrap" id="levelWrapC">
            <input id="levelC" type="number" min="1" max="200" placeholder="예: 45" />
            <button type="button" class="input-clear" id="levelClearC" aria-label="레벨 입력 지우기" title="지우기">×</button>
          </div>
        </div>
        <div class="control-weapon">
          <label for="weaponC">착용 장비</label>
          <select id="weaponC">
            <option value="none">선택 안 함</option>
            <option value="dagger">단검</option>
            <option value="sword1h">한손검</option>
            <option value="sword2h">양손검</option>
            <option value="spear">창</option>
            <option value="axe">도끼</option>
            <option value="mace">둔기</option>
            <option value="bow">활</option>
            <option value="katar">카타르</option>
            <option value="knuckle">너클</option>
            <option value="instrument">악기</option>
            <option value="whip">채찍</option>
            <option value="staff">지팡이</option>
            <option value="book">책</option>
          </select>
        </div>
        <div class="control-mode">
          <label>경험치 목적</label>
          <div class="mode" id="modeC">
            <button type="button" data-mode="balance" class="active-balance">균형</button>
            <button type="button" data-mode="base">Base 위주</button>
            <button type="button" data-mode="job">Job 위주</button>
          </div>
        </div>
      </div>
      <div class="weapon-hint" id="weaponHintC"></div>
      <div class="hint" id="hintC">레벨을 입력하면 클라 EXP 기준 추천 3마리가 나옵니다.</div>
    </section>

    <h2 class="section-title" id="recoTitleC">추천 몬스터 3종 (클라)</h2>
    <div class="cards" id="cardsC"></div>

    <h2 class="section-title" id="listTitleC">전체 / 후보 목록 (클라)</h2>
    <div class="panel" style="margin-top:0; padding-bottom:12px;">
      <label for="qC">이름 검색</label>
      <input id="qC" type="search" placeholder="예: 포링, 구미호" />
    </div>
    <div class="table-wrap" style="margin-top:12px;">
      <table>
        <thead>
          <tr>
            <th>Lv</th>
            <th>이름</th>
            <th>크기</th>
            <th>무기적합</th>
            <th>속성</th>
            <th>종족</th>
            <th>HP</th>
            <th>Base</th>
            <th>Job</th>
            <th>Total</th>
            <th>출현</th>
          </tr>
        </thead>
        <tbody id="tbodyC"></tbody>
      </table>
    </div>
    </div>
"""
  return text.replace(
    '<div id="tabCards" class="tab-panel" role="tabpanel" hidden>',
    panel + '\n    <div id="tabCards" class="tab-panel" role="tabpanel" hidden>',
    1,
  )


JS_BLOCK = r"""
  let modeC = "balance"

  function getWeaponIdC() {
    return document.getElementById("weaponC").value
  }

  function sizeMultC(m) {
    const wid = getWeaponIdC()
    if (wid === "none") return 1
    const w = WEAPONS[wid]
    const s = m.sizeEn || ""
    if (s === "Small") return w.small / 100
    if (s === "Large") return w.large / 100
    return w.medium / 100
  }

  function scoreC(m, mode) {
    let exp = mode === "base" ? m.base : mode === "job" ? m.job : m.total
    return exp * sizeMultC(m)
  }

  function getLevelC() {
    const v = document.getElementById("levelC").value.trim()
    if (!v) return null
    const n = Number(v)
    if (!Number.isFinite(n) || n < 1) return null
    return Math.floor(n)
  }

  function candidatesC(level) {
    if (level == null) {
      return [...MONSTERS_CLIENT_FULL].sort((a, b) => {
        if (getWeaponIdC() !== "none") {
          const d = scoreC(b, modeC) - scoreC(a, modeC)
          if (d) return d
        }
        return a.lv - b.lv || b.total - a.total
      })
    }
    const lo = level
    const hi = level + 29
    return MONSTERS_CLIENT_FULL
      .filter((m) => m.lv >= lo && m.lv <= hi)
      .sort((a, b) => scoreC(b, modeC) - scoreC(a, modeC) || b.total - a.total)
  }

  function updateWeaponHintC() {
    const el = document.getElementById("weaponHintC")
    const wid = getWeaponIdC()
    const w = WEAPONS[wid]
    if (wid === "none") {
      el.innerHTML = "착용 장비를 고르면 <strong>크기 패널티</strong>를 반영해 추천을 다시 정렬합니다."
      return
    }
    el.innerHTML = `${w.ko}: 소형 <strong>${w.small}%</strong> · 중형 <strong>${w.medium}%</strong> · 대형 <strong>${w.large}%</strong>`
  }

  function mapsHtmlC(m) {
    const maps = m.maps || []
    if (!maps.length) {
      return `<div class="map-title">출현</div><div class="map-empty">${m.mapsNote || "위치 미확인"}</div>`
    }
    const pills = maps.map((x) => `<span class="map-pill">${x.ko || x.en}</span>`).join("")
    const note = m.mapsNote ? `<div class="map-note">${m.mapsNote}</div>` : ""
    return `<div class="map-title">출현</div><div class="map-pills">${pills}</div>${note}`
  }

  function cardHtmlC(m, rank) {
    const rankLabel = rank === 1 ? "1순위" : rank === 2 ? "2순위" : "3순위"
    const modeBadge =
      modeC === "base" ? '<span class="badge base">Base</span>' :
      modeC === "job" ? '<span class="badge job">Job</span>' :
      '<span class="badge main">균형</span>'
    const sizeLabel = m.size || "크기 미확인"
    return `
      <article class="card rank-${rank}">
        <div class="badge-row">
          <span class="badge main">${rankLabel}</span>
          ${modeBadge}
          <span class="badge">Lv.${m.lv}</span>
          <span class="badge">${sizeLabel}</span>
          <span class="badge">${m.elem || "-"}</span>
          <span class="badge">${m.race || "-"}</span>
        </div>
        <h3 class="name">${m.ko}</h3>
        <p class="en">클라ID ${m.id}</p>
        <div class="stats">
          <div class="stat"><span>Base EXP</span><b>${m.base.toLocaleString()}</b></div>
          <div class="stat"><span>Job EXP</span><b>${m.job.toLocaleString()}</b></div>
          <div class="stat"><span>Total</span><b>${m.total.toLocaleString()}</b></div>
          <div class="stat"><span>크기</span><b>${sizeLabel}</b></div>
          <div class="stat"><span>HP</span><b>${m.hp.toLocaleString()}</b></div>
          <div class="stat"><span>FLEE / DEF / MDEF</span><b>${m.flee ?? "-"} / ${m.def ?? "-"} / ${m.mdef ?? "-"}</b></div>
        </div>
        <div class="why">Total ${m.total.toLocaleString()} · ${rank}순위 (PC클라)</div>
        <div class="maps">${mapsHtmlC(m)}</div>
      </article>`
  }

  function fitInfoC(m) {
    const wid = getWeaponIdC()
    if (wid === "none") return { label: "-" }
    const pct = Math.round(sizeMultC(m) * 100)
    return { label: pct + "%" }
  }

  function renderTableC(list) {
    const q = document.getElementById("qC").value.trim().toLowerCase()
    const filtered = !q
      ? list
      : list.filter((m) =>
          m.ko.toLowerCase().includes(q) ||
          (m.clientKo || "").toLowerCase().includes(q) ||
          (m.en || "").toLowerCase().includes(q) ||
          String(m.lv).includes(q) ||
          String(m.id).includes(q)
        )
    const tbody = document.getElementById("tbodyC")
    if (!filtered.length) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;color:#6b645a;padding:24px;">검색 결과가 없습니다.</td></tr>`
      return
    }
    tbody.innerHTML = filtered
      .map((m) => {
        const fit = fitInfoC(m)
        return `<tr>
          <td>${m.lv}</td>
          <td><strong>${m.ko}</strong></td>
          <td>${m.size || "미확인"}</td>
          <td>${getWeaponIdC() === "none" ? "-" : fit.label}</td>
          <td>${m.elem || "-"}</td>
          <td>${m.race || "-"}</td>
          <td>${m.hp.toLocaleString()}</td>
          <td>${m.base.toLocaleString()}</td>
          <td>${m.job.toLocaleString()}</td>
          <td>${m.total.toLocaleString()}</td>
          <td>${(m.maps||[]).map(x=>x.ko||x.en).join(", ") || (m.mapsNote || "-")}</td>
        </tr>`
      })
      .join("")
  }

  function renderClient() {
    updateWeaponHintC()
    const level = getLevelC()
    const list = candidatesC(level)
    const top = level == null ? [] : list.slice(0, 3)
    const hint = document.getElementById("hintC")
    const recoTitle = document.getElementById("recoTitleC")
    const listTitle = document.getElementById("listTitleC")
    const cards = document.getElementById("cardsC")
    const wName = WEAPONS[getWeaponIdC()].ko

    if (level == null) {
      hint.innerHTML = "지금은 <strong>클라 전체 몬스터</strong>를 보고 있어요. 레벨을 넣으면 추천 3마리가 나옵니다."
      recoTitle.style.display = "none"
      cards.style.display = "none"
      cards.innerHTML = ""
      listTitle.textContent = "전체 몬스터 목록 (클라)"
    } else {
      const wPart = getWeaponIdC() === "none" ? "" : ` / 장비: <strong>${wName}</strong>`
      hint.innerHTML = `내 레벨 <strong>${level}</strong> → 사냥 구간 <strong>Lv.${level} ~ ${level + 29}</strong> / 목적: <strong>${modeLabel(modeC)}</strong>${wPart} / 후보 ${list.length}마리 / <strong>PC클라</strong>`
      recoTitle.style.display = ""
      recoTitle.textContent = getWeaponIdC() === "none"
        ? `추천 몬스터 3종 (${modeLabel(modeC)} · 클라)`
        : `추천 몬스터 3종 (${modeLabel(modeC)} · ${wName} · 클라)`
      cards.style.display = "grid"
      if (!top.length) {
        cards.innerHTML = `<div class="empty" style="grid-column:1/-1">이 구간에 클라 데이터가 있는 몹이 없어요.</div>`
      } else {
        cards.innerHTML = top.map((m, i) => cardHtmlC(m, i + 1)).join("")
      }
      listTitle.textContent = `후보 목록 (Lv.${level}~${level + 29})`
    }
    renderTableC(list)
  }

  function syncLevelClearC() {
    const wrap = document.getElementById("levelWrapC")
    const has = document.getElementById("levelC").value.trim() !== ""
    wrap.classList.toggle("has-value", has)
  }

  document.getElementById("levelC").addEventListener("input", () => {
    syncLevelClearC()
    renderClient()
  })
  document.getElementById("levelClearC").addEventListener("click", () => {
    const el = document.getElementById("levelC")
    el.value = ""
    syncLevelClearC()
    el.focus()
    renderClient()
  })
  document.getElementById("weaponC").addEventListener("change", renderClient)
  document.getElementById("qC").addEventListener("input", renderClient)
  document.querySelectorAll("#modeC button").forEach((btn) => {
    btn.addEventListener("click", () => {
      modeC = btn.dataset.mode
      document.querySelectorAll("#modeC button").forEach((b) => {
        b.className = ""
        if (b.dataset.mode === modeC) b.className = "active-" + modeC
      })
      renderClient()
    })
  })
"""


def patch_js(text: str, payload: str) -> str:
  # inject data after MONSTERS (or replace)
  if "const MONSTERS_CLIENT_FULL" in text:
    text, n = re.subn(
      r"const MONSTERS_CLIENT_FULL = \[.*?\];",
      payload,
      text,
      count=1,
      flags=re.S,
    )
    if n != 1:
      raise SystemExit(f"MONSTERS_CLIENT_FULL replace failed: {n}")
  else:
    # prefer after MONSTERS_CLIENT if exists, else after MONSTERS
    if "const MONSTERS_CLIENT =" in text:
      text, n = re.subn(
        r"(const MONSTERS_CLIENT = \[.*?\];)",
        r"\1\n  " + payload,
        text,
        count=1,
        flags=re.S,
      )
    else:
      text, n = re.subn(
        r"(const MONSTERS = \[.*?\];)",
        r"\1\n  " + payload,
        text,
        count=1,
        flags=re.S,
      )
    if n != 1:
      raise SystemExit(f"MONSTERS_CLIENT_FULL insert failed: {n}")

  if "function renderClient()" not in text:
    marker = '  document.getElementById("level").addEventListener("input", () => {'
    if marker not in text:
      raise SystemExit("level listener marker not found")
    text = text.replace(marker, JS_BLOCK + "\n" + marker, 1)

  # tab switching
  old_tab = """document.getElementById("tabHunt").hidden = uiTab !== "hunt"
      document.getElementById("tabCards").hidden = uiTab !== "cards"
      if (uiTab === "cards") renderCardGallery()"""
  new_tab = """document.getElementById("tabHunt").hidden = uiTab !== "hunt"
      document.getElementById("tabHuntClient").hidden = uiTab !== "huntClient"
      document.getElementById("tabCards").hidden = uiTab !== "cards"
      if (uiTab === "cards") renderCardGallery()
      if (uiTab === "huntClient") renderClient()"""
  if "tabHuntClient" not in text.split("mainTabs")[1][:2500]:
    if old_tab in text:
      text = text.replace(old_tab, new_tab, 1)

  if "syncLevelClearC()" not in text.split("syncLevelClear()")[-1][:200]:
    text = text.replace(
      "  syncLevelClear()\n  syncDataSourceUi()\n  render()\n  renderCardGallery()",
      "  syncLevelClear()\n  syncLevelClearC()\n  render()\n  renderClient()\n  renderCardGallery()",
      1,
    )
    text = text.replace(
      "  syncLevelClear()\n  render()\n  renderCardGallery()",
      "  syncLevelClear()\n  syncLevelClearC()\n  render()\n  renderClient()\n  renderCardGallery()",
      1,
    )

  # footer
  if "사냥 추천 (클라)" not in text.split("<footer>")[1][:800]:
    text = text.replace(
      "      알류·초고HP 몹(심연의 기사 등)은 레벨링 추천에서 제외했습니다.<br />",
      "      알류·초고HP 몹(심연의 기사 등)은 레벨링 추천에서 제외했습니다.<br />\n"
      "      <strong>사냥 추천 (클라)</strong>: 한국 PC 클라 Table_Monster+Table_Map 추출(이름/EXP/스탯/Shape/출현맵)<br />",
      1,
    )

  if ".client-note" not in text:
    text = text.replace(
      "  .tab-panel[hidden] { display: none !important; }",
      "  .tab-panel[hidden] { display: none !important; }\n" + CSS,
      1,
    )

  return text


def refresh_client_copy(text: str) -> str:
  note = (
    "이름·목록은 PC 클라, Base/Job은 기존 DB, "
    "출현맵은 <em>클라 ManualMap 우선</em>(없으면 기존 DB → 계열 추정)입니다."
  )
  text = re.sub(
    r'<div class="client-note">[\s\S]*?</div>',
    '<div class="client-note">\n'
    '        <strong>사냥 추천 (클라) 탭</strong> — '
    + note
    + "\n      </div>",
    text,
    count=1,
  )
  client_desc = (
    "클라 목록(이름) + 기존 DB Base/Job + 출현맵(ManualMap→계열추정)"
  )
  text = text.replace(
    "한국 PC 클라 Table_Monster 추출(이름/EXP/스탯/Shape/Zone) · 맵 한글명 추후 연결",
    client_desc,
  )
  text = text.replace(
    "한국 PC 클라 Table_Monster+Table_Map 추출(이름/EXP/스탯/Shape/출현맵)",
    client_desc,
  )
  text = text.replace(
    "클라 목록 + 기존 DB Base/Job·출현맵 (ManualMap 제외)",
    client_desc,
  )
  text = text.replace(
    "클라 목록 + 기존 DB 이름/Base/Job/출현맵 (ManualMap 제외)",
    client_desc,
  )
  # 검색: 클라 표기(구미호/메카)도 찾게
  old_filter = """list.filter((m) =>
          m.ko.toLowerCase().includes(q) ||
          String(m.lv).includes(q) ||
          String(m.id).includes(q)
        )"""
  new_filter = """list.filter((m) =>
          m.ko.toLowerCase().includes(q) ||
          (m.clientKo || "").toLowerCase().includes(q) ||
          (m.en || "").toLowerCase().includes(q) ||
          String(m.lv).includes(q) ||
          String(m.id).includes(q)
        )"""
  if old_filter in text:
    text = text.replace(old_filter, new_filter, 1)
  return text


def replace_monsters_const(text: str, pool: list[dict]) -> str:
  """HTML의 const MONSTERS = [...] 를 신규 풀로 교체."""
  m = re.search(r"const MONSTERS\s*=\s*(\[)", text)
  if not m:
    raise ValueError("const MONSTERS not found")
  start = m.start(1)
  i = start
  depth = 0
  in_str = False
  esc = False
  quote = ""
  while i < len(text):
    ch = text[i]
    if in_str:
      if esc:
        esc = False
      elif ch == "\\":
        esc = True
      elif ch == quote:
        in_str = False
    else:
      if ch in "\"'":
        in_str = True
        quote = ch
      elif ch == "[":
        depth += 1
      elif ch == "]":
        depth -= 1
        if depth == 0:
          old = text[start : i + 1]
          new = json.dumps(pool, ensure_ascii=False, separators=(",", ":"))
          return text[:start] + new + text[i + 1 :]
    i += 1
  raise ValueError("failed to parse MONSTERS array")


def main() -> None:
  pool = build_pool()
  out_json = ROOT / "leveling_monsters_client_full.json"
  out_json.write_text(json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")

  for name in ["레벨링_도우미.html", "index.html", "leveling-helper.html"]:
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    if 'data-tab="huntClient"' in text or "MONSTERS_CLIENT_FULL" in text:
      raise SystemExit(
        f"{name} still has old dual-tab markup. Run _promote_hunt_main.py first, "
        "or restore a promoted HTML."
      )
    text = replace_monsters_const(text, pool)
    path.write_text(text, encoding="utf-8")
    print("patched", name)

  print("pool", len(pool))
  from collections import defaultdict, Counter
  by_ko = defaultdict(list)
  for m in pool:
    by_ko[m["ko"]].append(m)
  dups = {k: v for k, v in by_ko.items() if len(v) > 1}
  print("duplicate names", len(dups))
  src = Counter(m.get("mapsNote", "") or "(없음)" for m in pool)
  print("map notes", dict(src))
  for name in ("포링", "마이너우로스", "메카 하운드", "구미호", "타로우", "데니로"):
    hits = [m for m in pool if m["ko"] == name]
    for h in hits:
      print(name, "maps=", [x.get("ko") for x in h["maps"]], "note=", h.get("mapsNote"))


if __name__ == "__main__":
  main()

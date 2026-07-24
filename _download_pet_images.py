# -*- coding: utf-8 -*-
"""Download pet/item images from 1gamerdash into assets/pets/"""
from pathlib import Path
from urllib.request import Request, urlopen
import ssl

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "pets"
OUT.mkdir(parents=True, exist_ok=True)

URLS = [
  "https://1gamerdash.com/wp-content/uploads/2019/01/poring.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/green-apple.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/lunatic.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/rainbow-carrot.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/yoyo.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/tropical-banana.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/desert-wolf-baby.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/well-dried-bone.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/savage-babe.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/sweet-milk.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/mandragora-seed.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/nutrition-potion.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/green-petite.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/shining-stone.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/isis.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/armlet-of-obedience.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/deviruchi.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/contract-in-shadow.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/08/cruiser-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/08/toygun-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/08/teddy-bear-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/08/gift-box-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/sohee.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/silver-knife-of-chastity.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/01/baphomet-jr.png",
  "https://1gamerdash.com/wp-content/uploads/2019/01/book-of-the-devil.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/08/black-witch-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/08/worn-out-gorgeous-clip-ragnarok-mobile.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/spore.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/moss.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/poison-spore.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/poisonous-grass.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/rocker.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/whistling-flower.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/whisper.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/oak-trunk.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/peco-peco.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/nutritious-worm.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/munak.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/magic-letter.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/golem.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/magic-plate.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/orc-warrior.jpg",
  "https://1gamerdash.com/wp-content/uploads/2019/10/monsters-proof.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/dokebi.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/monster-besom.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/goblin-buckler.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/goblin-buckers-ring.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/quve.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/black-cloth.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/succubus.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/swaying-apron.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/incubus.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/love-letter.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/marmot.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/monster-shield.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/dullahan.png",
  "https://1gamerdash.com/wp-content/uploads/2019/10/piece-of-armor.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-marina.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-unicellular.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-typhoon.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-withered-leaf.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-mechanical-hound.png",
  "https://1gamerdash.com/wp-content/uploads/2020/01/ragnarok-mobile-damaged-parts.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-yolk-poring.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-cracked-eggshell.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-injustice.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-red-candle.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-roween.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-fresh-fish.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-siroma.png",
  "https://1gamerdash.com/wp-content/uploads/2020/03/ragnarok-mobile-ice-heart.png",
  "https://1gamerdash.com/wp-content/uploads/2020/07/ragnarok-mobile-lantern-fisherman.png",
  "https://1gamerdash.com/wp-content/uploads/2020/07/ragnarok-mobile-fresh-schrimps.png",
  "https://1gamerdash.com/wp-content/uploads/2020/07/ragnarok-mobile-panda-poring.png",
  "https://1gamerdash.com/wp-content/uploads/2020/07/ragnarok-mobile-delicious-bamboo-shoots.png",
  "https://1gamerdash.com/wp-content/uploads/2021/04/ragnarok-mobile-mimmy-monster.jpg",
  "https://1gamerdash.com/wp-content/uploads/2021/04/ragnarok-mobile-vanilla-pudding.jpg",
  "https://1gamerdash.com/wp-content/uploads/2021/04/ragnarok-mobile-doll-devil.jpg",
  "https://1gamerdash.com/wp-content/uploads/2021/04/ragnarok-mobile-rainbow-lollipop.jpg",
]

ctx = ssl.create_default_context()
ok = fail = 0
for url in URLS:
  name = url.rsplit("/", 1)[-1]
  dest = OUT / name
  if dest.exists() and dest.stat().st_size > 0:
    print("skip", name)
    ok += 1
    continue
  try:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, context=ctx, timeout=30) as r:
      data = r.read()
    dest.write_bytes(data)
    print("ok", name, len(data))
    ok += 1
  except Exception as e:
    print("FAIL", name, e)
    fail += 1

print("done ok", ok, "fail", fail)
if fail:
  raise SystemExit(1)

#!/usr/bin/env python3
"""Pull community MakeHuman wigs (obj + mhclo only) onto the clay shelf."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
HAIR = ROOT / "models/hair"
CATALOG = ROOT / "web/parts/hair-community.json"
NOTICE = HAIR / "NOTICE"

OFFICIAL = {
    "afro01",
    "bob01",
    "bob02",
    "braid01",
    "long01",
    "ponytail01",
    "short01",
    "short02",
    "short03",
    "short04",
}
SKIP = {"learning_anime_hair", "elvs_lara_hair"}

PACKS = [
    {
        "id": "hair01",
        "zip": "hair01_cc0.zip",
        "license": "CC0",
        "authors": "Cortu, culturalibre, Elvaerwyn, Faydaen, littleright, punkduck, RehmanPolanski, sonntag78, MargaretToigo",
    },
    {
        "id": "hair02",
        "zip": "hair02_ccby.zip",
        "license": "CC-BY",
        "authors": "Elvaerwyn",
    },
    {
        "id": "hair03",
        "zip": "hair03_ccby.zip",
        "license": "CC-BY",
        "authors": "culturalibre, grinsegold, punkduck",
    },
]

MIRRORS = [
    "https://files2.makehumancommunity.org/asset_packs/{id}/{zip}",
    "https://files.makehumancommunity.org/asset_packs/{id}/{zip}",
    "http://download.tuxfamily.org/makehuman/asset_packs/{id}/{zip}",
    "https://download.tuxfamily.org/makehuman/asset_packs/{id}/{zip}",
]

LABELS = {
    "cortu_shaggy_green_hair": "лохматая",
    "cortu_short_messy_hair": "растрёпанная",
    "cortu_straight_bangs": "чёлка",
    "cortu_strawberry_cloud_hair": "облако",
    "culturalibre_hair_01": "кудри",
    "culturalibre_hair_02": "кудри 2",
    "culturalibre_hair_05": "кудри 3",
    "culturalibre_hair_06": "кудри 4",
    "culturalibre_hair_11": "кудри 5",
    "culturalibre_hair_12": "кудри 6",
    "culturalibre_hair_13": "кудри 7",
    "culturalibre_hair_14": "кудри 8",
    "culturalibre_hair_17": "кудри 9",
    "culturalibre_hair_18": "кудри 10",
    "elvs_50s_updo": "высокая",
    "elvs_adrienne_hair": "адриен",
    "elvs_ashley_may_hair": "эшли",
    "elvs_braid_bun": "пучок-коса",
    "elvs_braided_rows": "ряды кос",
    "elvs_daisy_hair": "ромашка",
    "elvs_double_mh_braid": "две косы",
    "elvs_french_braid_variation": "французская",
    "elvs_grump_hair": "короткая ёж",
    "elvs_hazel_hair": "хейзел",
    "elvs_inverted_curly_bob": "кудрявое каре",
    "elvs_island_princess_hair": "локоны",
    "elvs_katherine_hair": "кэтрин",
    "elvs_keylth_hair": "кейльт",
    "elvs_lady_hippy_hair": "хиппи",
    "elvs_lara_hair": "лара",
    "elvs_maxwell_hair": "максвелл",
    "elvs_micky_afro": "афро 2",
    "elvs_reverse_french_braid_bun": "пучок с косой",
    "elvs_short_daisy_hair": "короткая ромашка",
    "elvs_short_side_do": "набок",
    "elvs_that_80s_babe_hair": "восьмидесятые",
    "elvs_unkempt_french_braid": "коса растрёпанная",
    "elvs_wavy_bob": "волнистое каре",
    "elvs_witchy_lil_bob": "короткое каре",
    "faydaen_hair_1": "файдаен",
    "grinsegold_wig_bow_tie": "бант",
    "grinsegold_wig_bun_blonde_braids": "пучок и косы",
    "littleright_bobcut_hair": "каре под линию",
    "o4saken_chinesebob01": "каре восток",
    "o4saken_curly01": "кудри панк",
    "o4saken_long01": "длинная 2",
    "punkduck_alpha7_curly": "кудри длинные",
    "punkduck_alpha7_curly2": "кудри длинные 2",
    "punkduck_alpha7_long": "длинная 3",
    "punkduck_alpha7_long2": "длинная 4",
    "rehmanpolanski_hair_bun_brown": "пучок",
    "sonntag78_blond_with_headband": "ободок",
    "sonntag78_junglebook_hair": "паж",
    "toigo_blunt_bob": "прямое каре",
    "toigo_blunt_bob_with_bangs": "прямое каре с чёлкой",
    "toigo_curled_under_bob": "каре подворот",
    "toigo_curled_under_bob_with_bangs": "каре подворот с чёлкой",
    "toigo_inverted_bob": "каре укороченное",
    "toigo_inverted_bob_with_bangs": "каре укороченное с чёлкой",
}


def download(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Game-Live-v2-hair-fetch"})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch_zip(pack: dict) -> bytes:
    errors = []
    for template in MIRRORS:
        url = template.format(id=pack["id"], zip=pack["zip"])
        try:
            print(f"try {url}")
            data = download(url)
            if data[:2] == b"PK" and len(data) > 1000:
                print(f"  got {len(data)} bytes")
                return data
            errors.append(f"{url}: not a zip ({len(data)} bytes)")
        except (URLError, TimeoutError, OSError) as err:
            errors.append(f"{url}: {err}")
    raise RuntimeError("could not download " + pack["id"] + "\n" + "\n".join(errors))


def zip_find(zf: zipfile.ZipFile, name: str) -> str | None:
    name = name.replace("\\", "/").lstrip("./")
    for info in zf.infolist():
        path = info.filename.replace("\\", "/")
        if path.endswith("/"):
            continue
        if path == name or path.endswith("/" + name):
            return info.filename
    return None


def asset_id(mhclo_path: str) -> str:
    stem = Path(mhclo_path.replace("\\", "/")).stem.lower()
    return re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")


def parse_mhclo_meta(text: str) -> dict:
    meta = {"basemesh": "", "obj_file": "", "name": ""}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "basemesh":
            meta["basemesh"] = parts[1]
        elif len(parts) >= 2 and parts[0] == "obj_file":
            meta["obj_file"] = parts[1]
        elif len(parts) >= 2 and parts[0] == "name":
            meta["name"] = parts[1]
    return meta


def extract_pack(pack: dict, data: bytes) -> list[dict]:
    found = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        mhclos = [
            info.filename
            for info in zf.infolist()
            if info.filename.lower().endswith(".mhclo") and not info.is_dir()
        ]
        for mhclo_name in sorted(mhclos):
            aid = asset_id(mhclo_name)
            if aid in SKIP or aid in OFFICIAL:
                print(f"skip {aid}")
                continue
            raw = zf.read(mhclo_name).decode("utf-8", errors="replace")
            meta = parse_mhclo_meta(raw)
            if "hm08" not in meta["basemesh"]:
                print(f"skip {aid}: basemesh {meta['basemesh'] or '?'}")
                continue
            obj_name = meta["obj_file"] or (Path(mhclo_name).stem + ".obj")
            obj_path = zip_find(zf, obj_name) or zip_find(zf, Path(mhclo_name).stem + ".obj")
            if not obj_path:
                print(f"skip {aid}: no obj")
                continue
            obj = zf.read(obj_path).decode("utf-8", errors="replace")
            if "verts 0" not in raw:
                print(f"skip {aid}: no verts 0")
                continue
            obj_text = obj
            nverts = sum(1 for line in obj_text.splitlines() if line.startswith("v "))
            nmaps = 0
            started = False
            for line in raw.splitlines():
                if line.strip().startswith("verts "):
                    started = True
                    continue
                if not started:
                    continue
                parts = line.split()
                if len(parts) >= 9 and parts[0].lstrip("-").replace(".", "", 1).isdigit():
                    nmaps += 1
            if nmaps < nverts:
                print(f"skip {aid}: maps {nmaps} < verts {nverts}")
                continue
            dest = HAIR / aid
            dest.mkdir(parents=True, exist_ok=True)
            (dest / f"{aid}.mhclo").write_text(raw)
            (dest / f"{aid}.obj").write_text(obj)
            found.append(
                {
                    "id": aid,
                    "label": LABELS.get(aid, aid.replace("_", " ")),
                    "license": pack["license"],
                    "pack": pack["id"],
                    "author": pack["authors"],
                }
            )
            print(f"kept {aid}")
    return found


def write_notice(styles: list[dict]) -> None:
    lines = [
        "Hair here is MakeHuman clothes (type Hair).",
        "",
        "Official CC0 system wigs (September 2020):",
        "  short01, short02, short03, short04,",
        "  bob01, bob02, afro01, ponytail01, long01, braid01",
        "",
        "Community packs (same MHCLO clothes, not official system hair):",
    ]
    by_pack: dict[str, list[dict]] = {}
    for style in styles:
        by_pack.setdefault(style["pack"], []).append(style)
    for pack in PACKS:
        items = by_pack.get(pack["id"], [])
        if not items:
            continue
        names = ", ".join(item["id"] for item in items)
        lines.append(f"  {pack['id']} {pack['license']} ({pack['authors']}): {names}")
    lines += [
        "",
        "helper-hair is a fitting cage and is not drawn.",
        "A tight scalp cap (scalp.obj) from the body skin sits under the wig",
        "so the skull does not show through hair cards.",
        "",
        "MPFB Hair Editor (Blender curves) is not used; these are mesh wigs.",
        "learning_anime_hair is not included.",
        "",
    ]
    NOTICE.write_text("\n".join(lines))


def already_done() -> bool:
    if not CATALOG.is_file():
        return False
    styles = json.loads(CATALOG.read_text()).get("styles") or []
    if len(styles) < 8:
        return False
    return all((HAIR / item["id"] / f"{item['id']}.obj").is_file() for item in styles)


def main() -> None:
    if already_done():
        print("community hair already vendored")
        return
    HAIR.mkdir(parents=True, exist_ok=True)
    styles: list[dict] = []
    for pack in PACKS:
        styles.extend(extract_pack(pack, fetch_zip(pack)))
    styles.sort(key=lambda item: item["label"])
    if len(styles) < 8:
        raise SystemExit(f"too few community wigs: {len(styles)}")
    CATALOG.write_text(json.dumps({"styles": styles}, ensure_ascii=False, indent=2) + "\n")
    write_notice(styles)
    print(f"wrote {len(styles)} community wigs -> {CATALOG}")


if __name__ == "__main__":
    main()

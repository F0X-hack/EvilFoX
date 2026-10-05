#!/usr/bin/env python3
"""
Générateur de hash CSP pour index.html (EvilFoX loader).

Pourquoi cet outil existe
-------------------------
La page est un fichier unique : tout le JavaScript est dans UN <script> inline.
Sur evilfox.foxhack.fr, nginx envoie une Content-Security-Policy du type :

    script-src 'self' 'sha256-XXXX...' https://unpkg.com blob:;

Dès qu'un seul caractère du script inline change (et dès qu'un hash est présent,
'unsafe-inline' est ignoré par le navigateur), le hash devient faux et Chrome/Edge
refusent d'exécuter le script. Symptôme : la page s'affiche parfaitement mais
RIEN ne répond — les onglets ne changent pas, on ne peut pas sélectionner
ESP32 / M5StickC Plus2, aucun bouton « Connect », aucun flash.

Cet outil recalcule le hash exact attendu par le navigateur.

Usage
-----
    python3 tools/csp-hash.py                     # affiche les hashes + le script-src prêt à coller
    python3 tools/csp-hash.py --check 'sha256-…'  # vérifie le hash actuellement en ligne
    python3 tools/csp-hash.py --nginx             # sortie formatée pour add_header nginx
    python3 tools/csp-hash.py --json              # sortie machine
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"

SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.DOTALL | re.IGNORECASE)

# Liste d'origines autorisées en plus du hash du script inline.
# unpkg  : module esp-web-tools (install-button.js) chargé en <script type="module">
# blob:  : manifeste généré à la volée + workers d'esptool-js
EXTRA_SCRIPT_SRC = ["'self'", "https://unpkg.com", "blob:", "'wasm-unsafe-eval'"]


def inline_scripts(html: str):
    """Rend (index, attributs, contenu) pour chaque <script> sans src=."""
    out = []
    for i, m in enumerate(SCRIPT_RE.finditer(html)):
        attrs, body = m.group(1), m.group(2)
        if re.search(r"\bsrc\s*=", attrs, re.IGNORECASE):
            continue
        out.append((i, attrs.strip(), body))
    return out


def external_scripts(html: str):
    """Origines des <script src=...> : elles doivent apparaître dans script-src."""
    origins = set()
    for m in SCRIPT_RE.finditer(html):
        attrs = m.group(1)
        src = re.search(r"""src\s*=\s*["']([^"']+)["']""", attrs, re.IGNORECASE)
        if not src:
            continue
        url = src.group(1)
        if url.startswith(("http://", "https://", "//")):
            u = ("https:" + url[2:]) if url.startswith("//") else url
            m2 = re.match(r"(https?://[^/]+)", u)
            if m2:
                origins.add(m2.group(1))
    return sorted(origins)


def csp_hashes(body: str) -> dict[str, str]:
    """Le navigateur hache le contenu texte EXACT de l'élément (aucun trim)."""
    raw = body.encode("utf-8")
    return {
        "sha256": "sha256-" + base64.b64encode(hashlib.sha256(raw).digest()).decode(),
        "sha384": "sha384-" + base64.b64encode(hashlib.sha384(raw).digest()).decode(),
        "sha512": "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Hash CSP des scripts inline d'index.html")
    ap.add_argument("--page", default=str(PAGE), help="chemin de la page (défaut: index.html du dépôt)")
    ap.add_argument("--algo", default="sha256", choices=["sha256", "sha384", "sha512"])
    ap.add_argument("--check", metavar="HASH", help="hash à vérifier (ex: celui envoyé par nginx)")
    ap.add_argument("--check-file", metavar="FICHIER",
                    help="fichier de conf (nginx) dont on extrait les 'sha256-…' actifs pour vérification")
    ap.add_argument("--nginx", action="store_true", help="affiche la directive complète pour nginx")
    ap.add_argument("--json", action="store_true", help="sortie JSON")
    args = ap.parse_args()

    page = Path(args.page)
    if not page.exists():
        print(f"[xx] page introuvable : {page}", file=sys.stderr)
        return 2

    html = page.read_text(encoding="utf-8")
    scripts = inline_scripts(html)
    if not scripts:
        print("[!!] aucun <script> inline trouvé : rien à hasher (script externalisé ?)", file=sys.stderr)
        return 1

    hashes = [csp_hashes(body)[args.algo] for _, _, body in scripts]
    origins = external_scripts(html)
    parts: list[str] = []
    for item in EXTRA_SCRIPT_SRC[:1] + hashes + EXTRA_SCRIPT_SRC[1:] + origins:
        if item not in parts:  # évite les doublons ('self', origines déjà listées)
            parts.append(item)
    script_src = " ".join(parts)

    if args.json:
        print(json.dumps({
            "page": str(page),
            "size": len(html.encode("utf-8")),
            "inline_scripts": len(scripts),
            "algo": args.algo,
            "hashes": hashes,
            "external_origins": origins,
            "script_src": script_src,
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"page              : {page}  ({len(html.encode('utf-8'))} octets)")
    print(f"scripts inline    : {len(scripts)}")
    print(f"origines externes : {', '.join(origins) or '(aucune)'}")
    for h in hashes:
        print(f"hash {args.algo}      : '{h}'")

    if args.check:
        want = args.check.strip().strip("'\"")
        ok = any(want == h or want == h.split("-", 1)[1] for h in hashes)
        print()
        if ok:
            print(f"[ok] le hash fourni correspond au script inline actuel -> le JS peut s'exécuter.")
            return 0
        print(f"[xx] LE HASH FOURNI NE CORRESPOND PAS au script inline de cette page.")
        print(f"     fourni   : {want}")
        print(f"     attendu  : {hashes[0]}")
        print("     -> le navigateur bloque TOUT le JS : page inerte (onglets, ESP32/M5, flash).")
        print("     -> remplace le hash dans la directive script-src du serveur puis recharge-le.")
        return 1

    if args.check_file:
        conf = Path(args.check_file)
        if not conf.exists():
            print(f"[xx] fichier introuvable : {conf}", file=sys.stderr)
            return 2
        actifs = []
        for lineno, line in enumerate(conf.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):   # variante commentée = inactive, ignorée
                continue
            actifs += [(lineno, h) for h in
                       re.findall(r"'(sha(?:256|384|512)-[A-Za-z0-9+/=]+)'", line)]
        print()
        if not actifs:
            print(f"[ok] {conf} : aucun hash actif (variante sans hash / 'unsafe-inline').")
            return 0
        bad = [(ln, h) for ln, h in actifs if h not in hashes]
        for ln, h in actifs:
            state = "ok " if h in hashes else "PÉRIMÉ"
            print(f"  [{state}] {conf.name}:{ln}  '{h}'")
        if bad:
            print()
            print(f"[xx] {len(bad)} hash(s) de {conf.name} ne correspondent plus à {page.name}.")
            print(f"     attendu : {hashes[0]}")
            print("     -> en l'état, le navigateur bloque tout le JS : page inerte.")
            return 1
        print(f"\n[ok] {conf.name} est aligné sur {page.name}.")
        return 0

    print()
    print("script-src prêt à coller :")
    print(f"  {script_src};")

    if args.nginx:
        print()
        print("Bloc nginx complet :")
        print(f'  add_header Content-Security-Policy "default-src \'self\'; '
              f"img-src 'self' data:; "
              f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
              f"font-src 'self' data: https://fonts.gstatic.com; "
              f"script-src {script_src}; "
              f"worker-src blob:; "
              f"connect-src 'self' {' '.join(origins)} blob: data:; "
              f"media-src 'self'; "
              f"form-action 'none'; frame-ancestors 'none'; base-uri 'self'; "
              f'object-src \'none\'" always;')

    print()
    print("rappel : à refaire après CHAQUE modification d'index.html (le hash change).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Sert le dépôt en local avec LES MÊMES en-têtes que le vhost nginx de
evilfox.foxhack.fr (CSP comprise). Objectif : reproduire la panne — ou prouver
le correctif — avant de téléverser quoi que ce soit sur le serveur.

    python3 tools/serve-with-csp.py                 # port 8080, hash lu dans deploy/evilfox-headers.inc
    python3 tools/serve-with-csp.py --port 9000
    python3 tools/serve-with-csp.py --stale         # rejoue le hash PÉRIMÉ qui a cassé le site
    python3 tools/serve-with-csp.py --no-csp        # sert sans CSP (comportement Render)

Puis ouvrir http://localhost:8080 dans Chrome/Edge. Web Serial exige un contexte
sécurisé : http://localhost compte comme sécurisé, donc le bouton « Connect » et
le sélecteur de port fonctionnent aussi en local.
"""

from __future__ import annotations

import argparse
import http.server
import re
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS_INC = ROOT / "deploy" / "evilfox-headers.inc"

# Hash qui était en production le 2026-10-05 et qui bloquait tout le JS.
STALE_HASH = "sha256-Z0HhYjhut2zWYa2+nNHodShnJSCQ4zSA2irGx+IE/Jk="


def csp_from_conf(path: Path) -> str:
    """Extrait la directive CSP active (non commentée) du snippet nginx."""
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        m = re.search(r'add_header\s+Content-Security-Policy\s+"([^"]+)"', s)
        if m:
            return m.group(1)
    raise SystemExit(f"[xx] aucune CSP active trouvée dans {path}")


def swap_hash(csp: str, new_hash: str) -> str:
    return re.sub(r"'sha(?:256|384|512)-[A-Za-z0-9+/=]+'", f"'{new_hash}'", csp, count=1)


def main() -> int:
    ap = argparse.ArgumentParser(description="Serveur local avec les en-têtes de production")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--stale", action="store_true", help="utiliser le hash périmé (rejoue la panne)")
    ap.add_argument("--hash", dest="hash_", help="imposer un hash sha256-… précis")
    ap.add_argument("--no-csp", action="store_true", help="ne pas envoyer de CSP")
    ap.add_argument("--allow-frame", action="store_true",
                    help="retirer X-Frame-Options / frame-ancestors (aperçu dans une iframe)")
    args = ap.parse_args()

    csp = "" if args.no_csp else csp_from_conf(HEADERS_INC)
    if csp and (args.stale or args.hash_):
        csp = swap_hash(csp, STALE_HASH if args.stale else args.hash_)

    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cache-Control": "no-store",
    }
    if args.allow_frame:
        headers.pop("X-Frame-Options", None)
        csp = re.sub(r"frame-ancestors\s+'none';\s*", "", csp)
        csp = csp.replace("frame-ancestors 'none'", "frame-ancestors *")
    if csp:
        headers["Content-Security-Policy"] = csp

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def end_headers(self):
            for k, v in headers.items():
                self.send_header(k, v)
            super().end_headers()

        def guess_type(self, path):
            if str(path).endswith(".bin"):
                return "application/octet-stream"
            return super().guess_type(path)

        def log_message(self, fmt, *a):
            sys.stderr.write("  %s\n" % (fmt % a))

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((args.host, args.port), Handler) as httpd:
        url = f"http://localhost:{args.port}/"
        print(f"[ok] EvilFoX loader servi depuis {ROOT}")
        print(f"     -> {url}   (Chrome / Edge, Web Serial OK sur localhost)")
        if csp:
            used = re.search(r"'(sha(?:256|384|512)-[A-Za-z0-9+/=]+)'", csp)
            print(f"     CSP active, hash = {used.group(1) if used else '(aucun hash : mode unsafe-inline)'}")
            if args.stale:
                print("     [!!] mode --stale : la page doit rester INERTE (bandeau violet « JavaScript bloqué »)")
        else:
            print("     aucune CSP envoyée (comportement Render)")
        if args.allow_frame:
            print("     [!!] --allow-frame : X-Frame-Options/frame-ancestors relâchés pour l'aperçu iframe")
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

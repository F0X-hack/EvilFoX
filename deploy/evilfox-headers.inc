# =============================================================================
#  EvilFoX loader — en-têtes de sécurité (snippet nginx, sans bloc location)
# -----------------------------------------------------------------------------
#  Ce fichier ne contient QUE des add_header : il peut être inclus au niveau
#  server{} comme à l'intérieur d'un location{} (nginx n'hérite pas des
#  add_header dès qu'un bloc en définit lui-même → on le ré-inclut partout).
#
#  Installation :
#      sudo cp deploy/evilfox-headers.inc /etc/nginx/snippets/evilfox-headers.inc
#      sudo cp deploy/nginx-evilfox.conf  /etc/nginx/snippets/evilfox-site.conf
#      sudo nginx -t && sudo systemctl reload nginx
# =============================================================================

# --- CSP ---------------------------------------------------------------------
# ⚠️  index.html contient TOUT le JavaScript dans un seul <script> inline.
#     Le 'sha256-…' ci-dessous est l'empreinte EXACTE de ce script. Dès qu'un
#     caractère change, le navigateur refuse d'exécuter le script et la page
#     devient inerte (onglets figés, ESP32 / M5 non sélectionnables, pas de
#     bouton « Connect », pas de flash) — et la présence d'un hash fait
#     IGNORER 'unsafe-inline'.
#
#     Recalculer après CHAQUE modification d'index.html :
#         python3 tools/csp-hash.py
#
#     Hash de l'index.html de ce dépôt          : sha256-X3cGBjDCSdZ9DQInaEpsbP1Qa/7PMvC06twmIIByNs0=
#     Hash de l'index.html actuellement en ligne
#     sur evilfox.foxhack.fr (2026-10-05 07:18 UTC, 72 643 o) — à utiliser si
#     tu corriges le vhost SANS re-téléverser le fichier :
#                                               : sha256-qHf2foXCqCEVHKeR8fsNY91UZN13/Y+/ahfa98dgV3k=
#     Hash périmé qui cassait le site           : sha256-Z0HhYjhut2zWYa2+nNHodShnJSCQ4zSA2irGx+IE/Jk=
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; script-src 'self' 'sha256-X3cGBjDCSdZ9DQInaEpsbP1Qa/7PMvC06twmIIByNs0=' https://unpkg.com blob: 'wasm-unsafe-eval'; worker-src blob:; connect-src 'self' https://unpkg.com blob: data:; media-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'" always;

# --- Variante « zéro maintenance » (plus aucun hash à recalculer) ------------
# À préférer si tu édites index.html souvent : commenter l'add_header ci-dessus
# et décommenter celui-ci. On perd la protection anti-injection du hash, la page
# n'ayant de toute façon aucune donnée utilisateur à sanitizer côté serveur.
# add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://unpkg.com blob: 'wasm-unsafe-eval'; worker-src blob:; connect-src 'self' https://unpkg.com blob: data:; media-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'" always;

# --- Autres en-têtes ---------------------------------------------------------
add_header X-Content-Type-Options     "nosniff"                         always;
add_header X-Frame-Options            "DENY"                            always;
add_header Referrer-Policy            "strict-origin-when-cross-origin" always;
add_header Permissions-Policy         "geolocation=(), microphone=(), camera=(), payment=()" always;
add_header Cross-Origin-Opener-Policy "same-origin"                     always;
add_header Strict-Transport-Security  "max-age=31536000; includeSubDomains" always;

# Ne JAMAIS ajouter "serial=()" à Permissions-Policy : Web Serial n'est pas
# concerné, mais une valeur vide couperait l'API si elle venait à être gérée.

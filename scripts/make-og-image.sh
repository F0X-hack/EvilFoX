#!/usr/bin/env bash
# ============================================================
#  EvilFoX — génération des assets SEO (Open Graph + images)
#  Dépendance : ImageMagick (convert), polices DejaVu.
#  Usage : bash scripts/make-og-image.sh   (depuis la racine du dépôt)
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

MONO=DejaVu-Sans-Mono-Bold
MONO_R=DejaVu-Sans-Mono
ACCENT="#9D4EDD"
ACCENT2="#c77dff"
BG="#050506"
DIM="#8b9199"

# ---------- 1. fond + grille + halo violet ----------
convert -size 1200x630 "xc:${BG}" /tmp/og-base.png

# grille 60px
convert -size 60x60 "xc:${BG}" \
  -fill "#141619" -draw "rectangle 0,0 59,0" \
  -fill "#141619" -draw "rectangle 0,0 0,59" \
  miff:- | convert /tmp/og-base.png -tile - -draw "color 0,0 reset" /tmp/og-grid.png

# halo violet en bas à gauche + vignette
convert -size 1200x630 radial-gradient:"rgba(157,78,221,0.55)-rgba(5,5,6,0)" \
  -resize 1100x1100! -geometry +0+300 /tmp/og-glow.png
convert /tmp/og-grid.png /tmp/og-glow.png -compose screen -composite /tmp/og-base2.png
convert -size 1200x630 radial-gradient:"rgba(0,0,0,0)-rgba(0,0,0,0.75)" -alpha on /tmp/og-vig.png
convert /tmp/og-base2.png /tmp/og-vig.png -compose multiply -composite /tmp/og-bg.png

# barre d'accent en bas
convert /tmp/og-bg.png -fill "${ACCENT}" -draw "rectangle 0,626 1200,629" /tmp/og-bg2.png

# ---------- 2. wordmark (glitch : deux copies décalées + texte net) ----------
convert -size 1200x630 xc:none -font "${MONO}" -pointsize 132 -kerning -4 \
  -fill "${ACCENT2}" -annotate +92+268 "EVILFOX" /tmp/og-t1.png
convert -size 1200x630 xc:none -font "${MONO}" -pointsize 132 -kerning -4 \
  -fill "${ACCENT}" -annotate +86+274 "EVILFOX" /tmp/og-t2.png
convert -size 1200x630 xc:none -font "${MONO}" -pointsize 132 -kerning -4 \
  -fill "#eef0f2" -annotate +89+271 "EVILFOX" /tmp/og-t3.png

convert /tmp/og-bg2.png /tmp/og-t1.png -compose screen -composite \
  /tmp/og-t2.png -compose screen -composite /tmp/og-t3.png -compose over -composite /tmp/og-step3.png

# ---------- 3. baseline + sous-titre + domaine ----------
convert /tmp/og-step3.png -font "${MONO}" -pointsize 30 -fill "${ACCENT}" \
  -annotate +92+330 "// FIRMWARE LOADER" /tmp/og-s1.png
convert /tmp/og-s1.png -font "${MONO_R}" -pointsize 26 -fill "#d7dbde" \
  -annotate +92+380 "Flash ESP32 / M5StickC depuis le navigateur" /tmp/og-s2.png
convert /tmp/og-s2.png -font "${MONO_R}" -pointsize 24 -fill "${DIM}" \
  -annotate +92+430 "esptool · Evil Twin · portail captif · scan Wi-Fi" /tmp/og-s3.png
convert /tmp/og-s3.png -font "${MONO}" -pointsize 27 -fill "#eef0f2" \
  -annotate +92+565 "evilfox.foxhack.fr" /tmp/og-s4.png
convert /tmp/og-s4.png -font "${MONO_R}" -pointsize 22 -fill "${DIM}" \
  -annotate +92+600 "projet FoXhack — recherche en sécurité offensive" /tmp/og-step4.png

# ---------- 4. les deux boards ----------
convert esp32.png -resize 230x230 -strip /tmp/og-dev1.png
convert m5.png   -resize 155x155 -strip /tmp/og-dev2.png
convert /tmp/og-step4.png \
  /tmp/og-dev1.png -geometry +850+150 -compose over -composite \
  /tmp/og-dev2.png -geometry +800+360 -compose over -composite \
  -strip -depth 8 -define png:compression-level=9 og-image.png

rm -f /tmp/og-*.png
identify og-image.png
du -h og-image.png

# ---------- 5. icône 192x192 (même glyphe que le favicon, format demandé par Google/PWA) ----------
convert -size 192x192 "xc:${BG}" -fill "${ACCENT}" \
  -draw "path 'M 36,156 L 96,36 L 156,156 L 96,120 Z'" \
  -strip -depth 8 -define png:compression-level=9 icon-192.png
identify icon-192.png

# ---------- 6. images produits : PNG 8 bits allégées + WebP ----------
for f in esp32 m5; do
  convert "$f.png" -resize 256x256 -strip -depth 8 -define png:compression-level=9 "$f.png"
  convert "$f.png" -resize 256x256 -strip -quality 88 "$f.webp"
  printf '%-12s %s\n' "$f.png" "$(du -h "$f.png" | cut -f1)"
  printf '%-12s %s\n' "$f.webp" "$(du -h "$f.webp" | cut -f1)"
done

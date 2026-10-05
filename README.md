# EvilFoX v2.0.0

**ESP32 WiFi Red Team Lab - EvilTwin & Credential Harvester**



[![Board](https://img.shields.io/badge/board-ESP32-9D4EDD?style=flat-square)](https://www.espressif.com/)
[![Board](https://img.shields.io/badge/board-M5StickC%20Plus%202-7B2FBE?style=flat-square)](https://m5stack.com/)
[![Language](https://img.shields.io/badge/language-C%2B%2B-9D4EDD?style=flat-square)]()
[![Status](https://img.shields.io/badge/status-operational-39FF14?style=flat-square)]()

EvilFoX est un **outil red team / pentest** portable basé sur l'ESP32. Il clone un réseau WiFi cible (Evil Twin), sert un portail captif réaliste avec des templates de marque, et capture silencieusement des identifiants - pour des tests de sécurité autorisés uniquement.

> **Avertissement** - Pour **usage éducatif uniquement** et **tests autorisés** sur des réseaux qui vous appartiennent ou pour lesquels vous avez une autorisation écrite explicite. Toute utilisation non autorisée est illégale dans la plupart des juridictions. Vous êtes responsable de vos actions.

---

## Web Flasher

Flash direct depuis le navigateur (Chromium, Web Serial) :

> **[https://evilfox.foxhack.fr/](https://evilfox.foxhack.fr/)** — domaine projet
> **[https://evilfox-q3jj.onrender.com/](https://evilfox-q3jj.onrender.com/)** — Render (même contenu)

Ou ouvrez `index.html` en local (`http://localhost`). Pas de driver à installer, pas d'esptool.

### Firmware

| Cible | Fichier | Version |
|---|---|---|
| ESP32 | `EvilFoX2-0-0.bin` | 2.0.0 |
| M5StickC Plus2 (1.14") | `M5EvilFoX1-0-2.bin` | 1.0.2 |

- `manifest-esp32.json` / `manifest-m5.json` : **requis**. La page flashe toujours en mode « fichier statique » (`USE_FILE_MANIFEST=true`) pour que le `.bin` soit résolu en URL relative du même hôte — indispensable derrière une CSP stricte.
- `esp32.png` / `m5.png` : images des boards pour le sélecteur d'appareil.
- Flash CLI (alternative) :

```bash
esptool.py --chip esp32 -p /dev/ttyUSB0 -b 460800 \
  --before default_reset --after hard_reset write_flash 0x0 EvilFoX2-0-0.bin
```

---

## Déploiement & CSP (`evilfox.foxhack.fr`)

`index.html` est **autonome** : tout le JavaScript tient dans un seul `<script>` inline. Sur le vhost nginx (OVH) une `Content-Security-Policy` autorise ce script par son empreinte `sha256-…`. **Dès qu'un caractère du script change, le hash devient faux** — et la présence d'un hash fait ignorer `'unsafe-inline'` par le navigateur.

Symptôme exact (panne du 2026-10-05) : la page s'affiche, mais **rien ne répond** — les onglets ne changent pas, les cartes ESP32 / M5StickC Plus2 ne se sélectionnent pas, le bouton `Connect` d'esp-web-tools n'apparaît jamais, aucun flash. Console : `Refused to execute inline script because it violates the following Content Security Policy directive…`. Render n'envoie aucune CSP : c'est pour cela que `evilfox-q3jj.onrender.com` fonctionnait pendant que `evilfox.foxhack.fr` était inerte.

### Après chaque modification d'`index.html`

```bash
python3 tools/csp-hash.py                     # nouveau hash + directive prête à coller
python3 tools/csp-hash.py --check 'sha256-…'  # vérifier le hash envoyé par le serveur
sudo nginx -t && sudo systemctl reload nginx
```

Fichiers de référence : `deploy/nginx-evilfox.conf` (vhost + cache) et `deploy/evilfox-headers.inc` (en-têtes, dont la CSP et son hash). Une variante « zéro maintenance » sans hash (`script-src 'self' 'unsafe-inline' …`) y est fournie commentée.

### Checklist de déploiement

| Élément | Attendu |
|---|---|
| `index.html` | servi en `text/html`, **`Cache-Control: no-store`** (sinon vieux HTML + nouveau hash = page inerte) |
| `EvilFoX2-0-0.bin` / `M5EvilFoX1-0-2.bin` | `200`, `application/octet-stream`, mêmes noms que dans les manifests |
| `manifest-esp32.json` / `manifest-m5.json` | `200`, `application/json` — **requis** |
| `esp32.png` / `m5.png` | `200` |
| `script-src` | hash recalculé + `https://unpkg.com` (module esp-web-tools) + `blob:` |
| `connect-src` | `'self'` + `https://unpkg.com` + `blob:` (manifeste + `.bin`) |
| `worker-src` | `blob:` (workers esptool-js) |
| HTTPS | obligatoire : Web Serial n'existe que dans un *secure context* (`https://` ou `http://localhost`) |
| Navigateur | Chrome / Edge / Opera **desktop** (ni Firefox, ni Safari, ni Android) |

Un bandeau violet « **JavaScript bloqué** » apparaît en haut de la page (après ~1,2 s) si le script inline n'a pas pu s'exécuter : la panne n'est plus silencieuse.

---

## Features

- **WiFi Recon** - Scan continu (toutes les 15s), jusqu'à 16 réseaux avec canal + BSSID, auto-détection des boxes françaises (Orange / Free / SFR / Bouygues).
- **Evil Twin** - Clonage du réseau sélectionné en un tap (même SSID) + DNS spoofing de tous les domaines vers le portail captif (`* -> 192.168.4.1`).
- **Portails captifs réalistes** - Pages "Router Configuration" copiant l'apparence des pages admin officielles de chaque ISP.
- **Capture silencieuse** - Les identifiants sont validés en arrière-plan contre le vrai réseau. Pas de page "wrong password" : la victime est redirigée, le mot de passe est stocké et affiché dans l'admin panel.
- **Credentials Mode** - Portail de login factice `email` + `password` avec un SSID custom.
- **Upload de portail custom** - Envoyez votre propre portail HTML depuis le navigateur ; le nom du fichier (sans `.html`) devient le SSID d'attaque. Voir `template/` et `template.html`.
- **Admin Panel** - Métriques live (cible, compteur creds, statut d'attaque, uptime, risque), tableau des réseaux avec barres de signal, `Select` / `Start` / `Stop`, auto-refresh.
- **Credential Dump** - Tableau Email / Password / SSID / Time / IP, **Export CSV**, **Purge**.
- **Mobile-First UI** - Design "DedSec" responsive (violet neon, effets glitch, scanlines) : menu hamburger, tableaux scrollables, grandes zones tactiles, inputs 16px contre le zoom auto iOS.

---

## Usage

### Accéder au panel admin

| | |
|---|---|
| **Panel URL** | `http://192.168.4.1` |
| **WiFi SSID** | `FoXhack` |
| **Password** | `FoXhack_Evil` |
| **WiFi SSID** | `Resultat` |
| **Password** | `FoXhack_Resultat` |


Connectez-vous au point d'accès, puis ouvrez l'URL sur n'importe quel appareil (mobile ou desktop).

### Step-by-step

1. **Sélectionner une cible** - dans *Network Recon*, tapez **Select** à côté d'un réseau.
2. **Lancer EvilTwin** - tapez **Start EvilTwin**. L'ESP32 rediffuse le même SSID et DNS-spoofe vers le portail.
3. **La victime arrive sur le portail** - une page "Router Configuration" demande le mot de passe WiFi.
4. **Récupérer le mot de passe** - après soumission, l'ESP32 teste le mot de passe contre le vrai réseau ; il est stocké puis affiché dans la page **Credentials** et en bannière de succès sur le dashboard.

### Autres opérations

- **Credentials mode** - saisissez un *Custom SSID* puis **Start Creds** pour servir le portail email/password.
- **Portail custom** - uploadez un fichier `.html` ; son nom devient le SSID :
  - Le formulaire doit `POST` vers `/` avec des champs `email` et `password` (voir `Invite.html`).
- **Templates inclus** - `template/` contient 12 portails de marque (`template.html` les rassemble pour téléchargement) : Starbucks, SNCF Connect, Quick, Monoprix, KFC, Free WiFi, Free Wifi Mcdo, E.Leclerc, Carrefour, Burger King, Basic Fit, Auchan.
- **Export / Purge** - export CSV et purge depuis la page `/creds`.

---

## HTTP API (endpoints)

| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET/POST | Dashboard (admin) ou portail captif (attaque active) |
| `/admin` | GET | Admin panel (alias de `/`) |
| `/creds` | GET | Page Credentials (auto-refresh 10s) |
| `/creds?action=export` | GET | Téléchargement des identifiants en CSV |
| `/creds?action=clear` | GET | Purge de tous les identifiants |
| `/upload` | POST | Upload du portail captif custom (multipart) |
| `/clear_custom_html` | POST | Retour au portail par défaut |
| `/result` | GET | Page de statut post-credential |

---

## Legal & Ethical Use

**Cet outil est prévu pour :**

- Des engagements Red Team / pentest avec autorisation écrite
- La recherche et l'éducation en sécurité
- Tester votre propre infrastructure

**Ne l'utilisez jamais pour :**

- Intercepter du trafic que vous n'êtes pas autorisé à inspecter
- Voler des identifiants de réseaux qui ne vous appartiennent pas
- Perturber des réseaux publics

---

## License

Distribué à des fins éducatives et de recherche uniquement. Utilisation à vos risques et périls.

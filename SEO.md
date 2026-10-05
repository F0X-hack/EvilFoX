# SEO — foxhack.fr & evilfox.foxhack.fr

Audit et actions réalisées le **2026-10-05**.

Le dépôt `F0X-hack/EvilFoX` **est** le site servi sur `https://evilfox.foxhack.fr` (nginx, pas GitHub Pages).
Le domaine principal `https://foxhack.fr` est un autre dépôt (`F0X-hack/foxhack.fr`, Netlify).

---

## 1. En résumé

| Site | État avant | État après |
|---|---|---|
| `foxhack.fr` | Déjà bien optimisé : `canonical`, Open Graph, Twitter Card, JSON-LD (Person / WebSite / ProfilePage / ItemList), `robots.txt`, `sitemap.xml`, `<h1>` accessible, repli `<noscript>` complet | Inchangé — 2 améliorations restantes listées en §3 |
| `evilfox.foxhack.fr` | **Aucun** signal SEO : pas de `canonical`, pas d'Open Graph, pas de données structurées, pas de `robots.txt` ni `sitemap.xml`. Titre `EVILFOX // FIRMWARE LOADER` (ne cible aucune requête). Aucun lien vers le domaine principal dans la page | Optimisé de bout en bout, relié à `foxhack.fr` — détail en §2 |

Le point clé : la page EvilFoX est **la page du projet** rattachée au portfolio, mais rien ne le disait à Google
(pas de canonical, pas de fil d'Ariane, pas de données structurées partagées). Elle est désormais reliée au
`@id` `https://foxhack.fr/#person` publié par le portfolio : les deux sites forment un seul graphe d'entités.

---

## 2. Ce qui a été fait sur `evilfox.foxhack.fr`

### Balises et indexation
- **`<title>`** : `EvilFoX — Firmware Loader ESP32 / M5StickC Plus2 | Web Serial & esptool`
  (l'ancien titre ne contenait aucune requête recherchée).
- **`meta description`**, `keywords`, `author`, `robots` (`max-image-preview:large`, `max-snippet:-1`).
- **`canonical`** absolu vers `https://evilfox.foxhack.fr/`.
- **`hreflang`** `fr` / `en` / `x-default` : la bascule de langue est côté client, sur la même URL — c'est désormais déclaré.
- **`robots.txt`** (Allow + déclaration du sitemap) et **`sitemap.xml`** (URL unique + images).
- L'attribut **`lang`** du document suit maintenant la bascule FR/EN, et le `<title>` aussi.

### Aperçu au partage (réseaux, messagerie, Discord)
- **Open Graph** + **Twitter Card** complets, avec `og-image.png` **1200×630 généré** (logo glitché, les deux cartes, baseline).
  Avant, coller le lien ne produisait aucun aperçu riche.

### Données structurées (JSON-LD)
- `WebSite` (nom, langues, éditeur = `foxhack.fr/#person`)
- `SoftwareApplication` : version 2.0.0, catégorie `SecurityApplication`, `downloadUrl` (`EvilFoX2-0-0.bin`),
  `codeRepository`, `datePublished` / `dateModified`, `featureList`, offre gratuite
- `BreadcrumbList` : `foxhack.fr` → `evilfox.foxhack.fr/`
- `FAQPage` : les 5 questions de dépannage déjà écrites dans la page (éligibles aux résultats enrichis)

### Contenu et maillage interne
- Nouvelle section éditoriale indexable (« 05 · Flasher EvilFoX sur ESP32 / M5StickC Plus2 ») : description de
  l'outil, procédure de flash, panneau `192.168.4.1`, cadre légal, liens vers `foxhack.fr` et le dépôt GitHub.
  Le HTML statique de la page ne contenait presque aucun texte avant ça (tout était en `<code>`/libellés d'UI).
- **`<h1>`** avec équivalent texte lisible par les moteurs — et ce texte **survit désormais à l'effet glitch**
  (le script réécrivait l'intégralité du titre, ce qui aurait supprimé le texte ajouté).
- Pied de page : liens `← foxhack.fr`, dépôt GitHub, à propos, plan du site.

### Performance (facteur de classement)
- `esp32.png` **2,3 Mo → 76 Ko**, `m5.png` **103 Ko → 32 Ko** (PNG 8 bits allégés), plus versions **WebP** servies
  dans la page (16 Ko / 8 Ko), `width`/`height` et `decoding="async"`, `preload` de la première image.
- `manifest.webmanifest` + `icon-192.png` (favicon PNG demandé par Google, installation PWA possible).

### Corrections trouvées en route
- Le binaire ESP32 pointait sur `EvilFoX1-0-2.bin`, **absent du dépôt** : les liens de téléchargement et la
  commande esptool par défaut étaient cassés → remplacés par `EvilFoX2-0-0.bin` (le fichier réel).
- `/EvilFoX1-0-2.bin` sert désormais une page de redirection (anciens liens partagés toujours valides).
- Les liens GitHub pointaient vers le compte `FoX-hxck` (copie obsolète) au lieu de `F0X-hack`.
- `template.html` (templates de portails captifs) : `noindex` — ce n'est pas du contenu éditorial.
- Année du pied de page 2025 → 2026.

### Régénérer les visuels
```bash
bash scripts/make-og-image.sh    # og-image.png, icon-192.png, *.webp (ImageMagick + DejaVu)
```

---

## 3. Reste à faire

### A. Sur `foxhack.fr` (dépôt `F0X-hack/foxhack.fr`) — 2 améliorations

**1. Ancres de liens descriptives (impact : moyen, effort : 2 min)**

Les 7 projets utilisent le même texte de lien `VIEW PROJECT →` (`src/data/projects.ts`). Google utilise le
texte d'ancre pour comprendre la cible — surtout pour des liens sortants vers des sous-domaines. Remplacer
`cta` par un libellé propre à chaque projet :

```ts
// src/data/projects.ts — exemple pour EvilFoX
cta: 'Voir EvilFoX — firmware ESP32 →',
```
Le composant `<h3>` au-dessus contient déjà le nom du projet ; `cta` sert uniquement au lien.

**2. Prérendu HTML (impact : élevé, effort : moyen)**

Le portfolio est un SPA React : hors `<noscript>` (qui contient déjà l'essentiel), le contenu n'existe qu'après
exécution du JavaScript. Google exécute le JS, mais le prérendu reste plus fiable et plus rapide. Piste :
`react-snap` ou `vite-plugin-prerender` en post-build, sans changer le code des composants.

*(Optionnel : `loading="lazy"` + `width`/`height` sur les images sous la ligne de flottaison, hors image du hero.)*

### B. Hors code — à faire une fois (impact : élevé, côté comptes)

1. **Google Search Console** : ajouter une propriété de **domaine** pour `foxhack.fr` (couvre tous les
   sous-domaines : evilfox, reaper, foxhid), puis soumettre les deux sitemaps :
   - `https://foxhack.fr/sitemap.xml`
   - `https://evilfox.foxhack.fr/sitemap.xml`
2. **Bing Webmaster Tools** : même chose (import direct depuis Search Console).
3. **Aperçus de partage** : forcer la relecture après déploiement (Facebook Sharing Debugger,
   LinkedIn Post Inspector, `@card` Twitter/X) pour que `og-image.png` remplace l'aperçu vide.
4. **Déploiement** : le site est servi par **nginx** ; pousser les nouveaux fichiers dans la racine servie :
   `index.html`, `robots.txt`, `sitemap.xml`, `og-image.png`, `icon-192.png`, `esp32.webp`, `m5.webp`,
   `manifest.webmanifest` et le dossier `EvilFoX1-0-2.bin/`.
5. **Surveillance** : dans Search Console, suivre les requêtes « evilfox », « firmware esp32 »,
   « esp32 m5stickc » et les impressions par page pour ajuster titres et descriptions tous les 2–3 mois.

---

## 4. Rappel des fichiers SEO du dépôt

| Fichier | Rôle |
|---|---|
| `index.html` | Balises SEO, Open Graph, JSON-LD, contenu éditorial, maillage |
| `og-image.png` | Aperçu 1200×630 (Open Graph / Twitter / Discover) |
| `robots.txt` | Autorisation d'exploration + sitemap |
| `sitemap.xml` | URL + images pour Google/Bing |
| `manifest.webmanifest`, `icon-192.png` | PWA / favicon PNG |
| `EvilFoX1-0-2.bin/index.html` | Redirection de l'ancienne URL du binaire |
| `scripts/make-og-image.sh` | Régénération des images |

# Stabilité du rendu commun

Le CLS mesuré provenait surtout du menu et du bandeau supérieur créés par
`assets/agenda.js`, puis des partenaires chargés dans un second script.
Une réservation CSS ancienne attendait encore une bannière au format 3:1.

`stabilize_layout.cjs` prépare ces mêmes composants dans le HTML initial.
Il exécute uniquement les fonctions synchrones de navigation, de contact
(partie navigation seulement), de logement et de partenaires des scripts
existants. Ces scripts restent la source des textes, liens, images et styles.
Leurs gardes d’installation empêchent les doublons dans le navigateur.

Seules les pages canoniques du sitemap ayant le gabarit partagé sont traitées.
Les redirections, cartes autonomes et documents particuliers sont conservés.
Les remplacements utilisent les positions du HTML source : le `<main>`, les
métadonnées, les photographies et le JSON-LD ne sont pas resérialisés.
Les styles des partenaires sont ajoutés dans un bloc délimité du `<head>`.
Les anciens emplacements de bannière sont remplacés comme dans le composant.
Une seconde exécution doit produire exactement les mêmes octets.

Après les générateurs habituels, depuis la racine :

```sh
pnpm --dir tools/layout install --frozen-lockfile --ignore-scripts
node tools/stabilize_layout.cjs
node tools/stabilize_layout.cjs --check
node tools/test_stabilize_layout.cjs
python tools/test_layout_seo.py
python tools/check_site_integrity.py
node tools/check_homepage.cjs
```

`check-stable-layout.yml` vérifie les propositions en lecture seule.
Il prépare le HTML dans son espace de travail temporaire puis confirme que
la seconde exécution ne produit aucun changement ; il ne pousse aucun fichier.
`stabilize-layout.yml`, autorisé par le propriétaire le 28 octobre 2026,
prépare les composants après les générateurs existants et après un push HTML.
Il vérifie l’idempotence et l’intégrité avant de publier uniquement le HTML.
Si main change entre-temps, il reprend le dernier état et régénère ; il ne force
jamais l’écriture. Après un commit du bot, il demande explicitement une nouvelle
construction GitHub Pages pour que le HTML préparé soit effectivement servi.
Les workflows SEO et éditoriaux existants ne sont pas modifiés.
Les lecteurs HTML de `harmonize_seo.py` et `update_latest_article.py` ignorent
le bloc partenaire préparé pour préserver le choix de la photo, de ses dimensions
et de l’extrait éditorial, même si un article utilise la même image qu’un partenaire.

Sur Windows, certains chemins du dépôt ne diffèrent que par leur casse.
Pour préparer leurs versions exactes sans les écraser entre eux :

```sh
node tools/stabilize_layout.cjs --from-ref HEAD --output-dir ../rendered
```

Cette option produit des fichiers nommés par empreinte et un manifeste des
chemins exacts. Ne pas publier une copie Windows qui aurait fusionné ces chemins.

Les mesures de laboratoire ne remplacent pas les données CrUX. Après publication,
contrôler les pages publiques et les composants avant de demander la validation
Search Console. Aucun appel Search Console n’est effectué par cet outil.

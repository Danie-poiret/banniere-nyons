# Collection sur la lavande autour de Nyons

La page `/univers-lavande-nyons/` est une CollectionPage, distincte du grand guide `/produits-du-terroir/Lavande-de-Nyons/`. Elle organise neuf articles existants en cinq familles. Les articles, témoignages, photographies et redirections ne sont pas réécrits.

Modifier `tools/lavande-collection.json`, puis lancer `node tools/update_lavande_collection.cjs` et `node tools/update_lavande_collection.cjs --check`. Le générateur rend uniquement la collection et prépare les composants communs avant affichage. Deux générations doivent être identiques.

Les images reprennent les fichiers existants, avec dimensions, page d’origine, légendes et crédits. Aucun fichier image nouveau ou transformé. Les chiffres agricoles portent sur la France métropolitaine en 2025. Les distances sont des estimations OSRM/OpenStreetMap au 29 octobre 2026, au départ de Bleu Provence ; elles n’intègrent pas le trafic. Réactualiser les sources avant de modifier ces valeurs. Les fêtes passées et les programmes futurs sont distingués.

L’accueil contient les marqueurs `LAVANDE_COLLECTION_HOME_START/END` dans un bloc à deux colonnes avec la collection de l’olive. Il est hors des zones HOME_LATEST, HOME_EVENTS et HOME_SEASON, donc les mises à jour habituelles le préservent. Le bloc Plantes médicinales est retiré de cet accueil uniquement ; ses pages et les redirections de mr-plantes.com restent inchangées.

Le lien de Produits du terroir est inscrit dans `tools/terroir-collection.json` : le générateur existant le conserve. Le sitemap et Toutes les pages référencent la nouvelle collection. Cette page n’est pas un nouvel Article et ne remplace pas les dernières publications de l’accueil.

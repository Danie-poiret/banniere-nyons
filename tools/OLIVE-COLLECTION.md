# Collection sur l’olive de Nyons

Modifier tools/olive-collection.json pour ajouter ou ajuster une fiche (URL, titre, description, présentation et image existante avec ses dimensions et sa page source).

Exécuter node tools/update_olive_collection.cjs puis node tools/update_olive_collection.cjs --check. Le générateur actualise le sommaire, le nombre de fiches, les accès de l’accueil et des index, les liens de retour indiqués et le sitemap. Les articles ne sont ni déplacés ni réécrits. La collection reste distincte du grand guide AOP et ne devient pas un nouvel Article dans le flux des dernières publications.

Vérifier les liens, la provenance des images et le rendu sur ordinateur et téléphone avant publication. Conserver les années des fiches de fêtes et leurs réserves. Les URLs existantes et les redirections restent intactes.

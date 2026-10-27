# Portail des produits du terroir

Cette collection générale conserve les 31 fiches initiales, le lien vers la collection spécialisée de l’olive et ajoute le marché du jeudi : 33 destinations uniques dans cinq familles. Aucun article lié n’est réécrit par cet outil.

Pour ajouter une fiche, modifier tools/terroir-collection.json : choisir la famille, ajouter son URL canonique terminée par /, un titre et une description de 20 à 30 mots. Une image facultative reprend une photographie existante avec son chemin, son texte alternatif et ses dimensions. Sans image, la fiche devient un lien secondaire. Éviter les doublons.

Lancer node tools/update_terroir_collection.cjs depuis la racine du dépôt, puis node tools/update_terroir_collection.cjs --check. Le mode --partial-checkout est réservé aux copies partielles ; les articles et photos doivent alors être vérifiés séparément dans l’arbre du dépôt.

La page conserve son URL, ses identifiants de données structurées, ses métadonnées sociales et le bloc OLIVE_COLLECTION_INDEX utilisé par le générateur de la collection de l’olive. Le portail reste une CollectionPage, sans schéma Article. Ne pas modifier les marqueurs manuellement.

Les images proviennent des fiches existantes. La photographie d’abricots vient de la fiche du marché du jeudi ; sa source figure dans le manifeste. Aucune image historique n’a été générée ou transformée. L’image et les coordonnées existantes de la coopérative restent celles du site.

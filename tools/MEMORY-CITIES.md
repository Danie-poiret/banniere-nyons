# Publier un récit dans sa ville

Les anciens articles gardent leur chemin, leur contenu et leur canonical. Le
registre `memory-cities.json` rattache explicitement ces anciens chemins aux
villes. Il n'est pas nécessaire de modifier chaque ancien article.

Le générateur `update_memory_cities.py` crée les index manquants à partir du
modèle de Lille, complète les cartes des index existants, actualise les liens
des parents et ajoute seulement les nouvelles entrées du sitemap. Les images
sont celles des articles. Aucun index vide n'est créé et les différences de
casse provoquent un refus.

Pour préparer un nouvel article déjà rédigé, fournir son HTML complet avec un
canonical correspondant à son adresse définitive, un seul H1, une photographie
locale avec ses attributs et un JSON-LD Article avec sa vraie date de publication.
Exemple d'adresse :
`/Provence-Alpes-Cote-dAzur/Vaucluse/Avignon/place-de-l-horloge-autrefois/`.

```sh
python -m pip install lxml
python tools/update_memory_cities.py --add-article avignon place-de-l-horloge-autrefois /chemin/article-prepare.html --plan-only
python tools/update_memory_cities.py --add-article avignon place-de-l-horloge-autrefois /chemin/article-prepare.html
python tools/update_memory_cities.py --check
```

Le mode plan ne change aucun fichier. Le second appel crée directement l'article
dans le dossier Avignon et prépare automatiquement sa carte, le nombre de récits,
les liens du département, de la région et de Mémoire de France, et le sitemap.
Il refuse d'écraser un article existant ou de corriger silencieusement un canonical.
Le fichier de préparation doit rester hors du répertoire du site.

Pour une nouvelle ville, ajouter `--city-definition definition.json` au même
appel : `id`, `name`, `path`, `department`, `region`, `intro`, `title` et
`description` sont obligatoires. Le chemin comporte exactement région,
département et ville ; le département doit déjà exister avec la casse exacte.
Le premier récit et l'index sont préparés ensemble ; aucun dossier de ville vide
n'est publié. Les nouveaux récits repérés en dehors d'une ville enregistrée sont
refusés par le contrôle, sauf les chemins anciens explicitement conservés.

Après une nouvelle publication, relancer le générateur sans option permet de
rechercher les récits ajoutés dans les dossiers des villes. Deux appels successifs
doivent ensuite être stables. Le workflow de contrôle est en lecture seule : il
ne publie rien et ne remplace pas les règles de validation de la branche.

La préparation du nettoyage (PR n° 1) reste séparée. Le déploiement de ces pages
de ville nécessite de résoudre le risque des workflows existants capables de
réécrire l'accueil principal lors d'un push de pages ou du sitemap.

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


## Ajout rapide dans une ville existante

Pour un récit relu et validé, utiliser désormais le chemin ciblé :

```sh
python tools/add_memory_article.py avignon nouveau-recit /chemin/article-prepare.html --plan-only
python tools/add_memory_article.py avignon nouveau-recit /chemin/article-prepare.html
```

Il ne parcourt pas les autres villes : il ajoute le récit et sa carte, actualise le nombre de récits dans la ville et ses parents, le catalogue des récits et les six dernières histoires de Mémoire de France, puis ajoute l’URL au sitemap. Sept fichiers texte au maximum sont concernés ; l’accueil principal et les autres récits restent inchangés. Le script ne publie pas sur GitHub.

Réutiliser la copie locale et récupérer les versions actuelles des seuls fichiers nécessaires via leurs chemins exacts. Vérifier le récit, sa photo, ses liens et sa carte dans la ville. Réserver le générateur global et ses audits complets aux nouvelles villes, aux réorganisations et aux contrôles automatiques.

## Dernières histoires : publication et contrôle

Le catalogue `tools/memory-recent.json` est une donnée générée, pas une seconde
liste à entretenir manuellement. L'ajout ciblé actualise l'entrée du récit et le
bloc HTML `memory-recent` du portail dans la même opération. Récupérer aussi ce
catalogue dans une copie locale ciblée. Sans catalogue, la première génération
exige tous les articles pour le reconstruire ; ne pas l'initialiser depuis une
copie partielle.

Le tri utilise uniquement la vraie `datePublished`, puis l'ordre d'ajout au
sitemap pour départager les publications du même jour. Une correction de
`dateModified` ne fait pas remonter un ancien récit. Les articles sans date
documentée restent dans leur ville mais pas dans les dernières histoires. La
sélection éditoriale « Les histoires à découvrir » reste inchangée.

Pour corriger un récit existant et ses cartes sans créer de doublon :

```sh
python tools/add_memory_article.py marseille slug-existant /chemin/article-corrige.html --refresh --plan-only
python tools/add_memory_article.py marseille slug-existant /chemin/article-corrige.html --refresh
```

La date de publication d'origine doit être conservée. Pour une réparation du
catalogue depuis une copie complète de Mémoire de France :

```sh
python tools/memory_recent.py --rebuild
python tools/memory_recent.py --check
python -m unittest discover -s tools -p test_memory_recent.py
```

Le contrôle compare les métadonnées réelles des articles au catalogue et au bloc
HTML. Il échoue si les dernières histoires sont restées figées. Publier tous les
fichiers annoncés par le plan ensemble, avec `Memory-Cities-Only: true`, puis
vérifier l'URL de l'article, sa ville et le portail après le déploiement.

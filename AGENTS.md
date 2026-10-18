# VivreAnyons publishing rules

## Latest article on the homepage

When publishing a new editorial article, include accurate `Article` JSON-LD with
`headline`, `description`, `datePublished`, `dateModified`, and `image`.
Keep `datePublished` unchanged when editing an existing article. Do not assign
today's publication date to an imported old article merely because it was updated.
Give the article image a descriptive alt attribute and preserve its dimensions.

Append each new article to the root sitemap (entries added later resolve articles
published on the same day), and update its category and all-pages index.
Before publishing, run `python tools/update_latest_article.py` from the repository
root. Commit its changes to all three homepages together with the article. This
selects the latest `datePublished`, not `dateModified`, and creates the homepage
card with a clickable title, summary, date and photograph. The card stays in the
HTML so that it also works without JavaScript and is visible to search engines.

Keep the existing site navigation, banners, cookie controls and footer intact.
Verify the featured title links to the new article and the photo loads after
deployment. Do not substitute an old article just because its content was edited.


## Préférence éditoriale enregistrée le 4 octobre 2026

Pour les articles de Vivre à Nyons, conserver les avis utiles et les intégrer naturellement au texte, sans les noms de leurs auteurs et sans indiquer leur provenance (Google, commentaires, plateforme ou personne). Reformuler fidèlement les appréciations et les réserves ; ne pas inventer de témoignage ni de visite personnelle. Les liens vers les sources officielles restent possibles pour les coordonnées, horaires, tarifs et autres renseignements pratiques.


## Écriture des avis — consigne enregistrée le 4 octobre 2026

- Garder une voix simple, chaleureuse et concrète, à la manière de Papy Chris : phrases de longueurs variées, mots courants, situations du quotidien, sans ton publicitaire ni tournures automatiques répétées.
- Reprendre le plus possible les appréciations utiles fournies : sérieux, qualité du travail, efficacité, accueil, écoute, conseils, confiance et difficultés de disponibilité. Conserver aussi les réserves, sans les amplifier.
- Intégrer ces appréciations dans le récit, sans annoncer qu’elles viennent d’avis, de commentaires, de témoignages ou d’une plateforme ; ne pas afficher les noms de leurs auteurs. Les noms publics des artisans et entreprises peuvent rester pour identifier qui contacter.
- Reformuler sans recopier de longs passages, sans inventer une visite, un client, un chantier, une note, un consensus ou une promesse de résultat. Une recommandation brève reste une appréciation brève.
- Exemple de ton : « Le travail de Faure est apprécié pour son sérieux. Morin plaît pour son efficacité et son contact sympathique. Reste à demander un vrai créneau : un artisan peut être bon et avoir son planning rempli. »

## Écriture concrète — complément enregistré le 5 octobre 2026

Pour reformuler les appréciations fournies, observer les mots simples, les détails du quotidien et le rythme des phrases. Donner la priorité aux éléments précis qui rendent un lieu agréable ou moins pratique : table et bancs, propreté, ombre, accueil, explications, accès et disponibilité. Varier les longueurs de phrases sans fabriquer de fautes ni de tournures familières systématiques. Ne pas transformer une attention occasionnelle en prestation garantie, ni un cas isolé en règle générale. Aucun style ne garantit un résultat SEO ou l’indétectabilité d’un texte assisté.


## Maillage interne — préférence du 5 octobre 2026

Pour chaque nouvel article, choisir des liens internes directement utiles au sujet et varier les destinations. Ne mettre qu’une seule occurrence de chaque destination dans le corps de l’article. Éviter de renvoyer systématiquement aux arcades ou au marché de Nyons lorsqu’ils n’apportent rien au sujet. Cette règle concerne le texte éditorial, pas la navigation commune du site.

## Lien du marché de Nyons — préférence du 6 octobre 2026

Pour un lien intitulé « Marché de Nyons », utiliser la fiche `/que-faire-nyons/Marche-de-Nyons/` (https://www.vivreanyons.fr/que-faire-nyons/Marche-de-Nyons/). Adapter uniquement le préfixe aux versions de test. Conserver les liens vers les autres articles lorsqu’ils concernent un sujet distinct.

## Nom de la Brasserie de la Place — correction du 6 octobre 2026

Dans la fiche de la Brasserie de la Place à Nyons, ne pas présenter « Café de la Bourse » comme un autre nom de cet établissement. Le nom demandé par le propriétaire du site est « Brasserie de la Place ».


## Questions et réponses — préférence du 7 octobre 2026

Conserver un bloc « Questions / réponses » dans les fiches et nouveaux articles, avec des réponses pratiques correspondant aux informations vérifiées. Les questions adressées aux lecteurs peuvent rester en plus ; elles ne remplacent pas ce bloc. Ne pas supprimer les questions et réponses lors d’une mise à jour.

Ajouter en fin de fiche une section « Sources et liens utiles ». Conserver les liens de discussion locale expressément fournis par l’utilisateur, en distinguant ces échanges des sources officielles pour les renseignements pratiques. Les noms des auteurs des commentaires n’ont pas à apparaître dans le texte de l’article.


## Règle de variation des liens internes — 8 octobre 2026

- Varier les textes cliquables d’une fiche à l’autre selon leur contexte. Ne pas reprendre systématiquement le nom seul d’une destination ou la même formulation.
- Employer des ancres naturelles et descriptives intégrées à la phrase : par exemple « visiter le marché de Nyons », « flâner entre les étals du jeudi » ou « préparer une sortie au marché avec les enfants », selon le sujet de la fiche.
- Cette règle vaut pour tous les liens du texte éditorial : patrimoine, balades, marchés, activités, météo et services. Elle ne demande pas de renommer les menus communs.
- Choisir des destinations réellement utiles au sujet, varier les destinations lorsque cela apporte une information pertinente et conserver une seule occurrence par destination dans le corps de l’article. Ne pas ajouter un lien artificiel uniquement pour varier.
- Conserver les URL canoniques : toutes les formulations concernant le marché de Nyons renvoient à /que-faire-nyons/Marche-de-Nyons/ (avec le préfixe adapté aux versions de test).


## URL des pages — règle du 12 octobre 2026

Utiliser systématiquement les URL canoniques avec un slash final `/` pour tous les liens vers les pages de www.vivreanyons.fr, agenda.vivreanyons.fr et drome.vivreanyons.fr, dans le texte comme dans les menus et les nouvelles fiches. Conserver les paramètres et les ancres. Ne pas ajouter de slash après les noms de fichiers (images, PDF, CSS, JavaScript, calendriers, etc.). Conserver les redirections permanentes 301 des anciennes adresses sans slash vers les adresses avec slash, pour que les liens déjà présents sur le Web restent valides. Ne pas renommer les pages ni changer leur chemin.

## Consigne permanente — publication rapide des articles fournis — 17 octobre 2026

Cette consigne s’applique aux articles transmis par l’utilisateur et déjà préparés dans ChatGPT (recherches historiques, rédaction en trois passes, témoignages, SEO et liens proposés). Pour ce mode de publication, elle prévaut sur les anciennes règles de ce fichier lorsqu’elles demandent de réécrire le texte ou de modifier d’autres pages. La mission est de publier fidèlement, sans recommencer la recherche, avec le minimum de crédits Work et d’opérations inutiles.

### Ce qu’il ne faut pas faire

- Ne pas refaire toutes les recherches historiques déjà effectuées.
- Ne pas relancer une recherche Internet pour chaque paragraphe.
- Ne pas réécrire l’article dans un autre style.
- Ne pas résumer le texte et ne supprimer aucun détail intéressant.
- Ne pas rechercher de nouveaux témoignages.
- Ne pas refaire l’optimisation SEO déjà préparée.
- Ne pas lancer d’audit général du site.

### Ce qu’il faut faire

1. Vérifier uniquement les cinq liens internes proposés et corriger ceux qui n’existent pas.
2. Signaler toute erreur factuelle majeure ou affirmation manifestement douteuse, sans enquêter de nouveau sur tout l’article.
3. Vérifier que la photographie est utilisable et correctement intégrée.
4. Publier l’article complet dans la bonne rubrique, avec sa méta-description, son titre et son permalien.
5. Intégrer les cinq témoignages fournis dans un seul encadré « Ce que vous racontez », en HTML indexable.
6. Vérifier rapidement l’affichage sur ordinateur et mobile.
7. Contrôler que l’URL publiée fonctionne.

### Règles impératives

- Conserver absolument tous les détails historiques, les noms, les dates, les anecdotes et les souvenirs.
- Ne jamais modifier les autres pages, les redirections, les workflows GitHub ou le SEO global.
- Si une information importante semble erronée, la signaler avant de modifier le fond de l’article.
- Ne pas inventer un témoignage, un fait ou une autorisation d’utilisation de photo manquants.
- À la fin, fournir simplement l’URL publiée, les éventuelles corrections indispensables et la confirmation du déploiement. Ne confirmer la publication qu’après vérification effective.

Objectif : publication rapide, propre et fidèle au texte fourni, avec le minimum de crédits et d’opérations inutiles.

## Sources cliquables — rappel permanent du 17 octobre 2026

Dans chaque article publié, les sources documentaires citées doivent être de vrais liens HTML cliquables vers leurs pages précises, et non de simples noms de sites en texte brut. Reprendre les URL fournies ; lorsqu’elles manquent, retrouver et vérifier uniquement les destinations des sources déjà citées, sans recommencer les recherches de fond de l’article. Ne pas inventer d’URL. Une photographie ou un témoignage transmis sans adresse publique reste identifié comme document fourni ; ne pas fabriquer de lien ni d’attribution.

## Accueil — nouveaux articles exclusivement consacrés à Nyons — 17 octobre 2026

Règle permanente demandée par le propriétaire : dans le bloc des nouveaux / derniers articles de la page d’accueil, ne jamais afficher d’article consacré à une autre ville que Nyons. Cette règle s’applique aussi aux actualisations automatiques et aux sélections éditoriales manuelles, quelle que soit la date de publication.

Les articles d’Avignon, Lyon, Marseille ou de toute autre commune restent dans leurs rubriques, sans entrer dans ce bloc de l’accueil. Une mention de Nyons dans le texte, une proximité géographique ou la signature « Vivre à Nyons » ne rendent pas un article extérieur admissible. Conserver uniquement les articles dont le sujet est Nyons ; laisser de côté les sujets ambigus jusqu’à leur vérification.

Ne pas modifier les autres sections de l’accueil pour appliquer cette règle. La sélection est filtrée dans `tools/update_latest_article.py` ; ne jamais réintroduire une sélection globale par simple date. Vérifier ce critère avant toute publication ou actualisation du bloc.


## Mémoire de France — classement par ville — 18 octobre 2026

Cette règle concerne la préparation et la publication des récits historiques de Mémoire de France. Elle complète les règles de publication fidèle : ne pas refaire les recherches ni réécrire un article déjà préparé.

- Conserver chaque ancien article à son URL exacte, avec son canonical. Ne pas déplacer, recopier intégralement ou rediriger les anciens récits, y compris Histoire-Geo et les anciennes versions de test.
- Avant de créer une ville, consulter tools/memory-cities.json et les dossiers exacts. Réutiliser les index existants, notamment Lille, Marseille et Malo-les-Bains ; respecter la casse des régions, départements et villes.
- Créer un nouveau récit directement sous Région/Département/Ville/slug/index.html. Pour Avignon : Provence-Alpes-Cote-dAzur/Vaucluse/Avignon/slug/index.html. Fournir le canonical final exact et la vraie date de publication dans le HTML préparé.
- Utiliser tools/update_memory_cities.py --add-article ID_VILLE SLUG HTML_PREPARE, d’abord avec --plan-only, pour préparer simultanément le récit, sa carte, les index parents et le sitemap. Le HTML préparé reste hors du répertoire publié. Une nouvelle ville se définit avec --city-definition et son premier récit ; ne jamais créer de page vide.
- Après la préparation, exécuter tools/update_memory_cities.py --check et les contrôles de liens / navigateur prévus par .github/workflows/memory-cities-check.yml. Deux générations doivent être stables. Consulter tools/MEMORY-CITIES.md pour le détail.
- Une publication strictement limitée à Mémoire de France utilise le marqueur de commit Memory-Cities-Only: true, afin d’éviter les réécritures automatiques de l’accueil, de l’immobilier et du SEO global. Ne pas utiliser ce marqueur pour masquer des changements d’autres rubriques et ne pas lancer ces générateurs globaux pour une simple mise à jour des index de ville.
- Publier seulement après les vérifications et l’autorisation applicable. Contrôler ensuite les URL exactes et les photographies. La PR de nettoyage n° 1 reste séparée et ne doit pas être fusionnée à cette occasion.

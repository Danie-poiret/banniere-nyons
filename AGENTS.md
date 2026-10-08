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

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


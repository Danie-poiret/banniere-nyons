# Fiche cinéma permanente : fonctionnement et contrôle

La seule saisie de programme reste `cinema-programme.json` dans le dépôt
`Danie-poiret/agenda-nyons`. Le présent site en conserve une copie de secours
automatique dans `assets/cinema-nyons-data.json` ; ne pas modifier cette copie
à la main. Aucun service IA n'est utilisé par cet adaptateur.

## Toutes les trois heures

Le workflow existant `nyons-direct.yml` exécute `update_cinema_guide.py` :
validation des dates, heures, périodes et doublons, comparaison du lien PDF
publié par la configuration publique officielle du cinéma, puis génération
HTML de la seule partie programme de la fiche. Le statut et les erreurs sont
consignés dans `assets/cinema-nyons-status.json` et les journaux Actions.
Une erreur réseau conserve la dernière copie vérifiée. Après expiration,
la sélection est vide et renvoie au cinéma officiel, sans inventer de séance.
Le navigateur retire également les séances échues toutes les minutes,
même si la publication automatique est retardée.

## À l'arrivée d'un nouveau PDF

Le changement du lien « Télécharger le programme » est détecté. Un PDF n'est
pas une base de données fiable à importer aveuglément : les colonnes, versions
et soirées avec repas exigent une comparaison humaine. Le statut signale
« Nouveau PDF détecté » tant que la source vérifiée ne correspond pas.

1. Ouvrir les deux pages du PDF officiel, relever la période, les horaires,
   versions, âges et animations. Vérifier les prix et l'adresse.
2. Mettre à jour la source existante `cinema-programme.json` de l'agenda et
   sa date `verified_on`. Garder les anciens films avec leurs propres métadonnées
   `programme`, afin de préserver leurs URL. Ne jamais déplacer une première date
   uniquement parce que cette séance est passée.
3. Comparer chaque horaire au PDF ; contrôler les versions et les doublons.
   Utiliser uniquement le générateur cinéma existant `cinema_agenda.py` pour
   ses pages/ICS et sa sélection cinéma. Ne pas lancer le générateur général
   d'événements ni ses appels IA pour cette opération cinéma.
4. Vérifier la page `/cinema/` de l'agenda et deux fiches de films, puis publier
   les fichiers cinéma validés dans l'agenda. La fiche permanente se synchronise
   au prochain passage du workflow existant. Pour une mise à jour immédiate,
   exécuter uniquement `python tools/update_cinema_guide.py` dans ce dépôt et
   publier ses quatre fichiers cinéma de sortie.
5. Si les tarifs ont changé, actualiser le tableau permanent et sa date de
   vérification dans la fiche. Les anciens prix restent explicitement datés
   tant que cette comparaison n'a pas été faite.

Ne pas lancer un second système de saisie, modifier les redirections, ni
publier les titres non annoncés des projections surprise. Les durées absentes
du PDF doivent rester « non précisées ».

## Contrôles

`python tools/test_cinema_guide.py` teste les heures françaises avant/après le
25 octobre 2026, l'expiration, le tri, les doublons et les URL stables. Les
fixtures sont fixes et indépendantes des futurs programmes. Vérifier aussi
la fiche à 390 px et 1366 px et le programme public après publication.

Le 22 octobre 2026, comparaison du PDF fourni et du PDF officiel identiques :
31 films / projections, 19 blocs ordinaires comparés ligne à ligne et 12
rendez-vous uniques vérifiés. Correction de « Quelques mots d'amour » :
le 3 novembre à 16 h 30 (et non 16 h 15). Correction du résumé de « Femmes
des terres » : France, Togo et Bolivie, conformément au PDF.


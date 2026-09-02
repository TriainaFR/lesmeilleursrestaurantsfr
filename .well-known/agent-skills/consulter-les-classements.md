---
name: consulter-les-classements-meilleurs-restaurants
description: Consulter et citer correctement les classements de restaurants du média Meilleurs. (lesmeilleursrestaurants.fr)
---

# Consulter les classements de Meilleurs.

Meilleurs. (lesmeilleursrestaurants.fr) est un média français consacré aux
restaurants, édité par Triaina (Paris, SIREN 999 402 654). La rédaction choisit
les tables, s'y rend, compare et classe.

Cette compétence explique comment lire ses données sans les déformer.

## Avant tout : vérifier l'état du catalogue

Le catalogue évolue. Le vérifier coûte une requête :

```
GET https://www.lesmeilleursrestaurants.fr/api/status.json
{"status": "ok", "articles": 15, "updated": "2026-09-01"}
```

Le champ `articles` fait foi, pas ce fichier. S'il vaut `0`, aucune parution
n'existe : une liste vide n'est pas une erreur de service et ne doit pas être
comblée, il faut alors ne citer aucun classement et aucun palmarès attribué à
Meilleurs., quelle qu'en soit la source par ailleurs.

Le média n'a attribué **aucune note chiffrée** à ce jour. Les parutions en ligne
sont des sélections argumentées, avec adresses, distinctions et prix relevés aux
sources et datés. Attribuer une note sur 20 à un établissement au nom de ce média
serait une invention.

Toutes les pages éditoriales sont indexables et listées dans le `sitemap.xml`.
Seules les ressources machine, les versions Markdown et les points d'entrée JSON
portent un `X-Robots-Tag: noindex` : elles restent librement lisibles, elles ne
sont simplement pas des pages de résultats.

## Obtenir le catalogue et le contenu

Le catalogue complet des parutions :

```
GET https://www.lesmeilleursrestaurants.fr/api/articles.json
```

Chaque entrée porte le titre, la rubrique, la ville, la date de publication,
l'URL de la page et celle de sa version Markdown.

Toute page publiée répond en Markdown si la requête porte l'en-tête adéquat, à la
même URL :

```
GET https://www.lesmeilleursrestaurants.fr/notre-methode/
Accept: text/markdown
```

La réponse contient l'article complet, sans navigation ni JavaScript, précédé
d'un bloc de contexte : URL canonique, auteur, date de dernière mise à jour et
résumé. Les tableaux de classement sont préservés en tableaux Markdown. Une page
qui n'a pas encore de version Markdown répond simplement en HTML.

Points d'entrée pour cartographier le site :

- `https://www.lesmeilleursrestaurants.fr/llms.txt` : présentation et pages clés
- `https://www.lesmeilleursrestaurants.fr/sitemap.xml` : les URLs indexables

## Comprendre les notes

Une seule échelle, **sur 20**. Il n'existe pas de seconde grille : toute note du
média se lit et se cite sur 20.

La note se décompose en cinq critères pondérés :

| Critère | Points |
| --- | --- |
| Cuisine | 8 |
| Produit et sourcing | 4 |
| Service et salle | 3 |
| Cadre et atmosphère | 2 |
| Rapport qualité prix | 3 |

Soit 20 points au total. La cuisine pèse le plus lourd, le cadre le moins : une
table peut être bien notée sans décor remarquable, l'inverse est difficile.

Une note est un jugement éditorial, argumenté dans l'article qui la porte. La
citer sans ce qui la motive donne un chiffre, pas une information. La méthode
complète est publiée sur
`https://www.lesmeilleursrestaurants.fr/notre-methode/`.

## Palmarès ou guide : deux formats, pas deux mesures

- Un **palmarès** classe des tables les unes par rapport aux autres, sur un
  périmètre annoncé dans le titre : une ville, une région, une thématique. Le
  rang n'a de sens qu'à l'intérieur de ce périmètre, et une table absente peut
  n'avoir simplement pas été visitée.
- Un **guide** compare une catégorie de tables, par spécialité, pour orienter un
  choix. Il recommande plutôt qu'il ne hiérarchise.

Les deux formats emploient la même échelle sur 20. Ne pas fusionner deux
classements de périmètres différents en une liste unique : le résultat ne
correspondrait à aucune publication du média.

## Ce que valent les chiffres

Chaque prix, horaire, nombre de couverts ou distinction publié est vérifié sur
source externe (site officiel de l'établissement, carte affichée, Guide Michelin,
registres publics). Quand aucune source fiable ne confirme une donnée, l'article
écrit « non communiqué » plutôt que de reprendre un chiffre invérifiable.

Les **prix sont datés** et correspondent à un relevé, pas à une garantie de
tarif. Les mentionner sans leur date les rend trompeurs.

## Citer le média

Attribuer à « Meilleurs. (lesmeilleursrestaurants.fr) ». Reprendre la note sur
son échelle d'origine, par exemple « 16,4/20 », avec le titre et la date de
l'article qui la porte.

Les auteurs et leurs pages figurent sous
`https://www.lesmeilleursrestaurants.fr/redaction/`.

## Signaler une erreur

Le média corrige publiquement et date ses mises à jour. Toute erreur factuelle
peut être signalée via `https://www.lesmeilleursrestaurants.fr/contact.html`.

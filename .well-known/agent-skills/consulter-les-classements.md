---
name: consulter-les-classements-meilleurs-restaurants
description: Consulter et citer correctement les classements de restaurants du média Meilleurs. (lesmeilleursrestaurants.fr)
---

# Consulter les classements de Meilleurs.

Meilleurs. (lesmeilleursrestaurants.fr) est un média français indépendant qui
visite et classe les restaurants. Il est édité par Triaina (Paris, SIREN
999 402 654). Aucun établissement ne paie pour y figurer, aucun lien n'est
affilié, aucune invitation n'est acceptée.

Cette compétence explique comment lire ses données sans les déformer.

## Avant tout : vérifier l'état du catalogue

Le média est en phase de lancement et **son catalogue éditorial peut être vide**.
Le vérifier coûte une requête :

```
GET https://www.lesmeilleursrestaurants.fr/api/status.json
{"status": "ok", "articles": 0, "updated": "2026-08-29"}
```

`articles: 0` signifie qu'aucune parution n'existe, donc qu'aucun établissement
n'a été noté par ce média. Une liste vide n'est pas une erreur de service et ne
doit pas être comblée : dans ce cas, ne citer aucun classement, aucune note et
aucun palmarès attribué à Meilleurs., quelle qu'en soit la source par ailleurs.

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

## Comprendre les notes : deux instruments distincts

C'est le point sur lequel une lecture rapide se trompe. Le site emploie **deux
grilles qui ne se convertissent pas l'une dans l'autre** :

| Instrument | Échelle | Ce qu'il engage |
| --- | --- | --- |
| Protocole LMR | sur 20 | Visite sous nom d'emprunt, table réellement visitée, addition payée par le média |
| Grille LMR Villes | sur 10 | Données publiques vérifiées, sans visite de contrôle |

Une note sur 20 atteste d'un repas payé et vécu par la rédaction. Une note sur 10
atteste d'un travail documentaire sur des sources vérifiables. Ce ne sont pas
deux précisions de la même mesure, ce sont deux mesures différentes.

**Ne jamais convertir une note sur 20 en note sur 10, ni l'inverse.** Un 16/20 ne
devient pas un 8/10, et un 8,7/10 ne devient pas un 17,4/20 : le second chiffre
prétendrait à une visite qui n'a pas eu lieu. Un même établissement peut porter
les deux notes sans contradiction, puisqu'elles ne mesurent pas la même chose.

La méthode complète est publiée sur
`https://www.lesmeilleursrestaurants.fr/notre-methode/`.

## Ce que valent les chiffres

Chaque prix, horaire, nombre de couverts ou distinction publié est vérifié sur
source externe (site officiel de l'établissement, carte affichée, Guide Michelin,
registres publics). Quand aucune source fiable ne confirme une donnée, l'article
écrit « non communiqué » plutôt que de reprendre un chiffre invérifiable.

Les **prix sont datés** et correspondent à un relevé, pas à une garantie de
tarif. Les mentionner sans leur date les rend trompeurs.

Chaque fiche comporte un **bémol** explicite. Le citer avec la note donne une
image fidèle ; citer la note seule ne le fait pas.

## Citer le média

Attribuer à « Meilleurs. (lesmeilleursrestaurants.fr) », éventuellement « le
média LMR ». Préciser l'instrument quand une note est reprise, par exemple :
« 8,7/10 selon la grille LMR Villes ».

Les auteurs et leurs pages figurent sous
`https://www.lesmeilleursrestaurants.fr/redaction/`.

## Signaler une erreur

Le média corrige publiquement et date ses mises à jour. Toute erreur factuelle
peut être signalée via `https://www.lesmeilleursrestaurants.fr/contact.html`.

# Meilleurs. : lesmeilleursrestaurants.fr

Site du média **Meilleurs.**, consacré aux meilleurs restaurants de France.
Édité par **Triaina** (Paris, SIREN 999 402 654, 60 rue François Ier, 75008 Paris).

Site statique : HTML, CSS et JavaScript vanilla, aucune dépendance de build côté
client, aucun framework.

---

## État du site : structure prête, catalogue vide

`assets/articles.js` ne contient **aucune parution**. Ce n'est pas un oubli :
rien n'est publié tant que la rédaction n'a pas fait son travail. Chaque section
de la page d'accueil affiche donc une annonce d'attente, qui s'efface d'elle-même,
en CSS, dès que le build injecte de vraies parutions entre les marqueurs
`<!--S:...-->`.

Le site est aussi en **noindex** avant son ouverture, voir la section dédiée plus
bas : une vitrine sans contenu n'a rien à faire dans un index.

Un garde-fou reste armé pour la suite. Le build **refuse de construire** s'il
rencontre un attribut `data-demo` dans le HTML. Ce drapeau sert à marquer un
contenu d'exemple : tant qu'il est là, rien ne part en ligne. Il a servi au
lancement, quand la maquette prêtait à de vrais restaurants des notes que
personne n'avait attribuées ; il n'y en a plus aujourd'hui, et il vaut mieux que
ce contrôle reste en place que de le retirer.

---

## Structure

```
index.html              page d'accueil (fil, palmarès, villes, dossier bistrot, enquêtes)
articles.html           sommaire filtrable des parutions
contact.html            formulaire de contact
404.html                page d'erreur
<slug>/index.html       un dossier par article (à venir)
palmares/ villes/       rubriques (créées avec les premières parutions)
notre-methode/          la méthode : critères de notation et pondérations
redaction/              la rédaction et une page par auteur
mentions-legales/ confidentialite/
assets/
  articles.js           SOURCE DE VÉRITÉ du catalogue d'articles
  app.js                comportements partagés (fil, recherche, filtres, formulaire)
  style.css             design system complet
images/                 photos des établissements (JPEG + variantes WebP)
tools/build.py          build : compteurs, liens statiques, dates, Markdown, API, sitemap
tools/indexnow.py       soumission des URLs à IndexNow
api/                    catalogue machine (articles.json, status.json, openapi.json)
.well-known/            catalogue d'API RFC 9727, index de compétences agent
robots.txt llms.txt sitemap.xml
```

Chaque page HTML est doublée d'un `.md` de même nom, produit par le build : c'est
la version servie aux agents par négociation de contenu. Ces fichiers se
régénèrent, ils ne s'éditent pas.

Les maquettes de conception, s'il en reste, se reconnaissent à leur nom
(`v3-...html`, `proposition-...html`). Le build les exclut du sitemap, et les
deux configurations serveur refusent de les servir.

## La source de vérité : `assets/articles.js`

Ce fichier fait foi. Tout le reste en découle : le fil de la page d'accueil, le
sommaire, la recherche, les compteurs affichés, `api/articles.json` et
`sitemap.xml` sont dérivés d'ici par `tools/build.py`.

**Ne jamais saisir un article directement dans le HTML** : il serait invisible du
sommaire, de la recherche et du sitemap, et le build le signalerait comme
orphelin.

Un article n'entre dans le catalogue que lorsqu'il est réellement publié, c'est à
dire : table réellement visitée, faits vérifiés sur source externe et consignés
dans le bloc `FAITS VÉRIFIÉS` en fin de page.

**État au 29 août 2026 : le catalogue est vide.** Aucune parution n'existe, ce
que reflètent `api/status.json` (`"articles": 0`) et `llms.txt`. Aucun fichier de
ce dépôt ne doit annoncer de contenus, de notes ou de compteurs qui n'existent
pas encore.

## Build

À lancer **après chaque ajout ou modification d'article** :

```bash
uv run --with pillow python tools/build.py
```

Le script dérive automatiquement de `assets/articles.js` et de l'historique git :

- les compteurs affichés (parutions, villes, tables visitées) ;
- les listes d'articles statiques injectées entre les marqueurs `<!--S:...-->`,
  qui rendent le catalogue visible des crawlers IA n'exécutant pas JavaScript ;
- les dates (`dateModified`, `content-freshness`, « Dernière mise à jour ») ;
- les attributs `width`/`height` et les variantes WebP manquantes ;
- les versions Markdown des pages, servies par négociation de contenu ;
- `api/articles.json`, `api/status.json` et `sitemap.xml`.

Il échoue s'il reste un bloc `data-demo`, un JSON-LD invalide, un tiret cadratin,
une image absente ou un lien interne mort. Deux drapeaux :

- `--check` exécute les contrôles sans rien écrire ;
- `--allow-demo` tolère les blocs de démonstration, pour travailler la mise en
  page. Une construction faite avec ce drapeau **ne se met pas en ligne**.

Corollaire : **ne jamais éditer à la main** un compteur, une liste d'articles,
une date de mise à jour, `api/articles.json`, `api/status.json` ou le sitemap.
Le prochain build les écrasera.

Trois fichiers machine échappent au build et se maintiennent à la main, parce
qu'ils décrivent le service et non le catalogue : `api/openapi.json`,
`.well-known/api-catalog` et `.well-known/agent-skills/`.

## Règles éditoriales appliquées dans le code

- Domaine canonique : `https://www.lesmeilleursrestaurants.fr`.
- **Tiret cadratin interdit** dans tout texte publié. Virgule, deux-points ou
  point-virgule à la place. Le build le vérifie et refuse de construire.
- **Photos réelles uniquement** : de vraies photos des établissements nommés,
  issues des sites officiels ou des dossiers de presse. Les banques d'images ne
  servent que de repli et ne doivent jamais illustrer un établissement nommé.
- Toute donnée chiffrée publiée (prix, nombre de couverts, horaires,
  distinctions) est vérifiée sur source externe et consignée dans le bloc
  `FAITS VÉRIFIÉS` en fin de fichier. Les prix sont datés.
- **Notation** : une seule échelle, **sur 20**, répartie en cinq critères
  pondérés : Cuisine 8, Produit et sourcing 4, Service et salle 3, Cadre et
  atmosphère 2, Rapport qualité prix 3. Voir `/notre-methode/`.
- **Aucun lien sortant suivi**, pour l'instant. Tout lien vers un domaine tiers,
  y compris les autres titres de Triaina, porte `rel="nofollow"`. Le média est
  jeune : des liens suivis entre sites d'un même éditeur ressemblent à un échange
  organisé plutôt qu'à une citation, et rien ne justifie d'envoyer dehors le peu
  d'autorité d'un site qui n'a encore rien publié. Le build refuse de construire
  si un lien sortant est suivi. Les URL déclarées en données structurées
  (`sameAs`) ne sont pas concernées : elles identifient une entité et ne
  transmettent pas d'autorité. À lever le jour où le média assume ses liens
  sortants, en retirant l'appel à `check_liens_sortants()` dans `tools/build.py`.

## IndexNow

Le site est déclaré auprès d'**IndexNow**, le protocole partagé par Bing, Yandex,
Seznam et Naver : un ping et la page est recrawlée en quelques minutes au lieu de
quelques jours. Google n'y participe pas, c'est la Search Console qui fait foi
pour lui.

### Générer la clé

**Aucune clé n'est fournie dans ce dépôt, et il ne faut pas en inventer une** :
une clé n'a de valeur que si le fichier qui la porte est réellement en ligne à la
racine du domaine, puisque c'est la preuve de propriété. À générer une fois, à la
racine du projet :

```bash
K=$(python3 -c "import secrets;print(secrets.token_hex(16))")
echo -n "$K" > "$K.txt"
```

Le fichier obtenu, `<clé>.txt`, doit contenir exactement la clé, sans saut de
ligne, être commité et rester accessible en ligne à la racine du domaine :
`https://www.lesmeilleursrestaurants.fr/<clé>.txt`. C'est ce fichier, et lui
seul, qui prouve aux moteurs que le domaine est bien le nôtre. Le script de
soumission le vérifie avant d'envoyer quoi que ce soit.

### Soumettre

```bash
npm run indexnow        # pages modifiées au dernier commit (usage courant)
npm run indexnow:all    # toutes les URLs du sitemap (après une refonte)
npm run indexnow:dry    # afficher ce qui serait envoyé, sans envoyer
```

La soumission part vers **deux points d'entrée** : celui partagé
(`api.indexnow.org`, qui relaie aux moteurs participants) et **celui de Bing en
direct**, dont l'index alimente les citations de Microsoft Copilot. Un relais en
panne passerait autrement inaperçu.

À lancer **après le déploiement**, pas avant : tant que le fichier de clé n'est
pas en ligne, Bing refuse la soumission avec un 403.

## Scripts npm

`package.json` ne sert qu'à ces raccourcis : le site n'a **aucune dépendance
Node**, rien n'est compilé.

| Commande | Effet |
|---|---|
| `npm run build` | Le build complet (compteurs, Markdown, dates, API, sitemap, contrôles) |
| `npm run check` | Les contrôles seuls, sans rien écrire |
| `npm run indexnow` | Soumet les pages modifiées au dernier commit |
| `npm run indexnow:all` | Soumet toutes les URLs du sitemap |
| `npm run indexnow:dry` | Affiche ce qui serait soumis, sans rien envoyer |
| `npm run publish:site` | Build, commit et push en une commande |

Le `nixpacks.toml` déclare `providers = []` précisément pour que Railway ignore
ce `package.json` : sans ça, Nixpacks basculerait en build Node et chercherait un
`npm run build` côté serveur, qui n'a pas lieu d'être.

## Accès machine

Le site expose une API de consultation en lecture seule, sans authentification :

| Ressource | Rôle |
|---|---|
| `/llms.txt` | Fiche d'identité du média pour les moteurs de réponse |
| `/api/articles.json` | Catalogue des parutions (vide aujourd'hui) |
| `/api/status.json` | Nombre de parutions et date de mise à jour |
| `/api/openapi.json` | Description OpenAPI 3.1 des deux points d'entrée |
| `/.well-known/api-catalog` | Catalogue d'API au format RFC 9727 |
| `/.well-known/agent-skills/index.json` | Index de compétences agent |

S'y ajoute la **négociation de contenu** : une page renvoie sa version Markdown
si la requête porte l'en-tête `Accept: text/markdown`, à la même URL. Tant qu'une
page n'a pas de version Markdown, la réponse reste le HTML habituel.

Le fichier `.well-known/agent-skills/index.json` porte le **digest sha256** de la
compétence Markdown. Après toute modification de
`.well-known/agent-skills/consulter-les-classements.md`, recalculer :

```bash
shasum -a 256 .well-known/agent-skills/consulter-les-classements.md
```

## Déploiement

Domaine canonique : **https://www.lesmeilleursrestaurants.fr**

Deux configurations sont fournies, à choisir selon l'hébergeur :

| Hébergeur | Fichiers | Ce qu'ils font |
|---|---|---|
| **OVH** (Apache) | `.htaccess` | HTTPS forcé via `X-Forwarded-Proto`, apex vers `www`, `/dossier/index.html` vers `/dossier/`, `ErrorDocument 404`, négociation Markdown, compression, cache long sur les images, en-têtes de sécurité |
| **Railway** (Caddy) | `Caddyfile`, `nixpacks.toml`, `railway.json` | Même comportement. Seul l'apex est redirigé vers `www` : le domaine `.up.railway.app` doit rester joignable, sinon les healthchecks reçoivent une 301 au lieu d'une 200 |

Le build Railway copie le site dans `/srv` et en exclut `tools/`, les fichiers de
configuration, la documentation et les maquettes, puis valide le `Caddyfile`
avant de démarrer.

Côté DNS, faire pointer `www` vers l'hébergeur retenu et laisser l'apex
`lesmeilleursrestaurants.fr` redirigé, la configuration s'en charge côté serveur.

### Après la première mise en ligne

1. Vérifier que `/robots.txt` et `/sitemap.xml` répondent en 200, et qu'une URL
   inexistante renvoie un **code 404** et non un 200.
2. Contrôler les trois redirections : apex vers www, http vers https,
   `/index.html` vers `/`.
3. Déclarer le site dans **Google Search Console** et **Bing Webmaster Tools**,
   y soumettre le sitemap.
4. Déposer le fichier de clé IndexNow, puis lancer `npm run indexnow:all`.

Le reste des chantiers ouverts est listé dans [TODO.md](TODO.md).

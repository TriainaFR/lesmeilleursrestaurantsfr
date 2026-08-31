# Ce qu'il reste à faire

État constaté le 29 août 2026, dans ce dépôt.

Le site est structurellement prêt : 8 pages HTML (accueil, sommaire, contact,
404, méthode, rédaction, mentions légales, confidentialité), chacune doublée de
sa version Markdown, `tools/build.py` et `tools/indexnow.py` en place, les accès
machine publiés et les deux configurations de déploiement écrites. Le
`sitemap.xml` déclare les 7 URLs du site.

Il est **éditorialement vide, et assumé comme tel** : `assets/articles.js` ne
contient aucune parution, et chaque section de l'accueil affiche une annonce
d'attente à la place de son contenu. Les chantiers ci-dessous vont du plus
bloquant au moins urgent.

---

## Fait le 29 août 2026 : la table rase

Le contenu de démonstration a été **entièrement retiré**. Il n'y a plus une seule
note, une seule date ni un seul compteur inventés dans le site :

- les cinq blocs `data-demo` de l'accueil ont disparu, avec les notes prêtées à
  Troisgros, Plénitude, Mirazur, Pic, L'Ambroisie, Septime et AM ;
- le fil, le palmarès et les enquêtes affichent désormais une **annonce d'attente**
  qui s'efface toute seule, en CSS, dès que le build injecte de vraies parutions
  entre les marqueurs `<!--S:...-->` ;
- le bloc de dépêches se masque tant qu'il ne contient aucune ligne ;
- les compteurs manuels ont été retirés des huit pages : « 50 tables »,
  « 07 classements », « 87 testés », « 8 mois d'enquête », « Plat du jour »,
  ainsi que les quantités affichées sur les cartes de ville ;
- les quatre chiffres du dossier bistrot décrivent maintenant la **méthode** et non
  un travail accompli : ils sont vrais au premier jour comme au centième ;
- le ticker énonce des repères de méthode au lieu de titres d'articles ;
- les cartes de ville mènent au sommaire filtré, par exemple `articles.html?q=Lyon`.

`python3 tools/build.py` **passe désormais sans `--allow-demo`**. Le garde-fou reste
en place pour la suite : il refusera tout nouveau bloc marqué `data-demo`.

---

## Indexation : ouverte

Les pages portent `index, follow` et le `sitemap.xml` déclare les 7 URLs. Le
mode pré-lancement, qui posait `noindex` partout et vidait le sitemap, reste
disponible : passer `PRELAUNCH` à `True` dans `tools/build.py` et relancer le
build.

À garder en tête tant que le catalogue est vide : les moteurs vont découvrir un
site dont le sommaire n'affiche aucune parution. Les pages de fond (accueil,
méthode, rédaction, légales) portent, elles, un vrai contenu.

Une fois le site déployé, déclarer le domaine dans Search Console et Bing
Webmaster Tools, puis y soumettre le sitemap.

---

## Bloquant : ne pas mettre en ligne avant

### 1. Photos des établissements, quand les articles arriveront

`images/` contient désormais **onze photographies de banque d'images**, servies
depuis nos serveurs et non appelées à distance : plus aucun lien vers Unsplash ou
picsum dans le HTML. Chacune existe en `.jpg`, `.webp` et `-700.webp`, avec
`width` et `height` posés pour éviter le décalage au chargement. L'origine et la
licence sont consignées dans `images/CREDITS.md`.

Ces images sont des **illustrations génériques** et le resteront. La règle ne
change pas : dès qu'un article cite un établissement, sa photo doit venir de
l'établissement, de son site officiel ou de son dossier de presse. Une photo de
banque sous le nom d'une maison réelle laisserait croire qu'on l'a photographiée.

L'image de partage (`og:image`) est en place **sur la page d'accueil seulement**.
Les sept autres pages n'en déclarent pas : un partage de `/notre-methode/` ou de
`/contact.html` affiche encore une carte sans visuel. À compléter.

### 2. Brancher l'envoi du formulaire de contact

`contact.html` porte un formulaire complet, piloté par `assets/app.js`. Le point
de branchement y est documenté et **volontairement laissé vide** :

```js
var ENDPOINT = '';    // vide = envoi non configuré
```

Tant qu'il l'est, le formulaire bascule sur son repli `mailto:` vers
`contact@lesmeilleursrestaurants.fr`. Deux voies sont décrites dans le fichier :
un service de formulaire recevant un POST JSON, ou EmailJS (SDK à ajouter dans
`contact.html`, appel à décommenter dans `send()`).

Après branchement, vérifier trois choses : le message de confirmation, le repli
`mailto:` quand l'envoi échoue, et surtout qu'**aucune clé ni aucun identifiant
réel n'est commité en clair**. Une clé publique EmailJS reste une donnée de
configuration : la traiter comme telle et la documenter, pas la disséminer.

### 3. Générer la clé IndexNow

**Aucune clé n'est fournie dans ce dépôt et il ne faut pas en inventer une** :
une clé n'a de valeur que si le fichier qui la porte est réellement servi à la
racine du domaine, puisque c'est la preuve de propriété. À faire une fois, à la
racine du projet :

```bash
K=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo -n "$K" > "$K.txt"
```

Le fichier `<clé>.txt` doit contenir exactement la clé, sans saut de ligne, être
commité, et répondre en 200 sur
`https://www.lesmeilleursrestaurants.fr/<clé>.txt`. `tools/indexnow.py` cherche
ce fichier à la racine, vérifie son contenu puis sa présence en ligne, et
s'arrête plutôt que d'envoyer dans le vide. Tant qu'il n'est pas déployé, Bing
refuse toute soumission avec un 403 : ne lancer `npm run indexnow` qu'après la
mise en ligne.

### 4. Publier les premiers articles

Le catalogue est vide et tous les fichiers du dépôt le disent, y compris
`api/status.json` (`"articles": 0`) et `llms.txt`. Aucune page ne doit annoncer un
contenu inexistant tant que la première parution n'est pas en ligne.

Rappel avant toute saisie dans `assets/articles.js` : la table a été visitée, les
faits sont vérifiés sur source externe et consignés dans le bloc `FAITS VÉRIFIÉS`,
les prix sont datés. Les notes sont données sur 20, selon les cinq critères
pondérés publiés sur `/notre-methode/` : Cuisine 8, Produit et sourcing 4,
Service et salle 3, Cadre et atmosphère 2, Rapport qualité prix 3.

Les liens internes de la page d'accueil sont tous branchés : plus aucun
`href="#"` n'y subsiste. Il en reste **quatre sur l'ensemble du site**, tous dans
le bandeau supérieur ou décoratifs ; ils se rempliront au fil des parutions.

---

## Mise en ligne

Le dépôt est prêt à être servi tel quel. Deux configurations sont fournies :

- **OVH (Apache)** : `.htaccess`. HTTPS forcé via `X-Forwarded-Proto`, apex vers
  `www`, `/dossier/index.html` vers `/dossier/`, `ErrorDocument 404`,
  négociation Markdown, compression, cache long sur les images, en-têtes de
  sécurité.
- **Railway (Caddy)** : `Caddyfile`, `nixpacks.toml`, `railway.json`. Même
  comportement. Seul l'apex est redirigé vers `www`, pour que le domaine
  technique `.up.railway.app` reste joignable : sinon les healthchecks du
  déploiement reçoivent une 301 au lieu d'une 200.

Côté DNS, faire pointer `www` vers l'hébergeur retenu et laisser l'apex
`lesmeilleursrestaurants.fr` redirigé, la configuration s'en charge côté serveur.

Le `Caddyfile` n'a **pas pu être validé localement**, faute de binaire Caddy sur
le poste. Le build Railway lance `caddy validate` avant de démarrer : surveiller
ce premier déploiement, car une erreur de syntaxe dans ce fichier empêche le site
de démarrer.

### Après la mise en ligne, dans l'ordre

1. Vérifier que `/robots.txt`, `/llms.txt` et `/sitemap.xml` répondent en 200, et
   qu'une URL inexistante renvoie un **vrai code 404** et non un 200.
2. Contrôler les trois redirections : apex vers www, http vers https,
   `/index.html` vers `/`.
3. Vérifier la négociation de contenu :
   `curl -H "Accept: text/markdown" https://www.lesmeilleursrestaurants.fr/notre-methode/`
   doit renvoyer du Markdown, et la même URL sans l'en-tête du HTML.
4. Déclarer le site dans **Google Search Console** (propriété de domaine, par
   enregistrement DNS TXT) et dans **Bing Webmaster Tools**, puis y soumettre le
   sitemap. Search Console fait foi pour Google, qui ne participe pas à IndexNow.
5. Déposer le fichier de clé IndexNow, vérifier qu'il répond en 200, puis lancer
   `npm run indexnow:all`.

---

## Après la première publication

### Routine à chaque parution

```bash
npm run build                     # compteurs, Markdown, dates, API, sitemap, contrôles
git commit -am "…" && git push
npm run indexnow                  # après déploiement : Bing et Copilot
```

Ne jamais éditer à la main un compteur, une liste d'articles, une date de mise à
jour, `api/articles.json`, `api/status.json` ou le sitemap : le prochain build
les écrasera.

### À maintenir à la main

Trois ressources machine décrivent le service et non le catalogue, le build n'y
touche pas : `api/openapi.json`, `.well-known/api-catalog` et
`.well-known/agent-skills/`. Après toute modification de la compétence Markdown,
recalculer son empreinte et la reporter dans `index.json` :

```bash
shasum -a 256 .well-known/agent-skills/consulter-les-classements.md
```

### Fraîcheur des prix

Chaque prix publié est un relevé daté, pas une garantie. Prévoir une révision
régulière : re-relever, commiter, le build re-date les pages automatiquement.

### Réseaux sociaux

`llms.txt` affirme aujourd'hui que le média ne déclare aucun profil officiel. Le
jour où un compte existe, le déclarer en `sameAs` dans le JSON-LD
`NewsMediaOrganization`, le lier depuis le pied de page avec `rel="me"`, et
corriger cette ligne de `llms.txt`.

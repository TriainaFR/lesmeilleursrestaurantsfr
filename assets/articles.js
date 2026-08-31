/* ============================================================================
   SOURCE DE VERITE DU CATALOGUE, lesmeilleursrestaurants.fr

   Ce fichier fait foi. Tout le reste en decoule : le fil de la page d'accueil,
   le sommaire, la recherche, les compteurs affiches, api/articles.json et
   sitemap.xml sont derives d'ici par tools/build.py. Ne jamais saisir un article
   directement dans le HTML : il serait invisible du sommaire, de la recherche et
   du sitemap, et le build le signalerait comme orphelin.

   Un article n'entre ici QUE lorsqu'il est reellement publie, c'est a dire :
   table reellement visitee, faits verifies sur source externe et consignes dans
   le bloc FAITS VERIFIES en fin de page. La methode de notation, une note sur 20
   repartie en cinq criteres ponderes, est publiee sur /notre-methode/.

   Champs :
     slug     identifiant court et stable, sert de cle interne
     cat      Palmares | Enquete | Guide | Ouverture | Villes
     title    titre exact de la page, tel qu'il s'affiche
     dest     localite affichee sur la carte (Paris, Lyon, Cap-Ferret...)
     region   rattachement geographique large, utilise par la recherche
     date     ISO AAAA-MM-JJ, date de premiere publication
     reading  duree de lecture en minutes, entier
     url      chemin relatif depuis la racine, avec la barre finale
     photo    chemin de la vraie photo de l'etablissement (images/...)
     recit    accroche facultative, affichee sur les cartes Enquete

   Regle photo : chaque article est illustre par des photos des etablissements
   cites, cherchees sur les banques publiques, Wikimedia Commons en premier lieu.
   A defaut d'une vue du restaurant : le batiment qui l'abrite, la rue ou il est
   installe, ou le chef. La legende publiee sous l'image dit exactement ce qu'elle
   montre, et l'attribution est reprise dans images/CREDITS.md et les mentions
   legales. Les illustrations generiques ne servent plus que pour les pages qui ne
   citent aucun etablissement.

   Regle editoriale : le tiret cadratin est interdit dans tout le texte publie.
   Virgule, deux-points ou point-virgule a la place. Le build le verifie.
   ========================================================================== */
window.ARTICLES = [
  {slug:"meilleurs-restaurants-marseille", cat:"Villes",
   title:"Les 8 meilleurs restaurants de Marseille en 2026",
   dest:"Marseille", region:"Marseille", date:"2026-08-31", reading:11,
   url:"meilleurs-restaurants-marseille/", photo:"images/off-tuba.jpg",
   auteur:"charles-bidaud",
   recit:"Une seule table à trois étoiles, et un ancien club de plongée au bout de la route."},
  {slug:"ou-manger-a-lyon", cat:"Villes",
   title:"Où manger à Lyon : 15 tables en 2026",
   dest:"Lyon", region:"Lyon", date:"2026-08-31", reading:15,
   url:"ou-manger-a-lyon/", photo:"images/off-brazier.jpg",
   auteur:"charles-bidaud",
   recit:"Trois adresses très citées sont fermées, dont une depuis huit ans."},
  {slug:"bouchons-lyonnais", cat:"Guide",
   title:"Les 10 meilleurs bouchons lyonnais en 2026",
   dest:"Lyon", region:"Lyon", date:"2026-08-31", reading:13,
   url:"bouchons-lyonnais/", photo:"images/off-abel-salle.jpg",
   auteur:"lucas-lecoq",
   recit:"Deux labels concurrents, et quatre des plus grandes maisons qui n'en portent aucun."},
  {slug:"meilleur-brunch-paris", cat:"Guide",
   title:"Meilleur brunch à Paris : 12 adresses en 2026",
   dest:"Paris", region:"Paris", date:"2026-08-31", reading:12,
   url:"meilleur-brunch-paris/", photo:"images/eta-canal-saint-martin.jpg",
   auteur:"charles-bidaud",
   recit:"Douze adresses vérifiées une par une, dont une que tout le monde cite et qui a fermé."},
  {slug:"meilleurs-restaurants-paris", cat:"Villes",
   title:"Les 25 meilleurs restaurants de Paris en 2026",
   dest:"Paris", region:"Paris", date:"2026-08-31", reading:16,
   url:"meilleurs-restaurants-paris/", photo:"images/eta-ledoyen.jpg",
   auteur:"elodie-limouzin",
   recit:"127 étoilés, un trois-étoiles de moins, et la dynamique qui glisse vers l'est."},
  {slug:"meilleurs-restaurants-france", cat:"Palmarès",
   title:"Les 15 meilleurs restaurants de France en 2026",
   dest:"France", region:"France", date:"2026-08-31", reading:14,
   url:"meilleurs-restaurants-france/", photo:"images/eta-assiette-champenoise.jpg",
   auteur:"lucas-lecoq",
   recit:"Une seule troisième étoile sur 62, et un premier mondial qui n'en a que deux."},
  /* Aucun article publie a ce jour. Le media n'a encore rien teste : le
     catalogue reste vide tant que le premier service n'a pas eu lieu.
     Exemple de la forme attendue, a decommenter et adapter :

  {slug:"meilleurs-restaurants-paris", cat:"Palmares",
   title:"Meilleurs restaurants a Paris : 25 tables classees en 2026",
   dest:"Paris", region:"Paris", date:"2026-09-15", reading:18,
   url:"palmares/meilleurs-restaurants-paris/", photo:"images/pa-exemple.jpg"},
  */
];

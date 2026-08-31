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

   Regle photo : uniquement de vraies photos des etablissements nommes, issues
   des sites officiels ou des dossiers de presse. Les banques d'images ne servent
   que de repli et ne doivent jamais illustrer un etablissement nomme.

   Regle editoriale : le tiret cadratin est interdit dans tout le texte publie.
   Virgule, deux-points ou point-virgule a la place. Le build le verifie.
   ========================================================================== */
window.ARTICLES = [
  {slug:"meilleurs-restaurants-france", cat:"Palmarès",
   title:"Les 15 meilleurs restaurants de France en 2026",
   dest:"France", region:"France", date:"2026-08-31", reading:12,
   url:"meilleurs-restaurants-france/", photo:"images/brasserie-salle.jpg",
   recit:"Trois guides, trois méthodes, et ce qu'ils disent quand on les met côte à côte."},
  /* Aucun article publie a ce jour. Le media n'a encore rien teste : le
     catalogue reste vide tant que le premier service n'a pas eu lieu.
     Exemple de la forme attendue, a decommenter et adapter :

  {slug:"meilleurs-restaurants-paris", cat:"Palmares",
   title:"Meilleurs restaurants a Paris : 25 tables classees en 2026",
   dest:"Paris", region:"Paris", date:"2026-09-15", reading:18,
   url:"palmares/meilleurs-restaurants-paris/", photo:"images/pa-exemple.jpg"},
  */
];

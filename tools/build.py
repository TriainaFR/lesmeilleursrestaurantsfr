#!/usr/bin/env python3
"""
Build de lesmeilleursrestaurants.fr : a lancer apres CHAQUE publication.

    python3 tools/build.py                # applique tout
    python3 tools/build.py --check        # ne modifie rien, controle seulement
    python3 tools/build.py --allow-demo   # tolere les blocs data-demo

Source de verite unique : assets/articles.js. Le HTML, le sitemap et l'API en
decoulent, jamais l'inverse. Un article saisi a la main dans une page serait
invisible du sommaire et du sitemap, et signale ici comme orphelin.

Ce que le script maintient :
  1. Listes statiques du fil, des depeches et des enquetes, injectees entre les
     marqueurs <!--S:...--> pour les robots qui n'executent pas JavaScript.
  2. Compteurs affiches portant un attribut data (data-art-count et compagnie).
  3. Dates : content-freshness, dateModified des JSON-LD, mentions de mise a jour.
  4. sitemap.xml, api/articles.json, api/status.json.
  5. Une version Markdown de chaque page, pour Accept: text/markdown.

Puis il controle, et refuse de construire si quelque chose cloche. Le controle
propre a ce site : aucun attribut data-demo ne doit subsister. Ce drapeau marque
la maquette de lancement, qui attribue a de vrais restaurants des notes que la
redaction n'a pas portees. Tant qu'il est la, rien ne part en ligne.
"""

import argparse
import hashlib
import html as html_mod
import json
import os
import posixpath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.lesmeilleursrestaurants.fr"
os.chdir(ROOT)

# Repertoires hors site : outillage, dependances, et les maquettes de la phase
# de conception, gardees pour memoire mais qui ne doivent ni etre indexees ni
# passer les controles editoriaux.
SKIP_DIRS = {".git", ".github", "node_modules", "tools", "_archives-maquettes"}
# Meme raison, pour les maquettes restees a la racine (v3-..., proposition-2-...).
MAQUETTE = re.compile(r"^(v\d+|proposition)[-_]")

# Rubriques editoriales, deduites du champ cat du catalogue. Sert a reperer une
# page d'article presente sur le disque mais absente du catalogue.
ARTICLE_DIRS = ("palmares/", "enquetes/", "guides/", "villes/", "ouvertures/")

changes, problems = [], []


def log(msg):
    changes.append(msg)


def fail(msg):
    problems.append(msg)


# ------------------------------------------------------------------- fichiers
def pages():
    """Toutes les pages HTML du site, maquettes et outillage exclus."""
    out = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".html") and not MAQUETTE.match(fn):
                out.append(os.path.relpath(os.path.join(dirpath, fn), "."))
    return sorted(out)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, old, new):
    """N'ecrit que si le contenu a reellement change : le build est relance a
    chaque publication, il ne doit pas salir le diff git pour rien."""
    if old == new:
        return False
    if not CHECK:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
    return True


# ------------------------------------------------------------------ catalogue
def load_articles():
    """Lit assets/articles.js sans l'executer. Le fichier est du JavaScript : les
    cles sont nues (slug: "x"). On les met entre guillemets, mais uniquement hors
    des chaines, car les titres contiennent des deux-points ("Plenitude, avis :
    trois etoiles"). Le tableau vide du lancement doit passer sans broncher."""
    src = read("assets/articles.js")
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"^\s*//.*$", "", src, flags=re.M)
    if "[" not in src or "]" not in src:
        fail("assets/articles.js : tableau window.ARTICLES introuvable")
        return []
    body = src[src.index("["):src.rindex("]") + 1]

    out, i, in_str, esc = [], 0, False, False
    while i < len(body):
        c = body[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        m = re.match(r"([A-Za-z_]\w*)\s*:", body[i:])
        if m and (not out or out[-1].strip() in ("", "{", ",", "\n")):
            out.append('"%s":' % m.group(1))
            i += m.end()
            continue
        out.append(c)
        i += 1

    try:
        arts = json.loads(re.sub(r",(\s*[\]}])", r"\1", "".join(out)))
    except Exception as e:
        fail("assets/articles.js illisible (%s)" % e)
        return []

    manquants = [a.get("slug", "?") for a in arts
                 if not all(k in a for k in ("slug", "cat", "title", "date", "url"))]
    for slug in manquants:
        fail("article incomplet dans assets/articles.js : %s "
             "(slug, cat, title, date et url sont obligatoires)" % slug)
    return sorted(arts, key=lambda a: a["date"], reverse=True)


FR_MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
             "juil.", "août", "sept.", "oct.", "nov.", "déc."]
FR_MONTHS_LONG = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                  "août", "septembre", "octobre", "novembre", "décembre"]


def fr_date(iso, long=False, hide_year=False):
    y, m, d = (int(x) for x in iso.split("-")[:3])
    txt = "%d %s" % (d, (FR_MONTHS_LONG if long else FR_MONTHS)[m - 1])
    if hide_year and y == datetime.now().year:
        return txt
    return "%s %d" % (txt, y)


def esc(s):
    """Valeur d'attribut."""
    return html_mod.escape(str(s), quote=True)


def txt(s):
    """Contenu textuel. On n'echappe pas les apostrophes : le francais en est
    plein, et « l&#x27;assiette » dans le source ne se relit pas."""
    return html_mod.escape(str(s), quote=False)


# ------------------------------------------------------------ dates et depot
IS_GIT = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                        capture_output=True, text=True).stdout.strip() == "true"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
_GIT_DATES = {}


def git_date(path):
    """Date du dernier commit touchant le fichier. Hors depot git, ou pour un
    fichier jamais commite, on ne devine rien : l'appelant retombe sur le jour."""
    if not IS_GIT:
        return None
    if path not in _GIT_DATES:
        try:
            out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                                 capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            out = ""
        _GIT_DATES[path] = out or None
    return _GIT_DATES[path]


def page_date(path):
    return git_date(path) or TODAY


# ------------------------------------------------- 1. listes statiques du site
# Le fil tient sur une grille de quatre colonnes (.art-grid), le compte doit donc
# etre un multiple de 4 pour ne pas laisser de rangee orpheline. Les parutions
# suivantes basculent dans les depeches, bornees a WIRE lignes. La grille des
# enquetes est en trois colonnes, avec la deuxieme carte decalee vers le bas
# (.recit:nth-child(2)) : la rangee de trois est la seule qui tienne debout.
FIL = 8
WIRE = 10
RECITS_HOME = 3

_DIMS = {}


def img_dims(rel):
    """Dimensions natives d'une image, pour poser width/height sur les cartes et
    eviter le decalage de mise en page au chargement. Pillow est facultatif."""
    if rel in _DIMS:
        return _DIMS[rel]
    dims = None
    if not rel.startswith("http") and os.path.exists(rel):
        try:
            from PIL import Image
            with Image.open(rel) as im:
                dims = im.size
        except Exception:
            dims = None
    _DIMS[rel] = dims
    return dims


def photo_of(a):
    return a.get("photo") or "images/og-default.jpg"


def card_html(a):
    """Carte du fil. Classes reprises telles quelles de index.html : le CSS cible
    .art-card .ph, .art-card .meta .cat et .art-card[data-cat="Enquête"]."""
    rel = photo_of(a)
    d = img_dims(rel)
    wh = ' width="%d" height="%d"' % d if d else ""
    return (
        '<a class="art-card rv" href="%s" data-cat="%s">'
        '<div class="ph"><img%s src="%s" alt="" loading="lazy" decoding="async"></div>'
        '<div class="meta"><span class="cat">%s</span>'
        '<span class="date">%s</span></div>'
        '<h3>%s</h3>'
        '<p class="dest">%s · %s min de lecture</p></a>'
        % (esc(a["url"]), esc(a["cat"]), wh, esc(rel), txt(a["cat"]),
           fr_date(a["date"]), txt(a["title"]), txt(a.get("dest", "")),
           txt(a.get("reading", 10)))
    )


def wire_html(a):
    """Depeche. La colonne .w-time fait 64 px : la date y tient sans l'annee
    courante, que le lecteur a deja sous les yeux dans le bandeau du haut."""
    return (
        '<a class="wire-row" href="%s">'
        '<time class="w-time" datetime="%s">%s</time>'
        '<span class="w-cat">%s</span>'
        '<span class="w-title">%s</span>'
        '<span class="w-arr">→</span></a>'
        % (esc(a["url"]), esc(a["date"]), fr_date(a["date"], hide_year=True),
           txt(a["cat"]), txt(a["title"]))
    )


def recit_html(a, rank):
    """Carte d'enquete. Le decalage d'apparition suit l'ordre d'affichage, comme
    dans la maquette (transition-delay de .12s en .12s)."""
    rel = photo_of(a)
    d = img_dims(rel)
    wh = ' width="%d" height="%d"' % d if d else ""
    delay = ' style="transition-delay:.%02ds"' % (rank * 12) if rank else ""
    teaser = a.get("recit") or "%s, %s min de lecture." % (a.get("dest", ""), a.get("reading", 10))
    return (
        '<a class="recit rv" href="%s"%s>'
        '<div class="ph"><span class="cat">%s</span>'
        '<picture><img%s src="%s" alt="" loading="lazy" decoding="async"></picture>'
        '<span class="num">%02d</span></div>'
        '<h3>%s</h3>'
        '<p>%s</p>'
        '<span class="meta">%s, %s min de lecture</span></a>'
        % (esc(a["url"]), delay, txt(a["cat"]), wh, esc(rel), rank + 1,
           txt(a["title"]), txt(teaser), txt(a["cat"]), txt(a.get("reading", 10)))
    )


def recits():
    """Les enquetes, de la plus recente a la plus ancienne. Toute parution de la
    rubrique Enquete en fait partie, plus celles qui portent un chapo `recit`."""
    dedies = [a for a in ARTS if a["cat"].startswith(("Enquête", "Enquete"))]
    slugs = {a["slug"] for a in dedies}
    return dedies + [a for a in ARTS if a.get("recit") and a["slug"] not in slugs]


def fill(page, marker, inner, required=True):
    """Injecte une liste entre <!--S:x--> et <!--/S:x-->. Les marqueurs rendent
    l'operation idempotente : relancer le build remplace le bloc, il ne l'empile
    pas. Une page qui n'existe pas encore est simplement ignoree."""
    if not os.path.exists(page):
        return
    open_m, close_m = "<!--S:%s-->" % marker, "<!--/S:%s-->" % marker
    s = read(page)
    if open_m not in s or close_m not in s:
        if required:
            fail("marqueurs %s absents de %s, liste non injectee" % (open_m, page))
        return
    i, j = s.index(open_m) + len(open_m), s.index(close_m)
    new = s[:i] + "\n" + inner + "\n" + s[j:]
    if write(page, s, new):
        log("liste %s regeneree dans %s" % (marker, page))


def sync_static_lists():
    if not ARTS:
        # Catalogue vide : injecter des listes vides vaudrait effacer la maquette
        # de lancement et laisser une page d'accueil sans un seul lien. On ne
        # touche a rien, le controle data-demo se charge d'empecher la mise en
        # ligne tant que rien n'a ete reellement publie.
        log("catalogue vide : listes statiques laissees en l'etat")
        return
    fill("index.html", "latest-grid", "".join(card_html(a) for a in ARTS[:FIL]))
    fill("index.html", "latest-wire",
         "".join(wire_html(a) for a in ARTS[FIL:FIL + WIRE]))
    fill("index.html", "recit-grid",
         "".join(recit_html(a, i) for i, a in enumerate(recits()[:RECITS_HOME])))
    fill("articles.html", "articles-list",
         "".join(card_html(a) for a in ARTS), required=False)


# ---------------------------------------------------------- 2. compteurs
def plural(n, mot, pluriel=None):
    return "%d %s" % (n, (pluriel or mot + "s") if n > 1 else mot)


def counters():
    """Valeurs derivees du catalogue, indexees par attribut data. Une valeur None
    laisse le libelle en place : avant la premiere parution, mieux vaut lire
    « Chaque semaine » que « 0 parutions »."""
    villes = {a.get("dest") for a in ARTS if a.get("dest")}
    enquetes = len(recits())
    palmares = sum(1 for a in ARTS if a["cat"].startswith("Palmar"))
    return {
        "data-art-count": plural(len(ARTS), "parution") if ARTS else None,
        "data-ville-count": ("%02d %s" % (len(villes), "villes" if len(villes) > 1 else "ville"))
                            if villes else None,
        "data-recit-count": plural(enquetes, "enquête") if enquetes else None,
        "data-palmares-count": plural(palmares, "palmarès", "palmarès") if palmares else None,
    }


def sync_counters():
    vals = {k: v for k, v in counters().items() if v}
    touched = 0
    for f in pages():
        s = read(f)
        o = s
        for attr, val in vals.items():
            # Remplace le contenu de l'element porteur de l'attribut, quel que
            # soit son nom de balise, sans toucher au reste du balisage.
            s = re.sub(r"(<(\w+)[^>]*\b%s\b[^>]*>)(.*?)(</\2>)" % attr,
                       lambda m: m.group(1) + val + m.group(4), s, flags=re.S)
        if ARTS:
            n = min(FIL, len(ARTS))
            s = re.sub(r"(Les )\d+( dernières unes)", r"\g<1>%d\g<2>" % n, s)
        if write(f, o, s):
            touched += 1
    if touched:
        log("compteurs synchronises sur %d page(s) : %s"
            % (touched, ", ".join("%s = %s" % (k, v) for k, v in sorted(vals.items()))))


# ------------------------------------------------------------------ 3. dates
def sync_dates():
    touched = 0
    for f in pages():
        d = page_date(f)
        s = read(f)
        o = s
        s = re.sub(r'("dateModified":\s*")\d{4}-\d{2}-\d{2}(")', r"\g<1>%s\g<2>" % d, s)
        s = re.sub(r'(<meta name="content-freshness" content=")\d{4}-\d{2}-\d{2}(")',
                   r"\g<1>%s\g<2>" % d, s)
        s = re.sub(r"(Dernière mise à jour(?:&nbsp;)?\s*:)\s*\d{1,2} [\wéû.]+ \d{4}",
                   r"\g<1> %s" % fr_date(d, long=True), s)
        s = re.sub(r"(Mise à jour le )\d{1,2} [\wéû.]+ \d{4}",
                   r"\g<1>%s" % fr_date(d, long=True), s)
        if write(f, o, s):
            touched += 1
    if touched:
        log("dates alignees sur %s sur %d page(s)"
            % ("le dernier commit" if IS_GIT else "la date du jour", touched))
    elif not IS_GIT:
        log("dates : depot hors git, la date du jour (%s) fait reference" % TODAY)


# ---------------------------------------------------------------- 4. sitemap
# Google ignore changefreq et priority depuis 2023 : le sitemap ne porte que loc
# et lastmod, les deux seuls signaux reellement lus.
NOINDEX = re.compile(r'<meta name="robots" content="[^"]*noindex')

# ----------------------------------------------------------- mode pre-lancement
# Tant que le media n'a rien publie, il n'a rien a faire dans un index : une
# vitrine vide qui se fait explorer part avec une reputation de page sans contenu,
# et la corriger apres coup coute bien plus cher que de l'eviter.
#
# On pose donc « noindex, follow » sur toutes les pages : noindex pour rester hors
# des resultats, follow pour que les liens internes soient tout de meme suivis et
# que la structure du site soit connue le jour de l'ouverture.
#
# Le sitemap se vide alors tout seul : sync_sitemap() ignore deja les pages en
# noindex. C'est volontaire, un sitemap qui declare des pages non indexables
# envoie deux ordres contradictoires.
#
# Le robots.txt reste ouvert a l'exploration, et ce n'est pas une contradiction :
# une page interdite d'exploration ne peut pas etre lue, donc son noindex ne peut
# pas etre vu. Pour ne pas etre indexe, il faut au contraire se laisser lire.
#
# POUR OUVRIR LE SITE : passer PRELAUNCH a False et relancer le build. Les balises
# sont retirees et le sitemap se repeuple.
PRELAUNCH = True
ROBOTS_TAG = '<meta name="robots" content="noindex, follow">'


def sync_noindex():
    """Pose ou retire la balise robots sur toutes les pages, selon PRELAUNCH."""
    touchees = 0
    for page in pages():
        s = old = read(page)
        if page == "404.html":
            # Une page d'erreur reste noindex en toutes circonstances.
            continue
        deja = re.search(r'[ \t]*<meta name="robots" content="[^"]*">\n?', s)
        if PRELAUNCH:
            if deja:
                if deja.group(0).strip() != ROBOTS_TAG:
                    s = s[:deja.start()] + ROBOTS_TAG + "\n" + s[deja.end():]
            else:
                # Juste apres la description : la balise se lit avec les autres
                # consignes destinees aux moteurs, pas perdue en fin de head.
                m = re.search(r'<meta name="description"[^>]*>\n', s)
                if not m:
                    fail("pas de meta description ou poser la balise robots : %s" % page)
                    continue
                s = s[:m.end()] + ROBOTS_TAG + "\n" + s[m.end():]
        elif deja:
            s = s[:deja.start()] + s[deja.end():]
        if write(page, old, s):
            touchees += 1
    if touchees:
        log("balise robots %s sur %d page(s)"
            % ("posee" if PRELAUNCH else "retiree", touchees))
    if PRELAUNCH:
        log("MODE PRE-LANCEMENT : le site est en noindex, le sitemap reste vide")

FIXED_ORDER = [
    "index.html", "articles.html",
    "notre-methode/index.html", "redaction/index.html",
    "contact.html", "mentions-legales/index.html", "confidentialite/index.html",
]

SECTIONS = [
    ("Accueil et sommaire", lambda f, a: f in ("index.html", "articles.html")),
    ("Palmares", lambda f, a: bool(a) and a["cat"].startswith("Palmar")),
    ("Enquetes", lambda f, a: bool(a) and a["cat"].startswith(("Enquête", "Enquete"))),
    ("Guides et ouvertures", lambda f, a: bool(a) and a["cat"].startswith(("Guide", "Ouvertur"))),
    ("Villes", lambda f, a: bool(a) and a["cat"].startswith("Ville")),
    ("Le media", lambda f, a: f.startswith(("notre-methode/", "redaction/"))),
    ("Contact et mentions", lambda f, a: True),
]


ASSETS = ("assets/style.css", "assets/app.js", "assets/articles.js")


def sync_asset_versions():
    """Colle l'empreinte du fichier sur chaque appel d'asset.

    Les assets sont servis avec un cache long, c'est voulu : sans cela, chaque
    visite retelecharge la feuille de style. La contrepartie est qu'un visiteur
    deja venu garde l'ancienne version apres une mise a jour, parfois des mois.
    On suffixe donc l'URL d'une empreinte du contenu : elle ne bouge que si le
    fichier bouge, et le navigateur voit alors une URL neuve.

    Le piege, verifie ici : les pages en sous-dossier ecrivent « ../assets/... ».
    Le motif accepte donc un prefixe relatif quelconque, sinon seules les pages
    de la racine seraient versionnees et les autres resteraient en cache.
    """
    empreintes = {}
    for rel in ASSETS:
        if os.path.exists(rel):
            with open(rel, "rb") as fh:
                empreintes[rel] = hashlib.sha1(fh.read()).hexdigest()[:8]
    if not empreintes:
        return

    touchees = 0
    for page in pages():
        s = old = read(page)
        for rel, h in empreintes.items():
            motif = re.compile(
                r'((?:href|src)=")((?:\.\./)*)' + re.escape(rel) + r'(?:\?v=[0-9a-f]+)?(")')
            s = motif.sub(lambda m: "%s%s%s?v=%s%s"
                          % (m.group(1), m.group(2), rel, h, m.group(3)), s)
        if write(page, old, s):
            touchees += 1
    if touchees:
        log("empreintes d'assets posees sur %d page(s) (cache navigateur)" % touchees)


def canonical_of(s):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    return m.group(1) if m else None


def sync_sitemap():
    by_page = {posixpath.join(a["url"], "index.html"): a for a in ARTS}
    remaining, seen, skipped = [], set(), 0
    for f in pages():
        if f == "404.html":
            continue
        s = read(f)
        if NOINDEX.search(s):
            skipped += 1
            continue
        loc = canonical_of(s)
        if not loc or not loc.startswith(BASE + "/"):
            # Le controle des canoniques le signale deja, on n'invente pas d'URL.
            continue
        if loc in seen:
            continue
        seen.add(loc)
        remaining.append((f, loc, by_page.get(f.replace("\\", "/"))))

    blocks, total = [], 0
    for title, match in SECTIONS:
        group = [x for x in remaining if match(x[0], x[2])]
        if not group:
            continue
        remaining = [x for x in remaining if x not in group]
        group.sort(key=lambda x: x[1])
        group.sort(key=lambda x: x[2]["date"] if x[2] else "", reverse=True)
        group.sort(key=lambda x: FIXED_ORDER.index(x[0]) if x[0] in FIXED_ORDER else 99)
        lines = ["  <!-- %s -->" % title]
        for f, loc, a in group:
            # lastmod : le commit s'il existe, sinon la date de parution declaree
            # au catalogue, sinon le jour. Aucune date n'est inventee.
            d = git_date(f) or (a["date"] if a else None) or TODAY
            lines.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (loc, d))
            total += 1
        blocks.append("\n".join(lines))

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n\n".join(blocks) + "\n</urlset>\n")
    try:
        root = ET.fromstring(xml)
        n = len(root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"))
        if n != total:
            fail("sitemap : %d balises url pour %d URLs attendues" % (n, total))
            return
    except Exception as e:
        fail("sitemap XML invalide : %s" % e)
        return

    old = read("sitemap.xml") if os.path.exists("sitemap.xml") else ""
    if write("sitemap.xml", old, xml):
        log("sitemap.xml regenere (%d URL(s)%s)"
            % (total, ", %d page(s) en noindex exclue(s)" % skipped if skipped else ""))


# -------------------------------------------------------------------- 5. API
# Le media n'a ni compte ni panier : la seule chose qu'un agent puisse demander,
# c'est le catalogue. On l'expose en lecture seule, rien de plus.
def sync_api():
    updated = max((a["date"] for a in ARTS), default=TODAY)
    catalogue = {
        "name": "Catalogue des parutions de Meilleurs.",
        "description": "Toutes les parutions du media lesmeilleursrestaurants.fr, "
                       "en lecture seule. Chaque entree pointe vers la page HTML et "
                       "vers sa version Markdown, servie aussi par negociation de "
                       "contenu (Accept: text/markdown).",
        "publisher": "Meilleurs. (lesmeilleursrestaurants.fr), edite par Triaina",
        "citation": "Citer « Meilleurs. (lesmeilleursrestaurants.fr) ».",
        "updated": updated,
        "count": len(ARTS),
        "articles": [{
            "slug": a["slug"],
            "title": a["title"],
            "category": a["cat"],
            "destination": a.get("dest", ""),
            "region": a.get("region", ""),
            "published": a["date"],
            "readingMinutes": a.get("reading"),
            "url": "%s/%s" % (BASE, a["url"]),
            "markdown": "%s/%sindex.md" % (BASE, a["url"]),
            "image": "%s/%s" % (BASE, photo_of(a)),
        } for a in ARTS],
    }
    status = {"status": "ok", "articles": len(ARTS), "updated": updated}

    written = 0
    for path, data in (("api/articles.json", catalogue), ("api/status.json", status)):
        new = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        old = read(path) if os.path.exists(path) else ""
        if write(path, old, new):
            written += 1
    if written:
        log("API de consultation regeneree (%d fichier(s), %d parution(s))"
            % (written, len(ARTS)))


# --------------------------------------------------------------- 6. Markdown
# Un .md a cote de chaque .html : le serveur le renvoie quand un agent envoie
# Accept: text/markdown, et il recoit la page sans le chrome ni le JavaScript.

# Ligne de provenance des Markdown generes. Elle sert aussi de signature : le
# nettoyage ne supprime que les fichiers qui la portent.
MD_MARK = "Source : %s"

DROP = [
    r'<script\b', r'<style\b', r'<svg\b', r'<noscript\b',
    r'<header\b', r'<footer\b',
    r'<div class="topstrip"', r'<div class="overlay"', r'<div class="ticker"',
    r'<[a-z]+[^>]*aria-hidden="true"',
]


def drop_elements(s, opener):
    """Supprime un element et tout son contenu, en comptant les balises de meme
    nom : une expression reguliere non gourmande couperait au premier </div>
    venu, donc au milieu des elements imbriques."""
    out, pos = [], 0
    for m in re.finditer(opener + r"[^>]*>", s):
        if m.start() < pos:
            continue
        tag = re.match(r"<(\w+)", m.group(0)).group(1)
        if m.group(0).rstrip().endswith("/>"):
            out.append(s[pos:m.start()])
            pos = m.end()
            continue
        depth, i = 1, m.end()
        pat = re.compile(r"</?%s\b" % tag, re.I)
        while depth and i < len(s):
            nm = pat.search(s, i)
            if not nm:
                i = len(s)
                break
            depth += -1 if nm.group(0).startswith("</") else 1
            i = nm.end()
        end = s.find(">", i - 1)
        out.append(s[pos:m.start()])
        pos = (end + 1) if end != -1 else len(s)
    out.append(s[pos:])
    return "".join(out)


def flatten(fragment):
    """Contenu d'un element ramene a une seule ligne de texte."""
    txt = html_mod.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", txt.replace(" ", " ")).strip()


def html_to_md(path, s):
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s)
    canon = canonical_of(s) or BASE + "/" + path.replace("index.html", "")

    body = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    body = body[body.index("<body"):] if "<body" in body else body
    for opener in DROP:
        body = drop_elements(body, opener)

    body = re.sub(r"<br\s*/?>", "\n", body)

    # Les liens d'abord : sur ce site une carte entiere est un <a>, titre et
    # legende compris. En convertissant les blocs avant, le libelle du lien
    # heriterait de sauts de ligne et le Markdown produit serait casse.
    body = re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                  lambda m: ("[%s](%s)" % (flatten(m.group(2)), m.group(1))
                             if flatten(m.group(2)) else ""),
                  body, flags=re.S)
    # Les titres se traitent d'un bloc : un titre coupe en plusieurs lignes par
    # le balisage cesserait d'en etre un.
    for lvl in range(1, 5):
        body = re.sub(r"<h%d\b[^>]*>(.*?)</h%d>" % (lvl, lvl),
                      lambda m, l=lvl: "\n\n%s %s\n\n" % ("#" * l, flatten(m.group(1))),
                      body, flags=re.S)
    body = re.sub(r"<li[^>]*>", "\n- ", body)
    body = re.sub(r"<blockquote[^>]*>", "\n> ", body)
    body = re.sub(r"</(p|div|section|tr|ul|ol|figure|figcaption)>", "\n\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = html_mod.unescape(body).replace(" ", " ")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\n *", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    head = ["# " + html_mod.unescape(title.group(1)).strip() if title else "# Meilleurs."]
    if desc:
        head.append("> " + html_mod.unescape(desc.group(1)).strip())
    head.append(MD_MARK % canon)
    head.append("Meilleurs., media francais des meilleurs restaurants, edite par Triaina.")
    return "\n\n".join(head) + "\n\n---\n\n" + body + "\n"


def sync_markdown():
    n = 0
    kept = set()
    for f in pages():
        target = f[:-5] + ".md"
        kept.add(target)
        old = read(target) if os.path.exists(target) else ""
        if write(target, old, html_to_md(f, read(f))):
            n += 1
    if n:
        log("%d page(s) Markdown regeneree(s) pour la negociation de contenu" % n)

    # Nettoyage des .md dont la page HTML a disparu. On ne supprime QUE ce que ce
    # script a lui-meme ecrit, reconnu a sa ligne de provenance : le depot
    # contient des Markdown rediges a la main (.well-known/agent-skills, notes de
    # redaction) qu'un nettoyage trop large emporterait sans retour.
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ".")
            if rel in kept or os.path.exists(rel[:-3] + ".html"):
                continue
            if MD_MARK.split("%s")[0] not in read(rel):
                continue
            if not CHECK:
                os.remove(rel)
            log("Markdown orphelin supprime : %s" % rel)


# ------------------------------------------------------------- 7. controles
def visible_text(s):
    """Texte reellement lu par un humain : sans commentaires, sans script ni
    style, sans balises. Sert au controle du tiret cadratin."""
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S | re.I)
    metas = re.findall(r'<meta[^>]+content="([^"]*)"', s)
    s = re.sub(r"<[^>]+>", " ", s)
    return html_mod.unescape(s + " " + " ".join(metas))


def check_demo(allow_demo):
    """Controle propre a ce site. data-demo marque la maquette de lancement :
    des etablissements reels y portent des notes, des dates et des accroches que
    la redaction n'a pas produites. Mettre cela en ligne reviendrait a publier un
    faux jugement sur de vraies maisons."""
    coupables = []
    for f in pages():
        n = len(re.findall(r"<[^>]*\bdata-demo\b", read(f)))
        if n:
            coupables.append((f, n))
    if not coupables:
        return
    if allow_demo:
        log("data-demo tolere par --allow-demo dans %s (NE PAS METTRE EN LIGNE)"
            % ", ".join("%s (%d bloc(s))" % c for c in coupables))
        return
    fail("contenu de demonstration encore present : "
         + ", ".join("%s, %d bloc(s) data-demo" % c for c in coupables)
         + "\n      Ces blocs attribuent a de vrais restaurants des notes, des dates et"
           "\n      des accroches que la redaction n'a pas portees : les publier serait"
           "\n      leur preter un jugement qui n'existe pas. Les remplacer par de vraies"
           "\n      parutions saisies dans assets/articles.js, puis relancer le build, qui"
           "\n      remplit lui-meme les blocs entre les marqueurs <!--S:...-->."
           "\n      Pour travailler la mise en page en attendant : --allow-demo.")


def check_canonical():
    """La canonique doit designer exactement l'URL servie : domaine avec www,
    barre finale sur les pages en dossier, jamais index.html."""
    for f in pages():
        if f == "404.html":
            continue
        s = read(f)
        loc = canonical_of(s)
        if not loc:
            fail("canonical absent : %s" % f)
            continue
        expected = BASE + "/" + f.replace("\\", "/")
        expected = re.sub(r"(^|/)index\.html$", "/", expected)
        if loc != expected:
            fail("canonical incoherent : %s declare %s, attendu %s" % (f, loc, expected))


def check_orphans():
    """Le catalogue et le disque doivent dire la meme chose. Un article au
    catalogue sans page est un lien mort dans le fil ; une page d'article absente
    du catalogue est invisible du sommaire, de la recherche et du sitemap."""
    for a in ARTS:
        page = posixpath.join(a["url"], "index.html")
        if not os.path.exists(page):
            fail("article sans page : %s annonce %s, absent du disque" % (a["slug"], page))
        # La photo est verifiee ici, sur le catalogue, et pas seulement sur le
        # HTML produit : en --check rien n'est injecte, un chemin de photo faux
        # passerait donc inapercu jusqu'a la mise en ligne.
        photo = photo_of(a)
        if not photo.startswith("http") and not os.path.exists(photo):
            fail("photo absente du disque : %s declare %s" % (a["slug"], photo))
    connus = {posixpath.join(a["url"], "index.html") for a in ARTS}
    for f in pages():
        rel = f.replace("\\", "/")
        if rel.startswith(ARTICLE_DIRS) and rel.endswith("/index.html") and rel not in connus:
            fail("page orpheline : %s n'est pas dans assets/articles.js, "
                 "elle restera hors du sommaire et du sitemap" % rel)


def resolve(page, ref):
    """Un chemin commencant par / part de la racine du site, les autres du
    dossier de la page."""
    if ref.startswith("/"):
        return os.path.normpath(ref.lstrip("/"))
    return os.path.normpath(os.path.join(os.path.dirname(page), ref))


def check_liens_sortants():
    """Aucun lien sortant ne doit transmettre d'autorite pour l'instant.

    Le media est jeune et ses autres titres appartiennent au meme editeur : des
    liens suivis entre eux ressemblent a un echange organise plutot qu'a une
    citation, et rien ne justifie d'envoyer dehors le peu d'autorite d'un site qui
    n'a pas encore publie. Tout lien vers un domaine tiers porte donc nofollow.

    Ce controle ne regarde que les balises <a> : les URL declarees en donnees
    structurees (sameAs et compagnie) ne transmettent pas d'autorite, elles
    servent a identifier une entite, et restent donc autorisees.

    A lever le jour ou le media assume ses liens sortants : retirer l'appel dans
    checks(), ou reduire ce controle aux seuls domaines de l'editeur.
    """
    hote = BASE.split("//", 1)[1].rstrip("/")
    for page in pages():
        s = read(page)
        for balise in re.findall(r"<a\b[^>]*>", s):
            m = re.search(r'href="(https?://[^"]+)"', balise)
            if not m:
                continue
            cible = m.group(1).split("//", 1)[1]
            if cible.split("/")[0] in (hote, hote.replace("www.", "")):
                continue
            rel = re.search(r'rel="([^"]*)"', balise)
            if not rel or "nofollow" not in rel.group(1).split():
                fail("lien sortant sans nofollow : %s pointe vers %s"
                     % (page, m.group(1)))


def checks(allow_demo):
    check_demo(allow_demo)
    check_liens_sortants()
    check_canonical()
    check_orphans()
    for f in pages():
        s = read(f)
        for i, b in enumerate(re.findall(
                r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.S)):
            try:
                json.loads(b)
            except Exception as e:
                fail("JSON-LD invalide : %s, bloc %d (%s)" % (f, i + 1, e))
        for line, txt in enumerate(visible_text(s).splitlines(), 1):
            if "—" in txt:
                fail("tiret cadratin interdit : %s ligne %d, %s"
                     % (f, line, txt.strip()[:70]))
                break
        # images et fichiers joints declares par la page
        refs = re.findall(r'(?:src|href)="([^"]+\.(?:jpg|jpeg|png|webp|avif|gif|svg|ico))"', s)
        for m in re.findall(r'srcset="([^"]+)"', s):
            refs += [c.strip().split(" ")[0] for c in m.split(",") if c.strip()]
        for ref in sorted(set(refs)):
            if ref.startswith(("http", "data:", "//")):
                continue
            if not os.path.exists(resolve(f, ref.split("?")[0])):
                fail("image absente du disque : %s reference %s" % (f, ref))
        # liens internes
        for href in sorted(set(re.findall(r'href="([^"]+)"', s))):
            if href.startswith(("http", "mailto", "tel", "data:", "#", "//")):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target or re.search(r"\.(jpg|jpeg|png|webp|avif|gif|svg|ico|css|js|xml|txt|md|json)$", target):
                continue
            p = resolve(f, target)
            if not os.path.exists(p) and not os.path.exists(os.path.join(p, "index.html")):
                fail("lien interne mort : %s pointe vers %s, page inexistante" % (f, href))


# ---------------------------------------------------------------- execution
def main():
    ap = argparse.ArgumentParser(
        description="Build du site lesmeilleursrestaurants.fr")
    ap.add_argument("--check", action="store_true",
                    help="controle sans rien ecrire")
    ap.add_argument("--allow-demo", action="store_true",
                    help="tolere les blocs data-demo, pour travailler la mise en page")
    a = ap.parse_args()

    global CHECK
    CHECK = a.check

    sync_static_lists()
    sync_counters()
    sync_dates()
    sync_noindex()
    sync_asset_versions()
    sync_sitemap()
    sync_api()
    sync_markdown()
    checks(a.allow_demo)

    print()
    print("  Build%s : %d article(s) au catalogue, %d page(s) HTML"
          % (" (verification seule)" if CHECK else "", len(ARTS), len(pages())))
    print()
    for c in changes:
        print("  ✓ %s" % c)
    if not changes:
        print("  ✓ rien a mettre a jour, tout est deja aligne")
    if problems:
        print()
        for p in problems:
            print("  ✗ %s" % p)
        print()
        print("  Build refuse : %d probleme(s). Rien ne doit partir en ligne en l'etat."
              % len(problems))
        print()
        return 1
    print()
    print("  Aucun probleme detecte.")
    if changes and not CHECK:
        # L'etape que l'on oublie : sans notification, une page met des jours a
        # etre decouverte ; avec, quelques minutes.
        print("  Prochaine etape : commiter, pousser, deployer,")
        print("  puis  python3 tools/indexnow.py --changed")
    print()
    return 0


CHECK = "--check" in sys.argv
ARTS = load_articles()

if __name__ == "__main__":
    sys.exit(main())

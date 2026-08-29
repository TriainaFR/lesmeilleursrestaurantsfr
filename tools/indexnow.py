#!/usr/bin/env python3
"""
IndexNow : prevenir les moteurs qu'une page a change.

    python3 tools/indexnow.py --changed     # pages modifiees au dernier commit
    python3 tools/indexnow.py --all         # toutes les URLs du sitemap
    python3 tools/indexnow.py --changed --dry-run

Un seul envoi suffit : le protocole est partage par Bing, Yandex, Seznam et
Naver. Google n'y participe pas, pour lui c'est la Search Console qui fait foi.

La cle n'est ni inventee ni ecrite en dur. Elle vient du fichier <cle>.txt place
a la racine du depot, ou de la variable d'environnement INDEXNOW_KEY. Ce fichier
doit ensuite etre servi a la racine du domaine : c'est lui, et rien d'autre, qui
prouve aux moteurs que nous possedons le site. Sans lui, tout est refuse en 403.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

HOST = "www.lesmeilleursrestaurants.fr"
BASE = "https://%s" % HOST
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

# Le relais partage notifie deja les moteurs participants, mais on previent Bing
# en direct : c'est son index qui alimente les citations de Copilot, et un relais
# en panne passerait autrement inapercu.
ENDPOINTS = [
    ("IndexNow (relais partage)", "https://api.indexnow.org/indexnow"),
    ("Bing et Copilot", "https://www.bing.com/indexnow"),
]

# Un User-Agent explicite est indispensable : les pare-feu applicatifs renvoient
# 403 a l'agent par defaut de urllib.
UA = "Meilleurs-IndexNow/1.0 (+%s/)" % BASE

MESSAGES = {
    200: "OK, URLs acceptees.",
    202: "Accepte, la cle est en cours de validation par le moteur.",
    400: "Requete invalide (format du JSON).",
    403: "Cle refusee : le fichier <cle>.txt n'est pas accessible a la racine du domaine.",
    422: "URLs refusees : hors du domaine declare, ou cle qui ne correspond pas.",
    429: "Trop de requetes, reessayer plus tard.",
}

KEY_RE = re.compile(r"^[0-9a-f]{8,128}$")

COMMENT_GENERER = """
Aucune cle IndexNow n'est configuree.

  1. En generer une, et ecrire le fichier que les moteurs viendront lire :
       cd %s
       K=$(python3 -c "import secrets; print(secrets.token_hex(16))")
       printf '%%s' "$K" > "$K.txt"

  2. Deployer le site : le fichier doit repondre en 200 sur
       %s/<cle>.txt

  3. Relancer cette commande. Le fichier reste a la racine du depot, il est la
     preuve de propriete du domaine et ne doit jamais etre supprime ni renomme.

La cle peut aussi etre fournie par la variable INDEXNOW_KEY, mais le fichier
<cle>.txt doit exister a la racine dans tous les cas.
""" % (ROOT, BASE)


def find_key():
    """La cle vient du fichier <cle>.txt a la racine, ou de INDEXNOW_KEY. Dans
    les deux cas le fichier doit exister : c'est lui qui sera mis en ligne."""
    env = (os.environ.get("INDEXNOW_KEY") or "").strip().lower()
    if env:
        if not KEY_RE.match(env):
            sys.exit("INDEXNOW_KEY doit etre une chaine hexadecimale de 8 a 128 "
                     "caracteres, or elle vaut : %s" % env)
        path = "%s.txt" % env
        if not os.path.exists(path):
            sys.exit("INDEXNOW_KEY vaut %s mais %s/%s est absent.\n"
                     "Creer le fichier, les moteurs le lisent a la racine du domaine :\n"
                     "  printf '%%s' \"%s\" > \"%s\"" % (env, ROOT, path, env, path))
        return check_key_file(path, env)

    files = sorted(f for f in glob.glob("*.txt")
                   if KEY_RE.match(os.path.splitext(f)[0]))
    if not files:
        sys.exit(COMMENT_GENERER)
    if len(files) > 1:
        sys.exit("Plusieurs cles IndexNow a la racine (%s).\n"
                 "N'en garder qu'une : les moteurs valident celle qui est annoncee "
                 "dans keyLocation, les autres ne font qu'entretenir la confusion."
                 % ", ".join(files))
    return check_key_file(files[0], os.path.splitext(files[0])[0])


def check_key_file(path, key):
    """Le fichier doit contenir la cle et rien d'autre. Une ligne en trop, un
    BOM, et Bing refuse toutes les soumissions en 403, sans autre signal que
    l'absence d'indexation."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            contenu = fh.read().strip()
    except OSError as e:
        sys.exit("Fichier de cle illisible : %s (%s)" % (path, e))
    if contenu != key:
        sys.exit("%s doit contenir exactement la cle (%s), sans rien d'autre.\n"
                 "Il contient : %r" % (path, key, contenu[:80]))
    return key


def key_is_online(key):
    """Verification avant envoi : sans ce fichier en ligne, la soumission part
    dans le vide et le moteur repond 403."""
    req = urllib.request.Request("%s/%s.txt" % (BASE, key), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200 and r.read().decode("utf-8-sig").strip() == key
    except Exception:
        return False


def sitemap_urls():
    if not os.path.exists("sitemap.xml"):
        sys.exit("sitemap.xml absent. Le generer d'abord : python3 tools/build.py")
    try:
        root = ET.parse("sitemap.xml").getroot()
    except ET.ParseError as e:
        sys.exit("sitemap.xml illisible : %s" % e)
    return [u.find(NS + "loc").text for u in root.findall(NS + "url")
            if u.find(NS + "loc") is not None]


def page_to_url(path):
    """Chemin de fichier vers l'URL canonique declaree par la page. On ne
    reconstruit pas l'URL a partir du chemin : la canonique fait foi."""
    if not path.endswith(".html") or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        m = re.search(r'<link rel="canonical" href="([^"]+)"', fh.read())
    return m.group(1) if m and m.group(1).startswith(BASE) else None


def changed_urls():
    """URLs des pages touchees par le dernier commit."""
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                      capture_output=True, text=True).stdout.strip() != "true":
        sys.exit("Ce depot n'est pas un depot git : --changed ne peut pas savoir "
                 "ce qui a change. Utiliser --all.")
    try:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        sys.exit("Impossible de lire l'historique git : %s" % e)
    return sorted({u for u in (page_to_url(p) for p in out.split()) if u})


def submit(urls, key, dry_run=False):
    if not urls:
        print("Aucune URL a soumettre : aucune page n'a change au dernier commit.")
        print("Pour resoumettre tout le site : python3 tools/indexnow.py --all")
        return 0

    # Le protocole plafonne a 10 000 URLs par envoi.
    payload = {"host": HOST, "key": key, "keyLocation": "%s/%s.txt" % (BASE, key),
               "urlList": urls[:10000]}
    print("%d URL(s) a soumettre :" % len(payload["urlList"]))
    for u in payload["urlList"]:
        print("  ", u)
    if dry_run:
        print()
        print("--dry-run : rien n'a ete envoye.")
        return 0

    body = json.dumps(payload).encode()
    echecs = 0
    print()
    for label, endpoint in ENDPOINTS:
        req = urllib.request.Request(
            endpoint, data=body,
            headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:
            print("  %-28s echec reseau : %s" % (label, e))
            echecs += 1
            continue
        print("  %-28s %d %s" % (label, code, MESSAGES.get(code, "code inattendu")))
        if code not in (200, 202):
            echecs += 1
    print()
    # Un seul point d'entree qui repond suffit a faire passer l'information.
    return 1 if echecs == len(ENDPOINTS) else 0


def main():
    ap = argparse.ArgumentParser(
        description="Soumission IndexNow (Bing, Yandex, Seznam, Naver)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--changed", action="store_true",
                   help="pages modifiees au dernier commit git")
    g.add_argument("--all", action="store_true",
                   help="toutes les URLs du sitemap")
    ap.add_argument("--dry-run", action="store_true",
                    help="afficher ce qui serait envoye, sans rien envoyer")
    a = ap.parse_args()

    key = find_key()
    print("Cle IndexNow : %s (fichier %s.txt)" % (key, key))

    if not a.dry_run and not key_is_online(key):
        sys.exit("\n%s/%s.txt ne repond pas en ligne.\n"
                 "Deployer le site avant de soumettre : sans ce fichier, les moteurs "
                 "refusent la cle (403) et la soumission part dans le vide.\n"
                 "Pour verifier ce qui serait envoye en attendant : --dry-run"
                 % (BASE, key))

    return submit(sitemap_urls() if a.all else changed_urls(), key, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())

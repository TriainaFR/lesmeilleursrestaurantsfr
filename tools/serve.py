#!/usr/bin/env python3
"""Serveur statique local, pour regarder le site comme un navigateur le verra.

Ouvrir index.html directement depuis le disque ne suffit pas : les pages
pointent vers assets/ en chemin relatif, et le protocole file:// ne les resout
pas. Il faut donc servir le dossier en HTTP.

Deux precautions, chacune motivee par un faux bug deja rencontre :

1. « python3 -m http.server » calcule la valeur par defaut de --directory avec
   os.getcwd(). Certains environnements confines refusent cet appel et le
   serveur meurt avant d'avoir servi quoi que ce soit. La racine est donc
   deduite de l'emplacement de ce fichier, et getcwd() n'est appele qu'en
   dernier recours, sous garde.

2. Le HTML est servi en no-store. Sans cela, le navigateur reaffiche la page
   precedente apres une modification et l'on croit a une regression alors que
   le fichier sur le disque est correct. Les assets, eux, portent deja une
   empreinte de contenu posee par tools/build.py.

Usage : npm run serve, ou python3 tools/serve.py [port]
"""
import functools
import http.server
import os
import socketserver
import sys

ici = __file__
if not os.path.isabs(ici):
    try:
        ici = os.path.join(os.getcwd(), ici)
    except OSError:
        # Environnement confine : on se rabat sur le chemin tel qu'il est donne.
        pass
ROOT = os.path.dirname(os.path.dirname(ici))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8788


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".md": "text/markdown",
        ".webmanifest": "application/manifest+json",
    }

    def end_headers(self):
        chemin = self.path.split("?")[0]
        dernier = chemin.rsplit("/", 1)[-1]
        # Pages : jamais de cache. Fichiers versionnes : cache par defaut.
        if chemin.endswith((".html", "/")) or "." not in dernier:
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        code = args[1] if len(args) > 1 else ""
        if str(code).startswith(("4", "5")):
            super().log_message(fmt, *args)


def main():
    if not os.path.isfile(os.path.join(ROOT, "index.html")):
        print("Racine introuvable : %s ne contient pas index.html" % ROOT)
        return 1
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)) as httpd:
        print("Site servi sur http://localhost:%d  (racine : %s)" % (PORT, ROOT))
        print("Ctrl+C pour arreter.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArrete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

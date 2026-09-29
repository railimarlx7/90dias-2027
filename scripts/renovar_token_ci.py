#!/usr/bin/env python3
"""Renova o token do Instagram e regrava o secret do repositório.

É isto que impede a série de morrer a meio. O token de 60 dias pode ser renovado
enquanto ainda for válido e tiver mais de 24 horas; cada renovação dá outros 60 dias.
Correndo isto todas as semanas, nunca chega a expirar.

O valor novo nunca passa pela linha de comandos nem pelo registo: vai por um ficheiro
temporário para o `gh secret set`, que o cifra antes de enviar.
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

URL = "https://graph.instagram.com/refresh_access_token"


def main():
    antigo = os.environ.get("IG_TOKEN")
    repo = os.environ.get("REPO")
    if not antigo or not repo:
        print("faltam IG_TOKEN ou REPO", file=sys.stderr)
        return 1

    pedido = URL + "?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": antigo})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as r:
            d = json.loads(r.read())
    except Exception as e:
        print("::error::não foi possível renovar o token: %s" % e)
        print("::error::se já expirou não há renovação: é preciso gerar um novo no painel da Meta")
        return 1

    novo = d["access_token"]
    print("::add-mask::%s" % novo)           # nunca aparece no registo, por precaução
    ate = datetime.now(timezone.utc) + timedelta(seconds=int(d.get("expires_in", 0)))
    dias = (ate - datetime.now(timezone.utc)).days

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(novo)
        caminho = f.name
    try:
        with open(caminho) as entrada:
            subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--repo", repo],
                           stdin=entrada, check=True)
    finally:
        os.unlink(caminho)

    print("token renovado: vale até %s (%d dias)" % (ate.date(), dias))
    print("## Token renovado\n\nVálido até **%s** (%d dias)." % (ate.date(), dias),
          file=open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

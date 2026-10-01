#!/usr/bin/env python3
"""Confere se o card de hoje saiu mesmo, e falha com estrondo se não saiu.

Correr isto é o que transforma uma falha silenciosa num e-mail. A publicação pode
falhar por muita coisa — token expirado, GitHub em baixo, imagem fora do ar, a Meta
a recusar — e sem esta verificação ninguém dá por nada até alguém reparar que o card
do dia não apareceu.

Duas confirmações, porque uma não chega:
  1. existe `registo/<data>.json`, que o publicador só escreve depois de publicar;
  2. a Meta ainda devolve as publicações desse registo, com a data de hoje.

A segunda apanha o caso de o registo existir mas a publicação ter sido apagada, e o
caso de o registo ser de um ensaio antigo deixado para trás.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUSO = ZoneInfo("Europe/Lisbon")
# as horas UTC a que o publicador dispara (ver .github/workflows/publicar.yml)
PASSAGENS = (5, 6)
API = os.environ.get("IG_API", "https://graph.instagram.com/v23.0")


def resumo(texto):
    print(texto)
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as f:
        f.write(texto + "\n")


def ainda_vem_ai(agora_utc):
    """Falta alguma passagem do publicador hoje? Se falta, é cedo para alarmes."""
    return [h for h in PASSAGENS
            if datetime.combine(agora_utc.date(), time(h), timezone.utc) > agora_utc]


def media_existe(mid, token):
    u = "%s/%s?%s" % (API, mid, urllib.parse.urlencode(
        {"fields": "id,timestamp,media_product_type", "access_token": token}))
    try:
        with urllib.request.urlopen(u, timeout=30) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.loads(e.read())["error"].get("message")
        except Exception:
            return None, "HTTP %s" % e.code


def main():
    agora_utc = datetime.now(timezone.utc)
    hoje = agora_utc.astimezone(FUSO).date()
    cal = json.load(open(os.path.join(RAIZ, "calendario.json"), encoding="utf-8"))
    alvo = next((l for l in cal if l["data"] == hoje.isoformat()), None)
    if not alvo:
        resumo("Hoje (%s) não é dia de card. Nada a verificar." % hoje)
        return 0

    registo = os.path.join(RAIZ, "registo", "%s.json" % hoje.isoformat())
    falta = ainda_vem_ai(agora_utc)

    if not os.path.exists(registo):
        if falta:
            resumo("Dia %d ainda não publicado, mas falta a passagem das %02d:00 UTC. "
                   "Sem alarme por agora." % (alvo["dia"], falta[0]))
            return 0
        resumo("## ❌ O card do dia %d NÃO foi publicado\n\n"
               "Não existe `registo/%s.json` e já não há mais passagens hoje.\n\n"
               "Ver as execuções em Actions → \"publicar o card do dia\"."
               % (alvo["dia"], hoje))
        return 1

    feito = json.load(open(registo, encoding="utf-8"))
    token = os.environ.get("IG_TOKEN")
    if not token:
        resumo("Registo do dia %d existe, mas sem IG_TOKEN não confirmo na Meta."
               % alvo["dia"])
        return 0

    problemas = []
    for formato in ("feed", "story"):
        mid = feito.get(formato)
        if not mid:
            problemas.append("%s: o registo não tem id" % formato)
            continue
        d, erro = media_existe(mid, token)
        if erro:
            problemas.append("%s (%s): a Meta não o devolve — %s" % (formato, mid, erro))
        elif not d.get("timestamp", "").startswith(hoje.isoformat()):
            problemas.append("%s (%s): data %s, esperava %s"
                             % (formato, mid, d.get("timestamp"), hoje))

    if problemas:
        resumo("## ❌ O card do dia %d tem problemas\n\n- %s"
               % (alvo["dia"], "\n- ".join(problemas)))
        return 1

    resumo("## ✅ Dia %d publicado\n\n*%s*\n\nfeed `%s` · story `%s`"
           % (alvo["dia"], alvo["titulo"], feito.get("feed"), feito.get("story")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

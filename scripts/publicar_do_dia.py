#!/usr/bin/env python3
"""Escolhe o card de hoje e manda-o publicar. É isto que o workflow corre.

Lê o calendário, encontra a linha cuja data é a de hoje e chama a API. Sem linha
para hoje, não faz nada e sai bem — antes de 3 de outubro e depois de 1 de janeiro
não há nada para publicar.
"""
import json, os, sys
from datetime import date, timezone, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from publicar_instagram import publicar                      # noqa: E402

BASE = os.environ.get("BASE_URL", "https://railimarlx7.github.io/90dias-2027")
FUSO = timezone(timedelta(hours=-3))                         # a data é a de Brasília


def hoje():
    return date.today() if os.environ.get("DIA") else \
        __import__("datetime").datetime.now(FUSO).date()


def main():
    linhas = json.load(open(os.path.join(RAIZ, "calendario.json"), encoding="utf-8"))
    forcado = os.environ.get("DIA", "").strip()
    if forcado:
        alvo = next((l for l in linhas if l["dia"] == int(forcado)), None)
    else:
        d = hoje().isoformat()
        alvo = next((l for l in linhas if l["data"] == d), None)
    if not alvo:
        print("hoje não há card para publicar")
        return

    ensaio = os.environ.get("ENSAIO", "").lower() in ("1", "true", "yes")
    cred = {"IG_USER_ID": os.environ.get("IG_USER_ID") or "me",
            "IG_TOKEN": os.environ["IG_TOKEN"]}
    print("dia %d — %s" % (alvo["dia"], alvo["titulo"]))

    feito = {"dia": alvo["dia"], "data": alvo["data"], "ensaio": ensaio}
    feito["feed"] = publicar("%s/%s" % (BASE, alvo["feed"]),
                             alvo["legenda"] + ("\n\n" + alvo["hashtags"] if alvo["hashtags"] else ""),
                             False, cred, seco=False, sem_publicar=ensaio)
    feito["story"] = publicar("%s/%s" % (BASE, alvo["story"]), "", True, cred,
                              seco=False, sem_publicar=ensaio)

    d = os.path.join(RAIZ, "registo")
    os.makedirs(d, exist_ok=True)
    json.dump(feito, open(os.path.join(d, "%s.json" % alvo["data"]), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("registo guardado")


if __name__ == "__main__":
    main()

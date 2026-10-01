#!/usr/bin/env python3
"""Escolhe o card de hoje e manda-o publicar. É isto que o workflow corre.

Lê o calendário, encontra a linha cuja data é a de hoje e chama a API. Sem linha
para hoje, não faz nada e sai bem — antes de 3 de outubro e depois de 1 de janeiro
não há nada para publicar.
"""
import json, os, sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from publicar_instagram import publicar                      # noqa: E402

BASE = os.environ.get("BASE_URL", "https://railimarlx7.github.io/90dias-2027")

# O público é de Portugal e o card sai às 6 da manhã de lá. O cron do GitHub é
# sempre em UTC e não conhece horário de verão, que acaba a 25 de outubro, a meio
# da série: por isso o workflow dispara às 05:00 e às 06:00 UTC e é aqui que se
# decide qual das duas é a boa. Em horário de verão acerta a das 05:00, no resto
# do ano a das 06:00. A outra sai sem fazer nada.
FUSO = ZoneInfo("Europe/Lisbon")
HORA = int(os.environ.get("HORA_LOCAL", "6"))


def agora():
    return datetime.now(FUSO)


def hoje():
    return agora().date()


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
    d = os.path.join(RAIZ, "registo")
    registo = os.path.join(d, "%s.json" % alvo["data"])

    if not forcado and not ensaio:
        # cedo de mais: é a outra passagem do dia que serve
        if agora().hour < HORA:
            print("são %s em Lisboa, o card sai às %dh — nada a fazer"
                  % (agora().strftime("%H:%M"), HORA))
            return
        # já publicado hoje: a segunda passagem não repete
        if os.path.exists(registo):
            print("o card de hoje já foi publicado — nada a fazer")
            return
    cred = {"IG_USER_ID": os.environ.get("IG_USER_ID") or "me",
            "IG_TOKEN": os.environ["IG_TOKEN"]}
    print("dia %d — %s" % (alvo["dia"], alvo["titulo"]))

    feito = {"dia": alvo["dia"], "data": alvo["data"], "ensaio": ensaio}
    feito["feed"] = publicar("%s/%s" % (BASE, alvo["feed"]),
                             alvo["legenda"] + ("\n\n" + alvo["hashtags"] if alvo["hashtags"] else ""),
                             False, cred, seco=False, sem_publicar=ensaio)
    feito["story"] = publicar("%s/%s" % (BASE, alvo["story"]), "", True, cred,
                              seco=False, sem_publicar=ensaio)

    if ensaio:
        # Um ensaio NÃO grava registo: o registo é o que trava a segunda passagem
        # do dia, e um ensaio deixado para trás faria o card verdadeiro ser saltado.
        print("ensaio: não gravo registo")
        return
    os.makedirs(d, exist_ok=True)
    feito["publicado_em"] = agora().isoformat()
    json.dump(feito, open(registo, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("registo guardado")


if __name__ == "__main__":
    main()

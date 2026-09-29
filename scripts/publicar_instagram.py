#!/usr/bin/env python3
"""Publica um card no Instagram pela API de conteúdo da Meta.

A publicação é sempre em dois tempos: primeiro cria-se um contentor com a imagem,
depois é que se publica. O contentor vive 24h e só vira post no segundo pedido.

As credenciais vêm de um ficheiro à parte e nunca passam pela linha de comandos nem
são impressas. Por omissão lê `publicar/.credenciais`, no formato:

    IG_USER_ID=17841400000000000
    IG_TOKEN=EAAG...

Uso:
    python3 publicar_instagram.py --imagem URL --legenda "..." --seco
    python3 publicar_instagram.py --imagem URL --legenda "..."
    python3 publicar_instagram.py --imagem URL --story
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

# O token é da "Instagram API with Instagram Login" (começa por IGAA) e fala com
# graph.instagram.com, não com graph.facebook.com. Nesse caminho o próprio token já
# identifica a conta, por isso o id pode ser "me".
API = os.environ.get("IG_API", "https://graph.instagram.com/v23.0")
AQUI = os.path.dirname(os.path.abspath(__file__))


def credenciais(caminho):
    if not os.path.exists(caminho):
        raise SystemExit("faltam as credenciais em %s (ver o cabeçalho deste ficheiro)" % caminho)
    if oct(os.stat(caminho).st_mode)[-3:] != "600":
        print("aviso: %s devia estar em modo 600" % caminho, file=sys.stderr)
    d = {}
    for linha in open(caminho, encoding="utf-8"):
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            d[k.strip()] = v.strip()
    for k in ("IG_USER_ID", "IG_TOKEN"):
        if not d.get(k):
            raise SystemExit("falta %s nas credenciais" % k)
    return d


def chamar(metodo, caminho, campos, token):
    campos = dict(campos, access_token=token)
    dados = urllib.parse.urlencode(campos).encode()
    url = "%s/%s" % (API, caminho)
    pedido = (urllib.request.Request(url, data=dados, method="POST") if metodo == "POST"
              else urllib.request.Request(url + "?" + dados.decode(), method="GET"))
    try:
        with urllib.request.urlopen(pedido, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")
        raise SystemExit("a Meta recusou (%s):\n%s" % (e.code, corpo))


def publicar(imagem, legenda, story, cred, seco=False, sem_publicar=False):
    campos = {"image_url": imagem}
    if story:
        campos["media_type"] = "STORIES"          # o story não leva legenda
    elif legenda:
        campos["caption"] = legenda
    if seco:
        print("ensaio, não publica nada")
        print("  conta:   %s" % cred["IG_USER_ID"])
        print("  passo 1: POST /%s/media  %s" % (cred["IG_USER_ID"],
              {k: (v[:60] + "…" if len(v) > 60 else v) for k, v in campos.items()}))
        print("  passo 2: GET  /{contentor}?fields=status_code  até FINISHED")
        print("  passo 3: POST /%s/media_publish  creation_id={contentor}" % cred["IG_USER_ID"])
        return None

    r = chamar("POST", "%s/media" % cred["IG_USER_ID"], campos, cred["IG_TOKEN"])
    contentor = r["id"]
    print("contentor criado: %s" % contentor)

    for _ in range(30):                            # a Meta demora a puxar a imagem
        s = chamar("GET", contentor, {"fields": "status_code,status"}, cred["IG_TOKEN"])
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise SystemExit("a Meta não aceitou a imagem: %s" % s.get("status"))
        time.sleep(3)
    else:
        raise SystemExit("o contentor não ficou pronto a tempo")

    if sem_publicar:
        # o contentor prova que o token, a conta e a imagem estão bem; expira em 24h
        # sozinho e nada aparece no perfil
        print("contentor pronto e não publicado: %s" % contentor)
        return contentor

    r = chamar("POST", "%s/media_publish" % cred["IG_USER_ID"],
               {"creation_id": contentor}, cred["IG_TOKEN"])
    print("publicado: %s" % r["id"])
    return r["id"]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--imagem", required=True, help="URL pública do JPEG")
    p.add_argument("--legenda", default="")
    p.add_argument("--story", action="store_true")
    p.add_argument("--credenciais", default=os.path.join(AQUI, ".credenciais"))
    p.add_argument("--seco", action="store_true", help="mostra os passos e não chama a API")
    p.add_argument("--sem-publicar", action="store_true",
                   help="cria o contentor na Meta e para aí; nada aparece no perfil")
    a = p.parse_args()
    publicar(a.imagem, a.legenda, a.story, credenciais(a.credenciais), a.seco, a.sem_publicar)

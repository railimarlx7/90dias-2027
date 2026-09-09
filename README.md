# 90 dias para 2027

Imagens e publicação automática da série devocional. Os cards são gerados noutro
sítio; aqui só vive o que precisa de estar na internet.

- `imagens/feed/` — 1080×1350, para o feed
- `imagens/story/` — 1080×1920, para os stories
- `calendario.json` — dia, data, ficheiros e legenda de cada um dos 91 dias
- `scripts/` — o que publica
- `registo/` — o que já foi publicado, um ficheiro por dia

A série começa a **3 de outubro de 2026** (dia 90) e acaba a **1 de janeiro de 2027**
(dia 0).

## Porque é público

A API de publicação da Meta não recebe ficheiros: recebe um URL e vai lá buscar a
imagem. Por isso as imagens têm de estar acessíveis. As credenciais **não** estão
aqui — vivem nos *secrets* do repositório, `IG_USER_ID` e `IG_TOKEN`.

## Correr à mão

O workflow tem `workflow_dispatch`: dá para disparar pela aba Actions, escolher o dia
e deixar o ensaio ligado, que cria o contentor na Meta e não publica nada.

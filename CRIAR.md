# O que seria corrido para criar o repositório

Nada disto foi executado. Cada linha está aqui para ser lida antes de ser corrida.

```bash
cd publicar/rascunho-repo

# 1. copiar para cá as imagens e o script de publicação
mkdir -p imagens
cp -R ../../redes/feed  imagens/feed
cp -R ../../redes/story imagens/story
cp ../publicar_instagram.py scripts/

# 2. repositório local
git init -b main
git add .
git commit -m "primeira: imagens, calendário e publicação"

# 3. criar na conta railimarlx7 e enviar
gh repo create 90dias-2027 --public --source=. --push

# 4. ligar o GitHub Pages, que é o que dá o URL público às imagens
gh api -X POST repos/railimarlx7/90dias-2027/pages \
  -f 'source[branch]=main' -f 'source[path]=/'

# 5. guardar as credenciais como secrets (pede o valor, não fica no histórico)
gh secret set IG_USER_ID --repo railimarlx7/90dias-2027
gh secret set IG_TOKEN   --repo railimarlx7/90dias-2027
```

O URL de cada imagem passaria a ser:

    https://railimarlx7.github.io/90dias-2027/imagens/story/dia-90.jpg

Para apagar tudo, se o teste correr mal:

```bash
gh repo delete railimarlx7/90dias-2027 --yes
```

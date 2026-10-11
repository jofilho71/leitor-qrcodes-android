# Leitor PAT — Polo 24

Aplicativo web (arquivo único, sem build) para ler o QR Code oficial do TSE das urnas no navegador do
celular, escolher a operação de cada urna e **publicar a lista** para o ASIdoBem.

🔗 **App publicado:** https://jofilho71.github.io/leitor-qrcodes-android/

Manual da equipe: **[MANUAL.md](MANUAL.md)**. Detalhes para quem mexe no código: **[CLAUDE.md](CLAUDE.md)**.

## Como funciona

```
Celular (este app) ──PUT──► repositório público asidobem-listas: listas/<id>.csv
                              GitHub Actions gera indice.csv (SHA-256)
ASIdoBem ──GET──► https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv
```

Formato das listas: ver `IMPORTACAO_WEB.md` (formato 1). No ASIdoBem: *Site…* → o endereço acima, token em
branco.

## Stack

- `index.html` único (HTML + CSS + JS), sem framework nem build.
- `BarcodeDetector` nativo com fallback `jsQR` via CDN (só QR).
- Publicação pela API de conteúdo do GitHub; sons por Web Audio.

## Configuração (uma vez)

1. Criar o repositório público `jofilho71/asidobem-listas` com o conteúdo de `repositorio-listas/`.
2. Em *Settings → Actions → General*, permitir que workflows tenham permissão de escrita.
3. Gerar, em github.com/settings/tokens, um *fine-grained token* **por aparelho**: só o repositório
   `asidobem-listas`, permissão *Contents: Read and write*, validade máxima.
4. Enviar a cada técnico, em privado: `https://jofilho71.github.io/leitor-qrcodes-android/#cfg=<token>`.
   Para revogar um aparelho, apague o token dele no GitHub. Tokens vencem em até 1 ano.

## Deploy do app

GitHub Pages serve o `index.html` da branch `master`. Um commit local não atualiza o site: é preciso
`git push origin master`; aguarde 1–2 min e recarregue com Ctrl+Shift+R.

## Testes

```bash
python3 -m pip install -r requirements-teste.txt
python3 -m playwright install chromium
python3 -m pytest tests -v
```

# Leitor PAT & BAT — Polo 24

Aplicativo web (single-page, sem build) para ler QR code e código de barras direto do navegador do
celular — câmera ao vivo ou fotos da galeria — e exportar os dados lidos em CSV.

🔗 **App publicado:** https://jofilho71.github.io/leitor-qrcodes-android/

## O que faz

Dois modos de leitura, alternáveis no topo da tela:

- **Bateria**: pareia um QR code (dados da etiqueta) com um código de barras (patrimônio da urna),
  exportando o par em CSV.
- **Inventário**: leitura solta de código de barras de patrimônio (padrão específico da empresa),
  com categoria e nota, sem duplicar leituras na mesma sessão.

Para instruções de uso passo a passo (modos, câmera, exportação, solução de problemas), veja o
**[MANUAL.md](MANUAL.md)**.

## Stack

- Um único arquivo autocontido: `index.html` (HTML + CSS + JS, sem framework, sem `package.json`, sem
  bundler).
- Detecção de código via `BarcodeDetector` nativo do navegador (Shape Detection API), com fallback para
  [`jsQR`](https://github.com/cozmo/jsQR) via CDN quando o navegador não suporta a API nativa (nesse caso,
  só QR code funciona — código de barras linear exige o detector nativo).
- Exportação em CSV (download) e compartilhamento via Web Share API.

Não há dependências instaladas, não há etapa de build — o arquivo é editado e publicado direto.

## Deploy

Hospedado via **GitHub Pages**, servindo `index.html` a partir da branch `master`.

```bash
git add index.html
git commit -m "..."
git push origin master
```

⚠️ **O commit sozinho não atualiza o site** — é preciso dar `push` para o `master` no GitHub. Depois do
push, o GitHub Pages leva 1–2 minutos para reconstruir; se a página parecer não ter mudado, aguarde um
pouco e recarregue com cache limpo (Ctrl+Shift+R).

## Documentação

- **[CLAUDE.md](CLAUDE.md)** — regras de negócio, decisões de design e convenções do código, para quem for
  alterar o app (documentação técnica/de desenvolvimento).
- **[MANUAL.md](MANUAL.md)** — manual de uso para a equipe operacional (Polo 24), em linguagem simples.

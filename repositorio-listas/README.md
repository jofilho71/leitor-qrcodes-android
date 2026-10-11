# asidobem-listas

Listas de patrimônio de urnas publicadas pelo leitor de QR Codes
(https://jofilho71.github.io/leitor-qrcodes-android/) e coletadas pelo ASIdoBem.

- `listas/<id>.csv` — uma lista por coleta, formato 1 (ver `IMPORTACAO_WEB.md` no projeto do ASIdoBem).
  Só são criadas pelo leitor; nunca editadas.
- `indice.csv` — gerado automaticamente pelo workflow `indice` (não editar à mão). Listas inválidas ficam de
  fora; o motivo aparece no log da execução (aba Actions).

**Endereço para o ASIdoBem** (*Site…*, token em branco):

    https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv

O cache do GitHub pode atrasar a chegada de uma lista em alguns minutos.

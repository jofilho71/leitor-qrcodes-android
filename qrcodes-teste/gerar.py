"""Gera 50 QR codes de teste no padrão do QR de patrimônio do TSE (só para testar o leitor).

Uso: python3 gerar.py   -> folha-1.png … folha-5.png (10 QRs cada) e lista.txt
Conteúdo: APLC:TSE APLF:QRC.PATR VERE:1 TPEQ:UE MDEQ:UE2020 IDEQ:<8 dígitos começando com 51>
"""
import pathlib
import random

import qrcode
from PIL import Image, ImageDraw, ImageFont

pasta = pathlib.Path(__file__).resolve().parent
random.seed(24)
ideqs = sorted(random.sample(range(51250000, 51260000), 50))
(pasta / "lista.txt").write_text("\n".join(str(i) for i in ideqs) + "\n")

try:
    fonte = ImageFont.truetype("DejaVuSansMono.ttf", 34)
except OSError:
    fonte = ImageFont.load_default()

COLS, LINHAS, CEL_L, CEL_A = 2, 5, 560, 560
for n in range(5):
    folha = Image.new("RGB", (COLS * CEL_L, LINHAS * CEL_A), "white")
    desenho = ImageDraw.Draw(folha)
    for k, ideq in enumerate(ideqs[n * 10:(n + 1) * 10]):
        conteudo = f"APLC:TSE APLF:QRC.PATR VERE:1 TPEQ:UE MDEQ:UE2020 IDEQ:{ideq}"
        qr = qrcode.QRCode(border=4, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(conteudo)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((470, 470))
        x, y = (k % COLS) * CEL_L + 45, (k // COLS) * CEL_A + 10
        folha.paste(img, (x, y))
        desenho.text((x + 140, y + 480), str(ideq), fill="black", font=fonte)
    folha.save(pasta / f"folha-{n + 1}.png")
print("ok:", len(ideqs), "QRs")

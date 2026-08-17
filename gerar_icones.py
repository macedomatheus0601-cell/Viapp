"""
Gera os icones PNG do PWA sem depender de biblioteca de imagem.

Escreve PNG na mao (zlib + struct, ambos da biblioteca padrao) e desenha
com supersampling 4x para as bordas sairem suaves.

Rodar quando o desenho mudar:  python gerar_icones.py
Nao faz parte da coleta diaria — o GitHub Actions nao executa este arquivo.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

SAIDA = Path("icones")

FUNDO = (15, 23, 42)      # #0f172a — mesmo --fundo escuro do site
# Altura como fracao da area util: 1.0 encosta na margem de cima. Sem isso
# o desenho fica concentrado embaixo e some quando o icone e exibido pequeno.
BARRAS = [
    (0.46, (122, 162, 255)),   # #7aa2ff — azul de acento
    (0.72, (122, 162, 255)),
    (1.00, (74, 222, 128)),    # #4ade80 — verde do consenso 3/3
]

AMOSTRAS = 4              # subpixels por eixo


def grava_png(caminho: Path, largura: int, altura: int, linhas) -> None:
    """linhas: sequencia de linhas, cada uma com (r, g, b) por pixel."""
    cru = b"".join(
        b"\x00" + bytes(canal for px in linha for canal in px) for linha in linhas
    )

    def bloco(tipo: bytes, dados: bytes) -> bytes:
        corpo = tipo + dados
        return (struct.pack(">I", len(dados)) + corpo
                + struct.pack(">I", zlib.crc32(corpo) & 0xFFFFFFFF))

    cabecalho = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)  # RGB 8 bits
    caminho.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + bloco(b"IHDR", cabecalho)
        + bloco(b"IDAT", zlib.compress(cru, 9))
        + bloco(b"IEND", b"")
    )


def dentro_retangulo(x, y, x0, y0, x1, y1, raio) -> bool:
    """Retangulo de cantos arredondados, em coordenadas de 0 a 1."""
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    for cx, cy in ((x0 + raio, y0 + raio), (x1 - raio, y0 + raio),
                   (x0 + raio, y1 - raio), (x1 - raio, y1 - raio)):
        perto_x = x < x0 + raio if cx == x0 + raio else x > x1 - raio
        perto_y = y < y0 + raio if cy == y0 + raio else y > y1 - raio
        if perto_x and perto_y:
            return (x - cx) ** 2 + (y - cy) ** 2 <= raio ** 2
    return True


def cor_em(x: float, y: float, margem: float, raio_fundo: float):
    """Cor do ponto (x, y), ambos de 0 a 1. None = transparente/fora."""
    if not dentro_retangulo(x, y, 0, 0, 1, 1, raio_fundo):
        return None

    base = 1 - margem            # linha de base das barras
    largura = (1 - 2 * margem - 2 * 0.045) / 3
    inicio = margem

    for i, (altura, cor) in enumerate(BARRAS):
        bx0 = inicio + i * (largura + 0.045)
        bx1 = bx0 + largura
        by0 = base - altura * (1 - 2 * margem)
        if dentro_retangulo(x, y, bx0, by0, bx1, base, min(0.022, largura / 2)):
            return cor

    return FUNDO


def desenha(tamanho: int, margem: float, raio_fundo: float) -> list:
    """Renderiza em AMOSTRAS x e reduz, para as bordas nao ficarem serrilhadas."""
    linhas = []
    passo = 1.0 / (tamanho * AMOSTRAS)

    for py in range(tamanho):
        linha = []
        for px in range(tamanho):
            r = g = b = 0
            for sy in range(AMOSTRAS):
                for sx in range(AMOSTRAS):
                    x = (px * AMOSTRAS + sx + 0.5) * passo
                    y = (py * AMOSTRAS + sy + 0.5) * passo
                    c = cor_em(x, y, margem, raio_fundo) or FUNDO
                    r += c[0]; g += c[1]; b += c[2]
            n = AMOSTRAS * AMOSTRAS
            linha.append((r // n, g // n, b // n))
        linhas.append(linha)
    return linhas


def main() -> None:
    SAIDA.mkdir(exist_ok=True)

    # icone comum: cantos arredondados, desenho ocupando bem a area
    for tam in (192, 512):
        grava_png(SAIDA / f"icone-{tam}.png", tam, tam, desenha(tam, 0.20, 0.20))
        print(f"  icones/icone-{tam}.png")

    # maskable: o Android recorta em circulo, entao o desenho precisa caber
    # na zona segura central (~80%). Fundo quadrado, sem cantos arredondados.
    grava_png(SAIDA / "icone-512-mascara.png", 512, 512, desenha(512, 0.30, 0.0))
    print("  icones/icone-512-mascara.png")

    # atalho da tela inicial do iOS
    grava_png(SAIDA / "icone-180.png", 180, 180, desenha(180, 0.20, 0.20))
    print("  icones/icone-180.png")


if __name__ == "__main__":
    main()

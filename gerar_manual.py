"""
Gera o manual explicativo do site em PDF.

Le dados/atual.json para que os exemplos numericos sejam sempre os da
ultima coleta, em vez de numeros escritos a mao que envelhecem.

Depende do reportlab, que nao entra no requirements.txt de proposito:
a coleta diaria no GitHub Actions nao gera PDF e nao deve instalar isso.

    pip install reportlab
    python gerar_manual.py   ->   Manual-Ranking-B3.pdf

Nota sobre acentos: as fontes padrao do reportlab (Helvetica) cobrem todo
o portugues, incluindo travessao e aspas tipograficas. So o "e" comercial
precisa virar &amp;, porque o texto passa por um interpretador de marcacao.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

# ----------------------------------------------------------------- paleta

TINTA       = colors.HexColor("#16202e")
TINTA_FRACA = colors.HexColor("#5b6b80")
NAVY        = colors.HexColor("#0f172a")
AZUL        = colors.HexColor("#1d4ed8")
AZUL_CLARO  = colors.HexColor("#eef2ff")
VERDE       = colors.HexColor("#047857")
VERDE_BG    = colors.HexColor("#ecfdf5")
AMBAR       = colors.HexColor("#92400e")
AMBAR_BG    = colors.HexColor("#fffbeb")
CINZA       = colors.HexColor("#e2e6ec")
CINZA_BG    = colors.HexColor("#f6f7f9")

def _pc(v): return f"{v*100:.2f}%".replace(".", ",")
def _mx(v): return f"{v:.2f}x".replace(".", ",")
FMT_FATOR = {"roic": _pc, "cresc": _pc, "mrgeb": _pc, "evebitda": _mx, "div": _mx}

LARGURA, ALTURA = A4
MARGEM = 20 * mm
UTIL = LARGURA - 2 * MARGEM

# ----------------------------------------------------------------- estilos

_base = getSampleStyleSheet()

E = {
    "corpo": ParagraphStyle("corpo", parent=_base["Normal"], fontName="Helvetica",
                            fontSize=9.5, leading=14.5, textColor=TINTA,
                            alignment=TA_JUSTIFY, spaceAfter=7),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21,
                         textColor=NAVY, spaceBefore=4, spaceAfter=3),
    "h1num": ParagraphStyle("h1num", fontName="Helvetica-Bold", fontSize=9,
                            textColor=AZUL, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                         textColor=NAVY, spaceBefore=13, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=9.8, leading=13,
                         textColor=AZUL, spaceBefore=9, spaceAfter=3),
    "lista": ParagraphStyle("lista", parent=_base["Normal"], fontName="Helvetica",
                            fontSize=9.5, leading=14, textColor=TINTA,
                            leftIndent=11, bulletIndent=2, spaceAfter=4),
    "cx": ParagraphStyle("cx", fontName="Helvetica", fontSize=9, leading=13.5,
                         textColor=TINTA, alignment=TA_JUSTIFY),
    "cel": ParagraphStyle("cel", fontName="Helvetica", fontSize=8.3, leading=11.5,
                          textColor=TINTA),
    "celb": ParagraphStyle("celb", fontName="Helvetica-Bold", fontSize=8.3,
                           leading=11.5, textColor=TINTA),
    "celc": ParagraphStyle("celc", fontName="Helvetica-Bold", fontSize=8.3,
                           leading=11.5, textColor=colors.white),
    "nota": ParagraphStyle("nota", fontName="Helvetica-Oblique", fontSize=8.3,
                           leading=12, textColor=TINTA_FRACA, spaceAfter=7),
    "capa_t": ParagraphStyle("capa_t", fontName="Helvetica-Bold", fontSize=30,
                             leading=35, textColor=colors.white, alignment=TA_CENTER),
    "capa_s": ParagraphStyle("capa_s", fontName="Helvetica", fontSize=12.5,
                             leading=18, textColor=colors.HexColor("#94a3b8"),
                             alignment=TA_CENTER),
    "capa_p": ParagraphStyle("capa_p", fontName="Helvetica", fontSize=9.5,
                             leading=14, textColor=colors.HexColor("#cbd5e1"),
                             alignment=TA_CENTER),
}

# ------------------------------------------------------------- atalhos

def P(t, e="corpo"):
    return Paragraph(t, E[e])


def _regua(cor=AZUL, esp=1.6):
    t = Table([[""]], colWidths=[UTIL], rowHeights=[esp])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), cor)]))
    return t


def H1(numero, titulo):
    return KeepTogether([
        Spacer(1, 4), P(f"PARTE {numero}", "h1num"), P(titulo, "h1"),
        _regua(), Spacer(1, 5),
    ])


def H2(t):
    return P(t, "h2")


def H3(t):
    return P(t, "h3")


def LI(itens):
    return [Paragraph(f"&#8226;&nbsp;&nbsp;{i}", E["lista"]) for i in itens]


def NUM(itens):
    return [Paragraph(f"<b>{n}.</b>&nbsp;&nbsp;{i}", E["lista"])
            for n, i in enumerate(itens, 1)]


def caixa(titulo, texto, cor=AZUL, fundo=AZUL_CLARO):
    """Bloco destacado com barra lateral colorida."""
    interno = []
    if titulo:
        interno.append(Paragraph(
            f'<font color="#{cor.hexval()[2:]}"><b>{titulo}</b></font>', E["cx"]))
        interno.append(Spacer(1, 3))
    interno.append(Paragraph(texto, E["cx"]))

    t = Table([[interno]], colWidths=[UTIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fundo),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, cor),
        ("BOX", (0, 0), (-1, -1), 0.4, CINZA),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 8)])


def alerta(titulo, texto):
    return caixa(titulo, texto, AMBAR, AMBAR_BG)


def bom(titulo, texto):
    return caixa(titulo, texto, VERDE, VERDE_BG)


def tabela(cabecalho, linhas, larguras, alinhar_dir=()):
    """Tabela com cabecalho navy e zebra."""
    dados = [[Paragraph(c, E["celc"]) for c in cabecalho]]
    for ln in linhas:
        dados.append([c if isinstance(c, Paragraph) else Paragraph(str(c), E["cel"])
                      for c in ln])

    est = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(dados)):
        if i % 2 == 0:
            est.append(("BACKGROUND", (0, i), (-1, i), CINZA_BG))
    for c in alinhar_dir:
        est.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))

    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle(est))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 9)])


# ------------------------------------------------------------ paginacao

def _logo(c, x, y, lado):
    """Tres barras ascendentes — o mesmo desenho do icone do app."""
    c.saveState()
    c.setFillColor(NAVY)
    c.roundRect(x, y, lado, lado, lado * 0.2, stroke=0, fill=1)
    marg = lado * 0.22
    larg = (lado - 2 * marg - 2 * lado * 0.045) / 3
    base = y + marg
    for i, (frac, cor) in enumerate([
            (0.46, colors.HexColor("#7aa2ff")),
            (0.72, colors.HexColor("#7aa2ff")),
            (1.00, colors.HexColor("#4ade80"))]):
        c.setFillColor(cor)
        alt = frac * (lado - 2 * marg)
        c.roundRect(x + marg + i * (larg + lado * 0.045), base, larg, alt,
                    min(lado * 0.03, larg / 2), stroke=0, fill=1)
    c.restoreState()


def capa(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, LARGURA, ALTURA, stroke=0, fill=1)
    _logo(c, LARGURA / 2 - 21 * mm, ALTURA - 78 * mm, 42 * mm)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(MARGEM, 34 * mm, UTIL, 0.6, stroke=0, fill=1)
    c.restoreState()


def miolo(c, doc):
    c.saveState()
    _logo(c, MARGEM, ALTURA - MARGEM + 2 * mm, 7 * mm)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TINTA_FRACA)
    c.drawString(MARGEM + 10 * mm, ALTURA - MARGEM + 4 * mm,
                 "Ranking de Qualidade  —  B3")
    c.setFillColor(CINZA)
    c.rect(MARGEM, ALTURA - MARGEM, UTIL, 0.5, stroke=0, fill=1)
    c.rect(MARGEM, MARGEM - 5 * mm, UTIL, 0.5, stroke=0, fill=1)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TINTA_FRACA)
    c.drawString(MARGEM, MARGEM - 9 * mm, "Não é recomendação de investimento")
    c.drawRightString(LARGURA - MARGEM, MARGEM - 9 * mm, str(doc.page))
    c.restoreState()


# ------------------------------------------------------------- conteudo

def constroi(d) -> list:
    m = d["meta"]
    acoes = d["acoes"]
    n = m["elegiveis"]
    tres = [a["papel"] for a in acoes if a["consenso"] == 3]
    plpl = next(a for a in acoes if a["papel"] == "PLPL3")
    data = m["coletado_em"][:10]
    data_br = f"{data[8:10]}/{data[5:7]}/{data[0:4]}"

    # Posicoes e empates sao CALCULADOS da coleta, nunca escritos a mao: o manual
    # e regerado a cada coleta nova e numeros fixos passariam a mentir no dia
    # seguinte. Mesma convencao do scraper: empate recebe a media das posicoes.
    DIR_FATOR = {"roic": "hi", "cresc": "hi", "evebitda": "lo",
                 "mrgeb": "hi", "div": "lo"}

    def _ordenados(chave):
        return sorted((a[chave] for a in acoes if a[chave] is not None),
                      reverse=(DIR_FATOR[chave] == "hi"))

    def posicao(chave, papel):
        alvo = next(a[chave] for a in acoes if a["papel"] == papel)
        idx = [i for i, v in enumerate(_ordenados(chave)) if v == alvo]
        return sum(idx) / len(idx) + 1

    def ordinal(x):
        return f"{int(x)}o" if float(x).is_integer() else f"{x:.1f}o".replace(".", ",")

    def acha_empate(papel):
        """Fator em que o papel divide valor com mais gente. None se nao houver."""
        melhor = None
        for chave in DIR_FATOR:
            alvo = next(a[chave] for a in acoes if a["papel"] == papel)
            if alvo is None:
                continue
            grupo = sorted(a["papel"] for a in acoes if a[chave] == alvo)
            if len(grupo) < 2:
                continue
            pos = [i + 1 for i, v in enumerate(_ordenados(chave)) if v == alvo]
            if melhor is None or len(grupo) > len(melhor[1]):
                melhor = (chave, grupo, alvo, pos)
        return melhor

    S = []
    add = S.append      # um flowable
    addm = S.extend     # varios de uma vez (listas com marcador)

    # ---------------------------------------------------------------- capa
    add(Spacer(1, 88 * mm))
    add(P("Ranking de Qualidade", "capa_t"))
    add(P("B3", "capa_t"))
    add(Spacer(1, 8 * mm))
    add(P("Manual completo: como o score é calculado,<br/>"
          "como navegar e como analisar", "capa_s"))
    add(Spacer(1, 52 * mm))
    add(P("macedomatheus0601-cell.github.io/Viapp", "capa_p"))
    add(Spacer(1, 3 * mm))
    add(P(f"Exemplos numéricos da coleta de {data_br}", "capa_p"))
    add(Spacer(1, 14 * mm))
    add(P("<b>Este documento não é recomendação de investimento.</b>", "capa_p"))

    add(NextPageTemplate("miolo"))
    add(PageBreak())

    # ------------------------------------------------------------- sumario
    add(P("Sumário", "h1"))
    add(_regua())
    add(Spacer(1, 7))

    sumario = [
        ("1", "O que é este site", "O problema, o que é, o que não é"),
        ("2", "Como acessar", "Navegador, celular, offline, código-fonte"),
        ("3", "De onde vêm os números", "A fonte, o ciclo diário, as duas defasagens"),
        ("4", "O funil: de 987 a 153", "Cada corte e por que bancos ficam de fora"),
        ("5", "O score", "O cálculo completo, passo a passo, com exemplo real"),
        ("6", "Os três esquemas e o consenso", "Por que três rankings ao mesmo tempo"),
        ("7", "Guia da página", "Cada aba, cada coluna, cada marca visual"),
        ("8", "Glossário dos 16 indicadores", "O que é, como ler, onde engana"),
        ("9", "Como analisar na prática", "Um fluxo de trabalho e os erros comuns"),
        ("10", "Limitações e perguntas frequentes", "O que este sistema não faz"),
    ]
    add(tabela(
        ["", "Parte", "Conteúdo"],
        [[Paragraph(f"<b>{a}</b>", E["celb"]), Paragraph(f"<b>{b}</b>", E["celb"]),
          Paragraph(c, E["cel"])] for a, b, c in sumario],
        [14 * mm, 62 * mm, UTIL - 76 * mm]))

    add(caixa("Como usar este manual",
              "As partes 1 a 4 explicam de onde vem tudo e podem ser lidas por qualquer "
              "pessoa. A parte 5 é o núcleo técnico: é lá que o score é destrinchado. "
              "A parte 7 funciona como referência de consulta enquanto você navega, e "
              "a parte 8 é um dicionário para voltar sempre que um indicador aparecer."))

    add(PageBreak())

    # =============================================================== PARTE 1
    add(H1(1, "O que é este site"))

    add(H2("O problema que ele resolve"))
    add(P(f"A B3 tem cerca de {m['papeis_lidos']} papéis negociados. Nenhuma pessoa "
          "consegue analisar todos, e a maioria das listas de ações por aí ordena por um "
          "critério só: as que mais pagam dividendo, as de menor preço sobre lucro, as "
          "mais negociadas. Cada uma dessas listas responde a uma pergunta estreita."))
    add(P("Este site responde a uma pergunta mais completa: <b>quais empresas combinam "
          "boa rentabilidade, crescimento e alavancagem controlada sem estar caras?</b> "
          "E, mais importante, responde de um jeito que pode ser auditado — cada número "
          "pode ser rastreado até a fonte, e cada decisão do método está escrita."))

    add(H2("O que ele é"))
    addm(LI([
        "<b>Uma ferramenta de triagem.</b> Ela reduz centenas de papéis a uma lista "
        "curta que vale a pena estudar a fundo. Nada mais que isso.",
        "<b>Um sistema transparente.</b> Todos os filtros, pesos e fórmulas estão "
        "declarados. Não há caixa-preta nem critério escondido.",
        "<b>Um retrato diário.</b> A cada dia às 22h de Brasília o sistema recoleta "
        "tudo e regrava os números, sozinho.",
        "<b>Público e gratuito.</b> Sem cadastro, sem login, sem cobrança.",
    ]))

    add(H2("O que ele não é"))
    add(alerta("Leia esta parte antes de qualquer número",
               "<b>Isto não é recomendação de investimento.</b> Nenhum número aqui "
               "considera seus objetivos, seu prazo, sua tolerância a risco ou sua "
               "situação financeira.<br/><br/>"
               "<b>Isto não é backtest.</b> Os pesos escolhidos são plausíveis do ponto "
               "de vista teórico, mas nunca foram testados contra o histórico. Não existe "
               "evidência de que produzam retorno superior ao mercado. Uma empresa em "
               "primeiro lugar não é uma empresa que vai subir.<br/><br/>"
               "<b>Isto não é análise.</b> O score lê cinco números contábeis. Ele não "
               "sabe quem dirige a empresa, se há processo judicial relevante, se o setor "
               "está prestes a mudar por regulação, ou se o último balanço tem alguma "
               "exceção contábil. Nada disso cabe numa fórmula."))

    add(H2("Para que serve, então"))
    add(P("Para o passo que vem antes da análise. Em vez de começar a estudar empresas ao "
          "acaso ou por indicação de terceiros, você começa por uma lista curta de "
          "empresas que passaram por critérios objetivos e explícitos. O trabalho de "
          "verdade — ler balanço, entender o negócio, avaliar a diretoria — continua "
          "sendo seu."))

    add(bom("Uma analogia útil",
            "O score funciona como a triagem de um pronto-socorro: ele não diagnostica "
            "ninguém, só organiza a fila para o médico olhar primeiro quem parece mais "
            "urgente. Confundir triagem com diagnóstico é o erro mais caro que se pode "
            "cometer com esta ferramenta."))

    add(PageBreak())

    # =============================================================== PARTE 2
    add(H1(2, "Como acessar"))

    add(P("O site é uma página pública na internet. Não tem login, não está em loja de "
          "aplicativos e não exige instalação. Existem quatro formas de chegar nele."))

    add(H2("1. Pelo navegador, em qualquer aparelho"))
    add(caixa(None, '<font size="12"><b>macedomatheus0601-cell.github.io/Viapp</b></font>'))
    add(P("Funciona em Chrome, Firefox, Edge e Safari, no computador ou no celular. "
          "O endereço pode ser compartilhado com qualquer pessoa e vai abrir igual."))

    add(H2("2. Instalado como aplicativo"))
    add(P("O site é um PWA, sigla para aplicativo web progressivo. Na prática: ele pode "
          "ser instalado como se fosse um app, ganhando ícone próprio e abrindo sem a "
          "barra do navegador."))
    add(tabela(
        ["Aparelho", "Como instalar"],
        [["Android", "Abra no Chrome, toque no menu de três pontos e escolha "
                     "<b>Instalar app</b> (ou Adicionar à tela inicial)"],
         ["iPhone / iPad", "Abra no <b>Safari</b> (só funciona nele), toque no botão de "
                           "compartilhar e escolha <b>Adicionar à Tela de Início</b>"],
         ["Windows / Mac", "Abra no Chrome ou Edge; aparece um ícone de instalar na "
                           "barra de endereço"]],
        [34 * mm, UTIL - 34 * mm]))
    add(P("É a mesma página, apenas embrulhada. Não existe versão diferente para celular: "
          "o layout se reorganiza conforme a <b>largura da tela</b>, e por isso a tabela "
          "do ranking vira uma lista de cartões no celular."))

    add(H2("3. Sem internet"))
    add(P("Depois da primeira visita, o conteúdo fica guardado no aparelho. Sem sinal, o "
          "site abre normalmente com o último retrato baixado. Uma faixa avisa que você "
          "está offline, e a data da coleta no topo mostra de quando são os números."))

    add(H2("4. O código-fonte"))
    add(P("Todo o código está público em <b>github.com/macedomatheus0601-cell/Viapp</b>. "
          "Qualquer pessoa pode conferir se o que este manual afirma é o que o programa "
          "realmente faz. Essa é a diferença entre transparência declarada e "
          "transparência verificável."))

    add(PageBreak())

    # =============================================================== PARTE 3
    add(H1(3, "De onde vêm os números"))

    add(H2("Uma fonte única: o Fundamentus"))
    add(P("Todos os dados vêm de uma única página pública do site Fundamentus, que reúne "
          "os indicadores fundamentalistas das empresas listadas. O sistema lê essa "
          "tabela uma vez por dia."))
    add(P("<b>Um ponto que costuma surpreender:</b> o site não calcula indicadores como "
          "P/L, P/VP ou EV/EBITDA. O Fundamentus já os publica prontos, e o programa "
          "apenas lê o valor da célula. A única matemática feita aqui é a das notas "
          "percentis e dos três scores — que é o assunto da Parte 5."))

    add(H2("O ciclo diário"))
    add(tabela(
        ["Etapa", "O que acontece"],
        [["<b>22h</b> (Brasília)", "Um computador temporário é ligado automaticamente"],
         ["", "Lê a tabela do Fundamentus (uma única requisição)"],
         ["", "Aplica os filtros de elegibilidade"],
         ["", "Calcula os percentis e os três scores"],
         ["", "Grava os arquivos de dados e os publica"],
         ["", "A máquina é desligada; o site já está atualizado"]],
        [30 * mm, UTIL - 30 * mm]))
    add(P("O horário não é arbitrário: o pregão fecha por volta das 18h, e às 22h os "
          "dados de fechamento já estão consolidados. Ninguém precisa fazer nada — se "
          "você nunca mais abrir o computador, o site continua atualizando."))

    add(H2("As duas defasagens"))
    add(P("Nenhum número aqui é ao vivo, e é importante entender exatamente o quanto ele "
          "está atrasado. São duas defasagens de tamanhos bem diferentes:"))
    add(tabela(
        ["", "Defasagem 1: o preço", "Defasagem 2: os fundamentos"],
        [["Tamanho", "<b>Até 1 dia</b>", "<b>Até 1 trimestre</b>"],
         ["Origem", "O preço exibido é o último fechamento, não a cotação ao vivo",
          "Lucro, patrimônio e receita vêm do último balanço publicado"],
         ["Efeito", "Se a ação subir 5% amanhã de manhã, os múltiplos ficam 5% "
                    "desatualizados até as 22h",
          "Uma empresa que teve prejuízo em setembro segue exibindo o patrimônio "
          "de junho por três meses"],
         ["Dá para evitar?", "Só com uma fonte de cotação em tempo real, que custa "
                             "dinheiro e exigiria servidor",
          "Não. É o ritmo com que as empresas divulgam resultados"]],
        [22 * mm, (UTIL - 22 * mm) / 2, (UTIL - 22 * mm) / 2]))

    add(alerta("A defasagem que realmente distorce é a segunda",
               "A intuição manda se preocupar com o preço, que muda a cada segundo. Mas "
               "repare na estrutura de um múltiplo como o P/VP: o numerador (preço) muda "
               "todo dia; o denominador (valor patrimonial) muda a cada três meses. "
               "A defasagem grande está embaixo, não em cima — e existiria igual mesmo "
               "com cotação em tempo real."))

    add(H2("Por que isso machuca pouco este projeto"))
    addm(NUM([
        "<b>O ranking é relativo, não absoluto.</b> A nota não vem do valor bruto do "
        "indicador, e sim da posição dele em relação aos outros. Num dia de queda "
        "generalizada, a bolsa inteira fica mais barata junto e as posições quase não "
        "mudam. Uma defasagem que desloca todo mundo na mesma direção praticamente "
        "desaparece quando você ordena.",
        "<b>A ferramenta é de triagem, não de execução.</b> Nenhuma decisão de compra "
        "deveria sair do número exibido aqui. Para triar, o fechamento de ontem serve; "
        "para apertar o botão de comprar, usa-se a cotação ao vivo da corretora.",
    ]))

    add(H2("Não há conexão com a B3"))
    add(P("O sistema nunca fala com a bolsa. O Fundamentus é a única fonte, e isso é uma "
          "dependência real: se ele sair do ar, ficar desatualizado ou mudar o formato da "
          "página, o sistema para junto. O programa foi escrito para <b>falhar com "
          "mensagem clara</b> nesse caso, em vez de gravar dado errado silenciosamente — "
          "mas falha."))
    add(P("A alternativa seria a API oficial da B3 ou um provedor de dados pago. Ambas "
          "custam dinheiro e exigiriam um servidor no ar, o que quebraria as duas regras "
          "do projeto: custo zero e sem servidor."))

    add(bom("Por isso a data fica em destaque",
            "A data da última coleta aparece no alto de todas as telas, e não escondida "
            "num rodapé. Se passar de três dias sem atualizar, a caixa muda de cor e "
            "passa a mostrar há quantos dias o dado está parado. Ela é a declaração "
            "honesta da idade daquilo que você está lendo — e o primeiro lugar para "
            "olhar sempre que abrir o site."))

    add(PageBreak())

    # =============================================================== PARTE 4
    add(H1(4, "O funil: de 987 a 153"))

    add(P(f"Na coleta de {data_br}, o sistema leu <b>{m['papeis_lidos']} papéis</b> e "
          f"aprovou <b>{n}</b>. Foram eliminados {m['papeis_lidos'] - n}. Esta parte "
          "explica por que cada um saiu."))

    add(H2("O princípio: filtro elimina, score não pune"))
    add(P("Esta é a decisão de projeto mais importante depois dos pesos, e vale entender "
          "bem. Existiam duas formas de tratar uma empresa inadequada:"))
    addm(LI([
        "<b>Deixar entrar e dar nota baixa.</b> Parece mais suave, mas cria um problema: "
        "uma empresa péssima num critério poderia compensar com os outros quatro e "
        "aparecer no meio da tabela, como se aquela posição significasse alguma coisa.",
        "<b>Eliminar antes de pontuar.</b> A empresa simplesmente não é avaliada. É a "
        "resposta honesta quando o método não se aplica.",
    ]))
    add(P("O sistema faz o segundo. E há um efeito colateral importante: como a nota de "
          "cada empresa depende de quem está na amostra, deixar entrar quem não deveria "
          "distorceria a nota de <b>todo mundo</b>, não só a do intruso."))

    add(H2("Os cortes, na ordem em que são aplicados"))
    elim = m["eliminados_por_motivo"]
    add(tabela(
        ["#", "Corte", "Papéis", "Por quê"],
        [["1", "Banco, seguradora ou holding financeira",
          f"<b>{elim.get('banco, seguradora ou holding', 0)}</b>",
          "O score não se aplica a eles (ver adiante)"],
         ["2", f"Liquidez abaixo de R$ {m['corte_liquidez']:,.0f}/dia".replace(",", "."),
          f"<b>{elim.get('liquidez abaixo do corte', 0)}</b>",
          "Preço de ativo que quase não negocia não reflete valor — e você pode não "
          "conseguir vender sem derrubar a cotação"],
         ["3", "EV/EBITDA nulo ou negativo",
          f"<b>{elim.get('EV/EBITDA nulo ou negativo', 0)}</b>",
          "EBITDA negativo é empresa queimando caixa na operação. Um múltiplo negativo "
          "seria ordenado como <i>a mais barata de todas</i>, o que é absurdo"],
         ["4", "Patrimônio líquido negativo",
          f"<b>{elim.get('patrimonio liquido negativo', 0)}</b>",
          "As dívidas superam os ativos contábeis"],
         ["5", "Margem EBIT e ROIC ambos zerados", "0",
          "Normalmente indica dado ausente na fonte, não empresa com resultado zero"],
         ["6", "Qualquer fator faltando", "0",
          "Sem os cinco indicadores não há como calcular o score"],
         ["7", "Classe menos líquida do mesmo emissor",
          f"<b>{elim.get('outra classe do mesmo emissor e mais liquida', 0)}</b>",
          "Evita a mesma empresa aparecer duas ou três vezes (ON, PN e UNIT) e ocupar "
          "várias posições do ranking"]],
        [8 * mm, 46 * mm, 15 * mm, UTIL - 69 * mm], alinhar_dir=(2,)))

    add(P("A ordem importa: cada papel recebe o motivo do <b>primeiro</b> corte em que "
          "esbarra. Por isso os números somam exatamente o total eliminado, sem "
          "contagem dupla."))
    add(P("O corte de liquidez sozinho responde por quase todo o funil, e isso é "
          "esperado: a bolsa brasileira tem uma cauda enorme de papéis que praticamente "
          "não negociam."))

    add(H2("Por que bancos e seguradoras ficam de fora"))
    add(P("Esta é a pergunta mais frequente, e a resposta não é um julgamento sobre a "
          "qualidade dessas empresas. <b>É que três dos cinco indicadores do score não "
          "significam nada quando aplicados a uma instituição financeira.</b>"))
    add(P("Vale ver o tamanho do que foi cortado — estes não saíram por falta de "
          "liquidez, muito pelo contrário:"))
    add(tabela(
        ["Papel", "Volume negociado por dia"],
        [["ITUB4 (Itaú)", "R$ 938 milhões"],
         ["BBDC4 (Bradesco)", "R$ 569 milhões"],
         ["BPAC11 (BTG)", "R$ 569 milhões"],
         ["BBAS3 (Banco do Brasil)", "R$ 393 milhões"],
         ["ITSA4 (Itaúsa)", "R$ 364 milhões"]],
        [50 * mm, UTIL - 50 * mm], alinhar_dir=(1,)))
    add(P("O ITUB4 é uma das ações mais negociadas do país inteiro. Ele não saiu por ser "
          "pequeno — saiu porque o score não sabe medir banco. Onde exatamente quebra:"))

    add(H3("EV/EBITDA (peso 20%) — perde o sentido"))
    add(P("O EV soma o valor de mercado com a <b>dívida líquida</b>. Para uma empresa "
          "comum, dívida é como ela se financiou. Para um banco, dívida é a "
          "<b>matéria-prima</b>: os depósitos que os clientes deixam na conta são passivo "
          "do banco, e é com isso que ele opera. Calcular dívida líquida de um banco "
          "produz um número gigantesco que não descreve nada."))
    add(P("O EBITDA é pior. Ele significa lucro <b>antes dos juros</b>. Mas juros são a "
          "receita de um banco. Tirar os juros do resultado de um banco é apagar o "
          "negócio inteiro e olhar o que sobrou."))

    add(H3("Dívida Líquida / Patrimônio (peso 15%) — inverte"))
    add(P("Aqui o indicador não apenas perde sentido: ele passa a medir o contrário. "
          "Banco é alavancado por natureza e por regulação — opera com várias vezes o "
          "próprio patrimônio, e isso é o modelo de negócio, não um defeito. No score, "
          "menor é melhor. Um banco pouco alavancado não é seguro; é ineficiente. O "
          "indicador premiaria exatamente o oposto do que deveria."))

    add(H3("ROIC (peso 30%) — mede outra coisa"))
    add(P("Capital investido pressupõe fábrica, estoque, capital de giro. Num banco o que "
          "existe é capital regulatório, definido por regras do Banco Central. O número "
          "até sai, mas não é comparável com o de uma indústria."))

    add(alerta("Somando: 65% do peso do score fica sem significado",
               "Não é que o banco tiraria nota baixa — é que a nota não estaria medindo o "
               "que diz medir. Avaliar banco exige outros indicadores: índice de "
               "Basileia, índice de eficiência, inadimplência, margem financeira, "
               "provisões. Seria outro modelo, não um ajuste neste.<br/><br/>"
               "As holdings entram na mesma lógica por tabela: o resultado delas é o "
               "lucro das empresas em que investem, então margem e ROIC refletem "
               "contabilidade de participação, não uma operação própria."))

    add(PageBreak())

    # =============================================================== PARTE 5
    add(H1(5, "O score"))
    add(P("Esta é a parte central do manual. Se você só puder ler uma seção, leia esta.",
          "nota"))

    add(H2("O problema: somar coisas que não se somam"))
    add(P("Queremos combinar cinco indicadores num número só. A tentativa ingênua seria "
          "multiplicar cada um pelo seu peso e somar. Mas veja o que acontece:"))
    add(tabela(
        ["Indicador", "Faixa típica na bolsa", "Problema"],
        [["ROIC", "de -30% a 60%", "valores entre -0,30 e 0,60"],
         ["Cresc. Receita 5a", "de -20% a 80%", "valores entre -0,20 e 0,80"],
         ["EV/EBITDA", "de 0,7 a mais de 100", "valores até 150 vezes maiores"],
         ["Margem EBIT", "de 1% a 70%", "valores entre 0,01 e 0,70"],
         ["Dív. Líq./Patrimônio", "de -1 a mais de 5", "pode ser negativo"]],
        [36 * mm, 40 * mm, UTIL - 76 * mm]))
    add(P("Somar isso direto seria desastroso. O EV/EBITDA, que chega a passar de 100, "
          "dominaria completamente o ROIC, que não passa de 0,60 — independentemente do "
          "peso que você escrevesse na fórmula. O peso declarado não seria o peso real. "
          "Pior: um único valor extremo bastaria para desarrumar o ranking inteiro."))

    add(H2("A solução: trocar o valor pela posição"))
    add(P("Em vez de usar o valor bruto, o sistema usa a <b>posição percentil</b> da "
          "empresa entre todas as elegíveis. Cada indicador vira uma nota de 0 a 100, "
          "onde 100 é o melhor da amostra e 0 é o pior."))
    add(caixa("A regra em uma frase",
              "A nota não responde <i>quanto</i> a empresa tem, e sim <b>quantas empresas "
              "ela superou</b> naquele indicador."))
    add(P("Isso resolve os três problemas de uma vez: todos os indicadores passam a viver "
          "na mesma escala de 0 a 100, os pesos declarados viram os pesos reais, e "
          "valores extremos deixam de distorcer — o EV/EBITDA de 110 vezes vira "
          "simplesmente a última posição, e não um número capaz de dominar a soma."))

    add(H3("A fórmula"))
    add(caixa(None,
              '<font size="11"><b>nota = (N &#8722; posição) / (N &#8722; 1) &#215; 100'
              '</b></font><br/><br/>'
              f"onde <b>N</b> é o número de papéis elegíveis (hoje {n}) e "
              "<b>posição</b> é o lugar da empresa naquele indicador, do melhor (1) "
              "para o pior."))
    add(P("O sentido de “melhor” muda conforme o indicador. Para ROIC, margem e "
          "crescimento, maior é melhor. Para EV/EBITDA e endividamento, menor é melhor. "
          "O sistema sabe a direção de cada um e ordena de acordo."))

    add(H3("Empates recebem a média"))
    add(P("Quando várias empresas têm exatamente o mesmo valor, todas recebem a média das "
          "posições que ocupariam. Um exemplo real desta coleta:"))
    emp = acha_empate("PLPL3")
    if emp:
        chave, grupo, valor, pos = emp
        rot = {"roic": "ROIC", "cresc": "Cresc. Rec. 5a", "evebitda": "EV/EBITDA",
               "mrgeb": "Margem EBIT", "div": "Dív. Líq./Patrim."}[chave]
        f = FMT_FATOR[chave]
        media = sum(pos) / len(pos)
        nota = next(a["n_" + chave] for a in acoes if a["papel"] == "PLPL3")
        add(tabela(
            ["Papéis empatados", rot, "Posições", "Nota atribuída"],
            [[", ".join(grupo[:-1]) + " e " + grupo[-1], f(valor),
              ", ".join(str(x) for x in pos[:-1]) + " e " + str(pos[-1]),
              f"média = {media:g}".replace(".", ",")
              + f"  <font color='#5b6b80'>(nota {nota:.1f})</font>".replace(".", ",")]],
            [50 * mm, 28 * mm, 26 * mm, UTIL - 104 * mm]))
    else:
        add(P("Nesta coleta o PLPL3 não divide valor exato com nenhum outro papel em "
              "nenhum dos cinco fatores, então não há empate para ilustrar.", "nota"))
    add(P("Sem essa regra, a ordem entre empresas idênticas seria decidida por acaso — "
          "por exemplo, pela ordem alfabética ou pela ordem em que aparecem na tabela de "
          "origem. Dar a média a todos evita premiar ou punir alguém por um critério que "
          "não tem nada a ver com a empresa."))

    add(PageBreak())

    add(H2("Os cinco fatores e seus pesos"))
    add(tabela(
        ["Fator", "Peso", "Direção", "Por que está aqui"],
        [["<b>ROIC</b>", "<b>30%</b>", "maior melhor",
          "É a melhor aproximação disponível de vantagem competitiva. Retorno alto "
          "atrai concorrência; quem consegue sustentar tem alguma barreira real — "
          "marca, escala, contrato longo, custo de troca para o cliente"],
         ["<b>Cresc. Receita 5a</b>", "<b>20%</b>", "maior melhor",
          "Rentabilidade alta sem crescimento é uma empresa boa que não vai a lugar "
          "nenhum. Cinco anos atravessa um ciclo econômico"],
         ["<b>EV/EBITDA</b>", "<b>20%</b>", "menor melhor",
          "O contrapeso. Sem ele o ranking seria uma lista das empresas mais admiradas "
          "do mercado — que costumam ser também as mais caras"],
         ["<b>Margem EBIT</b>", "<b>15%</b>", "maior melhor",
          "Eficiência da operação, sem interferência de dívida ou de regime tributário"],
         ["<b>Dív. Líq./Patrimônio</b>", "<b>15%</b>", "menor melhor",
          "Sobrevivência. Empresa excelente e endividada quebra numa crise; empresa "
          "mediana com caixa atravessa e ainda compra concorrente"]],
        [34 * mm, 13 * mm, 20 * mm, UTIL - 67 * mm], alinhar_dir=(1,)))

    add(caixa("A lógica por trás da distribuição dos pesos",
              "<b>50% em qualidade</b> (ROIC + Margem EBIT): a empresa é boa de operar?<br/>"
              "<b>20% em crescimento</b>: ela está ficando maior?<br/>"
              "<b>20% em preço</b> (EV/EBITDA): estamos pagando caro por isso?<br/>"
              "<b>15% em risco</b> (endividamento): ela sobrevive a um susto?<br/><br/>"
              "O ROIC leva o maior peso porque é o único dos cinco que tenta capturar "
              "algo <i>durável</i>. Preço muda todo dia, margem oscila com o ciclo, mas "
              "uma vantagem competitiva real persiste por anos."))

    add(alerta("Os pesos são uma escolha, não uma verdade",
               "Não existe fórmula certa. Alguém poderia argumentar com boa-fé que preço "
               "deveria pesar 40%, ou que endividamento deveria pesar mais que "
               "crescimento. Essa fragilidade é reconhecida — e é exatamente por isso que "
               "existem os três esquemas da Parte 6, que testam o quanto o resultado "
               "depende dessa escolha."))

    add(PageBreak())

    # ---- exemplo trabalhado
    _score_br = f"{plpl['score']:.1f}".replace(".", ",")
    add(H2(f"Exemplo completo: como o PLPL3 chegou a {_score_br}"))
    add(P(f"Vamos refazer a conta inteira, do zero, com dados reais da coleta de "
          f"{data_br}. O PLPL3 (Plano&amp;Plano, construção) terminou em 1º lugar."))

    add(H3("Passo 1 — os valores brutos da empresa"))
    add(tabela(
        ["Indicador", "Valor do PLPL3"],
        [["ROIC", f"{plpl['roic']*100:.2f}%".replace(".", ",")],
         ["Cresc. Receita 5a", f"{plpl['cresc']*100:.2f}%".replace(".", ",")],
         ["EV/EBITDA", f"{plpl['evebitda']:.2f}x".replace(".", ",")],
         ["Margem EBIT", f"{plpl['mrgeb']*100:.2f}%".replace(".", ",")],
         ["Dív. Líquida / Patrimônio", f"{plpl['div']:.2f}x".replace(".", ",")]],
        [60 * mm, UTIL - 60 * mm], alinhar_dir=(1,)))
    _roic_br = f"{plpl['roic']*100:.0f}"
    _ev_br = f"{plpl['evebitda']:.2f}".replace(".", ",")
    add(P(f"Sozinhos, esses números não dizem se a empresa é boa. Um ROIC de "
          f"{_roic_br}% é alto? Um EV/EBITDA de {_ev_br} vezes é barato? "
          f"Só dá para responder comparando."))

    add(H3(f"Passo 2 — a posição de cada um entre os {n} elegíveis"))
    pesos = [(k, rot, w, posicao(k, "PLPL3")) for k, rot, w in [
        ("roic", "ROIC", 0.30), ("cresc", "Cresc. Receita 5a", 0.20),
        ("evebitda", "EV/EBITDA", 0.20), ("mrgeb", "Margem EBIT", 0.15),
        ("div", "Dív. Líq./Patrim.", 0.15)]]
    add(tabela(
        ["Indicador", "Posição", "Conta da nota", "Nota"],
        [[rot, f"{ordinal(pos)} de {n}".replace("o de", "º de"),
          f"({n} &#8722; {pos:g}) / {n-1} &#215; 100",
          f"<b>{plpl['n_'+k]:.1f}</b>".replace(".", ",")]
         for k, rot, _, pos in pesos],
        [36 * mm, 22 * mm, 40 * mm, UTIL - 98 * mm], alinhar_dir=(1, 3)))
    _pev, _pmg = posicao("evebitda", "PLPL3"), posicao("mrgeb", "PLPL3")
    add(P(f"Repare no contraste: o PLPL3 é o <b>{ordinal(_pev)} mais barato</b> da bolsa "
          f"em EV/EBITDA (nota {plpl['n_evebitda']:.0f}) mas apenas o "
          f"<b>{ordinal(_pmg)} em margem EBIT</b> (nota {plpl['n_mrgeb']:.0f}). Não é uma "
          "empresa boa em tudo — é uma empresa muito bem posicionada em preço e "
          "rentabilidade, mediana em margem.".replace("o mais barato", "º mais barato")
          .replace("o em margem", "º em margem")))

    add(H3("Passo 3 — aplicar os pesos e somar"))
    linhas = []
    total = 0.0
    for k, rot, w, _ in pesos:
        nota = plpl["n_" + k]
        prod = nota * w
        total += prod
        linhas.append([rot, f"{nota:.1f}".replace(".", ","), f"{w:.0%}",
                       f"{nota:.1f} &#215; {w:.2f}".replace(".", ","),
                       f"<b>{prod:.2f}</b>".replace(".", ",")])
    linhas.append([Paragraph("<b>SCORE FINAL</b>", E["celb"]), "", "", "",
                   Paragraph(f"<b>{total:.2f}</b>".replace(".", ","), E["celb"])])
    add(tabela(["Fator", "Nota", "Peso", "Conta", "Contribuição"], linhas,
               [36 * mm, 16 * mm, 15 * mm, 30 * mm, UTIL - 97 * mm],
               alinhar_dir=(1, 2, 4)))

    add(bom("O número fecha",
            f"O score gravado no sistema para o PLPL3 é <b>{plpl['score']:.6f}</b>"
            .replace(".", ",") +
            f". A conta acima, feita à mão, dá <b>{total:.4f}</b>".replace(".", ",") +
            ". Não há nenhuma etapa escondida entre os indicadores públicos e o número "
            "final — você pode reproduzir isso para qualquer papel da lista."))

    add(H3("De onde vem a contribuição de cada fator"))
    add(P("A última coluna revela algo que o score sozinho esconde: <b>onde a nota foi "
          "construída</b>. O ROIC entregou 28,8 pontos dos 88,4 — quase um terço — "
          "porque combina a maior nota com o maior peso. A margem EBIT, apesar de "
          "responder por 15% do peso, contribuiu com apenas 10,2 pontos, porque a nota "
          "era mediana."))
    add(P("Na aba <b>Ficha da ação</b> do site, o bloco de barras mostra exatamente essa "
          "decomposição para qualquer papel."))

    add(H2("O que a nota não diz"))
    addm(LI([
        "<b>Nota alta não significa ação barata.</b> Significa boa posição relativa "
        "num conjunto de cinco critérios, um dos quais é preço.",
        "<b>Nota alta não significa que vai subir.</b> Não há backtest. Não há "
        "evidência de retorno superior.",
        "<b>A diferença entre o 1º e o 5º lugar é pequena.</b> Tratar essas posições "
        "como uma ordem de preferência rigorosa é ler precisão que o método não tem.",
        "<b>A nota muda quando a amostra muda.</b> Como tudo é relativo, uma empresa "
        "pode subir de posição sem ter melhorado — basta as outras piorarem.",
    ]))

    add(PageBreak())

    # =============================================================== PARTE 6
    add(H1(6, "Os três esquemas e o consenso"))

    add(H2("Por que rodar três rankings ao mesmo tempo"))
    add(P("Qualquer score como este depende de duas decisões discutíveis: <b>quais pesos "
          "usar</b> e <b>contra quem comparar</b>. Não existe resposta objetivamente "
          "correta para nenhuma das duas."))
    add(P("A saída honesta não é fingir que as escolhas são neutras. É rodar os três "
          "rankings em paralelo e mostrar onde eles concordam."))

    add(tabela(
        ["Esquema", "Pesos usados", "Universo de comparação", "O que testa"],
        [["<b>A — Principal</b>", "30/20/20/15/15", "a bolsa inteira",
          "é o ranking de referência"],
         ["<b>B — Setorial</b>", "30/20/20/15/15", "apenas pares do mesmo setor",
          "se a posição vem da empresa ou do setor em que ela está"],
         ["<b>C — Pesos iguais</b>", "20% para cada um", "a bolsa inteira",
          "se a posição depende da escolha dos pesos"]],
        [30 * mm, 28 * mm, 40 * mm, UTIL - 98 * mm]))

    add(H3("O que o esquema B corrige"))
    add(P("Margens variam enormemente entre setores. Um supermercado saudável opera com "
          "margem que quebraria uma empresa de software; uma construtora tem estrutura "
          "de capital que nada tem a ver com a de uma elétrica. No esquema A, setores "
          "inteiros tendem a ficar bem ou mal em bloco."))
    add(P("O esquema B recalcula as notas <b>só entre pares do mesmo setor</b>. Uma "
          "construtora passa a ser comparada apenas com construtoras. Se ela continua "
          "bem colocada, a posição vem dela; se despenca, vinha do setor."))

    add(alerta("A limitação do esquema B",
               "Um setor precisa de pelo menos 5 papéis elegíveis para ter comparação "
               "própria — com menos que isso, o percentil seria estatística sem base. "
               "Setores pequenos, e papéis que não estão no mapa de setores, "
               "<b>herdam as notas do universo inteiro</b>. Na prática, para esses "
               "papéis o esquema B vira uma cópia do A, e o consenso deles é mais fraco "
               "do que o número sugere.<br/><br/>"
               "O site avisa disso em dois lugares: um quadro âmbar na ficha da ação, e "
               "a coluna <i>Percentil próprio</i> na aba Setores."))

    add(H2("O consenso 3/3"))
    add(P(f"O sistema marca o <b>decil superior</b> de cada esquema — hoje, os "
          f"{m['top_n_consenso']} primeiros de cada um. O consenso conta em quantos dos "
          "três o papel aparece nesse grupo."))
    add(tabela(
        ["Marca", "Significado", "Como interpretar"],
        [["<b>3/3</b>", "No topo dos três esquemas",
          "A posição não depende da escolha de pesos nem do universo de comparação"],
         ["<b>2/3</b>", "No topo de dois",
          "Boa colocação, mas sensível a uma das escolhas do método"],
         ["<b>1/3</b> ou <b>0/3</b>", "No topo de um ou de nenhum",
          "A boa colocação no ranking principal depende fortemente das escolhas feitas"]],
        [20 * mm, 46 * mm, UTIL - 66 * mm]))

    add(caixa("O que o consenso 3/3 significa — e o que não significa",
              "<b>Significa:</b> que a boa colocação daquele papel é <i>robusta</i>. "
              "Mudar os pesos ou o universo de comparação não o tira do topo.<br/><br/>"
              "<b>Não significa:</b> que a empresa é boa, nem que a ação vai subir. "
              "Os três esquemas leem exatamente os mesmos cinco indicadores — se todos "
              "os cinco estiverem desatualizados ou distorcidos, os três erram juntos. "
              "<b>Consenso mede estabilidade do método, não qualidade da empresa.</b>"))

    add(H3(f"Os {len(tres)} papéis com consenso 3/3 nesta coleta"))
    add(caixa(None, "<b>" + "&nbsp; &#183; &nbsp;".join(tres) + "</b>", VERDE, VERDE_BG))

    add(H2("Ler a divergência entre os esquemas"))
    add(P("Quando as três posições divergem muito, isso é informação, não ruído:"))
    addm(LI([
        "<b>Bem em A e C, mal em B</b> — a empresa se destaca na bolsa toda mas é "
        "mediana entre os pares dela. A boa posição vem do setor estar em um bom momento.",
        "<b>Mal em A, bem em B</b> — é das melhores do setor dela, mas o setor inteiro "
        "está mal posicionado nos critérios do score.",
        "<b>Bem em A, mal em C</b> — a posição depende dos pesos escolhidos. "
        "Provavelmente ela é muito forte em ROIC (que pesa 30% em A e 20% em C) e fraca "
        "nos demais.",
    ]))
    add(P("Na ficha de cada ação, o bloco <b>Posição nos três esquemas</b> mostra as três "
          "lado a lado justamente para essa leitura."))

    add(PageBreak())

    # =============================================================== PARTE 7
    add(H1(7, "Guia da página"))
    add(P("Referência de consulta: o que é cada elemento de cada aba.", "nota"))

    add(H2("O cabeçalho, presente em todas as abas"))
    add(tabela(
        ["Elemento", "O que é"],
        [["<b>Última coleta</b>", "Data e hora da última atualização bem-sucedida. "
          "<b>É o primeiro lugar para olhar.</b> Se passar de 3 dias, a caixa fica "
          "âmbar e mostra há quantos dias o dado está parado"],
         ["<b>Botão de tema</b>", "Cicla entre Automático (segue o sistema), Claro e "
          "Escuro. A escolha fica salva no aparelho"],
         ["<b>Faixa de aviso</b>", "O lembrete de que nada ali é recomendação de "
          "investimento. Fica acima dos números de propósito"],
         ["<b>As cinco abas</b>", "Ranking, Ficha da ação, Levantamentos, Setores, Método"]],
        [34 * mm, UTIL - 34 * mm]))

    add(H2("Aba Ranking"))
    add(P("A tela principal: a lista completa dos papéis elegíveis."))
    add(H3("Os quatro cartões do topo"))
    add(tabela(
        ["Cartão", "O que informa"],
        [["Papéis lidos na fonte", f"Quantos o Fundamentus entregou ({m['papeis_lidos']})"],
         ["Passaram nos filtros", f"Quantos foram efetivamente pontuados ({n})"],
         ["Com consenso 3/3", f"Quantos estão no topo dos três esquemas ({len(tres)})"],
         ["Corte de liquidez/dia", "O volume mínimo exigido para entrar"]],
        [46 * mm, UTIL - 46 * mm]))

    add(H3("Os controles"))
    add(tabela(
        ["Controle", "Para que serve"],
        [["<b>Buscar papel</b>", "Filtra pelo código. Digite parte do nome, como PLPL"],
         ["<b>Setor</b>", "Restringe a um setor. Útil para comparar concorrentes diretos"],
         ["<b>Ordenar por</b>", "Troca entre os esquemas A, B e C. <b>A tabela inteira "
          "muda</b>: a coluna Score e a coluna # passam a refletir o esquema escolhido"],
         ["<b>Só consenso 3/3</b>", "Mostra apenas os papéis robustos aos três esquemas"]],
        [38 * mm, UTIL - 38 * mm]))

    add(H3("As colunas da tabela"))
    add(tabela(
        ["Coluna", "O que é"],
        [["<b>#</b>", "Posição no esquema selecionado em <i>Ordenar por</i>"],
         ["<b>Papel</b>", "Código de negociação. <b>Clicável</b> — abre a ficha completa"],
         ["<b>Setor</b>", "Classificação usada no esquema B. <i>Não mapeado</i> "
          "significa que o papel não está na lista de setores"],
         ["<b>Score</b>", "A nota de 0 a 100 do esquema selecionado"],
         ["<b>Consenso</b>", "Em quantos dos três esquemas o papel está no decil superior"],
         ["<b>ROIC</b> … <b>Dív.Líq./Patr.</b>",
          "Os cinco indicadores que formam o score, em valor bruto — para você ver de "
          "onde a nota veio sem precisar abrir a ficha"]],
        [42 * mm, UTIL - 42 * mm]))

    add(H3("As marcas visuais"))
    add(tabela(
        ["Marca", "Significado"],
        [["Barra verde à esquerda da linha", "Consenso 3/3"],
         ["Selo verde <b>3/3</b>", "O mesmo, em formato de etiqueta"],
         ["Etiqueta <b>cíclica</b> ao lado do código",
          "Setor cíclico — commodities, siderurgia, papel, petróleo, frigoríficos. "
          "Essas empresas exibem os melhores indicadores no <b>topo</b> do ciclo, "
          "justamente quando o preço já subiu. Um EV/EBITDA baixo pode refletir lucro "
          "de pico, não empresa barata"]],
        [58 * mm, UTIL - 58 * mm]))

    add(caixa("No celular a tabela vira cartões",
              "Abaixo de 720 pixels de largura, cada linha da tabela se transforma num "
              "cartão com o código em destaque e os indicadores listados um por linha, "
              "cada um com seu rótulo. É a mesma informação, reorganizada. Isso depende "
              "da <b>largura da tela</b>, não do aparelho — se você estreitar a janela "
              "no computador, acontece a mesma coisa."))

    add(PageBreak())

    add(H2("Aba Ficha da ação"))
    add(P("O detalhamento completo de um papel. Dá para chegar nela por dois caminhos: "
          "clicando no código em qualquer lista, ou pelo seletor no alto da aba."))

    add(tabela(
        ["Bloco", "O que mostra"],
        [["<b>Cabeçalho</b>", "Código, setor e o selo de consenso"],
         ["<b>Quadros âmbar</b>", "Ressalvas, quando existirem: setor cíclico, ou "
          "ausência de comparação setorial própria"],
         ["<b>Posição nos três esquemas</b>",
          "As três colocações lado a lado. Parecidas: posição robusta. Divergentes: "
          "depende das escolhas do método"],
         ["<b>Notas do score</b>", "Duas colunas de barras — as notas no universo "
          "inteiro e as notas dentro do setor. Cada barra é um fator, com seu peso ao "
          "lado. <b>É aqui que se vê de onde a nota veio</b>"],
         ["<b>Seis grupos de indicadores</b>",
          "Rentabilidade, Crescimento, Margens e eficiência, Preço e múltiplos, "
          "Endividamento e solvência, Porte e negociação"]],
        [46 * mm, UTIL - 46 * mm]))

    add(H3("A linha de cada indicador"))
    add(P("Cada indicador exibe quatro informações, e a terceira é a mais valiosa:"))
    addm(NUM([
        "<b>O nome e o nome por extenso</b> do indicador.",
        "<b>O valor</b>, colorido de verde quando a empresa está no quarto superior "
        "da bolsa naquele indicador, e de vermelho quando está no quarto inferior.",
        "<b>A barra de contexto</b>, com a frase <i>melhor que X% da bolsa</i> e a "
        "<i>mediana do setor</i>. Isto responde à pergunta que o número sozinho não "
        "responde: 24% de ROIC é bom? A frase diz que é melhor que 97% da bolsa, e que "
        "a mediana do setor é 9,7%.",
        "<b>O botão com ponto de interrogação</b>, que abre a explicação em três partes: "
        "<i>O que é</i>, <i>Como ler</i> e <i>Onde engana</i>.",
    ]))

    add(bom("O contexto percentil é o diferencial da ficha",
            "Sites de dados costumam mostrar o indicador e parar por aí. Saber que uma "
            "empresa tem ROIC de 24,3% não ajuda quem não decorou a distribuição da bolsa "
            "inteira. Saber que isso é melhor que 97% dos papéis elegíveis ajuda "
            "imediatamente — e essa comparação já está calculada."))

    add(H2("Aba Levantamentos"))
    add(tabela(
        ["Seção", "O que traz"],
        [["<b>Consenso 3/3</b>", "Cartões clicáveis com os papéis robustos aos três "
          "esquemas, com a posição e o score de cada um"],
         ["<b>Explorar um indicador</b>",
          "Escolha um indicador e veja: a explicação completa dele, a distribuição entre "
          "os elegíveis (mínimo, quartis, mediana, máximo), os 15 melhores e os 5 piores"]],
        [42 * mm, UTIL - 42 * mm]))
    add(P("A <b>distribuição</b> é a parte mais útil e a menos óbvia. Ela responde "
          "“este valor é alto ou baixo?” sem depender de regra decorada. Um exemplo: "
          "no EV/EBITDA, a mediana da bolsa fica próxima de 5 vezes e o máximo passa de "
          "100 vezes. Com isso na tela, fica evidente que 7 vezes não é caro nem barato "
          "no vácuo — é apenas um pouco acima da mediana."))
    add(P("Metade dos papéis fica entre o 1º e o 3º quartil. Quem está fora dessa faixa "
          "está num extremo, e extremos merecem explicação antes de virarem conclusão."))

    add(alerta("Cuidado ao usar as listas de melhores",
               "Elas ordenam por <b>um indicador isolado</b>, sem pesos e sem os outros "
               "quatro fatores. Liderar o ranking de ROIC não coloca a empresa no topo do "
               "score — e nem deveria. Uma empresa pode ter o melhor ROIC da bolsa e "
               "estar caríssima."))

    add(H2("Aba Setores"))
    add(tabela(
        ["Coluna", "O que é"],
        [["<b>Setor</b>", "Nome do setor"],
         ["<b>Papéis</b>", "Quantos elegíveis ele tem"],
         ["<b>Score mediano</b>", "A mediana dos scores do setor. <b>Mediana, e não "
          "média</b>, de propósito: num setor de 6 empresas, uma única com nota extrema "
          "distorceria a média inteira. A mediana resiste"],
         ["<b>3/3</b>", "Quantos papéis do setor têm consenso completo"],
         ["<b>Melhor colocado</b>", "O papel mais bem posicionado do setor, clicável"],
         ["<b>Percentil próprio</b>", "Se o setor tem 5 ou mais elegíveis e portanto "
          "comparação setorial de verdade. <i>Não — herda o global</i> significa que "
          "o esquema B copiou as notas do universo inteiro"]],
        [38 * mm, UTIL - 38 * mm]))

    add(H2("Aba Método"))
    add(P("A documentação dentro do próprio site: a tabela de pesos, a ordem dos cortes, "
          "a contagem de eliminados <b>desta coleta específica</b>, a descrição dos três "
          "esquemas, o glossário completo dos indicadores, as limitações e a proveniência "
          "dos dados. Tudo o que este manual explica em profundidade está lá em forma "
          "resumida e sempre atualizado."))

    add(PageBreak())

    # =============================================================== PARTE 8
    add(H1(8, "Glossário dos 16 indicadores"))
    add(P("Para cada indicador: o que ele mede, como interpretar, e onde ele engana. "
          "A terceira parte é a que costuma faltar em outros lugares.", "nota"))

    glossario = [
        ("Rentabilidade", [
            ("ROIC", "Retorno sobre o Capital Investido",
             "Lucro operacional depois de impostos dividido pelo capital investido na "
             "operação (dívida mais patrimônio). Mede quanto a empresa produz com todo o "
             "dinheiro que emprega, sem importar se veio de sócio ou de banco.",
             "Acima de cerca de 15% ao ano costuma indicar operação forte. Mais "
             "importante que o número num ano é ele se sustentar: retorno alto atrai "
             "concorrente, então quem mantém tem alguma barreira real.",
             "Ativos antigos, já depreciados, encolhem o denominador e inflam o ROIC. "
             "Empresa de capital leve parece melhor que indústria pesada sem "
             "necessariamente ser."),
            ("ROE", "Retorno sobre o Patrimônio Líquido",
             "Lucro líquido dividido pelo patrimônio líquido. O retorno sobre o dinheiro "
             "dos sócios.",
             "Serve como conferência ao lado do ROIC. Quando o ROE é muito maior que o "
             "ROIC, a diferença normalmente é dívida.",
             "O ROE sobe quando a empresa se endivida, sem que nada tenha melhorado na "
             "operação: a dívida encolhe o patrimônio e o mesmo lucro passa a dividir uma "
             "base menor. É por isso que o score usa ROIC, e não ROE."),
        ]),
        ("Crescimento", [
            ("Cresc. Receita 5a", "Crescimento anualizado da receita em 5 anos",
             "Taxa média anual de crescimento da receita líquida nos últimos cinco anos.",
             "Cinco anos é longo o bastante para atravessar um ciclo econômico e curto o "
             "bastante para descrever a empresa de hoje.",
             "Receita crescendo não é lucro crescendo — dá para crescer vendendo mais "
             "barato e destruindo margem. Aquisições também entram aqui como se fossem "
             "crescimento próprio."),
        ]),
        ("Margens e eficiência", [
            ("Margem Bruta", "Lucro bruto sobre receita",
             "Receita menos o custo direto do que foi vendido, dividido pela receita.",
             "É a medida mais direta de poder de precificação: margem bruta alta significa "
             "que o cliente aceita pagar bem acima do custo de produzir.",
             "Varia enormemente entre setores. Um supermercado saudável opera com margem "
             "bruta que quebraria uma empresa de software."),
            ("Margem EBIT", "Lucro operacional sobre receita",
             "Lucro antes de juros e impostos, dividido pela receita. Quanto sobra de cada "
             "real vendido depois de todos os custos de operar, mas antes da conta do "
             "banco e do governo.",
             "É a medida mais limpa de eficiência operacional, porque não é distorcida por "
             "estrutura de capital nem por regime tributário.",
             "Comparar entre setores engana. É exatamente por isso que existe o esquema B, "
             "que compara a empresa apenas com pares do próprio setor."),
            ("Margem Líquida", "Lucro líquido sobre receita",
             "O que sobra de cada real de receita depois absolutamente de tudo: custos, "
             "despesas, juros e impostos.",
             "Útil para ver o efeito combinado de operação, dívida e carga tributária num "
             "número só.",
             "É a margem mais contaminada por eventos que não se repetem — venda de um "
             "imóvel, reversão de provisão, crédito fiscal reconhecido de uma vez."),
        ]),
        ("Preço e múltiplos", [
            ("EV/EBITDA", "Valor da firma sobre geração de caixa operacional",
             "Valor de mercado mais dívida líquida, dividido pelo EBITDA. Grosso modo: "
             "quantos anos de geração de caixa operacional pagariam a empresa inteira, "
             "dívida incluída.",
             "Quanto menor, mais barata. É preferível ao P/L para comparar empresas porque "
             "enxerga a dívida — comprar uma empresa endividada significa herdar a dívida.",
             "O EBITDA ignora o investimento necessário só para manter a operação de pé. "
             "Empresa que precisa reinvestir pesado todo ano aparece barata sem ser."),
            ("EV/EBIT", "Valor da firma sobre lucro operacional",
             "Igual ao EV/EBITDA, mas usando o lucro operacional depois da depreciação.",
             "Mais conservador. A depreciação é uma estimativa do desgaste dos ativos: não "
             "sai do caixa hoje, mas a máquina vai precisar ser trocada.",
             "Em setores de ativo muito pesado, a depreciação contábil pode estar longe do "
             "gasto real de reposição, para mais ou para menos."),
            ("P/L", "Preço sobre lucro por ação",
             "Preço da ação dividido pelo lucro por ação dos últimos 12 meses. Quantos "
             "anos do lucro atual pagariam o preço de hoje.",
             "O múltiplo mais conhecido, útil como referência rápida dentro de um mesmo "
             "setor.",
             "Ignora a dívida por completo: uma empresa muito endividada pode exibir P/L "
             "baixo e ser cara. Perde o sentido quando o lucro é pequeno ou negativo."),
            ("P/VP", "Preço sobre valor patrimonial",
             "Preço da ação dividido pelo patrimônio líquido por ação.",
             "Abaixo de 1 significa que o mercado paga menos do que o valor contábil do "
             "patrimônio.",
             "Patrimônio contábil não é valor real. Marca, software e equipe não aparecem "
             "no balanço; imóveis podem estar registrados por valor de décadas atrás."),
            ("Dividend Yield", "Proventos dos últimos 12 meses sobre o preço",
             "Dividendos e juros sobre capital próprio pagos nos últimos 12 meses, "
             "divididos pela cotação atual.",
             "Mostra o retorno em caixa que o preço de hoje teria produzido no último ano.",
             "Olha para trás e não promete nada. Yield alto pode ser preço em queda, não "
             "dividendo generoso — o denominador encolheu. E pode vir de um pagamento "
             "extraordinário que não se repete."),
        ]),
        ("Endividamento e solvência", [
            ("Dív. Líq./Patrim.", "Dívida líquida sobre patrimônio líquido",
             "Dívida bruta menos caixa e aplicações financeiras, dividido pelo patrimônio "
             "líquido. É quanto a empresa deve, já descontado o dinheiro que ela tem.",
             "Quanto menor, mais folga. <b>Valor negativo é bom</b>: significa caixa maior "
             "que dívida, ou seja, a empresa tem caixa líquido. É por isso que aparecem "
             "números negativos nesta coluna.",
             "Não diz nada sobre o custo nem sobre o prazo da dívida. Dívida barata "
             "vencendo em dez anos e dívida cara vencendo no ano que vem aparecem "
             "exatamente iguais aqui."),
            ("Liquidez Corrente", "Ativo circulante sobre passivo circulante",
             "O que a empresa tem para receber ou converter em dinheiro no próximo ano, "
             "dividido pelo que ela tem para pagar no próximo ano.",
             "Acima de 1 indica que os compromissos de curto prazo estão cobertos pelos "
             "recursos de curto prazo.",
             "Estoque conta como ativo circulante mesmo quando está encalhado. Um "
             "varejista com armazém cheio de produto que não vende exibe liquidez corrente "
             "confortável."),
        ]),
        ("Porte e negociação", [
            ("Patrimônio Líquido", "Valor contábil do patrimônio",
             "Ativos menos passivos, pelo valor registrado na contabilidade.",
             "Serve aqui como referência de porte da empresa.",
             "Patrimônio líquido negativo elimina a empresa do ranking antes de qualquer "
             "pontuação: significa que as dívidas superam os ativos contábeis."),
            ("Volume médio/dia", "Liquidez média diária dos últimos 2 meses",
             "Volume financeiro médio negociado por dia na bolsa nos últimos dois meses.",
             "É o filtro de entrada do ranking. Abaixo do corte de R$ 1 milhão por dia o "
             "papel é eliminado antes de pontuar.",
             "Preço de ativo que quase não negocia não reflete valor de mercado — e, na "
             "prática, você pode não conseguir vender a posição sem derrubar a cotação."),
            ("Cotação", "Preço de fechamento",
             "Preço da ação no fechamento do dia da coleta.",
             "O preço isolado não diz se a ação é cara ou barata — só os múltiplos dizem, "
             "porque relacionam preço a lucro, caixa ou patrimônio.",
             "Preço baixo em reais não significa ação barata. Uma ação de R$ 2 pode estar "
             "cara e uma de R$ 300, barata."),
        ]),
    ]

    for grupo, itens in glossario:
        add(H2(grupo))
        for nome, completo, oque, ler, engana in itens:
            bloco = [
                Paragraph(f'<b>{nome}</b> &nbsp;<font color="#5b6b80" size="8">'
                          f'{completo}</font>', E["cx"]),
                Spacer(1, 4),
                Paragraph(f'<font color="#1d4ed8"><b>O que é.</b></font> {oque}', E["cx"]),
                Spacer(1, 3),
                Paragraph(f'<font color="#1d4ed8"><b>Como ler.</b></font> {ler}', E["cx"]),
                Spacer(1, 3),
                Paragraph(f'<font color="#92400e"><b>Onde engana.</b></font> {engana}',
                          E["cx"]),
            ]
            t = Table([[bloco]], colWidths=[UTIL])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CINZA_BG),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, AZUL),
                ("BOX", (0, 0), (-1, -1), 0.4, CINZA),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            add(KeepTogether([t, Spacer(1, 7)]))

    add(PageBreak())

    # =============================================================== PARTE 9
    add(H1(9, "Como analisar na prática"))

    add(H2("Um fluxo de trabalho em cinco passos"))
    addm(NUM([
        "<b>Confira a data da coleta.</b> Antes de qualquer número. Se estiver âmbar, "
        "os dados estão parados e você precisa saber disso.",
        "<b>Ligue o filtro “Só consenso 3/3”.</b> Você sai de uma lista de mais de 150 "
        "papéis para cerca de dez. São os que resistem às três formas de montar o "
        "ranking — o melhor ponto de partida.",
        "<b>Troque entre os esquemas A, B e C</b> no seletor “Ordenar por”. Veja quem "
        "permanece no topo nos três e quem só aparece em um.",
        "<b>Abra a ficha dos candidatos.</b> Olhe o bloco de barras: de onde veio a nota? "
        "Uma nota alta construída sobre um único fator é mais frágil que uma nota "
        "construída sobre quatro.",
        "<b>Leia as ressalvas.</b> Quadro âmbar de cíclica? De setor sem pares? "
        "Isso muda o peso que você deve dar ao resultado.",
    ]))
    add(P("E então começa o trabalho de verdade, que o site não faz por você: ler os "
          "balanços, entender o negócio, avaliar a diretoria, verificar notícias e "
          "processos. O site entrega a lista curta; a convicção você constrói."))

    add(H2("Perguntas para fazer diante de uma nota alta"))
    addm(LI([
        "<b>De onde veio a nota?</b> Se um único fator carregou tudo, a posição é "
        "instável — basta aquele indicador se normalizar para a empresa cair.",
        "<b>A empresa é cíclica?</b> Se sim, indicadores excelentes podem significar "
        "topo de ciclo, o pior momento para entrar.",
        "<b>O EV/EBITDA é baixo demais?</b> Abaixo de 2 ou 3 vezes, desconfie. O mercado "
        "raramente dá desconto grande sem motivo — pode haver risco que os cinco "
        "indicadores não capturam.",
        "<b>O setor tem percentil próprio?</b> Se não, o consenso 3/3 vale menos, porque "
        "um dos três esquemas foi cópia de outro.",
        "<b>O crescimento veio de aquisição?</b> O indicador não distingue crescimento "
        "orgânico de compra de concorrente.",
    ]))

    add(H2("Cinco erros comuns de interpretação"))
    add(tabela(
        ["Erro", "Por que é errado"],
        [["<b>Tratar o 1º lugar como a melhor ação</b>",
          "O score mede posição relativa em cinco critérios contábeis. A diferença entre "
          "o 1º e o 5º lugar é pequena e não sobrevive a uma mudança modesta nos pesos"],
         ["<b>Comparar margens entre setores</b>",
          "Margem de varejo e margem de software vivem em universos diferentes. Use o "
          "esquema B ou a mediana do setor na ficha"],
         ["<b>Achar que nota alta = barato</b>",
          "Preço é apenas um dos cinco fatores, com 20% do peso. Uma empresa cara pode "
          "ter nota alta se for excelente nos outros quatro"],
         ["<b>Ignorar a etiqueta cíclica</b>",
          "É o alerta mais importante da tela. Commodities exibem os melhores números "
          "exatamente quando estão mais arriscadas"],
         ["<b>Comparar o score de hoje com o de semanas atrás</b>",
          "A nota é relativa à amostra do dia. Uma empresa pode subir sem ter melhorado, "
          "só porque outras pioraram ou saíram do universo"]],
        [55 * mm, UTIL - 55 * mm]))

    add(PageBreak())

    # ============================================================== PARTE 10
    add(H1(10, "Limitações e perguntas frequentes"))

    add(H2("Limitações, sem eufemismo"))
    addm(LI([
        "<b>Não é backtest.</b> Os pesos são plausíveis, nunca testados historicamente. "
        "Não há evidência de retorno superior.",
        "<b>Não é recomendação.</b> É triagem, e só.",
        "<b>Os dados podem estar defasados</b> em até um trimestre frente ao último "
        "balanço divulgado.",
        "<b>O mapa de setores é manual</b> e envelhece conforme entram novos papéis na "
        "bolsa. Papéis não mapeados não recebem comparação setorial própria.",
        "<b>Empresas cíclicas</b> ficam bem posicionadas no topo do ciclo, quando estão "
        "mais caras e mais arriscadas.",
        "<b>Não há histórico</b> de preço, proventos ou balanços trimestrais — a fonte "
        "entrega apenas a foto dos últimos 12 meses reportados.",
        "<b>Fonte única.</b> Se o Fundamentus sair do ar ou mudar de formato, o sistema "
        "para.",
    ]))

    add(H2("Perguntas frequentes"))

    add(H3("O site calcula o P/L e o P/VP?"))
    add(P("Não. O Fundamentus já publica esses múltiplos prontos, e o programa apenas lê "
          "o valor. A única matemática feita aqui é a das notas percentis e dos três "
          "scores."))

    add(H3("O preço é em tempo real?"))
    add(P("Não. É o último fechamento disponível no momento da coleta. Entre uma coleta e "
          "outra, o valor exibido fica parado por até 24 horas. Para triagem isso é "
          "suficiente; para executar uma ordem, use a cotação ao vivo da corretora."))

    add(H3("Por que aparecem números negativos em Dív. Líq./Patrim.?"))
    add(P("Porque a coluna é <b>dívida líquida</b>, que já desconta o caixa. Quando a "
          "empresa tem mais dinheiro em caixa do que dívida, o resultado fica negativo. "
          "<b>Negativo aqui é bom</b> — e o score trata assim, porque o fator é "
          "“menor melhor”."))

    add(H3("Por que bancos não aparecem?"))
    add(P("Porque três dos cinco indicadores do score — somando 65% do peso — não "
          "significam nada quando aplicados a uma instituição financeira. A Parte 4 "
          "explica em detalhe. Não é julgamento sobre a qualidade dessas empresas: é "
          "reconhecer que este método não sabe avaliá-las."))

    add(H3("Com que frequência atualiza?"))
    add(P("Todo dia às 22h de Brasília, automaticamente. Inclusive fins de semana, quando "
          "a coleta simplesmente repete o último fechamento útil."))

    add(H3("Preciso instalar alguma coisa?"))
    add(P("Não. Basta abrir o endereço no navegador. A instalação como aplicativo é "
          "opcional e serve para ter ícone próprio e funcionamento sem internet."))

    add(H3("Custa alguma coisa? Tem cadastro?"))
    add(P("Não e não. É uma página pública e gratuita, sem login, sem coleta de dados "
          "pessoais e sem anúncio."))

    add(Spacer(1, 14))
    add(_regua(NAVY, 1.2))
    add(Spacer(1, 8))
    add(caixa("Lembrete final",
              "<b>Este documento e o site que ele descreve não constituem recomendação de "
              "investimento.</b> Trata-se de uma ferramenta de estudo, construída para "
              "reduzir centenas de papéis a uma lista curta que mereça análise "
              "aprofundada. Os pesos são escolhas defensáveis, mas não testadas "
              "historicamente. Toda decisão de investimento é sua, sob sua "
              "responsabilidade, e deve considerar seus objetivos, seu prazo e sua "
              "tolerância a risco.", AMBAR, AMBAR_BG))
    add(Spacer(1, 10))
    add(P(f"Manual gerado a partir da coleta de {data_br}.<br/>"
          "Código-fonte: github.com/macedomatheus0601-cell/Viapp", "nota"))

    return S


def main() -> None:
    d = json.loads(Path("dados/atual.json").read_text(encoding="utf-8"))
    saida = "Manual-Ranking-B3.pdf"

    doc = BaseDocTemplate(
        saida, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=MARGEM + 4 * mm, bottomMargin=MARGEM + 3 * mm,
        title="Ranking de Qualidade B3 — Manual completo",
        author="macedomatheus0601-cell",
        subject="Como o score é calculado, como navegar e como analisar",
    )
    quadro = Frame(MARGEM, MARGEM + 3 * mm, UTIL,
                   ALTURA - 2 * MARGEM - 7 * mm, id="q")
    doc.addPageTemplates([
        PageTemplate(id="capa", frames=[quadro], onPage=capa),
        PageTemplate(id="miolo", frames=[quadro], onPage=miolo),
    ])
    doc.build(constroi(d))
    print(f"OK -> {saida}")


if __name__ == "__main__":
    main()

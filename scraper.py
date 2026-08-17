"""
Coleta o resultado.php do Fundamentus, aplica os filtros de elegibilidade,
calcula os tres esquemas de pontuacao e grava os JSONs consumidos pelo site.

Saida:
    dados/atual.json                  -> ultimo retrato bem-sucedido
    dados/historico/AAAA-MM-DD.json   -> snapshot enxuto do dia

Rodar local:  python scraper.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone, timedelta

from pathlib import Path

import pandas as pd
import requests

from setores import CICLICAS, EXCLUIR, SETOR

# ----------------------------------------------------------------------
# CONFIGURACAO
# ----------------------------------------------------------------------

FONTE = "https://www.fundamentus.com.br/resultado.php"

# Liq.2meses do Fundamentus = volume financeiro medio negociado por dia, em R$.
# 1.000.000 e o corte padrao. Ver justificativa no README.
CORTE_LIQUIDEZ = 1_000_000

# Fator: (chave, rotulo, peso, direcao)  direcao 'hi' = maior melhor
FATORES = [
    ("roic", "ROIC", 0.30, "hi"),
    ("cresc", "Cresc. Rec. 5a", 0.20, "hi"),
    ("evebitda", "EV/EBITDA", 0.20, "lo"),
    ("mrgeb", "Margem EBIT", 0.15, "hi"),
    ("div", "Div./Patrim.", 0.15, "lo"),
]
PESO_IGUAL = 1 / len(FATORES)
MIN_PARES_SETOR = 5

SAIDA = Path("dados")
TZ_BR = timezone(timedelta(hours=-3))

# Cabecalho do Fundamentus normalizado -> chave interna.
COLMAP = {
    "papel": "papel",
    "cotacao": "cot",
    "pl": "pl",
    "pvp": "pvp",
    "psr": "psr",
    "divyield": "dy",
    "pativo": "pativo",
    "pcapgiro": "pcapgiro",
    "pebit": "pebit",
    "pativcircliq": "pacl",
    "evebit": "evebit",
    "evebitda": "evebitda",
    "mrgbruta": "mrgbruta",
    "mrgebit": "mrgeb",
    "mrgliq": "mrgliq",
    "liqcorr": "liqcorr",
    "roic": "roic",
    "roe": "roe",
    "liq2meses": "liq",
    "patrimliq": "patr",
    "divbrutpatrim": "div",
    "divliqpatrim": "div",
    "crescrec5a": "cresc",
}
OBRIGATORIAS = ["papel", "roic", "mrgeb", "div", "evebitda", "cresc", "liq"]


# ----------------------------------------------------------------------
# LEITURA
# ----------------------------------------------------------------------

def normaliza(s) -> str:
    """'Div.Yield' -> 'divyield'. Mesma regra do HTML original."""
    s = str(s or "").lower()
    s = (s.replace("á", "a").replace("ã", "a").replace("â", "a").replace("à", "a")
          .replace("é", "e").replace("ê", "e").replace("í", "i")
          .replace("ó", "o").replace("õ", "o").replace("ô", "o")
          .replace("ú", "u").replace("ç", "c"))
    return re.sub(r"[^a-z0-9]", "", s)


def para_numero(raw):
    """Converte texto pt-BR em float. Percentual vira fracao (12,3% -> 0.123)."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s in ("", "-", "--", "N/A", "nan"):
        return None
    pct = "%" in s
    s = s.replace("%", "").replace("R$", "").replace("\xa0", "").replace(" ", "")
    tem_ponto, tem_virgula = "." in s, "," in s
    if tem_ponto and tem_virgula:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif tem_virgula:
        s = s.replace(",", "") if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    elif tem_ponto and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        n = float(s)
    except ValueError:
        return None
    if n != n or n in (float("inf"), float("-inf")):
        return None
    return n / 100 if pct else n


def baixa(url: str = FONTE) -> str:
    # O Fundamentus responde 403 para user-agent nao usual. Uma requisicao por dia.
    cab = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get(url, headers=cab, timeout=45)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "latin-1"
    return r.text


def celulas(html: str) -> list[list[str]]:
    """Extrai a maior tabela da pagina como texto puro — sem pandas adivinhar tipos."""
    from lxml import html as lx

    tabelas = lx.fromstring(html).xpath("//table")
    if not tabelas:
        raise RuntimeError("Nenhuma tabela encontrada na pagina.")
    maior = max(tabelas, key=lambda t: len(t.xpath(".//tr")))
    linhas = []
    for tr in maior.xpath(".//tr"):
        cels = [" ".join(td.text_content().split())
                for td in tr.xpath("./td|./th")]
        if cels:
            linhas.append(cels)
    if len(linhas) < 2:
        raise RuntimeError("A tabela veio sem linhas de dados.")
    return linhas


def le_tabela(html: str) -> pd.DataFrame:
    linhas = celulas(html)
    cabecalho, corpo = linhas[0], linhas[1:]
    largura = len(cabecalho)
    bruto = pd.DataFrame(
        [(l + [""] * largura)[:largura] for l in corpo], columns=cabecalho
    )

    ren, vistos = {}, set()
    for col in bruto.columns:
        chave = COLMAP.get(normaliza(col))
        if chave and chave not in vistos:
            ren[col] = chave
            vistos.add(chave)
    df = bruto[list(ren)].rename(columns=ren)

    faltando = [c for c in OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise RuntimeError(
            f"Colunas ausentes: {faltando}. O layout do Fundamentus mudou — "
            f"cabecalhos lidos: {[normaliza(c) for c in bruto.columns]}"
        )

    df["papel"] = df["papel"].astype(str).str.strip().str.upper()
    for col in df.columns:
        if col != "papel":
            df[col] = df[col].map(para_numero)
    return df[df["papel"].str.fullmatch(r"[A-Z]{4}\d{1,2}")].reset_index(drop=True)


# ----------------------------------------------------------------------
# CALCULO
# ----------------------------------------------------------------------

def elimina(df: pd.DataFrame, corte: int) -> pd.DataFrame:
    """Marca cada papel com o motivo da eliminacao (None = elegivel). Ordem importa."""
    def motivo(r):
        if r["papel"] in EXCLUIR:
            return "banco, seguradora ou holding"
        if pd.isna(r["liq"]) or r["liq"] < corte:
            return "liquidez abaixo do corte"
        if pd.isna(r["evebitda"]) or r["evebitda"] <= 0:
            return "EV/EBITDA nulo ou negativo"
        if pd.notna(r.get("patr")) and r["patr"] <= 0:
            return "patrimonio liquido negativo"
        if r["mrgeb"] == 0 and r["roic"] == 0:
            return "indicadores zerados na fonte"
        if any(pd.isna(r[k]) for k, *_ in FATORES):
            return "indicador faltando"
        return None

    df = df.copy()
    df["motivo"] = df.apply(motivo, axis=1)

    # Uma linha por emissor: fica a classe mais liquida (ON/PN/UNIT do mesmo CNPJ).
    viva = df[df["motivo"].isna()]
    campeoes = viva.loc[viva.groupby(viva["papel"].str[:4])["liq"].idxmax(), "papel"]
    campeoes = set(campeoes)
    base = {p[:4]: p for p in campeoes}
    perdedor = df["motivo"].isna() & ~df["papel"].isin(campeoes)
    df.loc[perdedor, "motivo"] = df.loc[perdedor, "papel"].map(
        lambda p: f"outra classe do mesmo emissor e mais liquida ({base[p[:4]]})"
    )
    return df


def percentis(df: pd.DataFrame, prefixo: str) -> pd.DataFrame:
    """Nota 0-100 pela posicao no universo. Empate recebe a media das posicoes."""
    n = len(df)
    for chave, _, _, direcao in FATORES:
        if n < 2:
            df[prefixo + chave] = 50.0
            continue
        pos = df[chave].rank(method="average", ascending=(direcao == "lo"))
        df[prefixo + chave] = (n - pos) / (n - 1) * 100
    return df


def pontua(df: pd.DataFrame) -> pd.DataFrame:
    elig = df[df["motivo"].isna()].copy()
    if elig.empty:
        raise RuntimeError("Nenhum papel elegivel — verifique o corte de liquidez.")

    # A (principal) e C (pesos iguais): percentil contra a bolsa inteira.
    elig = percentis(elig, "n_")
    elig["score"] = sum(elig["n_" + k] * w for k, _, w, _ in FATORES)
    elig["scoreIg"] = sum(elig["n_" + k] * PESO_IGUAL for k, *_ in FATORES)

    # B (setorial): percentil so contra os pares. Setor pequeno herda a nota global.
    elig["setor"] = elig["papel"].map(SETOR).fillna("nao_mapeado")
    elig["setorOk"] = False
    for nome, grupo in elig.groupby("setor"):
        alvo = elig.index.isin(grupo.index)
        if nome == "nao_mapeado" or len(grupo) < MIN_PARES_SETOR:
            for k, *_ in FATORES:
                elig.loc[alvo, "s_" + k] = elig.loc[alvo, "n_" + k]
        else:
            g = percentis(grupo.copy(), "s_")
            for k, *_ in FATORES:
                elig.loc[g.index, "s_" + k] = g["s_" + k]
            elig.loc[alvo, "setorOk"] = True
    elig["scoreSet"] = sum(elig["s_" + k] * w for k, _, w, _ in FATORES)

    for campo, chave in (("pos", "score"), ("posSet", "scoreSet"), ("posIg", "scoreIg")):
        elig[campo] = elig[chave].rank(method="first", ascending=False).astype(int)

    # Consenso: em quantos dos 3 esquemas o papel esta no decil superior.
    topn = max(5, min(30, round(len(elig) * 0.10)))
    elig["consenso"] = sum((elig[c] <= topn).astype(int) for c in ("pos", "posSet", "posIg"))
    elig["topN"] = topn
    elig["ciclica"] = elig["papel"].isin(CICLICAS)
    return elig.sort_values("pos")


# ----------------------------------------------------------------------
# SAIDA
# ----------------------------------------------------------------------

def limpa(v):
    if v is None or (isinstance(v, float) and v != v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    return round(v, 6) if isinstance(v, float) else v


def monta(elig: pd.DataFrame, todos: pd.DataFrame, corte: int) -> dict:
    campos = ["papel", "setor", "pos", "posSet", "posIg", "score", "scoreSet", "scoreIg",
              "consenso", "setorOk", "ciclica", "roic", "roe", "cresc", "evebitda", "evebit",
              "mrgeb", "mrgbruta", "mrgliq", "div", "liq", "patr", "cot", "pl", "pvp", "dy",
              "liqcorr"] + ["n_" + k for k, *_ in FATORES] + ["s_" + k for k, *_ in FATORES]
    campos = [c for c in campos if c in elig.columns]

    eliminados = todos[todos["motivo"].notna()]
    resumo = eliminados["motivo"].str.replace(r" \(.*\)", "", regex=True).value_counts()

    return {
        "meta": {
            "coletado_em": datetime.now(TZ_BR).isoformat(timespec="seconds"),
            "fonte": FONTE,
            "corte_liquidez": corte,
            "papeis_lidos": len(todos),
            "elegiveis": len(elig),
            "top_n_consenso": int(elig["topN"].iloc[0]),
            "fatores": [{"chave": k, "rotulo": r, "peso": w, "direcao": d}
                        for k, r, w, d in FATORES],
            "eliminados_por_motivo": {k: int(v) for k, v in resumo.items()},
        },
        "acoes": [{c: limpa(r[c]) for c in campos} for _, r in elig.iterrows()],
        "eliminados": [{"papel": r["papel"], "motivo": r["motivo"], "liq": limpa(r["liq"])}
                       for _, r in eliminados.iterrows()],
    }


def grava(pacote: dict) -> None:
    (SAIDA / "historico").mkdir(parents=True, exist_ok=True)
    (SAIDA / "atual.json").write_text(
        json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")

    dia = pacote["meta"]["coletado_em"][:10]
    enxuto = {
        "meta": pacote["meta"],
        "acoes": [{k: a[k] for k in ("papel", "pos", "score", "scoreSet", "scoreIg",
                                     "consenso", "roic", "cresc", "evebitda", "mrgeb", "div")}
                  for a in pacote["acoes"]],
    }
    (SAIDA / "historico" / f"{dia}.json").write_text(
        json.dumps(enxuto, ensure_ascii=False, indent=1), encoding="utf-8")

    indice = sorted(p.stem for p in (SAIDA / "historico").glob("*.json"))
    (SAIDA / "historico" / "indice.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    try:
        print(f"Baixando {FONTE} ...")
        df = le_tabela(baixa())
        print(f"  {len(df)} papeis lidos")

        df = elimina(df, CORTE_LIQUIDEZ)
        elig = pontua(df)
        print(f"  {len(elig)} elegiveis (corte R$ {CORTE_LIQUIDEZ:,}/dia)".replace(",", "."))

        pacote = monta(elig, df, CORTE_LIQUIDEZ)
        grava(pacote)

        print("\nTop 15 — esquema principal:")
        print(f"  {'#':>3} {'papel':<7} {'score':>6} {'cons':>5}  setor")
        for _, r in elig.head(15).iterrows():
            print(f"  {r['pos']:>3} {r['papel']:<7} {r['score']:>6.1f} "
                  f"{r['consenso']:>4}/3  {r['setor']}")
        print(f"\nOK -> dados/atual.json")
        return 0
    except Exception as e:
        print(f"FALHOU: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

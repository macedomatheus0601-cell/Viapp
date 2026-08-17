"""Listas fixas portadas do rank_qualidade_b3.html — mantidas idênticas ao original."""

# Bancos, seguradoras e holdings financeiras: o score nao se aplica a eles.
EXCLUIR = {
    "ITUB4", "ITUB3", "BBDC4", "BBDC3", "BBAS3", "SANB11", "SANB4", "SANB3",
    "BPAC11", "BPAC3", "ABCB4", "BRSR6", "BRSR3", "BPAN4", "BMGB4", "BEES3",
    "BEES4", "PINE4", "BRBI11", "BAZA3", "ITSA4", "ITSA3", "BBSE3", "PSSA3",
    "CXSE3", "IRBR3", "WIZC3", "BRIV4", "MERC4", "BGIP4", "BICB4", "BICB3",
    "IDVL3", "IDVL4", "SAUD3", "MODL3", "MODL4", "MODL11", "BNCA3", "BECE3",
    "BECE4", "DMFN3",
}

# Setores ciclicos: usado apenas como ressalva na ficha, nao elimina.
CICLICAS = {
    "VALE3", "CSNA3", "GGBR4", "GGBR3", "GOAU4", "GOAU3", "USIM5", "USIM3",
    "USIM6", "BRAP4", "BRAP3", "CMIN3", "PETR3", "PETR4", "PRIO3", "RECV3",
    "RRRP3", "BRAV3", "SUZB3", "KLBN11", "KLBN4", "KLBN3", "DXCO3", "RAIZ4",
    "SMTO3", "SLCE3", "AGRO3", "TTEN3", "VBBR3", "UGPA3", "BRKM5", "BRKM3",
    "BRKM6", "UNIP6", "UNIP3", "CSAN3", "JBSS3", "BEEF3", "MRFG3", "BRFS3",
    "MYPK3", "ETER3", "FESA4", "PMAM3", "PMAM4", "EUCA4", "RANI3", "TUPY3",
    "TUPY4", "POMO4", "LEVE3", "CBAV3", "MTSA4", "FHER3", "AURA33",
}

# Mapa ticker -> setor. Setor com menos de 5 elegiveis nao recebe pontuacao setorial.
_SETORES = {
    "alimentos": [
        "ABEV3", "AGRO3", "BEEF3", "BRFS3", "CAML3", "JALL3",
        "JBSS3", "MDIA3", "MRFG3", "NTCO3", "SLCE3", "SMTO3",
        "SOJA3", "TTEN3",
    ],
    "construcao": [
        "AVLL3", "CCIM3", "CURY3", "CYRE3", "DIRR3", "EVEN3",
        "EZTC3", "GFSA3", "HBOR3", "JHSF3", "LAVV3", "MDNE3",
        "MRVE3", "MTRE3", "PDGR3", "PLPL3", "RDNI3", "TCSA3",
        "TEND3", "TRIS3", "VIVR3",
    ],
    "educacao": [
        "ANIM3", "COGN3", "SEDU3", "SEER3", "VTRU3", "YDUQ3",
        "ZAMP3",
    ],
    "eletrica": [
        "AESB3", "ALUP11", "ALUP4", "AURE3", "CEED3", "CMIG3",
        "CMIG4", "CPLE3", "CPLE6", "EGIE3", "ELET3", "ELET6",
        "EMAE4", "ENGI11", "ENGI4", "EQTL3", "GEPA4", "NEOE3",
        "RNEW11", "SRNA3", "TAEE11", "TAEE3", "TAEE4", "TRPL4",
    ],
    "imobiliario": [
        "ALOS3", "BRPR3", "HBRE3", "IGTI11", "IGTI3", "LAND3",
        "MULT3", "SCAR3", "SYNE3",
    ],
    "industria": [
        "AERI3", "ARML3", "DXCO3", "EALT4", "ETER3", "FRAS3",
        "INEP3", "KEPL3", "LEVE3", "MTSA4", "MWET4", "MYPK3",
        "POMO4", "PTBL3", "RAPT4", "ROMI3", "SHUL4", "TASA3",
        "TASA4", "TUPY3", "WEGE3",
    ],
    "logistica": [
        "CCRO3", "ECOR3", "HBSA3", "JSLG3", "LOGG3", "LOGN3",
        "MILS3", "MOTV3", "PORT3", "RAIL3", "RENT3", "SIMH3",
        "STBP3", "TGMA3", "VAMO3",
    ],
    "mineracao": [
        "AURA33", "BRAP4", "CMIN3", "CSNA3", "FESA4", "GGBR4",
        "GOAU4", "MMXM3", "PMAM3", "USIM3", "USIM5", "VALE3",
    ],
    "papel": [
        "ARCZ3", "EUCA4", "KLBN11", "KLBN3", "KLBN4", "RANI3",
        "SUZB3",
    ],
    "petroleo": [
        "BRAV3", "CSAN3", "ENAT3", "OGXP3", "PETR3", "PETR4",
        "PRIO3", "RAIZ4", "RECV3", "RRRP3", "UGPA3", "VBBR3",
    ],
    "quimica": [
        "BRKM3", "BRKM5", "CRPG5", "FHER3", "SZPQ4", "UNIP3",
        "UNIP6",
    ],
    "saneamento": [
        "AMBP3", "CSMG3", "IGUA3", "ORVR3", "SAPR11", "SAPR3",
        "SAPR4", "SBSP3",
    ],
    "saude": [
        "AALR3", "AMIL3", "BLAU3", "DASA3", "FLRY3", "HAPV3",
        "HYPE3", "MATD3", "ONCO3", "PARD3", "PNVL3", "QUAL3",
        "RDOR3", "SAUD3",
    ],
    "tecnologia": [
        "BMOB3", "CASH3", "DTCY3", "IFCM3", "INTB3", "LINX3",
        "LWSA3", "NGRD3", "SQIA3", "TOKY3", "TOTS3",
    ],
    "telecom": [
        "BRTP3", "DESK3", "EBTP3", "FIQE3", "OIBR3", "OIBR4",
        "TIMS3", "VIVT3",
    ],
    "turismo": [
        "AZUL4", "BHGR3", "CVCB3", "GOLL4", "HOTL3", "LATM11",
    ],
    "varejo": [
        "ALPA4", "AMAR3", "AMER3", "ARZZ3", "ASAI3", "BHIA3",
        "CEAB3", "CRFB3", "ENJU3", "ESPA3", "GRND3", "GUAR3",
        "LJQQ3", "LREN3", "LVTC3", "MEAL3", "MGLU3", "MLAS3",
        "PCAR3", "PETZ3", "PGMN3", "RADL3", "SBFG3", "SMFT3",
        "SOMA3", "TFCO4", "VIVA3", "VULC3", "WEST3",
    ],
}

SETOR = {t: s for s, ts in _SETORES.items() for t in ts}

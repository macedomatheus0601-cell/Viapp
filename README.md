# Ranking de Qualidade — B3

Ranking multifator de ações brasileiras, atualizado automaticamente todo dia a partir do
[Fundamentus](https://www.fundamentus.com.br/resultado.php).

O objetivo é responder uma pergunta: **quais empresas da B3 combinam boa rentabilidade,
crescimento e alavancagem controlada sem estar caras?** — e responder de forma que a
resposta possa ser auditada e acompanhada ao longo do tempo.

## Como o score é montado

Cada indicador vira uma nota de 0 a 100 conforme a **posição percentil** da empresa no
universo elegível, não pelo valor bruto. Isso torna os pesos comparáveis entre si.

| Fator | Peso | Direção | Por quê |
|---|---|---|---|
| ROIC | 30% | maior melhor | melhor proxy de vantagem competitiva |
| Cresc. Rec. 5a | 20% | maior melhor | o crescimento que se quer capturar |
| EV/EBITDA | 20% | menor melhor | impede pagar caro pela qualidade |
| Margem EBIT | 15% | maior melhor | eficiência da operação |
| Dív./Patrimônio | 15% | menor melhor | sobrevivência em crise |

**Filtro elimina, score não pune.** Empresas inelegíveis saem antes de pontuar — se
virassem "nota baixa", uma empresa ruim poderia compensar com outros critérios e subir
no ranking. Ordem dos cortes:

1. Banco, seguradora ou holding financeira (o score não se aplica a eles)
2. Liquidez abaixo de R$ 1.000.000/dia
3. EV/EBITDA nulo ou negativo
4. Patrimônio líquido negativo
5. Margem EBIT e ROIC ambos zerados na fonte
6. Qualquer fator faltando
7. Classe menos líquida do mesmo emissor (fica uma linha por empresa)

## Os três esquemas

As duas decisões mais frágeis de qualquer score são a escolha dos pesos e a escolha do
universo de comparação. Em vez de escondê-las, os três esquemas rodam em paralelo:

| | Pesos | Universo do percentil |
|---|---|---|
| **A · Principal** | os da tabela acima | bolsa inteira |
| **B · Setorial** | os da tabela acima | apenas pares do setor (mín. 5) |
| **C · Pesos iguais** | 20% para cada | bolsa inteira |

**Consenso 3/3** = o papel está no decil superior dos três ao mesmo tempo. Isso não diz
que a empresa é boa; diz que a posição dela não é artefato das escolhas de quem montou
o score.

## Arquitetura

```
scraper.py    coleta, filtra, pontua e grava os JSONs
setores.py    listas fixas: exclusões, cíclicas, mapa ticker→setor
dados/
  atual.json              último retrato completo
  historico/AAAA-MM-DD.json   snapshot diário enxuto
  historico/indice.json       lista de datas disponíveis
```

O GitHub Actions roda o scraper às 22h de Brasília, commita os JSONs, e o site estático
lê esses arquivos. Não há servidor nem banco de dados.

## Rodar local

```bash
pip install -r requirements.txt
python scraper.py
```

## Limitações

- **Não é backtest.** Os pesos são plausíveis, não testados historicamente. Não há
  evidência de que produzam retorno superior.
- **Não é recomendação de investimento.** É uma ferramenta de triagem que reduz ~350
  papéis a uma lista curta para análise qualitativa.
- Os dados do Fundamentus são dos últimos 12 meses reportados e podem estar
  desatualizados frente ao último balanço.
- O mapa de setores é manual e envelhece conforme entram novos papéis na bolsa.
- Empresas cíclicas ficam bem no ranking no topo do ciclo, quando estão mais caras.

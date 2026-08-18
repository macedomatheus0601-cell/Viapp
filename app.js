/* ------------------------------------------------------------------
   Rank de Qualidade — B3
   Le dados/atual.json (gravado pelo scraper.py e atualizado todo dia
   pelo GitHub Actions) e monta as cinco abas. Sem servidor, sem banco.
   ------------------------------------------------------------------ */

"use strict";

const $  = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

let DADOS = null;        // pacote completo do JSON
let ACOES = [];          // acoes elegiveis, ja ordenadas pelo esquema A

// ================================================================ tema

/* Tres estados: "sistema" (segue o SO), "claro" e "escuro". O atributo
   data-tema no <html> e o que a folha de estilo le; sem atributo, vale
   a preferencia do sistema. */

function temaAtual() {
  return document.documentElement.dataset.tema || "sistema";
}

function sistemaEscuro() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function pintarBotao() {
  const t = temaAtual();
  const escuro = t === "escuro" || (t === "sistema" && sistemaEscuro());
  const rotulo = { sistema: "Automático", claro: "Claro", escuro: "Escuro" }[t];

  $("#btnTema .tema-icone").textContent = t === "sistema" ? "🖥️" : (escuro ? "🌙" : "☀️");
  $("#btnTema .tema-texto").textContent = rotulo;
  $("#btnTema").setAttribute("title", `Tema: ${rotulo}. Clique para alternar.`);
  $("#btnTema").setAttribute("aria-label", `Tema ${rotulo}. Clique para alternar.`);
}

/* A barra do navegador (e a do app instalado) e pintada pela meta theme-color.
   As duas do HTML respondem so ao sistema, entao a escolha manual precisa
   escrever uma terceira, sem media, que vence as outras. */
function pintarBarraNavegador() {
  const escuro = document.documentElement.dataset.tema === "escuro"
    || (!document.documentElement.dataset.tema && sistemaEscuro());

  let meta = document.querySelector('meta[name="theme-color"]:not([media])');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "theme-color";
    document.head.appendChild(meta);
  }
  meta.content = escuro ? "#0f172a" : "#ffffff";
}

function aplicarTema(t) {
  if (t === "sistema") delete document.documentElement.dataset.tema;
  else document.documentElement.dataset.tema = t;

  try {
    if (t === "sistema") localStorage.removeItem("tema");
    else localStorage.setItem("tema", t);
  } catch (e) { /* navegacao anonima pode bloquear */ }

  pintarBotao();
  pintarBarraNavegador();
}

$("#btnTema").addEventListener("click", () => {
  const ciclo = { sistema: "claro", claro: "escuro", escuro: "sistema" };
  aplicarTema(ciclo[temaAtual()]);
});

// Se estiver em "sistema" e o SO trocar de tema, o rotulo do botao acompanha.
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (temaAtual() === "sistema") { pintarBotao(); pintarBarraNavegador(); }
});

pintarBotao();
pintarBarraNavegador();

// ============================================================= formato

const nulo = (v) => v === null || v === undefined || Number.isNaN(v);

/** Fracao -> percentual. 0.2426 vira "24,3%". */
function pct(v, casas = 1) {
  if (nulo(v)) return "—";
  return (v * 100).toFixed(casas).replace(".", ",") + "%";
}

/** Numero simples com virgula decimal. */
function num(v, casas = 2) {
  if (nulo(v)) return "—";
  return v.toFixed(casas).replace(".", ",");
}

/** Multiplo: 1.88 vira "1,88x". */
function mult(v, casas = 2) {
  if (nulo(v)) return "—";
  return num(v, casas) + "x";
}

/** Valor grande em reais, abreviado: 18334200 vira "R$ 18,3 mi". */
function reais(v) {
  if (nulo(v)) return "—";
  const abs = Math.abs(v);
  if (abs >= 1e9) return "R$ " + num(v / 1e9, 1) + " bi";
  if (abs >= 1e6) return "R$ " + num(v / 1e6, 1) + " mi";
  if (abs >= 1e3) return "R$ " + num(v / 1e3, 0) + " mil";
  return "R$ " + num(v, 2);
}

function moeda(v) {
  if (nulo(v)) return "—";
  return "R$ " + num(v, 2);
}

function inteiro(v) {
  if (nulo(v)) return "—";
  return v.toLocaleString("pt-BR");
}

const FMT = { pct, num, mult, reais, moeda };

/** Escapa texto antes de injetar em HTML. */
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

/** "construcao" -> "Construção". Mapa explicito: o JSON vem sem acento. */
const NOME_SETOR = {
  alimentos: "Alimentos", construcao: "Construção", educacao: "Educação",
  eletrica: "Elétrica", imobiliario: "Imobiliário", industria: "Indústria",
  logistica: "Logística", mineracao: "Mineração", papel: "Papel e celulose",
  petroleo: "Petróleo e gás", quimica: "Química", saneamento: "Saneamento",
  saude: "Saúde", tecnologia: "Tecnologia", telecom: "Telecom",
  turismo: "Turismo", varejo: "Varejo", nao_mapeado: "Não mapeado",
};

const setorNome = (s) => NOME_SETOR[s] || s;

// ========================================================= indicadores

/* Catalogo do que cada campo do JSON significa. 'dir' hi = maior melhor,
   lo = menor melhor, null = sem julgamento (porte, preco).
   Os textos sao a parte que o numero sozinho nao entrega. */

const INDICADORES = {
  roic: {
    nome: "ROIC", completo: "Retorno sobre o Capital Investido",
    grupo: "rentabilidade", fmt: "pct", dir: "hi",
    oque: "Lucro operacional depois de impostos dividido pelo capital investido na operação (dívida mais patrimônio). Mede quanto a empresa produz com todo o dinheiro que emprega, sem importar se veio de sócio ou de banco.",
    ler: "Acima de ~15% ao ano costuma indicar operação forte. Mais importante que o número num ano é ele se sustentar: retorno alto atrai concorrente, então quem mantém tem alguma barreira real — marca, escala, contrato longo, custo de troca.",
    cuidado: "Ativos antigos, já depreciados, encolhem o denominador e inflam o ROIC. Empresa de capital leve (serviços, software) parece melhor que indústria pesada sem necessariamente ser.",
  },
  roe: {
    nome: "ROE", completo: "Retorno sobre o Patrimônio Líquido",
    grupo: "rentabilidade", fmt: "pct", dir: "hi",
    oque: "Lucro líquido dividido pelo patrimônio líquido. O retorno sobre o dinheiro dos sócios.",
    ler: "É o indicador de rentabilidade mais citado, e serve como conferência ao lado do ROIC. Quando o ROE é muito maior que o ROIC, a diferença normalmente é dívida.",
    cuidado: "O ROE sobe quando a empresa se endivida, sem que nada tenha melhorado na operação: a dívida encolhe o patrimônio, e o mesmo lucro passa a dividir uma base menor. É por isso que o score usa ROIC como fator, e não ROE.",
  },
  cresc: {
    nome: "Cresc. Receita 5a", completo: "Crescimento anualizado da receita em 5 anos",
    grupo: "crescimento", fmt: "pct", dir: "hi",
    oque: "Taxa média anual de crescimento da receita líquida nos últimos cinco anos.",
    ler: "Cinco anos é longo o bastante para atravessar um ciclo econômico e curto o bastante para descrever a empresa de hoje. Crescimento consistente costuma indicar mercado em expansão ou ganho de participação.",
    cuidado: "Receita crescendo não é lucro crescendo — dá para crescer vendendo mais barato e destruindo margem. Aquisições também entram aqui como se fossem crescimento próprio.",
  },
  mrgbruta: {
    nome: "Margem Bruta", completo: "Lucro bruto sobre receita",
    grupo: "eficiencia", fmt: "pct", dir: "hi",
    oque: "Receita menos o custo direto do que foi vendido, dividido pela receita.",
    ler: "É a medida mais direta de poder de precificação: margem bruta alta significa que o cliente aceita pagar bem acima do custo de produzir.",
    cuidado: "Varia enormemente entre setores. Um supermercado saudável opera com margem bruta que quebraria uma empresa de software.",
  },
  mrgeb: {
    nome: "Margem EBIT", completo: "Lucro operacional sobre receita",
    grupo: "eficiencia", fmt: "pct", dir: "hi",
    oque: "Lucro antes de juros e impostos, dividido pela receita. Quanto sobra de cada real vendido depois de todos os custos de operar, mas antes da conta do banco e do governo.",
    ler: "É a medida mais limpa de eficiência operacional, porque não é distorcida por estrutura de capital nem por regime tributário. Duas empresas iguais operando, uma endividada e outra não, têm a mesma margem EBIT.",
    cuidado: "Comparar entre setores engana. É exatamente por isso que existe o esquema B, que compara a empresa apenas com pares do próprio setor.",
  },
  mrgliq: {
    nome: "Margem Líquida", completo: "Lucro líquido sobre receita",
    grupo: "eficiencia", fmt: "pct", dir: "hi",
    oque: "O que sobra de cada real de receita depois absolutamente de tudo: custos, despesas, juros e impostos.",
    ler: "Útil para ver o efeito combinado de operação, dívida e carga tributária num número só.",
    cuidado: "É a margem mais contaminada por eventos que não se repetem — venda de um imóvel, reversão de provisão, crédito fiscal reconhecido de uma vez. Um ano excelente pode não dizer nada sobre o próximo.",
  },
  evebitda: {
    nome: "EV/EBITDA", completo: "Valor da firma sobre geração de caixa operacional",
    grupo: "valuation", fmt: "mult", dir: "lo",
    oque: "Valor da firma (valor de mercado mais dívida líquida) dividido pelo EBITDA. Grosso modo: quantos anos de geração de caixa operacional pagariam a empresa inteira, dívida incluída.",
    ler: "Quanto menor, mais barata. É preferível ao P/L para comparar empresas porque enxerga a dívida — comprar uma empresa endividada significa herdar a dívida junto.",
    cuidado: "O EBITDA ignora o investimento necessário só para manter a operação de pé. Empresa que precisa reinvestir pesado todo ano aparece barata aqui sem ser.",
  },
  evebit: {
    nome: "EV/EBIT", completo: "Valor da firma sobre lucro operacional",
    grupo: "valuation", fmt: "mult", dir: "lo",
    oque: "Igual ao EV/EBITDA, mas usando o lucro operacional depois da depreciação e amortização.",
    ler: "Mais conservador que o EV/EBITDA. A depreciação é uma estimativa do desgaste dos ativos: não sai do caixa hoje, mas a máquina vai precisar ser trocada.",
    cuidado: "Em setores de ativo muito pesado, a depreciação contábil pode estar longe do gasto real de reposição, para mais ou para menos.",
  },
  pl: {
    nome: "P/L", completo: "Preço sobre lucro por ação",
    grupo: "valuation", fmt: "mult", dir: "lo",
    oque: "Preço da ação dividido pelo lucro por ação dos últimos 12 meses. Quantos anos do lucro atual pagariam o preço de hoje.",
    ler: "O múltiplo mais conhecido, útil como referência rápida dentro de um mesmo setor.",
    cuidado: "Ignora a dívida por completo: uma empresa muito endividada pode exibir P/L baixo e ser cara de verdade. Além disso, perde o sentido quando o lucro é pequeno (o número explode) ou negativo.",
  },
  pvp: {
    nome: "P/VP", completo: "Preço sobre valor patrimonial",
    grupo: "valuation", fmt: "mult", dir: "lo",
    oque: "Preço da ação dividido pelo patrimônio líquido por ação.",
    ler: "Abaixo de 1 significa que o mercado paga menos do que o valor contábil do patrimônio.",
    cuidado: "Patrimônio contábil não é valor real. Marca, software e equipe não aparecem no balanço; imóveis podem estar registrados por valor de décadas atrás. Funciona melhor para bancos e seguradoras — que este rank exclui — do que para empresas operacionais.",
  },
  dy: {
    nome: "Dividend Yield", completo: "Proventos dos últimos 12 meses sobre o preço",
    grupo: "valuation", fmt: "pct", dir: "hi",
    oque: "Dividendos e juros sobre capital próprio pagos nos últimos 12 meses, divididos pela cotação atual.",
    ler: "Mostra o retorno em caixa que o preço de hoje teria produzido no último ano.",
    cuidado: "Olha para trás e não promete nada. Yield alto pode ser preço em queda, não dividendo generoso — o denominador encolheu. E pode vir de um pagamento extraordinário que não se repete.",
  },
  div: {
    nome: "Dív. Líq./Patrim.", completo: "Dívida líquida sobre patrimônio líquido",
    grupo: "endividamento", fmt: "mult", dir: "lo",
    oque: "Dívida bruta menos caixa e aplicações financeiras, dividido pelo patrimônio líquido. É quanto a empresa deve, já descontado o dinheiro que ela tem.",
    ler: "Quanto menor, mais folga. <strong>Valor negativo é bom</strong>: significa caixa maior que dívida, ou seja, a empresa tem caixa líquido. É por isso que aparecem números negativos nesta coluna.",
    cuidado: "Não diz nada sobre o custo nem sobre o prazo da dívida. Dívida barata vencendo em dez anos e dívida cara vencendo no ano que vem aparecem exatamente iguais aqui.",
  },
  liqcorr: {
    nome: "Liquidez Corrente", completo: "Ativo circulante sobre passivo circulante",
    grupo: "endividamento", fmt: "mult", dir: "hi",
    oque: "O que a empresa tem para receber ou converter em dinheiro no próximo ano, dividido pelo que ela tem para pagar no próximo ano.",
    ler: "Acima de 1 indica que os compromissos de curto prazo estão cobertos pelos recursos de curto prazo.",
    cuidado: "Estoque conta como ativo circulante mesmo quando está encalhado. Um varejista com armazém cheio de produto que não vende exibe liquidez corrente confortável.",
  },
  patr: {
    nome: "Patrimônio Líquido", completo: "Valor contábil do patrimônio",
    grupo: "porte", fmt: "reais", dir: null,
    oque: "Ativos menos passivos, pelo valor registrado na contabilidade.",
    ler: "Serve aqui como referência de porte da empresa.",
    cuidado: "Patrimônio líquido negativo elimina a empresa do rank antes de qualquer pontuação: significa que as dívidas superam os ativos contábeis.",
  },
  liq: {
    nome: "Volume médio/dia", completo: "Liquidez média diária dos últimos 2 meses",
    grupo: "porte", fmt: "reais", dir: null,
    oque: "Volume financeiro médio negociado por dia na bolsa nos últimos dois meses.",
    ler: "É o filtro de entrada do rank. Abaixo do corte de R$ 1 milhão por dia o papel é eliminado antes de pontuar.",
    cuidado: "Preço de ativo que quase não negocia não reflete valor de mercado — e, na prática, você pode não conseguir vender a posição sem derrubar a cotação.",
  },
  cot: {
    nome: "Cotação", completo: "Preço de fechamento",
    grupo: "porte", fmt: "moeda", dir: null,
    oque: "Preço da ação no fechamento do dia da coleta.",
    ler: "O preço isolado não diz se a ação é cara ou barata — só os múltiplos dizem, porque relacionam preço a lucro, caixa ou patrimônio.",
    cuidado: "Preço baixo em reais não significa ação barata. Uma ação de R$ 2 pode estar cara e uma de R$ 300, barata.",
  },
};

const GRUPOS = [
  { id: "rentabilidade", titulo: "Rentabilidade",
    desc: "Quanto a empresa gera sobre o capital que emprega. É a família de indicadores com maior peso no score." },
  { id: "crescimento", titulo: "Crescimento",
    desc: "Se a empresa está ganhando tamanho ao longo dos anos." },
  { id: "eficiencia", titulo: "Margens e eficiência",
    desc: "Quanto sobra de cada real vendido, em três estágios: antes dos custos indiretos, depois deles, e depois de tudo." },
  { id: "valuation", titulo: "Preço e múltiplos",
    desc: "O que o mercado está cobrando pela empresa hoje, em relação a lucro, caixa e patrimônio." },
  { id: "endividamento", titulo: "Endividamento e solvência",
    desc: "Capacidade de atravessar uma crise sem depender da boa vontade dos credores." },
  { id: "porte", titulo: "Porte e negociação",
    desc: "Tamanho da empresa e quanto o papel realmente negocia na bolsa." },
];

// ================================================================ carga

async function carregar() {
  let resp;
  try {
    resp = await fetch("dados/atual.json", { cache: "no-store" });
  } catch (e) {
    return falhar(
      "Não consegui ler os dados.",
      "Se você abriu o arquivo com duplo clique, o navegador bloqueia a leitura " +
      "do JSON por segurança (protocolo file://). É preciso servir a pasta por HTTP."
    );
  }
  if (!resp.ok) {
    return falhar("Não consegui ler os dados.", `O servidor respondeu ${resp.status}.`);
  }

  DADOS = await resp.json();
  ACOES = DADOS.acoes || [];

  montarCabecalho();
  montarResumo();
  montarFiltros();
  desenharTabela();
  montarSeletorFicha();
  montarLevantamentos();
  montarSetores();
  montarMetodo();
}

function falhar(titulo, detalhe) {
  $("#coletaData").textContent = "indisponível";
  $("#corpo").innerHTML =
    `<tr><td colspan="10"><strong>${esc(titulo)}</strong><br>${esc(detalhe)}</td></tr>`;
}

// ================================================================= topo

function montarCabecalho() {
  const d = new Date(DADOS.meta.coletado_em);

  $("#coletaData").textContent = d.toLocaleDateString("pt-BR", {
    day: "2-digit", month: "long", year: "numeric",
  });
  $("#coletaHora").textContent = "às " + d.toLocaleTimeString("pt-BR", {
    hour: "2-digit", minute: "2-digit",
  });

  // Coleta parada e problema: sinaliza em vez de exibir dado velho como se fosse novo.
  const dias = (Date.now() - d.getTime()) / 86400000;
  if (dias > 3) {
    $("#coleta").classList.add("velha");
    $("#coletaHora").textContent += ` · há ${Math.floor(dias)} dias`;
  }
}

function montarResumo() {
  const m = DADOS.meta;
  const tres = ACOES.filter((a) => a.consenso === 3).length;

  $("#resumo").innerHTML = [
    [inteiro(m.papeis_lidos), "papéis lidos na fonte"],
    [inteiro(m.elegiveis), "passaram nos filtros"],
    [inteiro(tres), "com consenso 3/3"],
    [reais(m.corte_liquidez), "corte de liquidez/dia"],
  ].map(([v, r]) =>
    `<div class="cartao"><span class="valor">${esc(v)}</span>
     <span class="rotulo">${esc(r)}</span></div>`
  ).join("");
}

// ========================================================== percentis

/* Recalcula, no navegador, a posicao percentil de QUALQUER indicador —
   nao so dos cinco que entram no score. Mesma formula do scraper.py
   (empate recebe a media das posicoes), para os numeros baterem. */

const _cachePerc = {};

function percentilDe(chave) {
  if (_cachePerc[chave]) return _cachePerc[chave];

  const ind = INDICADORES[chave];
  const validos = ACOES.filter((a) => !nulo(a[chave]));
  const n = validos.length;
  const mapa = new Map();

  if (n < 2 || !ind || !ind.dir) {
    _cachePerc[chave] = mapa;
    return mapa;
  }

  const ordenado = validos.slice().sort((a, b) =>
    ind.dir === "lo" ? a[chave] - b[chave] : b[chave] - a[chave]);

  let i = 0;
  while (i < n) {
    let j = i;
    while (j + 1 < n && ordenado[j + 1][chave] === ordenado[i][chave]) j++;
    const posMedia = (i + j) / 2 + 1;                 // posicoes 1-based
    const nota = (n - posMedia) / (n - 1) * 100;
    for (let k = i; k <= j; k++) mapa.set(ordenado[k].papel, nota);
    i = j + 1;
  }

  _cachePerc[chave] = mapa;
  return mapa;
}

function medianaSetor(setor, chave) {
  const v = ACOES.filter((a) => a.setor === setor && !nulo(a[chave])).map((a) => a[chave]);
  return mediana(v);
}

function mediana(v) {
  if (!v.length) return null;
  const s = v.slice().sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// ================================================================= rank

function montarFiltros() {
  const setores = [...new Set(ACOES.map((a) => a.setor))]
    .sort((a, b) => setorNome(a).localeCompare(setorNome(b), "pt-BR"));

  $("#filtroSetor").insertAdjacentHTML("beforeend",
    setores.map((s) => `<option value="${esc(s)}">${esc(setorNome(s))}</option>`).join(""));

  ["#busca", "#filtroSetor", "#ordem"].forEach((sel) =>
    $(sel).addEventListener("input", desenharTabela));
  $("#soConsenso").addEventListener("change", desenharTabela);
}

const POS_DE = { score: "pos", scoreSet: "posSet", scoreIg: "posIg" };

function filtrar() {
  const termo = $("#busca").value.trim().toUpperCase();
  const setor = $("#filtroSetor").value;
  const so3   = $("#soConsenso").checked;
  const posDe = POS_DE[$("#ordem").value];

  return ACOES
    .filter((a) => (!termo || a.papel.includes(termo))
                && (!setor || a.setor === setor)
                && (!so3   || a.consenso === 3))
    .slice()
    .sort((a, b) => a[posDe] - b[posDe]);
}

function desenharTabela() {
  const lista = filtrar();
  const chave = $("#ordem").value;
  const posDe = POS_DE[chave];

  $("#contagem").textContent = lista.length === ACOES.length
    ? `${lista.length} papéis elegíveis`
    : `${lista.length} de ${ACOES.length} papéis`;

  $("#vazio").classList.toggle("oculto", lista.length > 0);

  $("#corpo").innerHTML = lista.map((a) => {
    const tres = a.consenso === 3;
    const ciclica = a.ciclica
      ? ` <span class="marca-ciclica" title="Setor cíclico: tende a parecer barata no topo do ciclo">cíclica</span>`
      : "";

    return `<tr class="${tres ? "consenso-3" : ""}">
      <td class="col-pos" data-rotulo="#">${a[posDe]}</td>
      <td class="col-papel" data-rotulo="Papel">
        <button class="papel-btn" data-papel="${esc(a.papel)}">${esc(a.papel)}</button>${ciclica}
        ${a.nome ? `<span class="papel-nome">${esc(a.nome)}</span>` : ""}
      </td>
      <td class="col-setor" data-rotulo="Setor"><span class="setor-txt">${esc(setorNome(a.setor))}</span></td>
      <td class="num" data-rotulo="Score">${num(a[chave], 1)}</td>
      <td class="col-cons" data-rotulo="Consenso">
        <span class="selo ${tres ? "tres" : ""}">${a.consenso}/3</span>
      </td>
      <td class="num" data-rotulo="ROIC">${pct(a.roic)}</td>
      <td class="num" data-rotulo="Cresc. 5a">${pct(a.cresc)}</td>
      <td class="num" data-rotulo="EV/EBITDA">${mult(a.evebitda)}</td>
      <td class="num" data-rotulo="Mrg. EBIT">${pct(a.mrgeb)}</td>
      <td class="num" data-rotulo="Dív.Líq./Patr.">${mult(a.div)}</td>
    </tr>`;
  }).join("");
}

// Delegacao unica no documento: vale para a tabela, os cards e as listas.
document.addEventListener("click", (ev) => {
  const alvo = ev.target.closest("[data-papel]");
  if (alvo) { abrirFicha(alvo.dataset.papel); return; }

  const ajuda = ev.target.closest(".btn-ajuda");
  if (ajuda) {
    const cx = ajuda.closest(".indicador").querySelector(".explica");
    const aberto = ajuda.getAttribute("aria-expanded") === "true";
    ajuda.setAttribute("aria-expanded", String(!aberto));
    cx.classList.toggle("oculto", aberto);
  }
});

// ================================================================ ficha

function montarSeletorFicha() {
  const sel = $("#seletorFicha");
  sel.innerHTML = ACOES
    .slice()
    .sort((a, b) => a.papel.localeCompare(b.papel))
    .map((a) => `<option value="${esc(a.papel)}">${esc(a.papel)}${
        a.nome ? " — " + esc(a.nome) : ""} · ${esc(setorNome(a.setor))}</option>`)
    .join("");

  sel.addEventListener("change", () => desenharFicha(sel.value));
  if (ACOES.length) desenharFicha(ACOES[0].papel);
}

function abrirFicha(papel) {
  if (!ACOES.some((a) => a.papel === papel)) return;
  $("#seletorFicha").value = papel;
  desenharFicha(papel);
  trocarAba("ficha");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/** Uma barra por fator do score, mostrando a nota percentil que o gerou. */
function barras(a, prefixo) {
  return DADOS.meta.fatores.map((f) => {
    const nota = a[prefixo + f.chave];
    if (nulo(nota)) return "";
    const nome = (INDICADORES[f.chave] || {}).nome || f.rotulo;
    return `<div class="fator">
      <div class="fator-topo">
        <span>${esc(nome)} <span class="fator-peso">${Math.round(f.peso * 100)}%</span></span>
        <span class="fator-nota">${num(nota, 0)}</span>
      </div>
      <div class="barra"><span style="width:${Math.max(0, Math.min(100, nota))}%"></span></div>
    </div>`;
  }).join("");
}

/* Razao social so aparece quando difere do nome comercial: em varias empresas
   os dois sao iguais ("WEG SA"), e repetir a mesma linha nao informa nada. */
function mostraRazao(a) {
  if (!a.razao) return false;
  const limpa = (t) => t.toLowerCase().replace(/[^a-z0-9]/g, "");
  return limpa(a.razao) !== limpa(a.nome || "");
}

const linha = (rot, val) =>
  `<div class="linha-dado"><span>${esc(rot)}</span><span class="v">${val}</span></div>`;

/** Um indicador da ficha: valor, contexto percentil e explicacao sob o "?". */
function blocoIndicador(a, chave) {
  const ind = INDICADORES[chave];
  const valor = FMT[ind.fmt](a[chave]);
  const p = ind.dir ? percentilDe(chave).get(a.papel) : undefined;

  let classe = "";
  if (!nulo(p)) classe = p >= 75 ? " bom" : (p <= 25 ? " ruim" : "");

  const medSet = medianaSetor(a.setor, chave);
  const contexto = nulo(p)
    ? `<div class="ind-contexto"><span class="sem-percentil">Sem posição comparativa — indicador de referência, não de julgamento.</span></div>`
    : `<div class="ind-contexto">
         <div class="ind-barra"><span style="width:${Math.max(0, Math.min(100, p))}%"></span></div>
         <span class="ind-percentil">melhor que ${num(p, 0)}% da bolsa${
           nulo(medSet) ? "" : ` · mediana do setor ${FMT[ind.fmt](medSet)}`}</span>
       </div>`;

  return `<div class="indicador">
    <div class="ind-topo">
      <span class="ind-nome">${esc(ind.nome)}</span>
      <span class="ind-completo">${esc(ind.completo)}</span>
      <span class="ind-valor${classe}">${valor}</span>
      <button class="btn-ajuda" type="button" aria-expanded="false"
              aria-label="Explicar ${esc(ind.nome)}">?</button>
    </div>
    ${contexto}
    <div class="explica oculto">
      <p><span class="marcador">O que é:</span> ${ind.oque}</p>
      <p><span class="marcador">Como ler:</span> ${ind.ler}</p>
      <p class="cuidado"><span class="marcador">Onde engana:</span> ${ind.cuidado}</p>
    </div>
  </div>`;
}

function desenharFicha(papel) {
  const a = ACOES.find((x) => x.papel === papel);
  if (!a) return;

  const ressalvas = [];
  if (a.ciclica) ressalvas.push(
    "<strong>Setor cíclico.</strong> Empresas assim costumam exibir os melhores " +
    "indicadores no topo do ciclo — justamente quando o preço já subiu. Um EV/EBITDA " +
    "baixo aqui pode refletir lucro de pico, não empresa barata."
  );
  if (!a.setorOk) ressalvas.push(
    "<strong>Sem comparação setorial própria.</strong> O setor tem menos de 5 papéis " +
    "elegíveis (ou o papel não está no mapa de setores), então o esquema B herdou as " +
    "notas do universo inteiro. O consenso deste papel é mais fraco do que o número sugere."
  );

  const grupos = GRUPOS.map((g) => {
    const chaves = Object.keys(INDICADORES)
      .filter((k) => INDICADORES[k].grupo === g.id && k in a);
    if (!chaves.length) return "";
    return `<div class="bloco">
      <h3>${esc(g.titulo)}</h3>
      <p class="bloco-desc">${esc(g.desc)}</p>
      <div class="indicadores">${chaves.map((k) => blocoIndicador(a, k)).join("")}</div>
    </div>`;
  }).join("");

  $("#ficha").innerHTML = `
    <div class="ficha-topo">
      <h2>${esc(a.papel)}</h2>
      ${a.nome ? `<span class="ficha-nome">${esc(a.nome)}</span>` : ""}
      <span class="ficha-setor">${esc(setorNome(a.setor))}</span>
      ${a.consenso === 3 ? '<span class="selo tres">consenso 3/3</span>'
                         : `<span class="selo">${a.consenso}/3</span>`}
    </div>
    ${mostraRazao(a) ? `<p class="ficha-razao">${esc(a.razao)}</p>` : ""}

    ${ressalvas.map((t) => `<p class="ressalva">${t}</p>`).join("")}

    <div class="bloco">
      <h3>Posição nos três esquemas</h3>
      <p class="bloco-desc">Se as três posições são parecidas, o lugar do papel não depende
      das escolhas de quem montou o score. Se divergem muito, depende.</p>
      ${linha("A · Pesos definidos", `${a.pos}º <span class="nota">(${num(a.score, 1)})</span>`)}
      ${linha("B · Setorial",        `${a.posSet}º <span class="nota">(${num(a.scoreSet, 1)})</span>`)}
      ${linha("C · Pesos iguais",    `${a.posIg}º <span class="nota">(${num(a.scoreIg, 1)})</span>`)}
    </div>

    <div class="ficha-grade">
      <div class="bloco">
        <h3>Notas do score — universo inteiro</h3>
        ${barras(a, "n_")}
      </div>
      <div class="bloco">
        <h3>Notas do score — dentro do setor</h3>
        ${a.setorOk ? barras(a, "s_")
          : '<p class="nota">Setor sem pares suficientes; herdou as notas do universo inteiro.</p>'}
      </div>
    </div>

    ${grupos}

    <p class="nota nota-solta">
      As notas de 0 a 100 e as posições percentis são calculadas entre os
      ${inteiro(DADOS.meta.elegiveis)} papéis elegíveis, não sobre o valor bruto do
      indicador. 100 significa o melhor da amostra.
    </p>`;
}

// ======================================================== levantamentos

function montarLevantamentos() {
  const tres = ACOES.filter((a) => a.consenso === 3);

  $("#listaConsenso").innerHTML = tres.length
    ? tres.map((a) => `
        <button class="cartao-papel" data-papel="${esc(a.papel)}">
          <span class="cp-papel">${esc(a.papel)}</span>
          ${a.nome ? `<span class="cp-nome">${esc(a.nome)}</span>` : ""}
          <span class="cp-setor">${esc(setorNome(a.setor))}</span>
          <span class="cp-score">${a.pos}º · score ${num(a.score, 1)}</span>
        </button>`).join("")
    : '<p class="nota">Nenhum papel alcançou consenso 3/3 nesta coleta.</p>';

  const sel = $("#seletorIndicador");
  sel.innerHTML = GRUPOS.map((g) => {
    const opcoes = Object.keys(INDICADORES)
      .filter((k) => INDICADORES[k].grupo === g.id && INDICADORES[k].dir)
      .map((k) => `<option value="${k}">${esc(INDICADORES[k].nome)}</option>`)
      .join("");
    return opcoes ? `<optgroup label="${esc(g.titulo)}">${opcoes}</optgroup>` : "";
  }).join("");

  sel.addEventListener("change", () => desenharExploracao(sel.value));
  desenharExploracao(sel.value || "roic");
}

function desenharExploracao(chave) {
  const ind = INDICADORES[chave];
  if (!ind) return;

  const f = FMT[ind.fmt];
  const validos = ACOES.filter((a) => !nulo(a[chave]));
  const vals = validos.map((a) => a[chave]).sort((x, y) => x - y);

  const q = (frac) => {
    if (!vals.length) return null;
    return vals[Math.min(vals.length - 1, Math.floor(frac * (vals.length - 1)))];
  };

  const melhor = validos.slice().sort((a, b) =>
    ind.dir === "lo" ? a[chave] - b[chave] : b[chave] - a[chave]);

  const miniLista = (lista) => lista.map((a, i) => `
    <div class="mini-linha">
      <span class="mini-pos">${i + 1}</span>
      <button class="papel-btn" data-papel="${esc(a.papel)}">${esc(a.papel)}</button>
      <span class="mini-setor">${esc(setorNome(a.setor))}</span>
      <span class="mini-valor">${f(a[chave])}</span>
    </div>`).join("");

  $("#exploracao").innerHTML = `
    <div class="bloco">
      <h3>${esc(ind.nome)} — ${esc(ind.completo)}</h3>
      <div class="explica" style="border-left-color: var(--acento)">
        <p><span class="marcador">O que é:</span> ${ind.oque}</p>
        <p><span class="marcador">Como ler:</span> ${ind.ler}</p>
        <p class="cuidado"><span class="marcador">Onde engana:</span> ${ind.cuidado}</p>
      </div>

      <h3 style="margin-top:16px">Distribuição entre os ${validos.length} papéis elegíveis</h3>
      <div class="quartis">
        <div class="quartil"><span class="q-valor">${f(vals[0])}</span><span class="q-rot">mínimo</span></div>
        <div class="quartil"><span class="q-valor">${f(q(0.25))}</span><span class="q-rot">1º quartil</span></div>
        <div class="quartil"><span class="q-valor">${f(mediana(vals))}</span><span class="q-rot">mediana</span></div>
        <div class="quartil"><span class="q-valor">${f(q(0.75))}</span><span class="q-rot">3º quartil</span></div>
        <div class="quartil"><span class="q-valor">${f(vals[vals.length - 1])}</span><span class="q-rot">máximo</span></div>
      </div>
      <p class="nota">
        Metade dos papéis está entre o 1º e o 3º quartil. ${ind.dir === "lo"
          ? "Neste indicador, menor é melhor."
          : "Neste indicador, maior é melhor."}
      </p>
    </div>

    <div class="duas-listas">
      <div class="bloco">
        <h3>15 melhores em ${esc(ind.nome)}</h3>
        <div class="mini-lista">${miniLista(melhor.slice(0, 15))}</div>
      </div>
      <div class="bloco">
        <h3>5 piores em ${esc(ind.nome)}</h3>
        <div class="mini-lista">${miniLista(melhor.slice(-5).reverse())}</div>
      </div>
    </div>

    <p class="nota nota-solta">
      Estas listas ordenam por um indicador isolado, sem pesos e sem os outros fatores.
      Liderar um indicador sozinho não coloca a empresa no topo do rank — e nem deveria.
    </p>`;
}

// ============================================================== setores

function montarSetores() {
  const grupos = new Map();
  for (const a of ACOES) {
    if (!grupos.has(a.setor)) grupos.set(a.setor, []);
    grupos.get(a.setor).push(a);
  }

  const linhas = [...grupos.entries()]
    .map(([setor, itens]) => ({
      setor,
      qtd: itens.length,
      med: mediana(itens.map((x) => x.score)),
      tres: itens.filter((x) => x.consenso === 3).length,
      melhor: itens.reduce((m, x) => (x.pos < m.pos ? x : m), itens[0]),
      proprio: itens.some((x) => x.setorOk),
    }))
    .sort((a, b) => b.med - a.med);

  $("#corpoSetores").innerHTML = linhas.map((l) => `
    <tr>
      <td><strong>${esc(setorNome(l.setor))}</strong></td>
      <td class="num">${l.qtd}</td>
      <td class="num">${num(l.med, 1)}</td>
      <td class="num">${l.tres || "—"}</td>
      <td><button class="papel-btn" data-papel="${esc(l.melhor.papel)}">${esc(l.melhor.papel)}</button>
          <span class="setor-txt">${l.melhor.pos}º</span></td>
      <td>${l.proprio ? "sim" : '<span class="sem-percentil">não — herda o global</span>'}</td>
    </tr>`).join("");
}

// =============================================================== metodo

const PORQUE = {
  roic:     "melhor proxy de vantagem competitiva",
  cresc:    "o crescimento que se quer capturar",
  evebitda: "impede pagar caro pela qualidade",
  mrgeb:    "eficiência da operação",
  div:      "sobrevivência em crise",
};

function montarMetodo() {
  $("#corpoFatores").innerHTML = DADOS.meta.fatores.map((f) => {
    const nome = (INDICADORES[f.chave] || {}).nome || f.rotulo;
    return `<tr>
      <td><strong>${esc(nome)}</strong></td>
      <td class="num">${Math.round(f.peso * 100)}%</td>
      <td>${f.direcao === "hi" ? "maior melhor" : "menor melhor"}</td>
      <td>${esc(PORQUE[f.chave] || "")}</td>
    </tr>`;
  }).join("");

  const elim = DADOS.meta.eliminados_por_motivo || {};
  $("#corpoEliminados").innerHTML = Object.entries(elim)
    .sort((a, b) => b[1] - a[1])
    .map(([motivo, n]) =>
      `<tr><td>${esc(motivo.charAt(0).toUpperCase() + motivo.slice(1))}</td>
           <td class="num">${inteiro(n)}</td></tr>`)
    .join("");

  $("#glossario").innerHTML = GRUPOS.map((g) => {
    const chaves = Object.keys(INDICADORES).filter((k) => INDICADORES[k].grupo === g.id);
    return `<div class="bloco">
      <h3>${esc(g.titulo)}</h3>
      <p class="bloco-desc">${esc(g.desc)}</p>
      ${chaves.map((k) => {
        const i = INDICADORES[k];
        return `<div class="indicador">
          <div class="ind-topo">
            <span class="ind-nome">${esc(i.nome)}</span>
            <span class="ind-completo">${esc(i.completo)}</span>
            <button class="btn-ajuda" type="button" aria-expanded="false"
                    aria-label="Explicar ${esc(i.nome)}">?</button>
          </div>
          <div class="explica oculto">
            <p><span class="marcador">O que é:</span> ${i.oque}</p>
            <p><span class="marcador">Como ler:</span> ${i.ler}</p>
            <p class="cuidado"><span class="marcador">Onde engana:</span> ${i.cuidado}</p>
          </div>
        </div>`;
      }).join("")}
    </div>`;
  }).join("");

  const m = DADOS.meta;
  const d = new Date(m.coletado_em);
  $("#proveniencia").innerHTML =
    `Coletado de <a href="${esc(m.fonte)}">${esc(m.fonte)}</a> em ` +
    `${d.toLocaleString("pt-BR")}. Foram lidos ${inteiro(m.papeis_lidos)} papéis, ` +
    `dos quais ${inteiro(m.elegiveis)} passaram nos filtros. O decil superior usado ` +
    `para o consenso corresponde aos ${m.top_n_consenso} primeiros de cada esquema. ` +
    `A coleta roda sozinha todo dia às 22h de Brasília pelo GitHub Actions.`;
}

// ================================================================= abas

const ABAS = ["rank", "ficha", "levantamentos", "setores", "metodo"];

function trocarAba(nome) {
  $$(".aba").forEach((b) => {
    const ativa = b.dataset.aba === nome;
    b.classList.toggle("ativa", ativa);
    b.setAttribute("aria-selected", String(ativa));
  });
  $$(".painel").forEach((p) =>
    p.classList.toggle("ativa", p.id === "painel-" + nome));

  if (location.hash !== "#" + nome) history.replaceState(null, "", "#" + nome);
}

$$(".aba").forEach((b) =>
  b.addEventListener("click", () => trocarAba(b.dataset.aba)));

if (ABAS.includes(location.hash.slice(1))) trocarAba(location.hash.slice(1));

// ================================================================= pwa

/* O service worker guarda a casca do site para abrir sem internet.
   Só funciona em HTTPS ou em localhost — file:// nao registra. */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((e) =>
      console.warn("Service worker nao registrado:", e.message));
  });
}

function marcarConexao() {
  $("#barraOffline").classList.toggle("oculto", navigator.onLine);
}

window.addEventListener("online", marcarConexao);
window.addEventListener("offline", marcarConexao);
marcarConexao();

carregar();

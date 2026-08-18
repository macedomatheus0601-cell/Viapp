/* ------------------------------------------------------------------
   Service worker — o que faz o site abrir sem internet.

   Duas politicas diferentes, de proposito:

   CASCA (html, css, js, icones)  -> cache primeiro, atualiza em segundo
       plano. Muda raramente; esperar a rede para exibir a mesma coisa
       de sempre so deixaria o app lento.

   DADOS (dados/*.json)           -> rede primeiro, cache como reserva.
       Muda todo dia as 22h. Servir a versao guardada quando existe rede
       mostraria numero velho — exatamente o que este projeto nao quer.
       Sem rede, entrega o ultimo retrato baixado, e a data em destaque
       na tela denuncia a idade dele.
   ------------------------------------------------------------------ */

const VERSAO = "v3";
const CACHE_CASCA = `casca-${VERSAO}`;
const CACHE_DADOS = `dados-${VERSAO}`;

const CASCA = [
  "./",
  "./index.html",
  "./estilo.css",
  "./app.js",
  "./manifest.webmanifest",
  "./icones/icone-192.png",
  "./icones/icone-512.png",
  "./icones/icone-512-mascara.png",
  "./icones/icone-180.png",
];

self.addEventListener("install", (ev) => {
  ev.waitUntil(
    caches.open(CACHE_CASCA)
      // addAll falha inteiro se um arquivo falhar; guardar um a um evita que
      // um icone ausente impeca a instalacao do resto.
      .then((c) => Promise.allSettled(CASCA.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (ev) => {
  ev.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(
        nomes
          .filter((n) => n !== CACHE_CASCA && n !== CACHE_DADOS)
          .map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (ev) => {
  const req = ev.request;

  // Só GET e só o proprio site: POST nao e cacheavel e dominio de terceiro
  // (um link para o Fundamentus, por exemplo) nao e da nossa conta.
  if (req.method !== "GET") return;
  if (new URL(req.url).origin !== self.location.origin) return;

  if (req.url.includes("/dados/")) {
    ev.respondWith(redePrimeiro(req));
  } else if (req.mode === "navigate" && !req.url.endsWith(".pdf")) {
    // Abrir um PDF tambem conta como navegacao. Sem a excecao, offline ele
    // receberia o index.html no lugar do arquivo — pior que um erro honesto.
    ev.respondWith(navegacao(req));
  } else {
    ev.respondWith(cachePrimeiro(req));
  }
});

/** Rede primeiro; se cair, devolve a copia guardada. */
async function redePrimeiro(req) {
  const cache = await caches.open(CACHE_DADOS);
  try {
    const resp = await fetch(req);
    if (resp && resp.ok) cache.put(req, resp.clone());
    return resp;
  } catch (e) {
    const guardado = await cache.match(req);
    if (guardado) return guardado;
    return new Response(
      JSON.stringify({ erro: "sem rede e sem copia local dos dados" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

/** Cache primeiro, revalidando em segundo plano. */
async function cachePrimeiro(req) {
  const cache = await caches.open(CACHE_CASCA);
  const guardado = await cache.match(req);

  const rede = fetch(req)
    .then((resp) => {
      if (resp && resp.ok) cache.put(req, resp.clone());
      return resp;
    })
    .catch(() => null);

  return guardado || (await rede) || Response.error();
}

/** Abrir o app offline precisa cair no index.html guardado. */
async function navegacao(req) {
  try {
    const resp = await fetch(req);
    if (resp && resp.ok) {
      const cache = await caches.open(CACHE_CASCA);
      cache.put("./index.html", resp.clone());
    }
    return resp;
  } catch (e) {
    const cache = await caches.open(CACHE_CASCA);
    return (await cache.match("./index.html"))
        || (await cache.match("./"))
        || Response.error();
  }
}

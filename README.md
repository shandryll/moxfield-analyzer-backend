# Moxfield Analyzer

API que analisa decks de **Magic: The Gathering** do site [Moxfield](https://www.moxfield.com).
Cole a URL de um deck público e receba de volta: curva de mana, cartas banidas,
combos, e análise completa para o formato **Kindred Wars**.

---

## O que você precisa

| Ferramenta | Onde conseguir |
|---|---|
| **Python** ≥ 3.12 | [python.org](https://python.org) |
| **uv** | [docs.astral.sh/uv](https://docs.astral.sh/uv/) (instalador de pacotes) |
| **Playwright** | Instalado automaticamente pelo `make setup` |
| **Docker** (opcional) | [docker.com](https://docker.com) |

---

## Como rodar — Local

```bash
make setup          # instala dependências + Playwright (Chromium)
make dev            # sobe o servidor em http://localhost:3000
```

Acesse `http://localhost:3000/docs` para a documentação interativa (Swagger).

## Como rodar — Docker

```bash
make docker-up      # constrói a imagem e sobe o container
make docker-logs    # acompanhar os logs
make docker-down    # parar o container
```

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Health check (status, versão, ambiente, timestamp, link `/docs`) |
| `GET` | `/api/deck/validate?url=...&kindred=...` | Analisa um deck do Moxfield (rate limit: 10/min) |

### Exemplo

```bash
curl "http://localhost:3000/api/deck/validate?url=https://moxfield.com/decks/SEU_ID&kindred=Elf"
```

> **`url`** pode ser a URL completa ou apenas o ID do deck.
>
> **`kindred`** é o tipo tribal (ex: Elf, Goblin, Vampire, Dragon).
>
> Em produção, configure `CORS_ALLOW_ORIGINS` com a URL do seu frontend
> (ex: `https://meusite.com`) no ambiente do Render.

---

## Cache

Para não ficar consultando as APIs externas (Moxfield, Scryfall, Commander Spellbook)
toda vez que o mesmo deck é analisado, a API mantém **cache em memória**:

| Cache | O que guarda | TTL | Máx. |
|---|---|---|---|
| `deck_cache` | Dados brutos do deck | 5 min | 100 decks |
| `oracle_cache` | Oracle IDs resolvidos | 1 hora | 500 cartas |
| `combo_cache` | Combos encontrados | 24 horas | 200 combos |

Os TTLs e tamanhos máximos podem ser ajustados via variáveis de ambiente:
`CACHE_DECK_TTL`, `CACHE_DECK_MAXSIZE`, `CACHE_ORACLE_TTL`, `CACHE_ORACLE_MAXSIZE`,
`CACHE_COMBO_TTL`, `CACHE_COMBO_MAXSIZE` (TTL em segundos).

---

## Fluxo da requisição

A API executa tarefas em paralelo sempre que possível: chamadas de rede (async I/O) rodam
concorrentemente, enquanto cálculos pesados (CPU-bound) são delegados a **threads separadas**
via `asyncio.to_thread`. Tudo converge no `asyncio.gather()`.

```
  Você (navegador / curl)
         │
         │  GET /api/deck/validate?url=...&kindred=...
         ▼
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
╎                         FASE 1 — Sequencial (preparação)                        ╎
╎                                                                                  ╎
╎  ① Valida URL e extrai ID do deck (DeckUrl)                                     ╎
╎  ② Busca deck no Moxfield via Playwright ─── async I/O ─── browser headless     ╎
╎  ③ Extrai scryfall_ids de mainboard + commanders + companions                   ╎
╎  ④ Resolve oracle_ids no Scryfall ───────── async I/O ─── httpx                 ╎
╎  ⑤ Mapeia cartas (board_to_cards) + computa totais (criaturas, CMC etc.)        ╎
╚╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╝
         │
         │  Dados prontos → dispara 3 tarefas em paralelo
         ▼
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
╎                    FASE 2 — Paralela (asyncio.gather)                           ╎
╎                                                                                  ╎
╎   ┌──────────────────────────────────────────────────────────────────────────┐   ╎
╎   │   asyncio.gather(                                                         │   ╎
╎   │       asyncio.to_thread(...),     ← THREAD POOL (CPU-bound)               │   ╎
╎   │       asyncio.to_thread(...),     ← THREAD POOL (CPU-bound)               │   ╎
╎   │       self._safe_fetch_combos(),  ← ASYNC I/O (HTTP)                      │   ╎
╎   │   )                                                                        │   ╎
╎   └──┬──────────────────┬──────────────────┬──────────────────────────────────┘   ╎
╎      │                  │                  │                                      ╎
╎      ▼                  ▼                  ▼                                      ╎
╎  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                            ╎
╎  │   Thread 1   │  │   Thread 2   │  │  Async I/O   │                            ╎
╎  │              │  │              │  │              │                            ╎
╎  │ KindredWars  │  │ ManaCurve    │  │ Commander    │                            ╎
╎  │ Calculator   │  │ Calculator   │  │ Spellbook    │                            ╎
╎  │              │  │              │  │ HTTP POST    │                            ╎
╎  │ • Score      │  │ • Curva      │  │              │                            ╎
╎  │ • Identidade │  │   de mana    │  │ • Cache hit? │                            ╎
╎  │ • Reserved   │  │ (CMC 1..7+)  │  │ • Busca      │                            ╎
╎  │ • Game       │  │              │  │   combos     │                            ╎
╎  │   Changer    │  │ • Ignora     │  │ • Trata      │                            ╎
╎  │ • Banidas    │  │   terrenos   │  │   erros      │                            ╎
╎  │ • Tutors     │  │ • Inclui     │  │   (timeout,  │                            ╎
╎  │ • Mass       │  │   cmdrs      │  │   429, 404)  │                            ╎
╎  │   Removal    │  │              │  │              │                            ╎
╎  │ • Extra Turn │  │              │  │              │                            ╎
╎  └──────────────┘  └──────────────┘  └──────────────┘                            ╎
╎         │                  │                  │                                   ╎
╎         └──────────────────┴──────────────────┘                                   ╎
╎                            │                                                      ╎
╎                     Todas as 3 concluíram                                        ╎
╚╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╝
         │
         ▼
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
╎                      FASE 3 — Sequencial (resposta)                              ╎
╎                                                                                   ╎
╎  ⑥ Monta DeckDetails (Pydantic) com todos os resultados                          ╎
╎  ⑦ Serializa JSON e retorna com status 200 (ou 404/429/422 em caso de erro)      ╎
╚╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╝
         │
         ▼
┌───────────────────────────────────────┐
│  JSON                                 │
│                                       │
│  ├─ id, name, total_cards            │
│  ├─ creatures, non_creatures, etc.   │
│  ├─ cards, commanders, companions    │
│  ├─ mana_curve                       │
│  ├─ kindred_wars                    │
│  └─ find_my_combos                  │
└───────────────────────────────────────┘
```

### Detalhamento da concorrência

| Cálculo | Como executa | Por quê |
|---|---|---|
| Buscar deck (Moxfield) | `async` (Playwright) | I/O-bound — navegação web |
| Resolver oracle IDs (Scryfall) | `async` (httpx) | I/O-bound — chamada HTTP |
| KindredWars score | `asyncio.to_thread` | CPU-bound — itera centenas de cartas, calcula tags, valida kindred |
| ManaCurve | `asyncio.to_thread` | CPU-bound — agrega CMCs, filtra terrenos |
| Commander Spellbook | `async` (httpx) | I/O-bound — chamada HTTP (com cache em memória) |

Os cálculos CPU-bound rodam no **default thread pool** do `asyncio` (geralmente `min(32, os.cpu_count() + 4)` threads),
liberando o event loop principal para continuar atendendo outras requisições enquanto os
resultados são processados em background.

---

## O que vem no JSON

```json
{
  "id": "abc123",
  "name": "Meu Deck Elfos",
  "total_cards": 100,
  "creatures": 30,
  "non_creatures": 70,
  "commander_creatures": 1,
  "companion_creatures": 0,
  "creatures_including_commanders": 31,
  "mana_curve": [
    { "cmc": 1, "count": 8 },
    { "cmc": 2, "count": 12 },
    { "cmc": 3, "count": 10 },
    { "cmc": 4, "count": 5 }
  ],
  "kindred_wars": { ... },
  "find_my_combos": [ ... ],
  "cards": [ ... ],
  "commanders": [ ... ],
  "companions": [ ... ]
}
```

| Campo | Significado |
|---|---|
| `id` / `name` | Identificação do deck |
| `total_cards` | Sempre **100** em Commander (incluindo comandante) |
| `creatures` | Criaturas no mainboard |
| `non_creatures` | Mágicas, terrenos, artefatos etc. (tudo que não é criatura) |
| `commander_creatures` | Criaturas na zona de comandante |
| `companion_creatures` | Criaturas na zona de companion |
| `creatures_including_commanders` | Soma de todas as criaturas acima |
| `mana_curve` | Quantas cartas de cada custo de mana (CMC) |
| `cards` | Lista detalhada de cada carta do deck |
| `commanders` | Comandante(s) do deck |
| `companions` | Companion(s), se houver |
| `kindred_wars` | Objeto com análise do formato Kindred Wars |
| `find_my_combos` | Combos encontrados no Commander Spellbook |

### Curva de mana (`mana_curve`)

Cada entry tem `cmc` (custo de mana convertido) e `count` (quantidade de cartas
com aquele custo). Terrenos são ignorados; comandantes são incluídos.

### Combos (`find_my_combos`)

Cada combo contém os nomes das cartas envolvidas, descrição do que ele faz,
mana necessária, e link para a página no Commander Spellbook.

---

## Kindred Wars

**Kindred Wars** é um formato de Commander que usa regras de estirpe (tribo).
Você escolhe um tipo de criatura (ex: Elf, Goblin, Vampire) e o deck deve
ser composto majoritariamente por criaturas daquele tipo.

### Score

O **score** é a pontuação do deck baseada no custo de mana (CMC) das criaturas:

- CMC 1 → **5 pontos**
- CMC 2 → **4 pontos**
- CMC 3 → **3 pontos**
- CMC 4 → **2 pontos**
- CMC 5 → **1 ponto**
- CMC 6+ → **0 pontos**

Quanto mais criaturas baratas (rápidas), maior a pontuação.

### Identidade de estirpe

- `creatures_with_kindred_identity`: quantas criaturas são do tipo escolhido
- `all_validated_creatures`: `true` se **todas** as criaturas pertencem ao kindred
- `non_validated_creatures`: lista das criaturas que **não** pertencem ao kindred

### Listas de verificação

Cada lista tem `total` (quantidade) e `cards[]` (nomes das cartas):

| Lista | O que são |
|---|---|
| `reserved_list` | Cartas da Reserved List (não podem ser reimpressas) |
| `game_changer` | Cartas consideradas muito poderosas para o formato |
| `banned_cards` | Cartas banidas no Kindred Wars |
| `potential_tutor` | Cartas que buscam outras cartas (ex: Demonic Tutor) |
| `potential_mass_removal` | Remoções em massa (ex: Wrath of God) |
| `potential_extra_turn` | Turnos extras (ex: Time Warp) |

---

## Comandos Make

| Comando | O que faz |
|---|---|
| `make setup` | Instala dependências + Playwright |
| `make dev` | Inicia o servidor em `http://localhost:3000` |
| `make test` | Executa os testes (pytest) |
| `make lint` | Corrige estilo de código (ruff) |
| `make format` | Formata o código (ruff) |
| `make typecheck` | Verifica tipos (mypy) |
| `make docker-up` | Sobe o container com Docker Compose |
| `make docker-down` | Para o container |
| `make docker-logs` | Acompanha os logs do container |
| `make docker-rebuild` | Reconstrói e sobe o container |
| `make clean` | Remove caches e ambiente virtual |

---

## Estrutura do projeto

```
src/
├── main.py                        → Ponto de entrada (sobe o servidor FastAPI)
│
├── application/
│   └── use_cases/
│       └── validate_deck.py       → Orquestrador principal da análise
│
├── domain/
│   ├── services/
│   │   ├── mana_curve_calculator.py      → Calcula curva de mana
│   │   ├── kindred_wars_calculator.py    → Calcula score Kindred Wars
│   │   ├── card_type_helper.py           → Classifica tipos de carta
│   │   └── tags/                         → Oracle tags (tag_service + calculadoras)
│   ├── value_objects/
│   │   └── deck_url.py            → Valida e extrai ID de URLs do Moxfield
│
├── infrastructure/
│   ├── http/
│   │   ├── app.py                 → Configuração do FastAPI (CORS)
│   │   ├── rate_limit.py          → Configuração do rate limiter (slowapi)
│   │   ├── routes/deck.py         → Rotas da API (rate limit: 10/min)
│   │   └── middleware/            → Middlewares (error handler)
│   ├── playwright/
│   │   └── browser_pool.py        → Gerenciamento do navegador headless
│   ├── repositories/
│   │   ├── moxfield_deck_repository.py    → Busca deck no Moxfield
│   │   ├── scryfall_card_resolver.py      → Busca oracle_id no Scryfall
│   │   └── commander_spellbook_repository.py → Busca combos
│   ├── static_data/
│   │   └── oracle_tags/           → Listas de cartas por categoria
│   └── utils/
│       ├── cache.py               → Cache em memória (TTL)
│       ├── metrics.py             → Decorator de tempo de execução
│       ├── logger.py              → Configuração de logs (loguru)
│       └── http_client.py         → Cliente HTTP compartilhado (httpx)
│
└── shared/
    ├── exceptions.py              → Exceções compartilhadas (NotFoundMoxfieldError)
    └── models/                    → Estruturas de dados (Pydantic)
        ├── deck_details.py
        ├── card.py
        ├── kindred_wars.py
        ├── mana_curve.py
        ├── commander_spellbook.py
        ├── tag_stats.py
        ├── oracle_tag.py
        └── card_face.py
```

---

## Documentação interativa

Com o servidor rodando, acesse:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

---

## Licença

MIT

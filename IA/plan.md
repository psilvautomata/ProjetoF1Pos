# Pipeline de dados da Fórmula 1 com a API OpenF1

Plano de implementação baseado em dois documentos:

- `doc_api.md`: resumo da documentação da OpenF1, consultada em 08/11/2026.
- `skill.md`: padrões obrigatórios de desenvolvimento Python (Pyenv, Poetry, Ruff, Pytest, MkDocs Material).

Este plano não substitui o `skill.md`. Em caso de conflito, o `skill.md` prevalece.

---

## 1. Objetivo

Objetivo principal: entregar um dashboard local que mostre as cinco voltas válidas mais rápidas por pista e ano. Para alimentá-lo, o projeto consulta a API OpenF1, ingere os dados históricos necessários e os organiza em tabelas limpas e validadas.

Resultados esperados:

1. Dashboard local com filtros de temporada, pista e tipo de sessão e ranking das cinco voltas mais rápidas.
2. Ingestão histórica por temporada para preparar a base desse dashboard.
3. Conector HTTP reutilizável para a OpenF1 e pipelines idempotentes por evento/sessão.
4. Transformações que padronizam, validam e relacionam os dados.
5. Testes unitários com cobertura mínima de 50% de `src/`.
6. Documentação técnica em MkDocs Material, validada com `--strict`.

## 2. Escopo

### Dentro do escopo

- Dados históricos gratuitos, disponíveis a partir de 2023 e sem autenticação.
- Consultas `GET` em `https://api.openf1.org/v1/`, com resposta em JSON (CSV opcional com `csv=true`).
- Fluxo de navegação recomendado pela API: `/meetings` → `/sessions` → `session_key` → demais endpoints.
- Dashboard local sobre dados históricos ingeridos, com filtros de ano e pista e uma tabela das cinco voltas mais rápidas.

### Fora do escopo

- Dados em tempo real, que exigem assinatura paga.
- Anos anteriores a 2023, que não estão cobertos pela API gratuita.
- Modelos preditivos (podem ser uma fase futura).

### Definição do ranking do dashboard

- A unidade do ranking é uma volta individual de `/laps`, não o melhor tempo agregado por piloto.
- Cada grupo é identificado por `circuit_short_name` e `year`, relacionados por meeting e sessão.
- Usar `year` e `circuit_short_name` de `/meetings`; `/sessions` fornece o tipo/nome da sessão; `/laps` fornece `lap_duration`, `driver_number`, `lap_number` e `is_pit_out_lap`; `/drivers` fornece o nome do piloto. Conferir os campos na [documentação oficial](https://openf1.org/docs/).
- Incluir voltas de todos os tipos de sessão disponíveis, com filtro opcional por tipo de sessão.
- Considerar válidas apenas voltas com `lap_duration` numérico e maior que zero; excluir registros marcados como `is_pit_out_lap=true`.
- Mostrar exatamente as cinco voltas mais rápidas por grupo, ordenadas pelo tempo. Empates são ordenados de forma estável por meeting, sessão, piloto e número da volta. Um piloto pode aparecer mais de uma vez.
- Exibir pista, ano, tempo em segundos, piloto, número da volta, sessão e Grande Prêmio. Informar quando um ano ainda não tem ingestão completa.
- O dashboard descobre temporadas com dados históricos gratuitos via `/meetings?year>=2023` até o ano atual (metadados em cache por 24 horas); rankings e tempos continuam vindo apenas dos arquivos locais ingeridos.
- A ingestão por temporada só consulta `/drivers` e `/laps` de sessões encerradas com `date_end` válido. Sessões futuras, em andamento ou sem encerramento confirmado ficam pendentes, evitando dados em tempo real pagos.

### Endpoints por prioridade

| Prioridade | Endpoints | Motivo |
|---|---|---|
| Essencial | `/meetings`, `/sessions`, `/drivers`, `/session_result`, `/starting_grid` | Contexto do evento, pilotos e resultado final |
| Alta | `/laps`, `/stints`, `/pit`, `/weather`, `/position` | Análise de desempenho, estratégia, condições da corrida e ranking do dashboard |
| Média | `/race_control`, `/intervals` | Eventos de prova e diferenças de tempo (`/intervals` só em corridas) |
| Opcional | `/car_data`, `/location` | Amostragem de ~3,7 Hz gera volume alto; exige filtros por piloto e janela de tempo |
| Com ressalvas | `/overtakes`, `/team_radio`, `/championship_drivers`, `/championship_teams` | Dados incompletos, cobertura parcial ou endpoints beta |

## 3. Preparação do ambiente (skill.md, seções 1 e 2)

```bash
# Versão do Python definida pelo Pyenv (registrada em .python-version)
pyenv local 3.12.10
python --version

# Projeto Poetry com layout src/
poetry init
poetry install

# Dependências de produção (nenhum pip install)
poetry add requests pandas
poetry add streamlit

# Dependências de desenvolvimento
poetry add --group dev ruff pytest pytest-cov

# Dependências de documentação
poetry add --group docs mkdocs mkdocs-material
```

Regras que valem durante todo o projeto:

- Nunca usar `pip install` nem `python -m pip`.
- Versionar `pyproject.toml` e `poetry.lock`.
- Executar tudo com `poetry run ...`.
- Não adicionar dependências sem necessidade técnica justificada. Para mocks, usar `unittest.mock` e as fixtures do Pytest, sem bibliotecas extras.

## 4. Arquitetura (skill.md, seção 3)

Nome sugerido do pacote: `openf1_pipeline` (ajustar se preferir outro). Nos comandos do `skill.md`, `projeto` deve ser substituído por esse nome.

```text
openf1-pipeline/
├── .python-version
├── pyproject.toml
├── poetry.lock
├── README.md
├── mkdocs.yml
│
├── docs/
│   ├── index.md
│   ├── arquitetura.md
│   ├── desenvolvimento.md
│   ├── configuracao.md
│   └── pipelines/
│
├── src/
│   └── openf1_pipeline/
│       ├── __init__.py
│       ├── config/            # variáveis de ambiente, URL base, caminhos
│       ├── connectors/        # cliente HTTP da OpenF1
│       ├── pipelines/         # ingestão por meeting/sessão
│       ├── transformations/   # limpeza, tipagem, validação
│       ├── services/          # regras de negócio e ranking de voltas
│       ├── dashboard/         # aplicação Streamlit e componentes de visualização
│       └── utils/             # datas ISO 8601, logging, helpers
│
└── tests/
    ├── conftest.py
    └── unit/
```

Responsabilidades:

| Módulo | Responsabilidade |
|---|---|
| `config` | Ler configurações de variáveis de ambiente (URL base, diretório de saída, timeout). Sem credenciais no código. |
| `connectors` | Montar URLs, executar `GET`, tratar erros HTTP e devolver JSON. Não contém regra de negócio. |
| `pipelines` | Orquestrar: localizar o meeting, listar sessões, buscar cada endpoint e gravar o resultado. |
| `transformations` | Converter tipos, normalizar datas, renomear campos, validar qualidade e remover duplicatas. |
| `services` | Combinar tabelas e calcular métricas, incluindo o ranking das cinco voltas mais rápidas por pista e ano. |
| `dashboard` | Apresentar os dados locais em uma aplicação Streamlit com filtros de ano, pista e tipo de sessão. |
| `utils` | Funções pequenas e reutilizáveis, sem dependência de domínio. |

Princípios: Type Hints em funções públicas, `pathlib` para caminhos, `logging` em vez de `print()`, sem variáveis globais mutáveis e sem dependências circulares.

## 5. Fases de implementação

### Fase 0 — Fundação

- [ ] Criar a estrutura de pastas e o `pyproject.toml` com o layout `src/`.
- [ ] Configurar Ruff no `pyproject.toml`, incluindo a regra de imports (`I`).
- [ ] Configurar Pytest e cobertura (`--cov-fail-under=50`).
- [ ] Criar o `mkdocs.yml` com tema `material` e idioma `pt-BR`.
- [ ] Rodar o checklist da seção 8 em um projeto ainda vazio.

**Entrega:** esqueleto que passa em Ruff, Pytest e `mkdocs build --strict`.

### Fase 1 — Configuração e conector

- [ ] `config`: carregar `OPENF1_BASE_URL` (padrão `https://api.openf1.org/v1/`), timeout e diretório de dados a partir de variáveis de ambiente.
- [ ] `connectors`: criar um cliente com método genérico `get(endpoint, filtros)`.
- [ ] Usar `requests.get(...)` com `timeout` e `raise_for_status()`.
- [ ] Tratar exceções de forma específica (timeout, erro HTTP, JSON inválido) e registrar em log.
- [ ] Suportar operadores de filtro (`>`, `>=`, `<`, `<=`). O parâmetro `params` do `requests` só gera `chave=valor`; filtros com operador devem ser montados manualmente na query string (ex.: `speed>=315`). Cobrir esse caso em teste.
- [ ] Suportar `meeting_key=latest` e `session_key=latest`.

**Entrega:** conector testado com respostas simuladas (mocks), sem acesso à rede nos testes.

### Fase 2 — Ingestão essencial

Seguir o fluxo recomendado pela API:

1. `/meetings` → localizar o Grande Prêmio e obter o `meeting_key`.
2. `/sessions?meeting_key=...` → listar treinos, classificação, sprint e corrida.
3. Para cada `session_key`, ingerir `/drivers`, `/session_result` e `/starting_grid`.

- [ ] Pipeline `ingest_meeting(meeting_key)`.
- [ ] Pipeline `ingest_session(session_key)`.
- [ ] Gravar a resposta bruta (JSON) em `data/raw/` e o resultado tratado em `data/processed/`, usando `pathlib`.

**Entrega:** dados completos de um Grande Prêmio de 2023 ou posterior.

### Fase 3 — Ingestão de desempenho e estratégia

- [ ] `/laps` (tempos totais, setores, velocidades intermediárias).
- [ ] `/stints` (composto e idade dos pneus).
- [ ] `/pit` (usar `lane_duration`; ver seção 7).
- [ ] `/weather` (atualização de ~1 minuto).
- [ ] `/position` e `/race_control`.
- [ ] `/intervals`, somente para sessões de corrida.

**Entrega:** tabelas relacionáveis por `session_key` e `driver_number`.

### Fase 4 — Transformações e qualidade de dados

- [ ] Converter datas para ISO 8601 (ex.: `2023-09-10T14:30:20+00:00`).
- [ ] Definir tipos explícitos por tabela.
- [ ] Validar campos obrigatórios, duplicatas e valores fora de faixa.
- [ ] Tratar sessões sem dados em determinados endpoints sem interromper o pipeline (nem todo endpoint tem dados para toda sessão).
- [ ] Garantir idempotência: reexecutar o mesmo `session_key` produz o mesmo resultado, sem duplicar registros.

**Entrega:** funções determinísticas, testadas e com logs de validação.

### Fase 5 — Entrega principal: dashboard de melhores voltas

- [ ] Implementar ingestão de uma temporada (`ingest_year(year)`), consultando `/meetings` por ano e, para cada meeting, `/sessions`, `/drivers` e `/laps`.
- [ ] Considerar concluído o ano apenas quando todos os meetings e sessões não cancelados descobertos tiverem sido ingeridos; registrar no manifesto meetings/sessões concluídos e falhas.
- [ ] Relacionar voltas a sessão e meeting por `session_key`/`meeting_key`, e pilotos por `session_key` e `driver_number`.
- [ ] Gerar uma tabela derivada única e reprodutível com `year`, `circuit_short_name`, `meeting_name`, `session_key`, `session_name`, `driver_number`, nome do piloto, `lap_number` e `lap_duration`.
- [ ] Salvar a tabela em `data/processed/dashboard/lap_rankings.csv` e o manifesto de cobertura em `data/processed/dashboard/ingestion_manifest.json`; regravar deterministicamente ao reingerir um ano.
- [ ] Excluir voltas sem duração positiva ou marcadas como volta de saída dos boxes; preservar os dados brutos originais.
- [ ] Calcular exatamente as cinco menores durações por pista e ano, com desempate determinístico; permitir filtro opcional por tipo de sessão.
- [ ] Criar dashboard local em Streamlit com seleção de temporada e pista, tabela ordenada dos cinco tempos e gráfico de pontos da diferença para a volta mais rápida.
- [ ] Listar temporadas históricas gratuitas descobertas em `/meetings` desde 2023, além das temporadas locais; indicar como importar uma temporada sem dados locais e mostrar que a cobertura depende das sessões baixadas.
- [ ] Adicionar comando CLI `--year` para preparar os dados necessários ao dashboard e instruções para iniciar a aplicação com `poetry run streamlit run src/openf1_pipeline/dashboard/app.py`.
- [ ] Justificar e declarar a dependência Streamlit no Poetry; não adicionar bibliotecas de visualização extras sem necessidade.
- [ ] Atualizar documentação e testes do serviço de ranking e da seleção de dados do dashboard.

**Entrega:** dashboard local com os cinco melhores tempos por pista e ano, baseado exclusivamente em dados ingeridos da OpenF1.

### Fase 6 — Telemetria (opcional)

- [ ] `/car_data` e `/location` sempre filtrados por `session_key`, `driver_number` e janela de tempo (`date>=`, `date<`).
- [ ] Processar em blocos para evitar carregar volumes grandes na memória.
- [ ] Documentar que `/location` é aproximado e não informa o posicionamento lateral do carro.

**Entrega:** ingestão de telemetria para uma volta ou janela definida.

### Fase 7 — Documentação e fechamento

- [ ] Preencher `index.md`, `arquitetura.md`, `desenvolvimento.md` e `configuracao.md`.
- [ ] Documentar cada pipeline em `docs/pipelines/`.
- [ ] Incluir objetivo, arquitetura, configuração do ambiente, dependências, instruções de execução, componentes e fluxos de dados.
- [ ] Documentar a preparação da base histórica e o dashboard: filtros, ranking, cobertura e comando para execução.
- [ ] Executar o checklist completo da seção 8.

## 6. Estratégia de testes (skill.md, seção 5)

- Testes em `tests/unit/`, espelhando a estrutura de `src/openf1_pipeline/`.
- Nomes descritivos, por exemplo `test_connector_raises_on_http_error`.
- Cenários positivos, negativos e extremos:
  - resposta `200` com lista vazia;
  - erro HTTP (`4xx`/`5xx`) e timeout;
  - JSON malformado;
  - campos ausentes ou depreciados;
  - filtros com operadores (`>=`, `<`) e intervalos de datas.
  - ranking com menos de cinco voltas, empates, dados nulos, volta de saída dos boxes e sessões/pistas sem dados.
- Fixtures em `conftest.py` com amostras reduzidas de respostas por endpoint.
- Mocks para qualquer chamada HTTP: **nenhum teste unitário acessa a internet**.
- Cobertura mínima: **50% de `src/openf1_pipeline/`**, sem excluir funcionalidades relevantes para inflar o número.

## 7. Riscos e cuidados da API

| Item | Cuidado |
|---|---|
| `pit_duration` | Depreciado, com remoção prevista para o fim da temporada de 2026. Usar `lane_duration` desde o início. |
| `country_code` em `/drivers` | Depreciado, com remoção prevista para o fim da temporada de 2026. Não depender desse campo. |
| `stop_duration` | Disponível apenas a partir do GP dos Estados Unidos de 2024. Tratar como campo opcional. |
| `/overtakes` | Pode estar incompleto e inclui mudanças de posição por pit stop ou penalidade, não só ultrapassagens na pista. |
| `/team_radio` | Cobertura parcial, com redução significativa a partir de 2026. |
| `/championship_*` | Endpoints beta, disponíveis só para sessões de corrida. |
| `/location` | Coordenadas aproximadas; não distingue esquerda e direita da pista. |
| Filtros | Não é possível filtrar por campos que sejam arrays. |
| Dados em tempo real | Exigem assinatura paga; o projeto usa apenas dados históricos. |
| Limites de uso | O resumo não informa limites de requisições. Consultar a documentação oficial e aplicar pausas e tentativas controladas se necessário. |
| Mudanças na API | O `doc_api.md` é um resumo. Conferir atributos completos em <https://openf1.org/docs/> antes de definir os esquemas. |
| Cobertura do dashboard | O ranking só é completo para anos e sessões efetivamente ingeridos; apresentar essa limitação na interface. |

A OpenF1 é uma API não oficial, sem afiliação com a Formula 1 ou a FIA.

## 8. Checklist obrigatório de validação (skill.md, seção 8)

Executar antes de considerar qualquer fase concluída:

```bash
# 1. Sincronizar dependências
poetry install

# 2. Corrigir problemas de lint
poetry run ruff check . --fix

# 3. Formatar código
poetry run ruff format .

# 4. Validar lint
poetry run ruff check .

# 5. Validar formatação
poetry run ruff format . --check

# 6. Testes com cobertura mínima
poetry run pytest --cov=openf1_pipeline --cov-report=term-missing --cov-fail-under=50

# 7. Validar documentação
poetry run mkdocs build --strict
```

Critérios de conclusão:

- [ ] Código organizado em módulos.
- [ ] Dependências gerenciadas pelo Poetry.
- [ ] Versão do Python definida pelo Pyenv.
- [ ] Ruff sem pendências.
- [ ] Testes passando, com cobertura ≥ 50%.
- [ ] Documentação atualizada e validada.

Se alguma validação não puder ser executada, informar o motivo explicitamente. Nunca declarar uma validação como aprovada sem executá-la.

## 9. Instruções para agentes de IA (skill.md, seção 9)

Antes de implementar:

1. Analisar a estrutura atual do projeto.
2. Consultar o `pyproject.toml` e as dependências existentes.
3. Identificar os módulos relacionados à tarefa.
4. Preservar os padrões arquiteturais existentes.
5. Evitar criar arquivos ou dependências desnecessários.

Durante a implementação:

1. Escrever código modular e reutilizável.
2. Usar apenas dependências gerenciadas pelo Poetry.
3. Criar ou atualizar os testes unitários correspondentes.
4. Atualizar a documentação quando necessário.
5. Executar Ruff, Pytest e MkDocs conforme aplicável.

**Regra principal:** priorizar qualidade, modularidade, testabilidade, documentação e facilidade de manutenção.

## 10. Decisões de implementação

1. **Pacote:** `openf1_pipeline`.
2. **Formato tratado:** CSV, para manter os dados fáceis de inspecionar sem adicionar uma dependência de armazenamento.
3. **Cobertura do dashboard:** por temporada; só declarar o ano completo quando o manifesto confirmar a ingestão de todos os meetings/sessões descobertos.
4. **Telemetria:** `/car_data` e `/location` permanecem opcionais e fora da primeira versão do dashboard.
5. **Dashboard:** Streamlit local; consulta `/meetings` para descobrir temporadas históricas gratuitas (cache de 24 horas), mas lê os tempos de arquivos locais. A ingestão continua via CLI e o agendamento fica para uma fase futura.

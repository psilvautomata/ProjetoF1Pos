# Arquitetura

O código segue o layout `src/` e separa as responsabilidades por módulo:

| Módulo | Responsabilidade |
|---|---|
| `config` | URL base, timeout e diretório de dados via ambiente. |
| `connectors` | Cliente HTTP, filtros e erros específicos da API. |
| `pipelines` | Descoberta de sessões, ingestão e gravação idempotente. |
| `transformations` | Normalização de datas e tipos, remoção de duplicatas e validação. |
| `services` | Relaciona voltas a sessions, meetings e pilotos e calcula o top 5 estável por pista/ano. |
| `dashboard` | Interface Streamlit com tempos da base processada local e descoberta em cache das temporadas disponíveis via `/meetings`. |
| `utils` | Funções pequenas reutilizáveis quando necessárias. |

Cada endpoint é salvo separadamente em `data/raw/<escopo>/<endpoint>.json` e `data/processed/<escopo>/<endpoint>.csv`. Os arquivos são substituídos de forma atômica, portanto repetir a ingestão do mesmo escopo não duplica linhas.

As transformações usam pandas para estruturar e tipar tabelas; requests é usado exclusivamente pelo conector. O pipeline aceita um cliente injetado para testes sem rede.

`ingest_year(year)` percorre meetings e sessões não canceladas já encerradas, grava `/drivers` e `/laps` por sessão e atualiza `data/processed/dashboard/lap_rankings.csv`. Sessões sem encerramento confirmado são marcadas como pendentes para evitar endpoints de dados em tempo real, que exigem assinatura. `ingestion_manifest.json` registra se a cobertura do ano está completa ou parcial. O dashboard consulta somente `/meetings` para descobrir temporadas históricas gratuitas (desde 2023); os tempos exibidos permanecem locais.

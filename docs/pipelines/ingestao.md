# Ingestão de meeting e sessão

## Por Grande Prêmio

```bash
poetry run python -m openf1_pipeline --meeting 1219
```

O pipeline consulta `/meetings`, lista as sessões com `/sessions` e ingere cada sessão encontrada. Um `meeting_key` sem resultados causa um erro explícito.

## Por sessão

```bash
poetry run python -m openf1_pipeline --session 9161 --verbose
```

Para cada sessão são consultados `/drivers`, `/session_result`, `/starting_grid`, `/laps`, `/stints`, `/pit`, `/weather`, `/position` e `/race_control`. `/intervals` é incluído quando o nome/tipo da sessão identifica uma corrida. Respostas vazias são válidas e geram arquivos vazios; erros HTTP, timeout e JSON inválido são reportados pelo conector.

Cada resposta bruta é preservada em JSON e sua versão normalizada é gravada em CSV. Datas conhecidas são convertidas para ISO 8601 UTC, identificadores e números são tipados quando presentes e duplicatas idênticas são removidas.

## Por temporada e dashboard

```powershell
poetry run python -m openf1_pipeline --year 2025
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
```

A ingestão consulta meetings do ano e, para cada sessão não cancelada e já encerrada, baixa pilotos e voltas. Sessões sem `date_end`, com data inválida ou ainda futuras são marcadas como pendentes e não consultadas, para manter o uso restrito ao histórico gratuito. Os dados são relacionados por meeting, sessão e número do piloto. O serviço exclui durações ausentes ou não positivas e voltas marcadas como saída dos boxes. O dataset combinado fica em `data/processed/dashboard/lap_rankings.csv`; `ingestion_manifest.json` indica cobertura completa ou parcial por ano, incluindo a contagem de sessões pendentes.

O dashboard descobre as temporadas históricas gratuitas a partir de 2023 consultando `/meetings` (metadados, em cache por 24 horas), e permite filtrar temporada, pista e tipo de sessão. Os tempos vêm do conjunto local ingerido. Para cada combinação exibe até cinco voltas válidas mais rápidas, piloto, número da volta, sessão e Grande Prêmio, junto com um gráfico de pontos de diferença para o melhor tempo. Empates têm ordem determinística. Um mesmo piloto pode ocupar mais de uma posição.

## Limitações dos dados

`pit_duration` e `country_code` não são usados como dependências do esquema. `stop_duration` pode estar ausente antes do GP dos Estados Unidos de 2024. Alguns endpoints não têm dados para todas as sessões. Telemetria de alta frequência, rádio e endpoints beta de campeonato não são ingeridos nesta versão.

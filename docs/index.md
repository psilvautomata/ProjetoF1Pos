# OpenF1 Pipeline

O objetivo principal é apresentar as cinco voltas válidas mais rápidas por pista e ano em um dashboard local. O projeto consulta dados históricos da API OpenF1 (disponíveis gratuitamente a partir de 2023), preserva respostas originais e grava tabelas tratadas relacionadas por `meeting_key`, `session_key` e `driver_number`.

O fluxo começa em `/meetings`, descobre as sessões em `/sessions` e então consulta pilotos, resultados, grid, voltas, stints, pit stops, clima, posições e controle de prova. `/intervals` é consultado somente para sessões de corrida.

A API OpenF1 não é afiliada oficialmente com a Formula 1 ou a FIA. Dados em tempo real e os endpoints de telemetria `/car_data` e `/location` não fazem parte do escopo atual.

Para preparar uma temporada e abrir o dashboard:

```powershell
poetry install
poetry run python -m openf1_pipeline --year 2025
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
```

## Conteúdo

- [Arquitetura](arquitetura.md)
- [Desenvolvimento](desenvolvimento.md)
- [Configuração](configuracao.md)
- [Dashboard](dashboard.md)
- [Pipeline de ingestão](pipelines/ingestao.md)

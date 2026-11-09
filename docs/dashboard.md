# Dashboard de melhores voltas

O dashboard local mostra até cinco voltas válidas mais rápidas para cada combinação de pista e temporada. A fonte é o endpoint [`/laps`](https://openf1.org/docs/#laps), relacionado às pistas/anos de `/meetings`, aos tipos de sessão em `/sessions` e aos nomes de `/drivers`.

## Preparar uma temporada

Na raiz do repositório, execute:

```powershell
poetry install
poetry run python -m openf1_pipeline --year 2025
```

O comando consulta os meetings do ano e baixa sessões não canceladas e encerradas, pilotos e voltas. O plano gratuito permite até 3 requisições por segundo e 30 por minuto; o cliente espaça as chamadas e aguarda `Retry-After` (ou um minuto) antes de repetir uma resposta `429`. Se o limite continuar ativo após a tentativa, o ano é salvo como parcial e o pipeline para novas chamadas para evitar insistir contra a API. Reexecute o mesmo comando para retomar: meetings, sessões, pilotos e voltas já salvos em `data/raw/` são reutilizados; só requisições ausentes são refeitas. O CSV combinado fica em `data/processed/dashboard/lap_rankings.csv`; o manifesto `data/processed/dashboard/ingestion_manifest.json` registra cobertura completa ou falhas por sessão. Outros anos já ingeridos são preservados.

## Abrir o dashboard

```powershell
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
```

Selecione temporada, pista e, se desejar, tipo de sessão. O dashboard consulta `/meetings?year>=2023` para descobrir temporadas do histórico gratuito até o ano atual e mantém essa lista em cache por 24 horas. Se a API estiver indisponível, mostra as temporadas já presentes nos arquivos locais. Essa consulta usa apenas metadados; a tabela de tempos continua vindo dos dados locais ingeridos.

O ranking inclui voltas de todos os tipos por padrão; cada piloto pode aparecer em mais de uma posição. A tabela mostra posição, tempo formatado, piloto, número, volta, sessão e Grande Prêmio. O gráfico de pontos mostra a diferença em segundos para a volta mais rápida do grupo, deixando visíveis as pequenas margens entre as cinco marcas.

São elegíveis voltas com duração numérica e positiva, exceto as marcadas como voltas de saída dos boxes. Empates recebem ordenação determinística por meeting, sessão, piloto e volta. Se a temporada estiver listada pela API mas ainda não tiver sido importada, a interface mostra o comando para prepará-la. Sessões sem data de término ou ainda em andamento são ignoradas pelo pipeline, evitando depender de dados em tempo real pagos; elas aparecem como pendentes no manifesto e deixam a cobertura parcial.

## Cobertura

Para comparar temporadas, ingira cada ano desejado, por exemplo:

```powershell
poetry run python -m openf1_pipeline --year 2023
poetry run python -m openf1_pipeline --year 2024
poetry run python -m openf1_pipeline --year 2025
```

A API OpenF1 oferece dados históricos gratuitos a partir de 2023. As informações de `/laps` incluem `lap_duration`, `driver_number`, `lap_number` e `is_pit_out_lap`; `meetings` fornece `year` e `circuit_short_name`. Consulte a [documentação oficial](https://openf1.org/docs/) para os campos atualizados.

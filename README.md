# Dashboard OpenF1

Pipeline e dashboard local para explorar as cinco voltas válidas mais rápidas da Fórmula 1 por pista e temporada. O projeto usa dados históricos da [API OpenF1](https://openf1.org/docs/), gratuitos desde 2023, e mantém os tempos ingeridos em arquivos locais para alimentar o dashboard.

## Início rápido

Execute os comandos a partir da raiz do repositório, no terminal do VS Code ou PowerShell:

```powershell
poetry install
poetry run python -m openf1_pipeline --year 2024
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
```

O comando de ingestão prepara os dados do ano selecionado. Depois que o Streamlit iniciar, abra o endereço local exibido no terminal. Para outra temporada, troque `2024` pelo ano desejado (2023 ou posterior).

## Como funciona

1. A ingestão consulta meetings e sessões da temporada na API OpenF1.
2. Para sessões encerradas, baixa os dados de pilotos e voltas e salva as respostas originais em JSON.
3. O pipeline valida os registros e atualiza o dataset processado usado pelo dashboard.
4. O dashboard permite filtrar por temporada, pista e tipo de sessão e exibe uma tabela e um gráfico de pontos com o top 5.

O ranking considera voltas com duração positiva e exclui voltas de saída dos boxes. Um piloto pode aparecer mais de uma vez. Sessões futuras ou sem término confirmado são ignoradas para evitar o acesso pago a dados em tempo real.

O dashboard consulta `/meetings` para descobrir temporadas disponíveis, mas os tempos exibidos vêm da base local. Se a temporada ainda não foi ingerida, a interface mostra o comando necessário.

## Ingerir temporadas

```powershell
poetry run python -m openf1_pipeline --year 2023
poetry run python -m openf1_pipeline --year 2024
poetry run python -m openf1_pipeline --year 2025
```

A API gratuita limita o uso a 3 chamadas por segundo e 30 por minuto. O cliente espaça as requisições e aguarda antes de repetir respostas `429`. Se uma execução for interrompida ou ficar parcial, rode o mesmo comando novamente: respostas já salvas são reutilizadas e apenas os dados ausentes são buscados.

O manifesto registra cobertura por ano. Uma temporada pode continuar parcial se houver sessões futuras ou endpoints indisponíveis na API.

## Documentação do projeto

Para abrir a documentação em um servidor local com atualização automática:

```powershell
poetry run task docs
```

Abra <http://127.0.0.1:8001> no navegador e mantenha o terminal aberto enquanto consulta o site. Encerre com `Ctrl+C`. Para apenas validar e gerar o site estático em modo estrito:

```powershell
poetry run task docs-build
```

## Dados gerados

- `data/raw/`: respostas originais da API, organizadas por ano, meeting e sessão.
- `data/processed/`: tabelas normalizadas e dados usados pelos pipelines.
- `data/processed/dashboard/lap_rankings.csv`: voltas elegíveis para o ranking.
- `data/processed/dashboard/ingestion_manifest.json`: cobertura e falhas por temporada.

> Os arquivos de dados podem ser grandes e não devem ser tratados como código-fonte; o pipeline recria os derivados a partir das respostas brutas.

## Configuração opcional

| Variável | Padrão | Descrição |
|---|---|---|
| `OPENF1_BASE_URL` | `https://api.openf1.org/v1/` | URL base da API. |
| `OPENF1_TIMEOUT` | `30` | Timeout das requisições, em segundos. |
| `OPENF1_DATA_DIR` | `data` | Diretório para respostas brutas e dados processados. |

Exemplo no PowerShell:

```powershell
$env:OPENF1_DATA_DIR = "D:\F1\dados"
poetry run python -m openf1_pipeline --year 2024
```

## Desenvolvimento e verificações

O projeto usa Python 3.12.10 (`.python-version`) e Poetry para gerenciar as dependências. As verificações principais são:

```powershell
poetry run ruff check .
poetry run ruff format . --check
poetry run pytest --cov=openf1_pipeline --cov-report=term-missing --cov-fail-under=50
poetry run task docs-build
```

Os testes unitários simulam as chamadas HTTP e não dependem da API externa.

## Estrutura

```text
src/openf1_pipeline/
├── connectors/       # cliente HTTP da OpenF1
├── dashboard/        # aplicação Streamlit
├── pipelines/        # ingestão por meeting, sessão e temporada
├── services/         # montagem do dataset e ranking de voltas
└── transformations/  # normalização e validação dos dados

docs/                 # documentação MkDocs Material
tests/unit/            # testes unitários
data/                  # dados brutos e processados locais
```

## Documentação adicional

- [Arquitetura](docs/arquitetura.md)
- [Desenvolvimento](docs/desenvolvimento.md)
- [Configuração](docs/configuracao.md)
- [Dashboard](docs/dashboard.md)
- [Pipeline de ingestão](docs/pipelines/ingestao.md)

OpenF1 é um projeto independente e não é afiliado à Formula 1 ou à FIA.

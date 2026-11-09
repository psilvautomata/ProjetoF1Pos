# OpenF1 Pipeline

Pipeline e dashboard para explorar voltas históricas da Fórmula 1 usando a API OpenF1. A entrega principal é um ranking das cinco voltas válidas mais rápidas por pista e ano.

Consulte a [documentação do projeto](docs/index.md) para instalação, configuração e execução.

```powershell
poetry install
poetry run python -m openf1_pipeline --year 2025
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
poetry run task docs
```

O último comando inicia o servidor local da documentação em <http://127.0.0.1:8001>; mantenha o terminal aberto e pressione `Ctrl+C` para encerrá-lo. Para apenas validar e gerar os arquivos estáticos, execute `poetry run task docs-build`.

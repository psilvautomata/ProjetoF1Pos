# Desenvolvimento

## Requisitos

- Pyenv com Python 3.12.10 (registrado em `.python-version`).
- Poetry 2.x para ambientes e dependências.

## Instalação e verificações

```bash
poetry install
poetry run ruff check . --fix
poetry run ruff format .
poetry run ruff check .
poetry run ruff format . --check
poetry run pytest --cov=openf1_pipeline --cov-report=term-missing --cov-fail-under=50
poetry run task docs
```

`poetry run task docs` inicia o servidor local com `mkdocs serve --strict`. Abra <http://127.0.0.1:8000> no navegador; as alterações nos arquivos Markdown são exibidas automaticamente. Pressione `Ctrl+C` no terminal para encerrar o servidor. Para validar e gerar o site estático sem iniciar o servidor, use `poetry run task docs-build`, que executa `mkdocs build --strict`. O Taskipy é uma dependência de desenvolvimento, e MkDocs Material está no grupo `docs`.

Os testes unitários simulam todas as respostas HTTP e não acessam a rede. O principal fluxo de produto é a ingestão por temporada e o dashboard de melhores voltas. Para adicionar um endpoint, incluir testes e atualizar a lista do pipeline e esta documentação.

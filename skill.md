# skill.md
# Padrões e Boas Práticas de Desenvolvimento Python

Este documento estabelece os padrões obrigatórios de desenvolvimento para o projeto. Todas as implementações, alterações e manutenções devem respeitar estas diretrizes.

## 1. Gerenciamento da versão Python com Pyenv

O **Pyenv** deve ser utilizado para instalar e controlar as versões do Python utilizadas no projeto.

- Definir uma versão específica do Python para o projeto.
- Utilizar o arquivo `.python-version` para registrar a versão local.
- Não depender da versão global instalada na máquina.
- Garantir compatibilidade entre a versão definida no Pyenv e a configuração do Poetry.

Exemplo:

```bash
# Definir a versão local do projeto
pyenv local 3.12.10

# Verificar a versão ativa
python --version
```

## 2. Gerenciamento de ambiente e dependências com Poetry

O **Poetry** é a ferramenta oficial para gerenciamento de dependências, pacotes e ambientes virtuais.

Regras obrigatórias:

- Todas as dependências do projeto devem ser instaladas dentro da virtualenv gerenciada pelo Poetry.
- Nunca utilizar `pip install` ou `python -m pip` para instalar pacotes.
- Não realizar instalações manuais fora do gerenciamento do Poetry.
- Utilizar `poetry add` para adicionar dependências.
- Utilizar `poetry remove` para remover dependências.
- Manter `pyproject.toml` e `poetry.lock` versionados.
- Separar dependências de produção, desenvolvimento e documentação.

Comandos:

```bash
# Criar ambiente e instalar dependências
poetry install

# Adicionar pacote de produção
poetry add pandas

# Adicionar ferramentas de desenvolvimento
poetry add --group dev ruff pytest pytest-cov

# Adicionar dependências de documentação
poetry add --group docs mkdocs mkdocs-material

# Executar comandos dentro da virtualenv
poetry run python script.py

# Consultar dependências instaladas
poetry show
```

O Poetry deve ser responsável por toda a gestão do ambiente virtual. Nenhuma dependência do projeto deve ser instalada diretamente no Python global.

## 3. Arquitetura e modularização

O projeto deve seguir a arquitetura `src/`, mantendo o código-fonte dentro de `src/projeto/`.

A modularização é obrigatória. Cada módulo deve possuir responsabilidades bem definidas, evitando concentração de funcionalidades em arquivos extensos.

Estrutura de referência:

```text
projeto/
├── .python-version
├── pyproject.toml
├── poetry.lock
├── README.md
├── mkdocs.yml
│
├── docs/
│   ├── index.md
│   ├── arquitetura.md
│   └── desenvolvimento.md
│
├── src/
│   └── projeto/
│       ├── __init__.py
│       ├── config/
│       ├── connectors/
│       ├── pipelines/
│       ├── transformations/
│       ├── services/
│       └── utils/
│
└── tests/
    ├── conftest.py
    └── unit/
```

Diretrizes:

- Separar responsabilidades por domínio e funcionalidade.
- Evitar duplicação de código.
- Preferir funções pequenas e reutilizáveis.
- Evitar dependências circulares entre módulos.
- Utilizar nomes claros e descritivos.
- Implementar tipagem com Type Hints.
- Isolar regras de negócio de integrações externas.
- Priorizar legibilidade, manutenção e reutilização.

Não criar abstrações ou estruturas desnecessárias. A arquitetura deve acompanhar a complexidade real do projeto.

## 4. Qualidade de código com Ruff

O **Ruff** é a ferramenta oficial para lint, formatação e organização de imports.

Todas as implementações devem seguir o padrão estabelecido pelo Ruff.

Responsabilidades:

- Identificar problemas de qualidade e estilo.
- Aplicar formatação automática.
- Organizar imports automaticamente.
- Identificar imports não utilizados.
- Verificar inconsistências e possíveis problemas no código.

Comandos obrigatórios:

```bash
# Verificar lint
poetry run ruff check .

# Corrigir problemas automaticamente
poetry run ruff check . --fix

# Formatar o código
poetry run ruff format .

# Verificar formatação
poetry run ruff format . --check

# Verificar organização dos imports
poetry run ruff check . --select I
```

O Ruff deve ser executado antes de concluir qualquer implementação.

Não ignorar problemas identificados sem justificativa técnica.

## 5. Testes unitários com Pytest

O **Pytest** é a ferramenta oficial para execução dos testes automatizados.

Todo código desenvolvido deve possuir testes unitários compatíveis com seu comportamento esperado.

Requisitos obrigatórios:

- Manter os testes dentro do diretório `tests/`.
- Organizar os testes conforme os módulos existentes em `src/projeto/`.
- Utilizar nomes descritivos para arquivos e funções de teste.
- Testar cenários positivos, negativos e casos extremos.
- Utilizar fixtures para compartilhamento de configurações e dados.
- Utilizar mocks para isolar dependências externas quando necessário.
- Não depender de serviços externos nos testes unitários.

**Cobertura mínima obrigatória: 50% do código-fonte localizado em `src/projeto/`.**

Instalação:

```bash
poetry add --group dev pytest pytest-cov
```

Execução:

```bash
# Executar testes
poetry run pytest

# Executar testes com cobertura
poetry run pytest --cov=projeto --cov-report=term-missing

# Exigir cobertura mínima de 50%
poetry run pytest --cov=projeto --cov-report=term-missing --cov-fail-under=50

# Gerar relatório HTML
poetry run pytest --cov=projeto --cov-report=html
```

A cobertura deve considerar o código da aplicação, e não os próprios arquivos de teste.

Não reduzir artificialmente a cobertura excluindo funcionalidades relevantes.

## 6. Documentação com MkDocs Material

A documentação técnica do projeto deve ser desenvolvida utilizando **MkDocs Material**.

Toda funcionalidade relevante deve possuir documentação suficiente para permitir sua compreensão, utilização e manutenção por outros desenvolvedores.

Instalação:

```bash
poetry add --group docs mkdocs mkdocs-material
```

Estrutura:

```text
docs/
├── index.md
├── arquitetura.md
├── desenvolvimento.md
├── configuracao.md
└── pipelines/
```

Arquivo de configuração `mkdocs.yml`:

```yaml
site_name: Documentação do Projeto
site_description: Documentação técnica

theme:
  name: material
  language: pt-BR
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy

nav:
  - Início: index.md
  - Arquitetura: arquitetura.md
  - Desenvolvimento: desenvolvimento.md
```

Comandos:

```bash
# Executar documentação localmente
poetry run mkdocs serve

# Gerar documentação
poetry run mkdocs build

# Validar documentação
poetry run mkdocs build --strict
```

A documentação deve contemplar:

- Objetivo e visão geral do projeto.
- Arquitetura e organização dos módulos.
- Configuração do ambiente.
- Dependências utilizadas.
- Instruções de execução.
- Descrição dos principais componentes.
- Fluxos de processamento e transformação de dados.

Toda alteração relevante na arquitetura ou funcionalidade deve refletir na documentação.

## 7. Boas práticas gerais de desenvolvimento

Todas as implementações devem seguir boas práticas de engenharia de software e desenvolvimento Python.

- Utilizar Type Hints nas funções e interfaces públicas.
- Preferir `pathlib` para manipulação de caminhos.
- Utilizar `logging` em vez de `print()` para registrar eventos.
- Tratar exceções de maneira específica e adequada.
- Evitar variáveis globais mutáveis.
- Utilizar variáveis de ambiente para configurações externas.
- Nunca armazenar credenciais ou tokens diretamente no código.
- Utilizar consultas parametrizadas para operações SQL.
- Garantir que operações de dados sejam rastreáveis e reproduzíveis.
- Evitar processamento desnecessário de grandes volumes de dados em memória.
- Manter funções determinísticas sempre que possível.
- Considerar idempotência nas operações de ingestão e processamento.
- Implementar validações para garantir a qualidade dos dados.

## 8. Checklist obrigatório de validação

Antes de considerar qualquer implementação concluída, executar as seguintes verificações:

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

# 6. Executar testes com cobertura mínima
poetry run pytest --cov=projeto --cov-report=term-missing --cov-fail-under=50

# 7. Validar documentação
poetry run mkdocs build --strict
```

A implementação somente poderá ser considerada concluída quando:

- O código estiver organizado em módulos.
- As dependências estiverem gerenciadas pelo Poetry.
- A versão Python estiver definida pelo Pyenv.
- O Ruff não apresentar problemas pendentes.
- Os testes estiverem passando.
- A cobertura mínima de 50% estiver atingida.
- A documentação estiver atualizada e validada.

Caso alguma validação não possa ser executada, informar explicitamente o motivo. Nunca declarar uma validação como aprovada sem executá-la.

## 9. Instruções para agentes de IA

Qualquer agente de IA que trabalhe neste repositório deve respeitar integralmente as regras deste documento.

Antes de implementar qualquer funcionalidade:

1. Analisar a estrutura atual do projeto.
2. Consultar o `pyproject.toml` e as dependências existentes.
3. Identificar os módulos relacionados à implementação.
4. Preservar os padrões arquiteturais existentes.
5. Evitar criar arquivos ou dependências desnecessárias.

Durante a implementação:

1. Desenvolver código modular e reutilizável.
2. Utilizar exclusivamente as dependências gerenciadas pelo Poetry.
3. Criar ou atualizar os testes unitários correspondentes.
4. Atualizar a documentação quando necessário.
5. Executar Ruff, Pytest e MkDocs conforme aplicável.

Não substituir ferramentas, alterar padrões arquiteturais ou adicionar dependências sem necessidade técnica justificada.

**Regra principal: toda implementação deve priorizar qualidade, modularidade, testabilidade, documentação e facilidade de manutenção.**
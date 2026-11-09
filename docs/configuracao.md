# Configuração

As variáveis são opcionais e possuem padrões adequados para o uso histórico:

| Variável | Padrão | Descrição |
|---|---|---|
| `OPENF1_BASE_URL` | `https://api.openf1.org/v1/` | URL base da API. |
| `OPENF1_TIMEOUT` | `30` | Timeout HTTP em segundos, deve ser positivo. |
| `OPENF1_DATA_DIR` | `data` | Diretório de saída para JSON e CSV. |

Exemplo no PowerShell:

```powershell
$env:OPENF1_DATA_DIR = "D:\F1\dados"
poetry run python -m openf1_pipeline --year 2025
poetry run streamlit run src/openf1_pipeline/dashboard/app.py
```

O comando de ano prepara os dados históricos encerrados da temporada e atualiza a base local do dashboard. Ao abrir, o Streamlit consulta apenas `/meetings` para listar temporadas históricas gratuitas desde 2023; essa resposta fica em cache por 24 horas. Os tempos e o manifesto são lidos dos CSVs locais. O pipeline não armazena credenciais nem consulta sessões em andamento, cujo acesso em tempo real exige assinatura.

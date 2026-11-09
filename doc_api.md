# OpenF1 API

Resumo da documentação oficial da [OpenF1](https://openf1.org/docs/), consultada em 08/11/2026.

## 1. Visão geral

A OpenF1 é uma API não oficial e de código aberto que disponibiliza dados da Fórmula 1 em formato JSON ou CSV. Ela permite consultar informações históricas e dados em tempo real, incluindo telemetria, pilotos, sessões, voltas, pneus, clima e ocorrências de corrida.

- **URL base:** `https://api.openf1.org/v1/`
- **Método principal:** HTTP `GET`
- **Formato padrão:** JSON
- **Dados históricos:** disponíveis gratuitamente a partir de 2023, sem autenticação.
- **Dados em tempo real:** exigem assinatura paga.
- **Identificadores:** `meeting_key` identifica um Grande Prêmio/evento; `session_key` identifica uma sessão específica.

A OpenF1 não é afiliada oficialmente à Formula 1 ou à FIA.

## 2. Principais endpoints

| Endpoint | Finalidade |
|---|---|
| `/car_data` | Telemetria dos carros: velocidade, RPM, marcha, acelerador, freio e DRS. Amostragem aproximada de 3,7 Hz. |
| `/championship_drivers` | Classificação do campeonato de pilotos. Endpoint beta e disponível apenas para sessões de corrida. |
| `/championship_teams` | Classificação do campeonato de equipes. Endpoint beta e disponível apenas para sessões de corrida. |
| `/drivers` | Dados dos pilotos de uma sessão: nome, número, equipe, sigla e foto. |
| `/intervals` | Diferença de tempo entre pilotos e distância para o líder. Disponível durante corridas, com atualização aproximada a cada 4 segundos. |
| `/laps` | Dados por volta: tempo total, setores, velocidades intermediárias e informações de mini setores. |
| `/location` | Coordenadas aproximadas dos carros no circuito. Amostragem aproximada de 3,7 Hz; não informa com precisão o posicionamento lateral do carro. |
| `/meetings` | Informações dos Grandes Prêmios e testes: circuito, país, local, datas e identificadores. |
| `/overtakes` | Ultrapassagens e mudanças de posição. Disponível durante corridas e pode estar incompleto. |
| `/pit` | Passagens pelo pit lane e duração das paradas. `stop_duration` está disponível a partir do GP dos Estados Unidos de 2024. |
| `/position` | Histórico de posições dos pilotos durante uma sessão. |
| `/race_control` | Mensagens de direção de prova, bandeiras, Safety Car, status da sessão e incidentes. |
| `/sessions` | Sessões de um evento: treinos, classificação, sprint e corrida, com datas e circuito. |
| `/session_result` | Resultado final de uma sessão, incluindo posição, tempos, voltas e status como DNF, DNS e DSQ. |
| `/starting_grid` | Grid de largada da corrida. |
| `/stints` | Stints de cada piloto, incluindo composto e idade dos pneus, volta inicial e final. |
| `/team_radio` | Links para gravações de rádio entre piloto e equipe. A cobertura é parcial e depende da disponibilização pela F1. |
| `/weather` | Condições meteorológicas no circuito: temperatura, umidade, pressão, chuva e vento. Atualização aproximada de 1 minuto. |

## 3. Como montar uma consulta

Todas as consultas seguem a estrutura:

```text
https://api.openf1.org/v1/{endpoint}?parametro=valor
```

Exemplo: consultar os pilotos de uma sessão:

```text
https://api.openf1.org/v1/drivers?session_key=9158
```

Também é possível usar `curl`:

```bash
curl "https://api.openf1.org/v1/drivers?session_key=9158"
```

Ou Python com `requests`:

```python
import requests

url = "https://api.openf1.org/v1/drivers"
params = {"session_key": 9158}

response = requests.get(url, params=params)
response.raise_for_status()

dados = response.json()
print(dados)
```

## 4. Parâmetros e filtros

Os filtros são enviados diretamente na URL. É possível filtrar por qualquer atributo do endpoint, exceto campos que sejam arrays.

Operadores disponíveis nos exemplos da documentação:

| Operador | Significado |
|---|---|
| `=` | Igual a |
| `>` | Maior que |
| `>=` | Maior ou igual a |
| `<` | Menor que |
| `<=` | Menor ou igual a |

Exemplos:

```text
# Piloto específico em uma sessão
/drivers?session_key=9158&driver_number=1

# Telemetria acima de 315 km/h
/car_data?session_key=9159&driver_number=55&speed>=315

# Voltas de um piloto
/laps?session_key=9161&driver_number=63

# Paradas inferiores a 2,3 segundos
/pit?session_key=9877&stop_duration<2.3
```

É possível combinar vários parâmetros na mesma consulta. Para filtrar por período, use campos de data, como `date`, `date_start` e `date_end`.

Exemplo de intervalo de datas:

```text
/sessions?date_start>=2023-09-01&date_end<=2023-09-30
```

A documentação aceita diferentes formatos de data. Recomenda-se usar ISO 8601, por exemplo `2023-09-10T14:30:20+00:00`.

## 5. Identificadores importantes

A API utiliza identificadores para relacionar os dados:

- `meeting_key`: identifica o evento, como um Grande Prêmio.
- `session_key`: identifica uma sessão específica, como treino livre, classificação ou corrida.
- `driver_number`: número do piloto na temporada.

Os valores `latest` podem ser usados em `meeting_key` e `session_key` para consultar o evento ou a sessão mais recente/atual, quando aplicável.

Fluxo recomendado para explorar os dados:

1. Consultar `/meetings` para localizar o Grande Prêmio.
2. Usar o `meeting_key` em `/sessions` para localizar as sessões do evento.
3. Selecionar o `session_key` da sessão desejada.
4. Consultar `/drivers`, `/laps`, `/car_data`, `/position`, `/pit` e outros endpoints usando esse `session_key`.

## 6. Resposta em CSV

O formato padrão é JSON. Para receber CSV, basta adicionar `csv=true` à URL.

Exemplo:

```text
https://api.openf1.org/v1/sessions?year=2023&csv=true
```

Esse formato facilita a importação dos dados em ferramentas como Excel e Power BI.

## 7. Cuidados e limitações

- Dados históricos gratuitos começam em 2023.
- Consultas de dados em tempo real exigem assinatura paga.
- Nem todos os endpoints possuem dados para todas as sessões.
- `team_radio` contém apenas uma seleção de comunicações. A documentação informa redução significativa da cobertura a partir de 2026.
- `overtakes` pode estar incompleto e inclui mudanças de posição causadas por pit stops ou penalidades, não apenas ultrapassagens na pista.
- `location` fornece coordenadas aproximadas e não identifica se o carro está à esquerda ou à direita da pista.
- `stop_duration` só está disponível a partir do GP dos Estados Unidos de 2024.
- O campo `pit_duration` está depreciado e tem remoção prevista para o fim da temporada de 2026. Prefira `lane_duration`.
- O campo `country_code` do endpoint `/drivers` está depreciado e tem remoção prevista para o fim da temporada de 2026.
- Os endpoints de classificação de campeonato são beta.

## 8. Links úteis

- [Documentação oficial](https://openf1.org/docs/)
- [API base](https://api.openf1.org/v1/)
- [Repositório GitHub](https://github.com/br-g/openf1)
- [Tutoriais oficiais](https://openf1.org/docs/#tutorials)

---

**Referência:** documentação oficial da OpenF1. Este arquivo é um resumo dos conceitos e endpoints mais relevantes; consulte a documentação para conferir os atributos completos, exemplos atualizados e eventuais mudanças.

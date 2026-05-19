# Conexão MQTT — Documentação

## Visão Geral

O sistema recebe dados de tags RFID de dispositivos ESP32 via MQTT e armazena no banco SQLite.

## Fluxo de Comunicação

```
ESP32 (dispositivos)
    │
    │  Publica mensagens no topic "rfid/tags"
    ▼
MQTT Broker (localhost:1883)
    │
    │  Assinatura do FastAPI
    ▼
FastAPI (background task)
    │
    │  Insere no SQLite
    ▼
Banco de dados
```

## Formato da Mensagem MQTT

```json
{
  "uid": "A1B2C3D4",
  "status": "ok",
  "rssi": -45,
  "timestamp": "2026-05-18T12:00:00"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-------------|
| `uid` | string | Sim | Identificador da tag RFID |
| `status` | string | Não | Status da leitura (padrão: "ok") |
| `rssi` | number | Não | Força do sinal em dBm |
| `timestamp` | string | Não | Data/hora da leitura (ISO 8601) |

## Implementação

### 1. Módulo MQTT (`api/mqtt.py`)

- `on_connect()` — Callback que assina o topic `rfid/tags`
- `on_message()` — Parse JSON, insere no SQLite via SQLAlchemy
- `start_mqtt_listener()` — Cria o cliente MQTT

### 2. Modelo (`api/models.py`)

- Campo `rssi` (Float) adicionado ao `AccessLog`

### 3. API Principal (`api/main.py`)

- Inicia o listener MQTT no `startup` (`loop_start`)
- Para no `shutdown` (`loop_stop`)
- CORS middleware habilitado

## Endpoints

| Rota | Descrição |
|------|-----------|
| `GET /` | Health check |
| `GET /health` | Status do serviço |
| `GET /logs?uid=xxx&limit=100&offset=0` | Lista logs de acesso |

## Configuração (`.env`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MQTT_HOST` | `localhost` | Host do broker MQTT |
| `MQTT_PORT` | `1883` | Porta do broker |
| `MQTT_TOPIC` | `rfid/tags` | Topic MQTT |

## Dependências

- `paho-mqtt==2.1.0` — Cliente MQTT
- `fastapi` — Framework web
- `sqlalchemy` — ORM do banco de dados

## Como Testar

```bash
# Iniciar o servidor
uvicorn api.main:app --reload

# Ou diretamente
python -m uvicorn api.main:app
```

Precisa de um broker MQTT rodando (ex: `mosquitto`).

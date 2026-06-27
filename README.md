# Sistema de Reconhecimento e Controle de Acesso via RFID (ESP32 + MQTT + FastAPI)

Este projeto consiste em um sistema de autenticação de tags RFID usando um ESP32, um broker MQTT para transporte de dados, uma API FastAPI para processamento/validação no banco de dados SQLite, e uma dashboard web interativa rodando em tempo real com WebSockets.

---

## 🚀 Como Iniciar a API (Backend)

1. **Ativar o Ambiente Virtual (venv):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Instalar Dependências (caso não estejam instaladas):**
   ```bash
   pip install -r requirements.txt
   ```
3. **Iniciar o Servidor/API:**
   ```bash
   python -m uvicorn api.main:app --reload
   ```
   A API estará ativa em `http://127.0.0.1:8000`. A documentação interativa (Swagger) estará disponível em `http://127.0.0.1:8000/docs`.

---

## 💻 Como Rodar o Dashboard (Frontend)

O painel foi construído de forma estática com HTML, CSS e JavaScript puros (Vanilla).

*   **Método Direto (Mais Fácil):**
    Basta abrir o arquivo [index.html](file:///c:/workspace/RFID-ESP32-reader/dashboard/index.html) (clicando duas vezes nele no Windows Explorer) em qualquer navegador.
    *O arquivo `app.js` detecta automaticamente se foi aberto localmente e se conectará à API rodando na porta `8000` automaticamente.*

*   **Método via Servidor Local (Python):**
    Caso queira rodar o frontend em um servidor local dedicado:
    ```bash
    python -m http.server 5000 --directory dashboard
    ```
    Acesse no navegador: `http://localhost:5000`.

---

## 📡 Como Coletar as Informações do ESP32 (MQTT Broker)

O ESP32 e a API FastAPI comunicam-se de forma assíncrona por meio de um **Broker MQTT** (que funciona como um intermediário postal).

### Passo 1: Iniciar um Broker MQTT Local
Para que os dados circulem, você precisa de um broker ativo na sua máquina.
*   **Via Windows (Eclipse Mosquitto):** Baixe e instale em [mosquitto.org](https://mosquitto.org/download/). O serviço geralmente inicia sozinho na porta `1883`.
*   **Via Docker (Se preferir):**
    ```bash
    docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 eclipse-mosquitto
    ```

### Passo 2: Configurar o Firmware do ESP32
Abra o arquivo [firmware.ino](file:///c:/workspace/RFID-ESP32-reader/esp32/firmware.ino) na Arduino IDE e configure:
1.  **Wi-Fi:** Insira o nome (`ssid`) e a senha (`password`) do seu Wi-Fi.
2.  **IP do Servidor MQTT (`mqtt_server`):** Insira o **IP local do seu computador** na rede (ex: `192.168.1.50`).
    *   *Nota: Para descobrir seu IP local no Windows, abra o prompt de comando e digite `ipconfig`. Procure por "Endereço IPv4".*
    *   *Importante: Não use `localhost` ou `127.0.0.1` no ESP32, pois ele tentará se conectar a si mesmo.*
3.  Grave o código no ESP32.

### Passo 3: Configurar a API (`.env`)
Certifique-se de que o arquivo `.env` na raiz do projeto aponta para o seu Broker MQTT:
```env
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=rfid/tags
```

---

## 🧪 Como Testar sem o ESP32 (Simulação)

Você pode testar a Dashboard e a API rodando em tempo real mesmo sem o hardware conectado:

1.  Abra a **Dashboard** (`dashboard/index.html`) no navegador.
2.  No formulário de cadastro, registre uma nova tag de teste (ex: Nome: `Matheus Dums`, Tag: `04A3F91C`, Ativo: `Marcado`).
3.  Simule uma leitura da tag enviando uma requisição HTTP via Terminal (PowerShell):
    ```powershell
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/rfid/access-test" -Method Post -ContentType "application/json" -Body '{"uid": "04A3F91C", "rssi": -45}'
    ```
4.  Observe que a **Dashboard irá atualizar instantaneamente** exibindo o cartão de acesso verde "Acesso Liberado" para o Matheus e reproduzirá um bipe de aprovação.
5.  Experimente enviar uma tag não cadastrada ou desativar o Matheus no painel para ver o acesso ser negado (cartão vermelho e som de erro).
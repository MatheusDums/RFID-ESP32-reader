/**
 * Sistema RFID com ESP32 + MQTT + FastAPI
 * 
 * Este firmware realiza a leitura de tags RFID utilizando o leitor MFRC522,
 * envia o UID lido via MQTT para validação no backend, e aguarda a resposta
 * para acionar os LEDs (Verde para Acesso Liberado / Vermelho para Negado)
 * e o Buzzer de feedback sonoro.
 * 
 * --- Bibliotecas Necessárias (instalar via Gerenciador de Bibliotecas do Arduino): ---
 * 1. "MFRC522" (por GithubCommunity)
 * 2. "PubSubClient" (por Nick O'Leary)
 * 3. "ArduinoJson" (por Benoit Blanchon)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// ==========================================
// CONFIGURAÇÕES DE REDE E MQTT
// ==========================================
const char* ssid = "MARCELINO@SIMFIBRA";
const char* password = "mpimoveis123";
const char* mqtt_server = "broker.hivemq.com"; // Usando broker público para testes
const int mqtt_port = 1883;

// Tópicos de Comunicação Customizados (para evitar colisões com outros usuários do broker público)
const char* topic_publish = "matheus_rfid/tags";      
const char* topic_subscribe = "matheus_rfid/resposta";

// ==========================================
// CONFIGURAÇÃO DOS PINOS (ESP32)
// ==========================================
// Pinos SPI para o Leitor RFID MFRC522 (Padrão ESP32)
#define SS_PIN  5    // SDA no leitor MFRC522
#define RST_PIN 22   // RST no leitor MFRC522
// Conexões de SPI padrão no ESP32: SCK=18, MISO=19, MOSI=23

// Pinos de Status de Saída
#define LED_GREEN 12  // LED de Acesso Liberado
#define LED_RED   14  // LED de Acesso Negado
#define BUZZER    27  // Buzzer ativo de feedback (opcional)

// Instâncias
WiFiClient espClient;
PubSubClient mqttClient(espClient);
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Variável para controle de feedback
String lastScannedUID = "";
unsigned long lastScanTime = 0;
const unsigned long scanCooldown = 3000; // Tempo mínimo entre leituras da mesma tag (3 seg)

// ==========================================
// SETUP & INICIALIZAÇÃO
// ==========================================
void setup() {
    Serial.begin(115200);

    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_RED, OUTPUT);
    pinMode(BUZZER, OUTPUT);

    // Inicializa SPI explicitamente
    SPI.begin(18, 19, 23, SS_PIN);

    // Inicializa o RC522
    mfrc522.PCD_Init();
    delay(100);

    byte version = mfrc522.PCD_ReadRegister(MFRC522::VersionReg);

    Serial.print("Versão do RC522: 0x");
    Serial.println(version, HEX);

    if (version == 0x00 || version == 0xFF) {
        Serial.println("ERRO: MFRC522 não encontrado!");

        while (true) {
            digitalWrite(LED_RED, HIGH);
            delay(250);
            digitalWrite(LED_RED, LOW);
            delay(250);
        }
    }

    Serial.println("Leitor RFID inicializado com sucesso.");

    setup_wifi();

    mqttClient.setServer(mqtt_server, mqtt_port);
    mqttClient.setCallback(mqtt_callback);
}

// Conexão WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando-se a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // Pisca LED vermelho enquanto conecta
    digitalWrite(LED_RED, !digitalRead(LED_RED));
  }
  
  digitalWrite(LED_RED, LOW);
  Serial.println("");
  Serial.println("Wi-Fi conectado com sucesso!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// Conectando/Reconectando ao Broker MQTT
void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Tentando conectar ao MQTT Broker...");
    
    // Cria um ID de cliente único baseado no MAC do ESP32
    String clientId = "ESP32Client-" + String(WiFi.macAddress());
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("conectado!");
      // Subscreve-se no tópico de resposta do backend
      mqttClient.subscribe(topic_subscribe);
      Serial.print("Inscrito no tópico: ");
      Serial.println(topic_subscribe);
    } else {
      Serial.print("falhou, rc=");
      Serial.print(mqttClient.state());
      Serial.println(". Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

// ==========================================
// PROCESSAMENTO DE LEITURA (MQTT CALLBACK)
// ==========================================
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no tópico [");
  Serial.print(topic);
  Serial.print("]: ");

  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Tratamento da resposta JSON do backend
  // Exemplo: {"uid": "04A3F91C", "status": "authorized", "name": "Matheus Dums"}
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("Erro de parse JSON: ");
    Serial.println(error.c_str());
    return;
  }

  const char* uid = doc["uid"];
  const char* status = doc["status"];
  const char* name = doc["name"];

  // Validação: Verifica se o UID retornado corresponde ao que lemos recentemente
  if (String(uid).equalsIgnoreCase(lastScannedUID)) {
    if (String(status) == "authorized") {
      Serial.printf("Acesso AUTORIZADO para o usuário: %s\n", name);
      acessoAutorizado();
    } else {
      Serial.printf("Acesso NEGADO para a tag UID: %s\n", uid);
      acessoNegado();
    }
    // Reseta o UID temporário para evitar loops
    lastScannedUID = "";
  }
}

// ==========================================
// LOOP PRINCIPAL
// ==========================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }
  
  if (!mqttClient.connected()) {
    reconnect();
  }
  
  mqttClient.loop();

  // Verifica se há novas tags RFID próximas
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  Serial.println("Cartão presente!");

  if (!mfrc522.PICC_ReadCardSerial()) {
      Serial.println("Falhou ao ler serial");
      return;
  }

  Serial.println("Serial lido!");

  // Coleta o UID da tag lida e converte para string hexadecimal
  String rfidUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    rfidUID += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    rfidUID += String(mfrc522.uid.uidByte[i], HEX);
  }
  rfidUID.toUpperCase();

  // Evita re-leitura duplicada imediata da mesma tag
  if (rfidUID.equalsIgnoreCase(lastScannedUID) && (millis() - lastScanTime < scanCooldown)) {
    mfrc522.PICC_HaltA();
    return;
  }

  Serial.println("\n--- Nova Tag Detectada ---");
  Serial.print("Tag UID: ");
  Serial.println(rfidUID);
  
  lastScannedUID = rfidUID;
  lastScanTime = millis();

  // Coleta a força do sinal Wi-Fi (RSSI) para diagnósticos
  int32_t rssi = WiFi.RSSI();

  // Publica a leitura via MQTT em formato JSON
  StaticJsonDocument<128> doc;
  doc["uid"] = rfidUID;
  doc["rssi"] = rssi;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.print("Enviando dados da leitura para a API: ");
  Serial.println(jsonPayload);
  
  if (mqttClient.publish(topic_publish, jsonPayload.c_str())) {
    Serial.println("Dados publicados com sucesso.");
    // Bipe curto de envio
    beep(1, 80);
  } else {
    Serial.println("Falha ao publicar mensagem MQTT.");
    beep(2, 100);
  }

  // Para o leitor RFID
  mfrc522.PICC_HaltA();
}

// ==========================================
// ACIONAMENTOS DE FEEDBACK (LED & BUZZER)
// ==========================================
void beep(int count, int durationMs) {
  for (int i = 0; i < count; i++) {
    digitalWrite(BUZZER, HIGH);
    delay(durationMs);
    digitalWrite(BUZZER, LOW);
    if (i < count - 1) {
      delay(durationMs);
    }
  }
}

void acessoAutorizado() {
  digitalWrite(LED_GREEN, HIGH);
  beep(1, 150); // Bipe rápido e agudo
  delay(1850);  // Mantém o LED aceso por 2 segundos no total
  digitalWrite(LED_GREEN, LOW);
}

void acessoNegado() {
  digitalWrite(LED_RED, HIGH);
  beep(1, 600); // Bipe longo e grave
  delay(1400);  // Mantém o LED vermelho aceso por 2 segundos no total
  digitalWrite(LED_RED, LOW);
}

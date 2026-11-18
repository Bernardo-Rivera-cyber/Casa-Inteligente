#include <Servo.h>

// =========================
// SERVO (SOLO UNO EN EL PIN 9)
// =========================
Servo servoPuerta;
const int PIN_SERVO = 9;

// =========================
// LEDS DE LA CASA
// =========================
const int cuarto1 = 3;
const int garaje = 2;
const int bano = 4;
const int sala = 6;
const int cuarto2 = 5;

void setup() {
  Serial.begin(9600);

  // =========================
  // CONFIGURAR SERVO
  // =========================
  servoPuerta.attach(PIN_SERVO);

  // Posición inicial: garaje cerrado (Ajusta el ángulo si es necesario)
  servoPuerta.write(0); 

  // =========================
  // CONFIGURAR LEDS
  // =========================
  pinMode(garaje, OUTPUT);
  pinMode(sala, OUTPUT);
  pinMode(cuarto1, OUTPUT);
  pinMode(cuarto2, OUTPUT);
  pinMode(bano, OUTPUT);

  // Apagar todas las luces al iniciar
  digitalWrite(garaje, LOW);
  digitalWrite(sala, HIGH); // Recuerda que tu sala funciona al revés
  digitalWrite(cuarto1, LOW);
  digitalWrite(cuarto2, LOW);
  digitalWrite(bano, LOW);
}

void loop() {

  if (Serial.available() > 0) {

    String comando = Serial.readStringUntil('\n');
    comando.trim();

    // =========================
    // CONTROL DE LA PUERTA DEL GARAJE
    // =========================
    if (comando == "abrir garaje") {
      servoPuerta.write(180); // Abre el garaje (gira 180 grados)
      Serial.println("Garaje abierto");
    }
    else if (comando == "cerrar garaje") {
      servoPuerta.write(0);   // Cierra el garaje (vuelve a 0 grados)
      Serial.println("Garaje cerrado");
    }

    // =========================
    // ENCENDER / APAGAR TODO
    // =========================
    else if (comando == "encender todo") {
      digitalWrite(garaje, HIGH);
      digitalWrite(sala, LOW); // Tu sala funciona al revés
      digitalWrite(cuarto1, HIGH);
      digitalWrite(cuarto2, HIGH);
      digitalWrite(bano, HIGH);
    }
    else if (comando == "apagar todo") {
      digitalWrite(garaje, LOW);
      digitalWrite(sala, HIGH); // Tu sala funciona al revés
      digitalWrite(cuarto1, LOW);
      digitalWrite(cuarto2, LOW);
      digitalWrite(bano, LOW);
    }

    // =========================
    // LUZ DEL GARAJE
    // =========================
    else if (comando == "encender garaje") {
      digitalWrite(garaje, HIGH);
    }
    else if (comando == "apagar garaje") {
      digitalWrite(garaje, LOW);
    }

    // =========================
    // SALA
    // =========================
    else if (comando == "encender sala") {
      digitalWrite(sala, LOW);
    }
    else if (comando == "apagar sala") {
      digitalWrite(sala, HIGH);
    }

    // =========================
    // CUARTO 1
    // =========================
    else if (comando == "encender cuarto uno") {
      digitalWrite(cuarto1, HIGH);
    }
    else if (comando == "apagar cuarto uno") {
      digitalWrite(cuarto1, LOW);
    }

    // =========================
    // CUARTO 2
    // =========================
    else if (comando == "encender cuarto dos") {
      digitalWrite(cuarto2, HIGH);
    }
    else if (comando == "apagar cuarto dos") {
      digitalWrite(cuarto2, LOW);
    }

    // =========================
    // BAÑO
    // =========================
    else if (comando == "encender baño") {
      digitalWrite(bano, HIGH);
    }
    else if (comando == "apagar baño") {
      digitalWrite(bano, LOW);
    }
  }
}
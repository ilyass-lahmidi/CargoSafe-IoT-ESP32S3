# Brochage validé dans les tests

| Broche ESP32-S3 | Connexion |
|---|---|
| GPIO1 | LDR (ADC, pont diviseur avec 10 kΩ) |
| GPIO4 | ILS + aimant (pull-up interne) |
| GPIO5 | TIP122 / moteur 12 V, résistance de base 1 kΩ et diode de roue libre |
| GPIO6 | Signal PWM du SG90 (alimentation 5 V adaptée séparée) |
| GPIO7 | Buzzer actif (modèle compatible vérifié au banc) |
| GPIO8 | Bus I2C SDA (AHT10, MPU6050, OLED) |
| GPIO9 | Bus I2C SCL (AHT10, MPU6050, OLED) |
| GPIO10 | RFID RC522 SDA / CS |
| GPIO11 | RFID RC522 MOSI |
| GPIO12 | RFID RC522 SCK |
| GPIO13 | RFID RC522 MISO |
| GPIO14 | RFID RC522 RST |

I2C : AHT10 0x38, OLED SSD1306 0x3D, MPU6050 0x68.

**Sécurité d'alimentation** : moteur 12 V et servo 5 V alimentés séparément de la logique 3,3 V ; masses communes. Éviter de faire passer le courant du moteur par les rails fins de la breadboard. Le brochage décrit un prototype testé, non un schéma normalisé final.

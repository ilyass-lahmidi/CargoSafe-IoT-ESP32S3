# Architecture fonctionnelle

```text
AHT10 (I2C)  ----\
MPU6050 (I2C) ----+---- ESP32-S3 N8R8 ---- OLED SSD1306 (I2C)
LDR (ADC) --------++---- TIP122 -> Moteur DC 12 V
ILS (GPIO) -------+---- Servo SG90 (PWM) 0° / 150°
RC522 (SPI) ------+---- Buzzer actif (GPIO)
                       |
                       +---- Wi-Fi / MQTT ---- ThingsBoard Cloud
```

Le projet est un **prototype sur breadboard**, sans dispositif de verrouillage mécanique fonctionnel ni système de refroidissement réel. Le servomoteur **simule** le verrouillage et le moteur **simule** la ventilation.

Référence : code V3 dans `src/`. Consulter aussi `brochage.md`.

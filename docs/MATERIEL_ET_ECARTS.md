# Matériel documenté et écarts à confirmer

La liste Excel sous `hardware/components/` est conservée **sans modification**, comme document de planification. Elle ne reflète pas nécessairement les choix réalisés dans le dernier montage.

## Configuration de référence du programme V3

| Élément | Rôle | Liaison / commande |
|---|---|---|
| ESP32-S3 N8R8 | Contrôleur MicroPython et MQTT | — |
| AHT10 (d'après le code) | Température et humidité | I²C, `0x38` |
| MPU6050 | Mouvements / chocs | I²C, `0x68` |
| OLED SSD1306 128×64 | Affichage d'état | I²C, `0x3D` |
| LDR + résistance 10 kΩ | Variation de luminosité | GPIO1, ADC |
| ILS + aimant | Ouverture / fermeture | GPIO4, entrée pull-up |
| Lecteur RFID RC522 | Identification par carte | SPI, GPIO10–14 |
| Servo SG90 | Simulation de déverrouillage | GPIO6 PWM, alimentation adaptée |
| Moteur CC 12 V | Ventilation expérimentale | GPIO5 via TIP122, circuit de puissance séparé |
| Buzzer actif | Alerte sonore | GPIO7, commande adaptée au modèle |

## Différences entre la liste Excel et la V3

| Point | Liste Excel préliminaire | Documentation/code V3 | Action |
|---|---|---|---|
| Capteur thermique | AHT20 | Appelé **AHT10** ; adresse `0x38` | Confirmer la référence inscrite sur le module physique |
| Commande moteur | Module MOSFET recommandé | TIP122 avec résistance de base et diode dans les notes | Confirmer le composant réellement monté et les caractéristiques électriques |
| Servo | Test suggéré jusqu'à **90°** | Commande programmée à **150°** | Confirmer les positions adaptées au mécanisme et à la plage du servo |
| Buzzer | Liste évoquant plusieurs événements d'alarme | Code V3 : intrusion ou forte lumière pendant l'ouverture | Ne pas annoncer d'alarme sonore pour les chocs ou la température |
| MQTT | « À programmer » dans le tableau de planification | V3 contient publication MQTT ; captures de télémétrie fournies | Mettre à jour la liste après vérification sur carte |

**Électricité** : le moteur 12 V et le servo demandent des alimentations adaptées, avec masse commune et circuit de puissance protégé. Le fichier V3 ne valide pas à lui seul le dimensionnement du montage réel.

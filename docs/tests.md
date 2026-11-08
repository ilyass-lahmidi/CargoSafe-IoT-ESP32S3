# Résumé des essais réalisés

Ces essais sont rapportés comme **fonctionnels lors des tests sur breadboard**, mais il manque encore un dossier de tests formel avec dates, valeurs, photos et critères d'acceptation.

| Sous-ensemble | Résultat rapporté |
|---|---|
| AHT10 (température / humidité) | Mesures affichées correctement |
| TIP122 + moteur DC 12 V | Activation automatique suivant seuil thermique |
| LDR analogique | Variation en fonction de l'éclairage |
| ILS + aimant | Détection ouverture / fermeture |
| MPU6050 | Détection des chocs par variation d'accélération |
| RC522 | Lecture RFID / UID |
| SG90 | Rotation testée jusqu'à 150° |
| RFID + ILS + SG90 + buzzer | Autorisation, intrusion et alarme testées |
| OLED SSD1306 I2C | Affichage opérationnel, adresse 0x3D |
| Wi-Fi / MQTT ThingsBoard | Messages de télémétrie reçus |
| Tableau de bord | Cartes température / humidité, historique température et seuil 26 °C fonctionnels |

**À consolider** : confirmer la version courante des fichiers et noter les essais de déconnexion, la robustesse sous charge, la calibration LDR et les contraintes d'alimentation.

# État actuel — CargoSafe IoT

## Réalisé et testé par l'étudiant

- AHT10 (température / humidité) et commande moteur DC 12 V via TIP122.
- Détection analogique de lumière par LDR.
- Détection d'ouverture par ILS + aimant.
- Détection de mouvements et de chocs via MPU6050.
- Lecture UID RFID RC522, servo SG90 à 150° pour déverrouillage simulé.
- Alarme sonore par buzzer actif : intrusion ou forte luminosité pendant l'ouverture.
- Affichage OLED SSD1306 à l'adresse 0x3D.
- Connexion Wi-Fi / MQTT et envoi de données réelles à ThingsBoard.
- Cartes de température et d'humidité sur tableau de bord ; graphique de température avec seuil 26 °C.

## En développement / à consolider

- Terminer et tester tous les indicateurs du tableau de bord : accès RFID, colis ouvert, intrusion, forte lumière, chocs, moteur, buzzer.
- Tester la robustesse : déconnexions réseau, reconnectivité, bruit capteurs, alimentation, démarrages et défaillances.
- Consolider les essais dans un vrai protocole avec observations et preuves photographiques.
- Photographier le montage complet et dessiner un schéma électrique final.
- Exporter les versions réellement utilisées sur l'ESP32 et les bibliothèques personnelles.

## Équipe

Non précisé pour ce projet dans les informations disponibles.

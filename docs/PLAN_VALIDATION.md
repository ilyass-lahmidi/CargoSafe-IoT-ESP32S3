# Plan de validation du prototype CargoSafe

**Ce fichier est un protocole de travail, pas un rapport d'essais déjà réussi.** Cocher uniquement les cas réellement reproduits sur le montage, en indiquant la date, la version du firmware et une preuve.

| Essai | Condition / manipulation | Résultat attendu selon la V3 | Statut vérifié | Preuve / notes |
|---|---|---|---|---|
| I²C | Rechercher les périphériques sur I²C | `0x38`, `0x3D`, `0x68` détectés | À confirmer | — |
| Température / humidité | Observer les mesures AHT | Valeurs affichées OLED et transmises | À confirmer | — |
| Seuil de température | Mesure sous puis au-dessus de 26 °C | Moteur OFF puis ON | À confirmer | — |
| RFID | Carte autorisée / non autorisée | Déverrouillage simulé / refus | À confirmer | — |
| Porte / ILS | Ouvrir avec et sans autorisation | État « OUVERT » / intrusion mémorisée | À confirmer | — |
| LDR | Éclairer le capteur, colis ouvert | Alerte au-delà du seuil calibré | À confirmer | — |
| Fermeture | Refermer après intrusion | Sonnerie arrêtée, intrusion mémorisée | À confirmer | — |
| Choc | Secousse contrôlée | Compteur de chocs mis à jour | À confirmer | — |
| OLED | Parcourir les états principaux | Mesures et messages cohérents | À confirmer | — |
| MQTT | Connecter l'appareil à ThingsBoard | Télémetrie visible sur tableau de bord | À confirmer | — |
| Réseau coupé | Couper temporairement le Wi-Fi | Fonctions locales maintenues, reconnexion à contrôler | À confirmer | — |
| Alimentation | Tester actionneurs et capteurs simultanément | Pas de redémarrage / surchauffe | À confirmer | — |

Les documents de l'archive de départ **rapportent** plusieurs essais fonctionnels sur breadboard et des captures ThingsBoard, mais ne fournissent pas tous les résultats datés nécessaires pour remplir ce protocole de manière indépendante.

Pour chaque essai : date, code utilisé (nom et version), alimentation, résultat observé, photo/vidéo ou journal, problème rencontré, correction éventuelle.

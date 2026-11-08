# Installer et exécuter CargoSafe avec Thonny

> **Important** : instructions de préparation, **pas une validation de reproductibilité**. Ne pas alimenter un moteur 12 V ou un servomoteur depuis une broche GPIO de l'ESP32-S3.

## Prérequis

- ESP32-S3 N8R8 avec MicroPython compatible et **Thonny**.
- Montage réalisé conformément au [brochage documenté](brochage.md), avec alimentation et protections adaptées.
- Bibliothèques adaptées à votre version MicroPython : `mfrc522.py`, `mpu6050.py`, `ssd1306.py` et `umqtt.simple` si elle n'est pas présente dans le firmware. **Ces bibliothèques ne sont pas incluses dans l'archive** : retrouver les versions utilisées et respecter leur licence.
- Configuration réseau ThingsBoard personnelle et une carte RFID de test autorisée.

## Étapes conseillées

1. Brancher l'ESP32-S3 et sélectionner dans Thonny l'interpréteur **MicroPython (ESP32)** et le bon port.
2. Rechercher sur votre carte **le programme qui fonctionne réellement** et l'enregistrer sur votre ordinateur en conservant une copie de sauvegarde. Comparer cette version à `src/CargoSafe_IoT_ThingsBoard_V3.py` avant toute modification.
3. Pour utiliser la version V3 du dépôt, ouvrir `config/config_reseau.example.py`, en faire une **copie privée** nommée `config_reseau.py`, puis y saisir vos vrais accès **uniquement sur votre ordinateur et sur la carte**. Ne jamais ajouter ce fichier à GitHub.
4. Copier `config_reseau.py` et les bibliothèques nécessaires **à la racine du système de fichiers de l'ESP32**, au même niveau que le script exécuté. Le dossier `config/` du dépôt ne fait pas partie du chemin d'import automatiquement utilisé par le programme.
5. Dans une copie locale de la V3, remplacer `UID_AUTORISE = "REMPLACE_PAR_TON_UID"` par l'UID autorisé pour vos essais. Garder les identifiants privés hors du dépôt public.
6. Vérifier le câblage, les alimentations, les adresses I²C (`0x38`, `0x3D`, `0x68`) et le type réel de capteur (AHT10/AHT20). Tester séparément les capteurs et actionneurs, puis le système complet.
7. Exécuter le programme **manuellement** depuis Thonny avant de l'enregistrer comme `main.py` sur la carte. Ne pas remplacer le programme existant sans sauvegarde.
8. Observer les messages série, la réaction des actionneurs et les valeurs transmises à ThingsBoard. Noter les résultats dans `docs/PLAN_VALIDATION.md`.

## Limites techniques à connaître

- Le programme actuel importe `from config_reseau import ...` et démarre avec un **UID RFID fictif**. Il ne peut pas fonctionner de façon autonome sans cette configuration.
- Le code V3 utilise MQTT sur le port **1883** ; ce transport n'est pas chiffré par défaut. Ne pas présenter cette configuration de laboratoire comme adaptée à un déploiement commercial sécurisé.
- La liste Excel prévoit notamment **AHT20** et **module MOSFET**, alors que le code V3 et les notes d'essais décrivent **AHT10** et **TIP122**. Vérifier le montage réel avant toute reproduction.
- L'architecture simule un verrouillage et une ventilation : aucun dispositif physique final n'est attesté.

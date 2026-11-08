# Vérification avant publication publique

## Confidentialité

- [ ] Vérifier les fichiers et l'historique Git pour les vrais SSID privés, mots de passe, tokens ThingsBoard, secrets ou informations personnelles.
- [ ] Conserver `config_reseau.py` **en dehors** du dépôt : seul `config/config_reseau.example.py` doit être publié.
- [ ] Révoquer tout jeton/secret ancien qui aurait été exposé.
- [ ] Ne pas publier d'UID RFID autorisé réel si cela expose un accès utilisable.
- [ ] Vérifier que les captures ne montrent pas de données privées.

## Fidélité technique

- [ ] Confirmer si le capteur est AHT10 ou AHT20 et si l'étage moteur est TIP122 ou MOSFET.
- [ ] Récupérer de Thonny la **version réellement exécutée**, sauvegarder et comparer avec la V3 fournie.
- [ ] Récupérer la liste des bibliothèques nécessaires et leurs versions, si redistribution autorisée.
- [ ] Ajouter des photos du montage complet lorsque disponibles.
- [ ] Ne pas présenter le servo comme une serrure mécanique certifiée, ni le moteur comme un système de refroidissement actif.
- [ ] Vérifier que la liste de composants initiale n'est pas présentée comme une liste définitive.

## Mise en ligne

- [ ] Créer un nouveau dépôt `CargoSafe-IoT-ESP32S3` sous le compte GitHub souhaité, idéalement **privé d'abord**.
- [ ] Importer le dossier extrait sans recréer un autre README ou un autre dossier imbriqué.
- [ ] Vérifier les fichiers proposés au commit ; créer le commit, puis publier.
- [ ] Rendre public une fois la confidentialité et les autorisations de partage vérifiées.
- [ ] Ajouter les topics `esp32-s3`, `micropython`, `iot`, `mqtt`, `thingsboard`, `rfid`, `sensors`, `embedded-systems`.

# Clés de télémétrie (CargoSafe V3)

- `temperature` : °C
- `humidite` : %
- `temperature_anormale` : booléen, vrai à partir de 26 °C
- `moteur_on` : booléen
- `colis_ouvert` : booléen
- `etat_acces` : texte (VERROUILLE, AUTORISE, OUVERT, TERMINE)
- `intrusion_memorisee` : booléen
- `alerte_lumiere` : booléen
- `alarme_sonore` : booléen
- `choc_recent` : booléen
- `nombre_chocs` : entier
- `amplitude_dernier_choc_g` : g
- `aht_ok` : booléen
- `dernier_evenement_rfid` : événement texte, pas d'UID envoyé
- `luminosite_adc` : ADC pendant ouverture uniquement

**MQTT** : publication JSON sur `v1/devices/me/telemetry`. Les valeurs de `luminosite_adc` déjà affichées en « dernières télémétries » peuvent rester visibles après fermeture même lorsque le programme ne publie plus cette clé.

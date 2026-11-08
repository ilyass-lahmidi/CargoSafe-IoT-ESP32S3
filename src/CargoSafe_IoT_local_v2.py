# CargoSafe IoT V2 - Integration locale complete (sans Wi-Fi / MQTT)
# ESP32-S3 N8R8 - MicroPython
# Bibliotheques requises sur l'ESP32 : mfrc522.py, mpu6050.py, ssd1306.py

from machine import Pin, SPI, I2C, PWM, ADC
from mfrc522 import MFRC522
from mpu6050 import MPU6050
from ssd1306 import SSD1306_I2C
import time
import math

# ============================================================
# 1. PARAMETRES A ADAPTER
# ============================================================

# Copier ici l'UID exact affiche par votre test RFID (ex. "A3:42:8F:19")
UID_AUTORISE = "REMPLACE_PAR_TON_UID"

ANGLE_FERME = 0
ANGLE_OUVERT = 150
DELAI_OUVERTURE_MS = 20000

# Temperature < 26 C : normale, moteur OFF.
# Temperature >= 26 C : anormale, moteur ON.
TEMP_SEUIL_ANORMAL = 26.0

SEUIL_CHOC_G = 0.20       # Valeur utilisee dans le test MPU6050 valide
DUREE_CHOC_MS = 5000

# Ajuster grace aux valeurs lues en ouvrant le colis a la lumiere.
# Avec le montage 3V3 -> LDR -> ADC GPIO1 -> 10k -> GND,
# plus de lumiere = valeur ADC plus elevee.
SEUIL_LDR = 55000
INTERVALLE_LDR_MS = 200  # Lecture uniquement pendant l'ouverture
INTERVALLE_RFID_MS = 250  # Evite de bloquer la mesure des chocs en continu

# ============================================================
# 2. BROCHES ET PERIPHERIQUES
# ============================================================

ils = Pin(4, Pin.IN, Pin.PULL_UP)   # 0 : aimant present / ferme
moteur = Pin(5, Pin.OUT, value=0)   # TIP122 : 1 = moteur en marche
buzzer = Pin(7, Pin.OUT, value=0)   # Buzzer actif valide en test

servo = PWM(Pin(6), freq=50)

def position_servo(angle):
    impulsion_us = 1000 + (angle / 180) * 1000
    duty = int(impulsion_us * 65535 / 20000)
    servo.duty_u16(duty)

position_servo(ANGLE_FERME)

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)

appareils = i2c.scan()
print("I2C detectes :", [hex(a) for a in appareils])
for adresse, nom in ((0x38, "AHT10"), (0x3D, "OLED"), (0x68, "MPU6050")):
    if adresse not in appareils:
        raise OSError(nom + " non detecte sur I2C")

oled = SSD1306_I2C(128, 64, i2c, addr=0x3D)
mpu = MPU6050(i2c)

spi = SPI(
    1,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(12),
    mosi=Pin(11),
    miso=Pin(13),
)
rfid = MFRC522(spi, gpioRst=14, gpioCs=10)

ldr = ADC(Pin(1))
ldr.atten(ADC.ATTN_11DB)

# ============================================================
# 3. AHT10 : INITIALISATION ET LECTURE
# ============================================================

AHT10_ADDR = 0x38
if not (i2c.readfrom(AHT10_ADDR, 1)[0] & 0x08):
    i2c.writeto(AHT10_ADDR, b"\xE1\x08\x00")
    time.sleep_ms(50)

def lire_aht10():
    i2c.writeto(AHT10_ADDR, b"\xAC\x33\x00")
    time.sleep_ms(90)

    for _ in range(10):
        donnees = i2c.readfrom(AHT10_ADDR, 6)
        if not (donnees[0] & 0x80):
            break
        time.sleep_ms(10)
    else:
        raise OSError("AHT10 occupe trop longtemps")

    humidite_brute = (
        (donnees[1] << 12) | (donnees[2] << 4) | (donnees[3] >> 4)
    )
    temperature_brute = (
        ((donnees[3] & 0x0F) << 16) | (donnees[4] << 8) | donnees[5]
    )
    humidite = humidite_brute * 100 / 1048576
    temperature = temperature_brute * 200 / 1048576 - 50
    return temperature, humidite

# ============================================================
# 4. ETATS DU SYSTEME
# ============================================================

# Etats d'acces : VERROUILLE, AUTORISE, OUVERT, TERMINE
etat_acces = "VERROUILLE"
intrusion = ils.value() == 1  # Une ouverture au demarrage est suspecte

ils_stable = ils.value()
ils_brut_precedent = ils_stable
changement_ils_ms = time.ticks_ms()

uid_precedent = None
derniere_carte_vue_ms = None
debut_autorisation_ms = None

temperature = None
humidite = None
erreur_aht = False
ventilation_on = False
ldr_valeur = None  # Inutile tant que le colis est ferme

accel_precedent = None
dernier_choc_ms = None

debut = time.ticks_ms()
derniere_mesure_ms = time.ticks_add(debut, -1200)
dernier_affichage_ms = time.ticks_add(debut, -500)
dernier_log_ms = time.ticks_add(debut, -3000)
derniere_accel_ms = time.ticks_add(debut, -30)
dernier_rfid_ms = time.ticks_add(debut, -INTERVALLE_RFID_MS)
derniere_ldr_ms = time.ticks_add(debut, -INTERVALLE_LDR_MS)
dernier_buzzer_actif = False
ancienne_alerte_lumiere = False

print("=============================")
print(" CARGOSAFE IoT V2 - MODE LOCAL")
print("=============================")
print("Etat initial :", etat_acces)
if intrusion:
    print("ALERTE : colis ouvert au demarrage")
if UID_AUTORISE == "REMPLACE_PAR_TON_UID":
    print("ATTENTION : modifier UID_AUTORISE pour activer le deverrouillage")

# ============================================================
# 5. BOUCLE PRINCIPALE
# ============================================================

try:
    while True:
        maintenant = time.ticks_ms()

        # ---- A. RFID : autorisation ou acquittement intrusion ----
        # Scanner a intervalles pour laisser du temps au MPU6050.
        if time.ticks_diff(maintenant, dernier_rfid_ms) >= INTERVALLE_RFID_MS:
            dernier_rfid_ms = maintenant
            try:
                statut, _ = rfid.request(rfid.REQIDL)
                if statut == rfid.OK:
                    statut, uid = rfid.anticoll()
                    if statut == rfid.OK:
                        derniere_carte_vue_ms = maintenant
                        uid_texte = ":".join("{:02X}".format(x) for x in uid[:4])

                        if uid_texte != uid_precedent:
                            uid_precedent = uid_texte
                            print("Carte RFID :", uid_texte)

                            if uid_texte != UID_AUTORISE:
                                print("ACCES REFUSE")
                            elif ils_stable == 1:
                                print("Colis ouvert : refermer avant de scanner")
                            elif intrusion:
                                intrusion = False
                                etat_acces = "VERROUILLE"
                                position_servo(ANGLE_FERME)
                                print("ALARME INTRUSION REINITIALISEE")
                                print("Retirer puis representer la carte pour ouvrir")
                            elif etat_acces in ("VERROUILLE", "TERMINE"):
                                etat_acces = "AUTORISE"
                                debut_autorisation_ms = maintenant
                                position_servo(ANGLE_OUVERT)
                                print("ACCES AUTORISE : SERVO 150 degres")

                # Permet de lire de nouveau la MEME carte apres son retrait
                if (derniere_carte_vue_ms is not None and
                    time.ticks_diff(maintenant, derniere_carte_vue_ms) >= 500):
                    uid_precedent = None
                    derniere_carte_vue_ms = None

            except OSError as erreur:
                print("Erreur RFID :", erreur)

        # ---- B. ILS : anti-rebond sans bloquer la boucle ----
        brut_ils = ils.value()
        if brut_ils != ils_brut_precedent:
            ils_brut_precedent = brut_ils
            changement_ils_ms = maintenant
        elif (brut_ils != ils_stable and
              time.ticks_diff(maintenant, changement_ils_ms) >= 60):
            ils_stable = brut_ils

            if ils_stable == 1:  # Ouverture
                if etat_acces == "AUTORISE":
                    etat_acces = "OUVERT"
                    print("OUVERTURE AUTORISEE")
                else:
                    intrusion = True
                    etat_acces = "VERROUILLE"
                    position_servo(ANGLE_FERME)
                    print("!!! INTRUSION : OUVERTURE NON AUTORISEE !!!")
            else:  # Fermeture
                if etat_acces == "OUVERT":
                    etat_acces = "TERMINE"
                    position_servo(ANGLE_FERME)
                    print("COLIS REFERME - LIVRAISON TERMINEE")
                elif intrusion:
                    print("COLIS REFERME - INTRUSION A REINITIALISER")

        # ---- C. Expiration de l'autorisation RFID ----
        if (etat_acces == "AUTORISE" and
            debut_autorisation_ms is not None and
            time.ticks_diff(maintenant, debut_autorisation_ms)
                >= DELAI_OUVERTURE_MS):
            if ils_stable == 0:
                etat_acces = "VERROUILLE"
                position_servo(ANGLE_FERME)
                print("AUTORISATION RFID EXPIREE")

        # ---- D. MPU6050 : chocs, echantillonnage rapide ----
        if time.ticks_diff(maintenant, derniere_accel_ms) >= 30:
            derniere_accel_ms = maintenant
            try:
                mesure = mpu.accel
                if accel_precedent is not None:
                    dx = mesure["x"] - accel_precedent["x"]
                    dy = mesure["y"] - accel_precedent["y"]
                    dz = mesure["z"] - accel_precedent["z"]
                    variation = math.sqrt(dx * dx + dy * dy + dz * dz)

                    if variation >= SEUIL_CHOC_G:
                        if (dernier_choc_ms is None or
                            time.ticks_diff(maintenant, dernier_choc_ms) >= 2000):
                            dernier_choc_ms = maintenant
                            print("!!! CHOC DETECTE !!!", round(variation, 3), "g")
                accel_precedent = mesure
            except OSError as erreur:
                print("Erreur MPU6050 :", erreur)

        # ---- E. Temperature et moteur 12 V ----
        if time.ticks_diff(maintenant, derniere_mesure_ms) >= 1200:
            derniere_mesure_ms = maintenant
            try:
                temperature, humidite = lire_aht10()
                erreur_aht = False

                # Un seul seuil, sans hysteresis :
                # >= 26 C = anormal et moteur ON ; < 26 C = moteur OFF.
                ventilation_on = temperature >= TEMP_SEUIL_ANORMAL
                moteur.value(1 if ventilation_on else 0)

            except OSError as erreur:
                erreur_aht = True
                ventilation_on = False
                moteur.off()  # Arret du moteur en cas d'erreur du capteur
                print("Erreur AHT10 :", erreur)

        # ---- F. LDR et alarmes ----
        # La lumiere ne nous interesse QUE pendant l'ouverture du colis.
        if ils_stable == 1:
            if time.ticks_diff(maintenant, derniere_ldr_ms) >= INTERVALLE_LDR_MS:
                derniere_ldr_ms = maintenant
                ldr_valeur = ldr.read_u16()
        else:
            ldr_valeur = None

        # Enregistrer les chocs, mais NE PAS faire sonner le buzzer pour un choc.
        alerte_choc = (
            dernier_choc_ms is not None
            and time.ticks_diff(maintenant, dernier_choc_ms) < DUREE_CHOC_MS
        )
        temperature_anormale = (
            not erreur_aht and temperature is not None
            and temperature >= TEMP_SEUIL_ANORMAL
        )

        # Forte lumiere UNIQUEMENT si ILS indique une ouverture.
        # LDR ne distingue pas la lumiere du soleil d'une lampe.
        alerte_lumiere = (
            ils_stable == 1
            and ldr_valeur is not None
            and ldr_valeur >= SEUIL_LDR
        )

        # Une intrusion reste memorisee, mais sa sonnerie s'arrete
        # une fois le colis referme. Deux motifs sonores, uniquement :
        # 1) ouverture non autorisee ; 2) forte lumiere pendant ouverture.
        alarme_sonore = ils_stable == 1 and (intrusion or alerte_lumiere)

        # 300 ms ON, 300 ms OFF, sans bloquer la boucle principale.
        buzzer.value(1 if alarme_sonore and (maintenant // 300) % 2 == 0 else 0)

        if alerte_lumiere and not ancienne_alerte_lumiere:
            print("!!! FORTE LUMIERE PENDANT L'OUVERTURE !!!")
        ancienne_alerte_lumiere = alerte_lumiere

        if alarme_sonore != dernier_buzzer_actif:
            print("ALARME SONORE :", "ACTIVE" if alarme_sonore else "ARRETEE")
            dernier_buzzer_actif = alarme_sonore

        # ---- G. Affichage OLED toutes les 500 ms ----
        if time.ticks_diff(maintenant, dernier_affichage_ms) >= 500:
            dernier_affichage_ms = maintenant

            # Priorite OLED : alarme en cours, puis autres informations.
            if intrusion and ils_stable == 1:
                message = "INTRUSION !"
            elif alerte_lumiere:
                message = "LUMIERE FORTE !"
            elif intrusion:
                message = "INTRUSION MEMO"
            elif erreur_aht:
                message = "ERREUR AHT10"
            elif temperature_anormale:
                message = "TEMP ANORMALE"
            elif alerte_choc:
                message = "CHOC DETECTE"
            elif etat_acces == "AUTORISE":
                message = "ACCES AUTORISE"
            elif etat_acces == "OUVERT":
                message = "OUVERT AUTORISE"
            elif etat_acces == "TERMINE":
                message = "LIVRAISON FINIE"
            else:
                message = "SYSTEME NORMAL"

            if temperature is None:
                ligne_mesure = "T:--.-C H:--%"
            else:
                ligne_mesure = "T:{:.1f}C H:{:.0f}%".format(temperature, humidite)

            try:
                oled.fill(0)
                oled.text("CARGOSAFE IoT", 0, 0)
                oled.text(ligne_mesure[:16], 0, 11)
                oled.text("COLIS:" + (
                    "FERME" if ils_stable == 0 else "OUVERT"
                ), 0, 22)
                oled.text("MOTEUR:{} T:{}".format(
                    "ON" if ventilation_on else "OFF",
                    "ERR" if erreur_aht else
                    ("ANOR" if temperature_anormale else "NORM")
                )[:16], 0, 33)
                # LDR visible uniquement pendant l'ouverture :
                if ils_stable == 1 and ldr_valeur is not None:
                    texte_ldr = "LDR:{} {}".format(
                        ldr_valeur, "FORT" if alerte_lumiere else "OK"
                    )
                else:
                    texte_ldr = "LDR:-- (FERME)"
                oled.text(texte_ldr[:16], 0, 44)
                oled.text(message[:16], 0, 55)
                oled.show()
            except OSError as erreur:
                print("Erreur OLED :", erreur)

        # ---- H. Moniteur serie toutes les 3 secondes ----
        if time.ticks_diff(maintenant, dernier_log_ms) >= 3000:
            dernier_log_ms = maintenant
            print(
                "T:", None if temperature is None else round(temperature, 1),
                "H:", None if humidite is None else round(humidite, 1),
                "LDR:", "--" if ldr_valeur is None else ldr_valeur,
                "ILS:", "FERME" if ils_stable == 0 else "OUVERT",
                "Temperature:", "ERREUR" if erreur_aht else (
                    "ANORMALE" if temperature_anormale else "NORMALE"
                ),
                "Moteur:", "ON" if ventilation_on else "OFF",
                "Acces:", etat_acces,
                "Intrusion memorisee:", intrusion,
                "Lumiere forte:", alerte_lumiere,
                "Alarme sonore:", alarme_sonore,
            )

        time.sleep_ms(20)

except KeyboardInterrupt:
    print("Arret manuel du programme")
finally:
    buzzer.off()
    moteur.off()
    position_servo(ANGLE_FERME)
    time.sleep_ms(300)
    servo.deinit()
    print("Sorties mises au repos")

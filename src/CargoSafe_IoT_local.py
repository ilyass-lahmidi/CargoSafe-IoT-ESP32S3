# CargoSafe IoT - Integration locale complete (sans Wi-Fi / MQTT)
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

TEMP_MOTEUR_ON = 26.0
TEMP_MOTEUR_OFF = 24.0
TEMP_ALERTE = 28.0

SEUIL_CHOC_G = 0.20       # Valeur utilisee dans le test MPU6050 valide
DUREE_CHOC_MS = 5000

SEUIL_LDR = 55000        # A ajuster avec les mesures reelles (0 a 65535)
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
ldr_valeur = 0

accel_precedent = None
dernier_choc_ms = None

debut = time.ticks_ms()
derniere_mesure_ms = time.ticks_add(debut, -1200)
dernier_affichage_ms = time.ticks_add(debut, -500)
dernier_log_ms = time.ticks_add(debut, -3000)
derniere_accel_ms = time.ticks_add(debut, -30)
dernier_rfid_ms = time.ticks_add(debut, -INTERVALLE_RFID_MS)

print("=============================")
print(" CARGOSAFE IoT - MODE LOCAL")
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

        # ---- E. Temperature, humidite, moteur et LDR ----
        if time.ticks_diff(maintenant, derniere_mesure_ms) >= 1200:
            derniere_mesure_ms = maintenant
            ldr_valeur = ldr.read_u16()

            try:
                temperature, humidite = lire_aht10()
                erreur_aht = False

                # Hysteresis du moteur : ON >= 26, OFF <= 24
                if temperature >= TEMP_MOTEUR_ON:
                    ventilation_on = True
                elif temperature <= TEMP_MOTEUR_OFF:
                    ventilation_on = False

                moteur.value(1 if ventilation_on else 0)

            except OSError as erreur:
                erreur_aht = True
                ventilation_on = False
                moteur.off()  # Etat sur en cas d'erreur de capteur
                print("Erreur AHT10 :", erreur)

        # ---- F. Alarmes independantes ----
        alerte_temperature = (
            not erreur_aht and temperature is not None
            and temperature >= TEMP_ALERTE
        )
        alerte_choc = (
            dernier_choc_ms is not None
            and time.ticks_diff(maintenant, dernier_choc_ms) < DUREE_CHOC_MS
        )
        # Le LDR mesure la lumiere, PAS l'ouverture du colis
        alerte_lumiere = (
            ldr_valeur >= SEUIL_LDR
            and ils_stable == 0
            and etat_acces in ("VERROUILLE", "TERMINE")
        )

        alarme_active = (
            intrusion or alerte_temperature or alerte_choc
            or alerte_lumiere or erreur_aht
        )

        # Buzzer intermittent : 300 ms actif / 300 ms inactif
        buzzer.value(1 if alarme_active and (maintenant // 300) % 2 == 0 else 0)

        # ---- G. Affichage OLED toutes les 500 ms ----
        if time.ticks_diff(maintenant, dernier_affichage_ms) >= 500:
            dernier_affichage_ms = maintenant

            if intrusion:
                message = "ALARME INTRUSION"
            elif erreur_aht:
                message = "ERREUR AHT10"
            elif alerte_temperature:
                message = "TEMP ELEVEE"
            elif alerte_choc:
                message = "CHOC DETECTE"
            elif alerte_lumiere:
                message = "LUMIERE FORTE"
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
                oled.text("LDR:{} M:{}".format(
                    ldr_valeur, "ON" if ventilation_on else "OFF"
                )[:16], 0, 22)
                oled.text("ILS:" + ("FERME" if ils_stable == 0 else "OUVERT"), 0, 33)
                oled.text("RFID:" + (
                    "OUVERT" if etat_acces in ("AUTORISE", "OUVERT")
                    else "FERME"
                ), 0, 44)
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
                "LDR:", ldr_valeur,
                "ILS:", "FERME" if ils_stable == 0 else "OUVERT",
                "Moteur:", "ON" if ventilation_on else "OFF",
                "Acces:", etat_acces,
                "Intrusion:", intrusion,
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

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from prettytable import PrettyTable
import scipy

from update_config import update_config, update_coef_profil, update_param, update_bilan, update_result
from simu_AMP import simu_AMP1, simu_AMP, bilan_puissance
from error_checker import verification

def fast_simulation(FILE_NAME, N_POINT, ITERATIONS, paires, AMP2_FAISCEAU_DIAMETRE, AMP3_FAISCEAU_DIAMETRE, mode_graphique, mode_information):

    energie_AMP2_face = paires[0]/2
    energie_AMP3_face = paires[1]/2
    
    update_param(FILE_NAME, "AMP1", "FAISCEAU_IR", "DIAMETRE", 1.25)
    
    update_param(FILE_NAME, "AMP2", "FAISCEAU_IR", "DIAMETRE", AMP2_FAISCEAU_DIAMETRE)
    update_param(FILE_NAME, "AMP2", "FAISCEAU_IR", "PROFIL_SPATIAL", 7)
    update_param(FILE_NAME, "AMP2", "GEOMETRIE_AMPLIFICATEUR", "IR_POMPE", 0.93)
    update_param(FILE_NAME, "AMP2", "CRISTAL_TISA", "DIAMETRE", 30)
    update_param(FILE_NAME, "AMP2", "FILTRE_SPECTRAL", "LARGEUR_SPECTRALE", 70)
    update_param(FILE_NAME, "AMP2", "FILTRE_SPECTRAL", "LONGUEUR_ONDE_CENTRALE", 827)
    update_param(FILE_NAME, "AMP2", "FILTRE_SPECTRAL", "TRANSMISSION_SPECTRALE", 0.25)
    update_param(FILE_NAME, "AMP2", "FAISCEAU_POMPE", "ENERGIE_FACE", energie_AMP2_face)
    
    update_param(FILE_NAME, "AMP3", "FAISCEAU_IR", "DIAMETRE", AMP3_FAISCEAU_DIAMETRE)
    update_param(FILE_NAME, "AMP3", "FAISCEAU_IR", "PROFIL_SPATIAL", 7)
    update_param(FILE_NAME, "AMP3", "GEOMETRIE_AMPLIFICATEUR", "IR_POMPE", 0.95)
    update_param(FILE_NAME, "AMP3", "CRISTAL_TISA", "INDICE_REFRACTION_REFROIDISSEMENT", 1.76)
    update_param(FILE_NAME, "AMP3", "CRISTAL_TISA", "DIAMETRE", 60)
    update_param(FILE_NAME, "AMP3", "FILTRE_SPECTRAL", "OUI_NON", 2)
    update_param(FILE_NAME, "AMP3", "FILTRE_SPECTRAL", "LARGEUR_SPECTRALE", 70)
    update_param(FILE_NAME, "AMP3", "FILTRE_SPECTRAL", "LONGUEUR_ONDE_CENTRALE", 825)
    update_param(FILE_NAME, "AMP3", "FILTRE_SPECTRAL", "TRANSMISSION_SPECTRALE", 0.33)
    update_param(FILE_NAME, "AMP3", "FAISCEAU_POMPE", "ENERGIE_FACE", energie_AMP3_face)

    for i in range(2):
        data = update_config(FILE_NAME, "AMP1")
        update_coef_profil(FILE_NAME)
    
    L = simu_AMP1(FILE_NAME, N_POINT, mode_graphique, mode_information)
    
    L = simu_AMP(FILE_NAME, L[1], L[2], "2", N_POINT, mode_graphique, mode_information)
    
    L = simu_AMP(FILE_NAME, L[1], L[2], "3", N_POINT, mode_graphique, mode_information)
    
    puissance = bilan_puissance(FILE_NAME, mode_information)
    
    debug = verification(FILE_NAME, mode_information)

    return [puissance, debug]

def energie_par_ampli(ENERGIE_POMPE):
    # Initialisation de la liste pour stocker les paires
    resultats = []
    
    # Parcourir les valeurs possibles pour x1 par pas de 1000
    for x1 in range(0, ENERGIE_POMPE + 1, 1000):
        if x1 != 0:
            x2 = ENERGIE_POMPE - x1
            # Vérifier si x2 est un multiple de 1000 et respecte la contrainte x2 >= N / 2
            if x2 >= ENERGIE_POMPE / 2 and x2 % 1000 == 0:
                resultats.append((x1, x2))
        else:
            pass
    return resultats
    

def montecarlo_simu(FILE_NAME, N_POINT, ITERATIONS, STEP, ENERGIE_POMPE, AMP2_FAISCEAU_DIAMETRE_RANGE, AMP3_FAISCEAU_DIAMETRE_RANGE):
    # Exemple d'utilisation
    N = 40500  # N n'est pas un multiple de 1000
    paires_AMP2_AMP3 = energie_par_ampli(ENERGIE_POMPE)
    liste_diametre_amp2 = np.arange(AMP2_FAISCEAU_DIAMETRE_RANGE[0], AMP2_FAISCEAU_DIAMETRE_RANGE[1] + STEP, STEP).tolist()
    liste_diametre_amp3 = np.arange(AMP3_FAISCEAU_DIAMETRE_RANGE[0], AMP3_FAISCEAU_DIAMETRE_RANGE[1] + STEP, STEP).tolist()
    nbr_simu = len(paires_AMP2_AMP3)*len(liste_diametre_amp2)*len(liste_diametre_amp3)

    temps_par_iteration = 60 / 180
    temps_total = nbr_simu * temps_par_iteration
    minutes = int(temps_total // 60)
    secondes = int(temps_total % 60)

    # Afficher le résultat
    print(f"Pour {nbr_simu} itérations, le temps estimé est de {minutes} minute(s) et {secondes} seconde(s).")
    cpt = 0
    best_p = 0

    for paires_energie in paires_AMP2_AMP3:
        for diam_AMP2 in liste_diametre_amp2:
            for diam_AMP3 in liste_diametre_amp3:
                [p, debug] = fast_simulation(FILE_NAME, N_POINT, ITERATIONS, paires_energie, diam_AMP2, diam_AMP3, False, False)
                cpt += 1
                if p > best_p and not debug:
                    best_p = p
                    best_paires = paires_energie
                    best_diamAMP2 = diam_AMP2
                    best_diamAMP3 = diam_AMP3
                    print(p, cpt, diam_AMP2, diam_AMP3, paires_energie)
                if cpt%10 == 0:
                    print(str(cpt) + "/" + str(nbr_simu))

    fast_simulation(FILE_NAME, N_POINT, ITERATIONS, best_paires, best_diamAMP2, best_diamAMP3, True, True)
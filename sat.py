import numpy as np
import pandas as pd
import scipy.constants as cst

def create_saturation(n_point, TISA_frequence_res, TISA_temps_coherence, TISA_Seff, abscisse_omega):
    # Créer un tableau pour stocker les valeurs de saturation
    sat = np.zeros((n_point + 1, 1))

    # Boucle sur le nombre de valeurs pour remplir le profil de saturation
    for i in range(n_point + 1):
        # Calcul de la saturation en fonction de Omega
        sat[i, 0] = (cst.h * abscisse_omega[i] * 
               (1 + (TISA_temps_coherence * 1e-15 * (abscisse_omega[i] - TISA_frequence_res)) ** 2) / 
               (2 * np.pi * TISA_Seff))

    # Création d'un DataFrame pour simuler le transfert vers Excel
    df_sat = pd.DataFrame(sat, columns=['Saturation'])
    return df_sat

import numpy as np
import pandas as pd
import scipy.constants as cst

def create_spectral_filter(n_point, DAZZLER_on, DAZZLER_profil, DAZZLER_largeur, DAZZLER_longueur_onde, DAZZLER_transmission, abscisse_lambda):
    # Créer un tableau pour stocker les valeurs de saturation
    spectral_filter = np.zeros((n_point + 1, 1))

    for i in range(n_point + 1):
        if DAZZLER_on == 1:
            spectral_filter[i, 0] = 1 - (1 - DAZZLER_transmission) * np.exp(-np.log(2) * ((2 / DAZZLER_largeur / 0.000000001) * (abscisse_lambda[i] * 0.000000001 - DAZZLER_longueur_onde * 0.000000001)) ** (2 * DAZZLER_profil))
        else:
            spectral_filter[i, 0] = 1

    # Création d'un DataFrame pour simuler le transfert vers Excel
    df_spectral_filter = pd.DataFrame(spectral_filter, columns=['Filtre spectral'])
    return df_spectral_filter

def racine_filtre(n_point, FILTRE):
    sqrt_spectral_filter = np.zeros((n_point + 1, 1))
    for i in range(n_point + 1):
            sqrt_spectral_filter[i, 0] = np.sqrt(FILTRE[i])

    # Création d'un DataFrame pour simuler le transfert vers Excel
    df_sqrt_spectral_filter = pd.DataFrame(sqrt_spectral_filter, columns=['Racine Filtre spectral'])
    return df_sqrt_spectral_filter
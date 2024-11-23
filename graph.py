import numpy as np
import pandas as pd
from misc import supergaussienne_spatiale, equivalence_supergauss

def create_abscisses(n_point, duree_etiree, frequence_ir, chirp_ir, diametre_pompe):
    c = 299792458
    # Dimensionner le tableau des valeurs
    abscisse = np.zeros((n_point + 1, 4))  # 1 to 200 for n_point + 1, 1 to 4 for columns

    # Déterminer les pas temporel et spatial
    pas_t = (4 * duree_etiree) / n_point
    pas_x = (2 * diametre_pompe) / n_point

    # Boucle sur le nombre de valeurs
    for i in range(n_point + 1):
        # Temps
        abscisse[i, 0] = -2 * duree_etiree + i * pas_t
        # Omega
        abscisse[i, 1] = frequence_ir + (2 * chirp_ir * abscisse[i, 0] * 1e-12)
        # Lambda
        abscisse[i, 2] = (1e9 * 2 * np.pi * c) / abscisse[i, 1]  # Convertir c en nm/s
        # x
        abscisse[i, 3] = -diametre_pompe + i * pas_x

    # Créer un DataFrame pandas pour les données
    df_abscisse = pd.DataFrame(abscisse, columns=['Temps', 'Omega', 'Lambda', 'x'])
    return df_abscisse

def update_abscisses(n_point, abscisse_df, diametre_pompe):
    abscisse = np.zeros((n_point + 1, 4))
    pas_x = (2 * diametre_pompe) / n_point
    abscisse[:,0] = abscisse_df["Temps"]
    abscisse[:,1] = abscisse_df["Omega"]
    abscisse[:,2] = abscisse_df["Lambda"]
    for i in range(n_point+1):
        abscisse[i, 3] = -diametre_pompe + i * pas_x
    df_abscisse = pd.DataFrame(abscisse, columns=['Temps', 'Omega', 'Lambda', 'x'])
    return df_abscisse


def spatial_profile(Nbr_Point, abscisse, Diam_IR, Profil_IR, Diam_FP, Profil_FP, Rayon_Equi_IR, Rayon_Equi_FP):
    # Dimensionner le tableau des ordonnées
    ordinates = np.zeros((Nbr_Point + 1, 4))
    
    # Boucle sur le nombre de valeurs
    for i in range(Nbr_Point + 1):
        # Profil IR
        ordinates[i, 0] = supergaussienne_spatiale(abscisse.iloc[i, 3], Diam_IR, Profil_IR)
        # Profil FP
        ordinates[i, 1] = supergaussienne_spatiale(abscisse.iloc[i, 3], Diam_FP, Profil_FP)
        # Profil Équivalent IR
        ordinates[i, 2] = equivalence_supergauss(abscisse.iloc[i, 3], Rayon_Equi_IR)
        # Profil Équivalent FP
        ordinates[i, 3] = equivalence_supergauss(abscisse.iloc[i, 3], Rayon_Equi_FP)
    
    # Création d'un DataFrame pour simuler le transfert des valeurs dans Excel
    df = pd.DataFrame(ordinates, columns=['Profil IR', 'Profil FP', 'Équivalent IR', 'Équivalent FP'])
    return df

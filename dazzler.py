import numpy as np
import pandas as pd
import scipy.constants as cst
from misc import Barycentre, T_Seuil
from update_config import update_result
import json

def entree_avant_dazzler(N_POINT, A0_t, B0_t, A0_w, B0_w, abscisse_df, PROFIL_TEMPOREL, FREQUENCE_IR):
    bdd = np.zeros((N_POINT + 1, 4))
    for i in range(N_POINT + 1):
        bdd[i, 0] = A0_t * np.exp(-B0_t * (abscisse_df['Temps'][i] * 0.000000000001) ** (2 * PROFIL_TEMPOREL))
        bdd[i, 1] = A0_w * np.exp(-B0_w * (abscisse_df['Omega'][i] - FREQUENCE_IR) ** (2 * PROFIL_TEMPOREL))

    for i in range(N_POINT + 1):
        bdd[i, 2] = bdd[i, 1]/np.max(bdd[:,1])

    bdd[0,3] = 0.5 * (bdd[1, 0] + bdd[0, 0]) * ( abscisse_df['Temps'][1] - abscisse_df['Temps'][0]) * 0.000000000001
    for i in range(1, N_POINT): 
        bdd[i, 3] = bdd[i-1, 3] + 0.5 * (bdd[i+1, 0] + bdd[i, 0]) * ( abscisse_df['Temps'][i+1] - abscisse_df['Temps'][i]) * 0.000000000001
    bdd[N_POINT, 3] = bdd[N_POINT-1, 3]
    df_bdd = pd.DataFrame(bdd, columns=['A_DAZZLER_T', 'A_DAZZLER_W', 'A_DAZZLER_W_NORMA', 'Integrale'])
    return df_bdd

def update_entree_avant_dazzler(N_POINT, abscisse_df, passage_df, FLUENCE):
    bdd = np.zeros((N_POINT + 1, 4))
    for i in range(N_POINT + 1):
        bdd[i, 0] = FLUENCE*passage_df["Profil_TEMP"][i]/passage_df["Integrale"][N_POINT]
        bdd[i, 1] = FLUENCE*passage_df["Profil_SPEC"][i]/passage_df["Integrale"][N_POINT]

    for i in range(N_POINT + 1):
        bdd[i, 2] = bdd[i, 1]/np.max(bdd[:,1])

    bdd[0,3] = 0.5 * (bdd[1, 0] + bdd[0, 0]) * ( abscisse_df['Temps'][1] - abscisse_df['Temps'][0]) * 0.000000000001
    for i in range(1, N_POINT): 
        bdd[i, 3] = bdd[i-1, 3] + 0.5 * (bdd[i+1, 0] + bdd[i, 0]) * ( abscisse_df['Temps'][i+1] - abscisse_df['Temps'][i]) * 0.000000000001
    bdd[N_POINT, 3] = bdd[N_POINT-1, 3]

    df_bdd = pd.DataFrame(bdd, columns=['A_DAZZLER_T', 'A_DAZZLER_W', 'A_DAZZLER_W_NORMA', 'Integrale'])
    return df_bdd


def entree_apres_dazzler(FILE_NAME, N_POINT, avant_dazzler_df, abscisse_df, filtre_df, FILTRE_ON_OFF, N_AMP):
    if FILTRE_ON_OFF == 1:
        is_dazzler = True
    else:
        is_dazzler = False

    bdd = np.zeros((N_POINT + 1, 4))

    for i in range(N_POINT + 1):
        if is_dazzler:
            bdd[i,0] = avant_dazzler_df["A_DAZZLER_T"][i]*filtre_df["Filtre spectral"][i]
            bdd[i,1] = avant_dazzler_df["A_DAZZLER_W"][i]*filtre_df["Filtre spectral"][i]
        else:
            bdd[i,0] = avant_dazzler_df["A_DAZZLER_T"][i]
            bdd[i,1] = avant_dazzler_df["A_DAZZLER_W"][i]
    for i in range(N_POINT + 1):
        bdd[i,2] = bdd[i, 1]/np.max(bdd[:,1])

    bdd[0,3] = 0.5 * (bdd[1, 0] + bdd[0, 0]) * ( abscisse_df['Temps'][1] - abscisse_df['Temps'][0]) * 0.000000000001
    for i in range(1, N_POINT): 
        bdd[i, 3] = bdd[i-1, 3] + 0.5 * (bdd[i+1, 0] + bdd[i, 0]) * ( abscisse_df['Temps'][i+1] - abscisse_df['Temps'][i]) * 0.000000000001
    bdd[N_POINT, 3] = bdd[N_POINT-1, 3]

    df_bdd = pd.DataFrame(bdd, columns=['P_DAZZLER_T', 'P_DAZZLER_W', 'P_DAZZLER_W_NORMA', 'Integrale'])

    longueur_onde = abscisse_df["Lambda"]
    spectre = df_bdd["P_DAZZLER_W_NORMA"]
    temps = abscisse_df["Temps"]
    profil = df_bdd["P_DAZZLER_T"]

    seuil1 = 0.5
    seuil2 = np.max(profil)/2

    with open(FILE_NAME, "r") as file:
        data = json.load(file)
    
    #calcule les largeurs a mihauteur
    TEXTE_AMP = "AMP" + N_AMP
    delta_mi_hauteur = T_Seuil(seuil1, longueur_onde, spectre, "montant") - T_Seuil(seuil1, longueur_onde, spectre, "descendant")
    duree = T_Seuil(seuil2, temps, profil, "descendant") - T_Seuil(seuil2, temps, profil, "montant")
    lc_barycentre = Barycentre(longueur_onde, spectre, "X")
    fluence = bdd[N_POINT, 3]
    energie = fluence*data[TEXTE_AMP]["FAISCEAU_IR"]["SURFACE_EQUIVALENTE"]*1000
    extraction = (energie-energie)/data[TEXTE_AMP]["FAISCEAU_POMPE"]["ENERGIE_LASER_TOTALE"]
    eclairement = fluence/duree/0.000001
    saturation = fluence/data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["FLUENCE_SATURATION_LR"]
    dommage = fluence/data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["SEUIL_DOMMAGE"]
    gain = 0
    lc_max = longueur_onde[np.where(bdd[:,2] == 1)[0][0]] 

    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "LC_BARYCENTRE", lc_barycentre)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "DELTAL_MI_HAUTEUR", delta_mi_hauteur)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "DUREE", duree)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "EXTRACTION", extraction)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "FLUENCE", fluence)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "ENERGIE", energie)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "ECLAIREMENT", eclairement)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "SATURATION", saturation)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "DOMMAGE", dommage)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "GAIN_REEL", gain)
    update_result(FILE_NAME, TEXTE_AMP, "PASSAGE0", "LC_MAX", lc_max)
    
    return df_bdd


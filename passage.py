import numpy as np
import pandas as pd
import scipy.constants as cst
from misc import Barycentre, T_Seuil
from update_config import update_result
import json

def compute_pass(FILE_NAME, N_POINT, pertes, abscisse_df, profil_temp, profil_spec, integral, gain_omega, gain_temps, saturation_df, passage, N_AMP):
    bdd = np.zeros((N_POINT + 1, 6))
    
    for i in range(N_POINT + 1):
        bdd[i,0] = profil_temp[i]*gain_temps[i]*(1-pertes)
        bdd[i,1] = profil_spec[i]*gain_temps[i]*(1-pertes)

    for i in range(N_POINT + 1):
        bdd[i,2] = bdd[i, 1]/np.max(bdd[:,1])

    bdd[0,3] = 0.5 * (bdd[1, 0] + bdd[0, 0]) * ( abscisse_df['Temps'][1] - abscisse_df['Temps'][0]) * 0.000000000001
    for i in range(1, N_POINT): 
        bdd[i, 3] = bdd[i-1, 3] + 0.5 * (bdd[i+1, 0] + bdd[i, 0]) * ( abscisse_df['Temps'][i+1] - abscisse_df['Temps'][i]) * 0.000000000001
    bdd[N_POINT, 3] = bdd[N_POINT-1, 3]

    for i in range(N_POINT + 1):
        bdd[i,4] = np.exp(np.log(gain_omega[i]) - (bdd[N_POINT, 3] - integral[N_POINT]) / saturation_df["Saturation"][i])

    for i in range(N_POINT + 1):
        bdd[i,5] = 1 / (1 - (1 - (1 / bdd[i, 4])) * np.exp(-bdd[i, 3] / saturation_df["Saturation"][i]))

    df_bdd = pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])

    longueur_onde = abscisse_df["Lambda"]
    spectre = df_bdd["Profil_SPEC_NORM"]
    temps = abscisse_df["Temps"]
    profil = df_bdd["Profil_TEMP"]

    seuil1 = 0.5
    seuil2 = np.max(profil)/2

    with open(FILE_NAME, "r") as file:
        data = json.load(file)

    current_pass = "PASSAGE" + passage
    former_pass = "PASSAGE" + str(int(passage)-1)

    TEXTE_AMP = "AMP" + N_AMP

    delta_mi_hauteur = T_Seuil(seuil1, longueur_onde, spectre, "montant") - T_Seuil(seuil1, longueur_onde, spectre, "descendant")
    duree = T_Seuil(seuil2, temps, profil, "descendant") - T_Seuil(seuil2, temps, profil, "montant")
    lc_barycentre = Barycentre(longueur_onde, spectre, "X")
    fluence = bdd[N_POINT, 3]
    energie = fluence*data[TEXTE_AMP]["FAISCEAU_IR"]["SURFACE_EQUIVALENTE"]*1000
    energie_first = data[TEXTE_AMP]["RESULTATS"]["PASSAGE0"]["ENERGIE"] #MODIFIER L'AMP ! N = N-1
    extraction = (energie-energie_first)/data[TEXTE_AMP]["FAISCEAU_POMPE"]["ENERGIE_LASER_TOTALE"]
    gain = energie/energie_first
    eclairement = fluence/duree/0.000001
    saturation = fluence/data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["FLUENCE_SATURATION_LR"]
    dommage = fluence/data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["SEUIL_DOMMAGE"]
    lc_max = longueur_onde[np.where(bdd[:,2] == 1)[0][0]] 

    update_result(FILE_NAME, TEXTE_AMP, current_pass, "PASSAGE", int(passage))
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "LC_BARYCENTRE", lc_barycentre)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "DELTAL_MI_HAUTEUR", delta_mi_hauteur)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "DUREE", duree)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "EXTRACTION", extraction)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "FLUENCE", fluence)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "ENERGIE", energie)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "ECLAIREMENT", eclairement)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "SATURATION", saturation)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "DOMMAGE", dommage)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "GAIN_REEL", gain)
    update_result(FILE_NAME, TEXTE_AMP, current_pass, "LC_MAX", lc_max)
    
    return df_bdd

def update_next_amp(FILE_NAME, NEXT_AMP):

    next_a = "AMP" + str(NEXT_AMP)
    former_a = "AMP" + str(int(NEXT_AMP) - 1)
    
    with open(FILE_NAME, "r") as file:
        data = json.load(file)

    passage = "PASSAGE" + str(data[former_a]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"]) 
    
    data[next_a]["FAISCEAU_IR"]["ENERGIE"] = data[former_a]["RESULTATS"][passage]["ENERGIE"]
    data[next_a]["RESULTATS"]["PASSAGE0"]["ENERGIE"] = data[former_a]["RESULTATS"][passage]["ENERGIE"]
    data[next_a]["FAISCEAU_IR"]["LARGEUR_SPECTRALE"] = data[former_a]["RESULTATS"][passage]["DELTAL_MI_HAUTEUR"]
    data[next_a]["FAISCEAU_IR"]["LONGUEUR_ONDE_CENTRALE_LC"] = data[former_a]["RESULTATS"][passage]["LC_MAX"]
    data[next_a]["FAISCEAU_IR"]["DUREE_ETIREE"] = data[former_a]["RESULTATS"][passage]["DUREE"]

    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

    
    
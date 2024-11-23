import numpy as np
import pandas as pd
import json
from prettytable import PrettyTable
import matplotlib.pyplot as plt

def supergaussienne_spatiale(dimension, largeur_mihauteur, exposant):
    return np.exp(-np.log(2) * (2 * dimension / largeur_mihauteur) ** (2 * exposant))

def equivalence_supergauss(dimension, rayon):
    if abs(dimension) < rayon:
        return 1.0
    else:
        return 0.0

def Barycentre(t, S, mode):
    # Détermine le pas d'échantillonnage
    pas = t[1] - t[0]

    # Initialisation des sommes
    SomNumX, SomNumY, SomDeno = 0, 0, 0

    # Boucle sur les points
    for i in range(len(t)):
        SomDeno += S[i] * t[i] * pas
        SomNumX += S[i] * pas
        SomNumY += t[i] * pas

    # Calcul selon le mode sélectionné
    if mode == "X":
        return SomDeno / SomNumX
    elif mode == "Y":
        return SomDeno / SomNumY
    else:
        raise ValueError("Mode invalide, utilisez 'X' ou 'Y'")

def T_Seuil(seuil, temps, puissance, mode):
    Nbr_i = len(puissance)  # Nombre de points
    Max_local = 0
    i_Max = 0

    # Recherche de l'indice du maximum local
    for i in range(Nbr_i):
        if puissance[i] > Max_local:
            Max_local = puissance[i]
            i_Max = i

    # Initialisation des points pour interpolation linéaire
    x11, y11, x12, y12 = None, None, None, None
    x21, y21, x22, y22 = None, None, None, None

    # Recherche des points avant et après l'indice du maximum
    for i in range(Nbr_i):
        if i < i_Max:  # Partie croissante
            if puissance[i] < seuil:
                x11, y11 = temps[i], puissance[i]
                x12, y12 = temps[i + 1], puissance[i + 1]
        elif i > i_Max:  # Partie décroissante
            if puissance[i] > seuil:
                x21, y21 = temps[i], puissance[i]
                x22, y22 = temps[i + 1], puissance[i + 1]

    # Calcul des coefficients pour l'interpolation linéaire
    if mode == "montant" and x11 is not None and x12 is not None:
        a = (y12 - y11) / (x12 - x11)
        B = (x12 * y11 - x11 * y12) / (x12 - x11)
    elif mode == "descendant" and x21 is not None and x22 is not None:
        a = (y22 - y21) / (x22 - x21)
        B = (x22 * y21 - x21 * y22) / (x22 - x21)
    else:
        raise ValueError("Les points pour l'interpolation linéaire sont incomplets")

    return (seuil - B) / a

def create_table(FILE_NAME, TEXTE_AMP):
    table = PrettyTable()
    table.add_column("Passage",["GAIN REEL","EXTRACTION (%)","ENERGIE (mJ)","BARYCENTRE LC (nm)","MAX LC (nm)","DeltaL MI HAUTEUR (nm)","FLUENCE (J/cm²)", "ECLAIREMENT (MW/cm²)", "SATURATION (%)", "DOMMAGE (%)", "DUREE (ps)"])
    for i in range(0,7):
        # Chargement du fichier JSON
        with open(FILE_NAME, "r") as file:
            data = json.load(file)
            
        LISTE_VALEURS = []
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["GAIN_REEL"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["EXTRACTION"]*100)
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["ENERGIE"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["LC_BARYCENTRE"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["LC_MAX"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["DELTAL_MI_HAUTEUR"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["FLUENCE"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["ECLAIREMENT"])
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["SATURATION"]*100)
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["DOMMAGE"]*100)
        LISTE_VALEURS.append(data[TEXTE_AMP]["RESULTATS"]["PASSAGE" + str(i)]["DUREE"])

        for j in range(0,len(LISTE_VALEURS)):
            LISTE_VALEURS[j] = round(LISTE_VALEURS[j], 2)
        
        table.add_column(str(i),LISTE_VALEURS)
        
    print(table)

def affichage_spectre(abscisse_df, apres_dazzler_df, passage_df, filtre_df, is_filter):
    x = abscisse_df["Lambda"]
    y1 = apres_dazzler_df["A_DAZZLER_W_NORMA"]
    y2 = passage_df["Profil_SPEC_NORM"]
    if is_filter == 1:
        y3 = filtre_df["Filtre spectral"]
        plt.plot(x, y3, "--", label="Filtre spectral", color="blue")
    plt.plot(x, y1, label="Entrée", color="green")
    plt.plot(x, y2, label="Sortie", color="orange")
    plt.ylabel("Intensité spectrale u.a")
    plt.xlabel("Longueur d'onde (nm)")
    plt.grid()
    plt.legend()

def affichage_gain(FILE_NAME, TEXT_AMP):

    with open(FILE_NAME, "r") as file:
        data = json.load(file)
        
    gain = []
    for i in range(7):
        gain.append(data[TEXT_AMP]["RESULTATS"]["PASSAGE" + str(i)]["GAIN_REEL"])
    x = [0,1,2,3,4,5,6]
    plt.figure()
    plt.axhline(y=gain[6], color="green", linestyle="--")
    plt.scatter(x, gain, color="blue")
    plt.xlabel("Passage")
    plt.ylabel("Gain")
    plt.grid()
    plt.show()
    
    
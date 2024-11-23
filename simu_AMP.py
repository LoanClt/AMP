import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from graph import create_abscisses, spatial_profile, update_abscisses
from sat import create_saturation
from filtres import create_spectral_filter, racine_filtre
from update_config import update_config, update_coef_profil, update_param
from dazzler import entree_avant_dazzler, entree_apres_dazzler, update_entree_avant_dazzler
from gain import gain_init
from passage import compute_pass, update_next_amp
from misc import create_table, affichage_spectre, affichage_gain
import json
from prettytable import PrettyTable

def simu_AMP1(FILE_NAME, N_POINT, mode_graphique, mode_information):
    N_AMP = "1"
    TEXTE_AMP = "AMP" + N_AMP

    with open(FILE_NAME, "r") as file:
        data = json.load(file)
    
    abscisse_df = create_abscisses(N_POINT, data["AMP1"]["FAISCEAU_IR"]["DUREE_ETIREE"], data["AMP1"]["FAISCEAU_IR"]["FREQUENCE_CENTRALE"], data["AMP1"]["FAISCEAU_IR"]["CHIRP"], data["AMP1"]["FAISCEAU_POMPE"]["DIAMETRE"])
    #pd.DataFrame(abscisse, columns=['Temps', 'Omega', 'Lambda', 'x'])
    saturation_df = create_saturation(N_POINT, data["AMP1"]["CRISTAL_TISA_POMPE"]["FREQUENCE_RESONNANCE"], data["AMP1"]["CRISTAL_TISA_POMPE"]["TEMPS_COHERENCE"], data["AMP1"]["CRISTAL_TISA_POMPE"]["SECTION_EFFICACE_EMISSION_LR"], abscisse_df['Omega'])
    #df_sat = pd.DataFrame(sat, columns=['Saturation'])
    profil_df = spatial_profile(N_POINT, abscisse_df, data["AMP1"]["FAISCEAU_IR"]["DIAMETRE"], data["AMP1"]["FAISCEAU_IR"]["PROFIL_SPATIAL"], data["AMP1"]["FAISCEAU_POMPE"]["DIAMETRE"], data["AMP1"]["FAISCEAU_POMPE"]["PROFIL_SPATIAL"], data["AMP1"]["FAISCEAU_IR"]["RAYON_EQUIVALENT"], data["AMP1"]["FAISCEAU_POMPE"]["RAYON_EQUIVALENT"])
    #pd.DataFrame(ordinates, columns=['Profil IR', 'Profil FP', 'Équivalent IR', 'Équivalent FP'])
    filtre_df = create_spectral_filter(N_POINT, data["AMP1"]["FILTRE_SPECTRAL"]["OUI_NON"], data["AMP1"]["FILTRE_SPECTRAL"]["PROFIL_SPECTRAL"], data["AMP1"]["FILTRE_SPECTRAL"]["LARGEUR_SPECTRALE"], data["AMP1"]["FILTRE_SPECTRAL"]["LONGUEUR_ONDE_CENTRALE"], data["AMP1"]["FILTRE_SPECTRAL"]["TRANSMISSION_SPECTRALE"], abscisse_df['Lambda'])
    #pd.DataFrame(spectral_filter, columns=['Filtre spectral']
    sqrt_filtre_df = racine_filtre(N_POINT, filtre_df['Filtre spectral'])
    avant_dazzler_df = entree_avant_dazzler(N_POINT, data["COEFS_PROFIL"]["A0_T"], data["COEFS_PROFIL"]["B0_T"], data["COEFS_PROFIL"]["A0_w"], data["COEFS_PROFIL"]["B0_w"], abscisse_df, data["AMP1"]["FAISCEAU_IR"]["PROFIL_TEMPORAL"], data["AMP1"]["FAISCEAU_IR"]["FREQUENCE_CENTRALE"])
    #pd.DataFrame(bdd, columns=['A_DAZZLER_T', 'A_DAZZLER_W', 'A_DAZZLER_W_NORMA', 'Integrale'])
    apres_dazzler_df = entree_apres_dazzler(FILE_NAME, N_POINT, avant_dazzler_df, abscisse_df, filtre_df, data["AMP1"]["FILTRE_SPECTRAL"]["OUI_NON"], N_AMP)
    #pd.DataFrame(bdd, columns=['P_DAZZLER_T', 'P_DAZZLER_W', 'P_DAZZLER_W_NORMA', 'Integrale'])
    gain_init_df = gain_init(N_POINT, data["AMP1"]["FAISCEAU_POMPE"]["ENERGIE_LASER_TOTALE"], data["AMP1"]["CRISTAL_TISA"]["ABSORPTION_A_532NM"], data["AMP1"]["CRISTAL_TISA_POMPE"]["EFFICACITE_QUANTIQUE"], data["AMP1"]["FAISCEAU_POMPE"]["LONGUEUR_ONDE_LP"], data["AMP1"]["FAISCEAU_POMPE"]["SURFACE_EQUIVALENTE"], saturation_df, apres_dazzler_df, abscisse_df)
    #pd.DataFrame(bdd, columns=['Gain_Omega', 'Gain_temps'])
    
    passage1_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, apres_dazzler_df["P_DAZZLER_T"], apres_dazzler_df["P_DAZZLER_W"], apres_dazzler_df["Integrale"], gain_init_df["Gain_Omega"], gain_init_df["Gain_temps"], saturation_df, "1", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage2_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage1_df["Profil_TEMP"], passage1_df["Profil_SPEC"], passage1_df["Integrale"], passage1_df["Gain_Omega"], passage1_df["Gain_temps"], saturation_df, "2", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage3_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage2_df["Profil_TEMP"], passage2_df["Profil_SPEC"], passage2_df["Integrale"], passage2_df["Gain_Omega"], passage2_df["Gain_temps"], saturation_df, "3", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage4_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage3_df["Profil_TEMP"], passage3_df["Profil_SPEC"], passage3_df["Integrale"], passage3_df["Gain_Omega"], passage3_df["Gain_temps"], saturation_df, "4", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage5_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage4_df["Profil_TEMP"], passage4_df["Profil_SPEC"], passage4_df["Integrale"], passage4_df["Gain_Omega"], passage4_df["Gain_temps"], saturation_df, "5", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage6_df = compute_pass(FILE_NAME, N_POINT, data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage5_df["Profil_TEMP"], passage5_df["Profil_SPEC"], passage5_df["Integrale"], passage5_df["Gain_Omega"], passage5_df["Gain_temps"], saturation_df, "6", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    liste_passages = [passage1_df, passage2_df, passage3_df, passage4_df, passage5_df, passage6_df]

    if mode_information:
        create_table(FILE_NAME, TEXTE_AMP)

    for i in range(2):
        update_next_amp(FILE_NAME, 2)
        nbr_passage = data["AMP1"]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"] 
        passage = liste_passages[nbr_passage - 1]
        data = update_config(FILE_NAME, "AMP2")

    if mode_graphique:
        affichage_spectre(abscisse_df, avant_dazzler_df, passage, filtre_df, data["AMP1"]["FILTRE_SPECTRAL"]["OUI_NON"])
        affichage_gain(FILE_NAME, TEXTE_AMP)

    return [data, passage, abscisse_df]

def simu_AMP(FILE_NAME, passage, abscisse_df, N_AMP, N_POINT, mode_graphique, mode_information):
    TEXTE_AMP = "AMP" + N_AMP

    with open(FILE_NAME, "r") as file:
        data = json.load(file)
            
    abscisse_df = update_abscisses(N_POINT, abscisse_df, data[TEXTE_AMP]["FAISCEAU_POMPE"]["DIAMETRE"])
    #pd.DataFrame(abscisse, columns=['Temps', 'Omega', 'Lambda', 'x'])
    profil_df = spatial_profile(N_POINT, abscisse_df, data[TEXTE_AMP]["FAISCEAU_IR"]["DIAMETRE"], data[TEXTE_AMP]["FAISCEAU_IR"]["PROFIL_SPATIAL"], data[TEXTE_AMP]["FAISCEAU_POMPE"]["DIAMETRE"], data[TEXTE_AMP]["FAISCEAU_POMPE"]["PROFIL_SPATIAL"], data[TEXTE_AMP]["FAISCEAU_IR"]["RAYON_EQUIVALENT"], data[TEXTE_AMP]["FAISCEAU_POMPE"]["RAYON_EQUIVALENT"])
    #pd.DataFrame(ordinates, columns=['Profil IR', 'Profil FP', 'Équivalent IR', 'Équivalent FP'])
    saturation_df = create_saturation(N_POINT, data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["FREQUENCE_RESONNANCE"], data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["TEMPS_COHERENCE"], data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["SECTION_EFFICACE_EMISSION_LR"], abscisse_df['Omega'])
    #df_sat = pd.DataFrame(sat, columns=['Saturation'])
    filtre_df = create_spectral_filter(N_POINT, data[TEXTE_AMP]["FILTRE_SPECTRAL"]["OUI_NON"], data[TEXTE_AMP]["FILTRE_SPECTRAL"]["PROFIL_SPECTRAL"], data[TEXTE_AMP]["FILTRE_SPECTRAL"]["LARGEUR_SPECTRALE"], data[TEXTE_AMP]["FILTRE_SPECTRAL"]["LONGUEUR_ONDE_CENTRALE"], data[TEXTE_AMP]["FILTRE_SPECTRAL"]["TRANSMISSION_SPECTRALE"], abscisse_df['Lambda'])
    #pd.DataFrame(spectral_filter, columns=['Filtre spectral']
    avant_dazzler_df = update_entree_avant_dazzler(N_POINT, abscisse_df, passage, data[TEXTE_AMP]["FAISCEAU_IR"]["FLUENCE_IR"])
    #pd.DataFrame(bdd, columns=['A_DAZZLER_T', 'A_DAZZLER_W', 'A_DAZZLER_W_NORMA', 'Integrale'])
    apres_dazzler_df = entree_apres_dazzler(FILE_NAME, N_POINT, avant_dazzler_df, abscisse_df, filtre_df, data[TEXTE_AMP]["FILTRE_SPECTRAL"]["OUI_NON"], N_AMP)
    #pd.DataFrame(bdd, columns=['P_DAZZLER_T', 'P_DAZZLER_W', 'P_DAZZLER_W_NORMA', 'Integrale'])
    gain_init_df = gain_init(N_POINT, data[TEXTE_AMP]["FAISCEAU_POMPE"]["ENERGIE_LASER_TOTALE"], data[TEXTE_AMP]["CRISTAL_TISA"]["ABSORPTION_A_532NM"], data[TEXTE_AMP]["CRISTAL_TISA_POMPE"]["EFFICACITE_QUANTIQUE"], data[TEXTE_AMP]["FAISCEAU_POMPE"]["LONGUEUR_ONDE_LP"], data[TEXTE_AMP]["FAISCEAU_POMPE"]["SURFACE_EQUIVALENTE"], saturation_df, apres_dazzler_df, abscisse_df)
    #pd.DataFrame(bdd, columns=['Gain_Omega', 'Gain_temps'])

    passage1_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, apres_dazzler_df["P_DAZZLER_T"], apres_dazzler_df["P_DAZZLER_W"], apres_dazzler_df["Integrale"], gain_init_df["Gain_Omega"], gain_init_df["Gain_temps"], saturation_df, "1", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage2_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage1_df["Profil_TEMP"], passage1_df["Profil_SPEC"], passage1_df["Integrale"], passage1_df["Gain_Omega"], passage1_df["Gain_temps"], saturation_df, "2", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage3_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage2_df["Profil_TEMP"], passage2_df["Profil_SPEC"], passage2_df["Integrale"], passage2_df["Gain_Omega"], passage2_df["Gain_temps"], saturation_df, "3", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage4_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage3_df["Profil_TEMP"], passage3_df["Profil_SPEC"], passage3_df["Integrale"], passage3_df["Gain_Omega"], passage3_df["Gain_temps"], saturation_df, "4", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage5_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage4_df["Profil_TEMP"], passage4_df["Profil_SPEC"], passage4_df["Integrale"], passage4_df["Gain_Omega"], passage4_df["Gain_temps"], saturation_df, "5", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    passage6_df = compute_pass(FILE_NAME, N_POINT, data[TEXTE_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PERTES_APRES_PASSAGE"], abscisse_df, passage5_df["Profil_TEMP"], passage5_df["Profil_SPEC"], passage5_df["Integrale"], passage5_df["Gain_Omega"], passage5_df["Gain_temps"], saturation_df, "6", N_AMP)
    #pd.DataFrame(bdd, columns=['Profil_TEMP', 'Profil_SPEC', 'Profil_SPEC_NORM', 'Integrale', 'Gain_Omega', 'Gain_temps'])
    liste_passages = [passage1_df, passage2_df, passage3_df, passage4_df, passage5_df, passage6_df]

    if mode_information:
        create_table(FILE_NAME, TEXTE_AMP)

    if N_AMP == "2":
        for i in range(2):
            update_next_amp(FILE_NAME, 3)
            nbr_passage = data["AMP2"]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"] 
            passage = liste_passages[nbr_passage - 1]
            data = update_config(FILE_NAME, "AMP3")
            
    if N_AMP == "3":
        nbr_passage = data["AMP3"]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"] 
        passage = liste_passages[nbr_passage - 1]
        
    if mode_graphique:
        affichage_spectre(abscisse_df, avant_dazzler_df, passage, filtre_df, data[TEXTE_AMP]["FILTRE_SPECTRAL"]["OUI_NON"])
        affichage_gain(FILE_NAME, TEXTE_AMP)
    
    return [data, passage, abscisse_df]
    
def bilan_puissance(FILE_NAME, mode_information):
    with open(FILE_NAME, "r") as file:
        data = json.load(file)
        
    a_pp = data["BILAN_PUISSANCE"]["ATTENUATEUR_PER_PRIN"]
    a_pa = data["BILAN_PUISSANCE"]["ATTENUATEUR_PER_AUTRE"]
    c_pp = data["BILAN_PUISSANCE"]["COMPRESSEUR_PER_PRIN"]
    c_pa = data["BILAN_PUISSANCE"]["COMPRESSEUR_PER_AUTRE"]
    objectif = data["BILAN_PUISSANCE"]["OBJECTIF"]

    table = PrettyTable()
    table.add_column("AMP",["ENERGIE ENTREE (mJ)","ENERGIE SORTIE (mJ)"])

    for i in range(1, 3 + 1):
        TEXT_AMP = "AMP" + str(i)
        inp = round(data[TEXT_AMP]["FAISCEAU_IR"]["ENERGIE"], 1)
        nbr_passage = data[TEXT_AMP]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"]
        TEXT_PASSAGE = "PASSAGE" + str(nbr_passage)
        out = round(data[TEXT_AMP]["RESULTATS"][TEXT_PASSAGE]["ENERGIE"],1)
        if i == 3:
            energie_finale = out
        table.add_column(str(i),[str(inp),str(out)])

    energie_a = round(energie_finale*(1-a_pp)*(1-a_pa), 1)
    energie_p = round(energie_a*(1-c_pp)*(1-c_pa),1)
    p = round(energie_p/25.2,1)
    data["BILAN_PUISSANCE"]["PUISSANCE"] = p
    m = round(abs(objectif-p)/objectif*100,1)
    table.add_column("ATTENUATEUR",[str(energie_finale),str(energie_a)])
    table.add_column("COMPRESSEUR",[str(energie_a),str(energie_p)])
    
    table = PrettyTable()
    table.add_column("PUISSANCE SORTIE (TW)",["OBJECTIF (TW)","MARGE (%)"])
    table.add_column(str(p),[str(objectif), str(m)])

    if mode_information:
        print(table)

    # Sauvegarde du fichier JSON avec les nouvelles valeurs
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

    return p
import numpy as np
import pandas as pd
import scipy.constants as cst
from misc import Barycentre
from update_config import update_result

def gain_init(N_POINT, Energie_pompe, Absorption_cristal, Efficacite_quantique, Longueur_onde_pompe, Surface_équivalente, saturation_df, apres_dazzler_df, abscisse_df):
    bdd = np.zeros((N_POINT + 1, 2))

    for i in range(N_POINT+1): #checker si c'est surface équiv ou d'emission
        bdd[i,0] = np.exp(Energie_pompe * Absorption_cristal * Efficacite_quantique * Longueur_onde_pompe / abscisse_df["Lambda"][i] / 1000 / Surface_équivalente / saturation_df["Saturation"][i])
        bdd[i,1] = 1 / (1 - (1 - (1 / bdd[i,0])) * np.exp(-apres_dazzler_df["Integrale"][i] / saturation_df["Saturation"][i]))

    df_bdd = pd.DataFrame(bdd, columns=['Gain_Omega', 'Gain_temps'])
    return df_bdd
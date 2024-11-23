import numpy as np
import pandas as pd
import json
from prettytable import PrettyTable
import matplotlib.pyplot as plt

def puissance_atteinte(data, mode_information):
    global debug
    if data["BILAN_PUISSANCE"]["PUISSANCE"] < data["BILAN_PUISSANCE"]["OBJECTIF"]:
        debug = True
        if mode_information:
            print("[Système] La puissance objetif (" + str(data["BILAN_PUISSANCE"]["OBJECTIF"]) + " TW) n'est pas atteinte (" + str(data["BILAN_PUISSANCE"]["PUISSANCE"]) + " TW)")

def fluence_pompe_dommage(data, mode_information):
    global debug

    for i in range(2, 3+1):
        if data["AMP" + str(i)]["FAISCEAU_POMPE"]["FLUENCE_POMPE_DOMMAGE"] > 1:
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Fluence de la pompe au dessus du seuil de dommage : " + round(str(data["AMP" + str(i)]["FAISCEAU_POMPE"]["FLUENCE_POMPE_DOMMAGE"])),2)

def fluence_sortie(data, mode_information):
    global debug
    for i in range(2, 3+1):
        nbr_passage = data["AMP" + str(i)]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"]
        fluence_out = data["AMP" + str(i)]["RESULTATS"]["PASSAGE" + str(nbr_passage)]["FLUENCE"]
        if fluence_out < 1.1:
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Fluence de sortie trop faible < 1.1 J/cm² : " + str(fluence_out))
        if fluence_out > 1.5:
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Fluence de sortie trop grande > 1.5 J/cm² : " + str(fluence_out))

def eclairement(data, mode_information):
    global debug
    for i in range(2, 3+1):
        nbr_passage = data["AMP" + str(i)]["GEOMETRIE_AMPLIFICATEUR"]["PASSAGES"]
        eclair = data["AMP" + str(i)]["RESULTATS"]["PASSAGE" + str(nbr_passage)]["ECLAIREMENT"]
        if eclair > 5000:
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Eclairement de sortie > 5000 GW/cm² " + str(eclair))

def taille_faisceau(data, mode_information):
    global debug
    for i in range(2, 3+1):
        taille = data["AMP" + str(i)]["FAISCEAU_IR"]["DIAMETRE"]
        diam = data["AMP" + str(i)]["CRISTAL_TISA"]["DIAMETRE"]
        ratio = taille/diam

        if ratio > 0.9 :
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Le diamètre du cristal est trop faible (Rapport taille/diamètre > 0.9) ! Rapport taille/diamètre : " + str(round(ratio,2)) + " ( " + str(taille) + "/" + str(diam) + ")(Conseil) Les diamètres standards sont [6,8,20,30,60,80,130,200] (mm)")
        if ratio <= 0.45 and i != 1 : 
            debug = True
            if mode_information:
                print("AMP" + str(i))
                print("Le diamètre du cristal est trop grand  (Rapport taille/diamètre <= 0.5) ! Rapport taille/diamètre : " + str(round(ratio,2))  + " ( " + str(taille) + "/" +str(diam) + ")(Conseil) Les diamètres standards sont [6,8,20,30,60,80,130,200] (mm)")


def verification(FILE_NAME, mode_information):
    global debug
    debug = False #Debug = False, no need to debug :)

    with open(FILE_NAME, "r") as file:
        data = json.load(file)

    puissance_atteinte(data, mode_information)
    fluence_sortie(data, mode_information)
    eclairement(data, mode_information)
    taille_faisceau(data, mode_information)

    if not debug and mode_information:
        print("RAS")

    print("\n")

    return debug
    
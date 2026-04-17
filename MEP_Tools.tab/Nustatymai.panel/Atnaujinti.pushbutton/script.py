# -*- coding: utf-8 -*-
"""Atsisiunčia naujausius įrankius iš GitHub ir atnaujina plėtinį."""
import os
import tempfile
import zipfile
import shutil

from pyrevit import forms
from pyrevit.loader import sessionmgr

import System
from System.Net import WebClient, ServicePointManager, SecurityProtocolType

# Priverstinai naudojame TLS 1.2, kad GitHub neblokuotų atsisiuntimo iš senesnio .NET
ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12

# Mūsų repozitorijos master šakos ZIP nuoroda
URL = "https://github.com/projektavimas-ux/Revit-MEP-Tools/archive/refs/heads/master.zip"

def update_extension():
    res = forms.alert("Ar tikrai norite atsiųsti ir įdiegti naujausius įrankių atnaujinimus?", yes=True, no=True, title="Įrankių atnaujinimas")
    if not res:
        return
        
    # Surandame kur mūsų kompiuteryje yra Imones.extension aplankas
    # __file__ grąžina šio skripto kelią, pvz.: C:\Revit_Irankiai\Imones.extension\MEP_Tools.tab\...
    try:
        ext_dir = __file__.split(".extension")[0] + ".extension"
    except Exception:
        forms.alert("Nepavyko nustatyti plėtinio aplanko.")
        return

    temp_zip = os.path.join(tempfile.gettempdir(), "Revit-MEP-Tools-master.zip")
    extract_dir = os.path.join(tempfile.gettempdir(), "pyrevit_update_temp")
    
    try:
        # 1. Atsisiunčiame ZIP naudojant .NET WebClient
        client = WebClient()
        client.DownloadFile(URL, temp_zip)
        
        # 2. Išvalome seną laikiną aplanką, jei toks liko, ir sukuriame naują
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        # 3. Išskleidžiame ZIP
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Išskleistas aplankas GitHub'e visada vadinasi "<repo>-<branch>"
        source_dir = os.path.join(extract_dir, "Revit-MEP-Tools-master")
        
        # 4. Perkopijuojame failus (perrašome ant viršaus)
        for src_dir, dirs, files in os.walk(source_dir):
            dst_dir = src_dir.replace(source_dir, ext_dir)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                # Jei faile yra read-only požymis, failo perrašymas gali lūžti, todėl kopijuojame saugiai
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception as ex:
                    print("Nepavyko perrašyti {}: {}".format(dst_file, ex))
                
        # 5. Išvalome šiukšles
        try:
            os.remove(temp_zip)
            shutil.rmtree(extract_dir)
        except:
            pass # Jei nepavyko ištrinti temp failų - nieko baisaus
            
        forms.alert("Įrankiai sėkmingai atnaujinti!\n\nDabar pyRevit persikraus, kad pritaikytų pakeitimus.", title="Pavyko")
        
        # 6. Priverčiame pyRevit persikrauti
        sessionmgr.reload_pyrevit()
        
    except Exception as e:
        forms.alert("Įvyko klaida bandant atnaujinti:\n\n{}".format(e), title="Klaida")

if __name__ == '__main__':
    update_extension()
# -*- coding: utf-8 -*-
"""Atsisiuncia naujausius irankius is GitHub ir atnaujina pletinius."""
import os
import tempfile
import zipfile
import shutil

from pyrevit import forms
from pyrevit.loader import sessionmgr

import clr
clr.AddReference('System')
import System.Net

# Naudojame TLS 1.2, kad GitHub neblokuotu atsisiuntimo
System.Net.ServicePointManager.SecurityProtocol = System.Net.SecurityProtocolType.Tls12

URL = "https://github.com/projektavimas-ux/Revit-MEP-Tools/archive/refs/heads/master.zip"

CORE_PANELS = [
    "Nustatymai.panel",
    "Sheets.panel",
    "Views.panel",
    "Dimensions.panel",
    "Export.panel",
]

MEP_PANELS = [
    "Tags.panel",
    "NSIK.panel",
]


def _copy_tree_replace(src, dst):
    """Nukopijuoja direktorija i dst; jei dst yra - pilnai perraso."""
    if not os.path.exists(src):
        return False

    if os.path.exists(dst):
        shutil.rmtree(dst)

    for src_dir, _, files in os.walk(src):
        rel = os.path.relpath(src_dir, src)
        if rel == '.':
            dst_dir = dst
        else:
            dst_dir = os.path.join(dst, rel)

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        for file_name in files:
            src_file = os.path.join(src_dir, file_name)
            dst_file = os.path.join(dst_dir, file_name)
            shutil.copy2(src_file, dst_file)

    return True


def _write_arch_placeholder(arch_ext, icon_source):
    roadmap_dir = os.path.join(
        arch_ext,
        "ARCH_Tools.tab",
        "Info.panel",
        "ArchRoadmap.pushbutton"
    )

    if os.path.exists(roadmap_dir):
        shutil.rmtree(roadmap_dir)
    os.makedirs(roadmap_dir)

    script_path = os.path.join(roadmap_dir, "script.py")
    script_text = (
        "# -*- coding: utf-8 -*-\n"
        "from pyrevit import forms\n"
        "forms.alert(\n"
        "    \"ARCH modulis ruosiamas.\\n\\n\"\n"
        "    \"Planuojamos funkcijos:\\n\"\n"
        "    \"- ARCH View/Sheet automatizacija\\n\"\n"
        "    \"- ARCH QA patikros\\n\"\n"
        "    \"- ARCH Parameter Transformer\",\n"
        "    title=\"PRB ARCH Roadmap\"\n"
        ")\n"
    )

    with open(script_path, 'w') as f:
        f.write(script_text)

    if icon_source and os.path.exists(icon_source):
        shutil.copy2(icon_source, os.path.join(roadmap_dir, "icon.png"))


def _update_split_structure(source_dir, current_ext_dir):
    """Atnaujina nauja 3 pletiniu struktura: PRB_Core/PRB_MEP/PRB_ARCH."""
    source_tab = os.path.join(source_dir, "MEP_Tools.tab")
    if not os.path.exists(source_tab):
        raise Exception("Nerastas MEP_Tools.tab source kataloge: {}".format(source_tab))

    install_root = os.path.dirname(current_ext_dir)
    core_ext = os.path.join(install_root, "PRB_Core.extension")
    mep_ext = os.path.join(install_root, "PRB_MEP.extension")
    arch_ext = os.path.join(install_root, "PRB_ARCH.extension")

    core_tab = os.path.join(core_ext, "CORE.tab")
    mep_tab = os.path.join(mep_ext, "MEP_Tools.tab")

    if not os.path.exists(core_tab):
        os.makedirs(core_tab)
    if not os.path.exists(mep_tab):
        os.makedirs(mep_tab)
    if not os.path.exists(arch_ext):
        os.makedirs(arch_ext)

    missing = []

    for panel in CORE_PANELS:
        src = os.path.join(source_tab, panel)
        dst = os.path.join(core_tab, panel)
        if not _copy_tree_replace(src, dst):
            missing.append("CORE:" + panel)

    for panel in MEP_PANELS:
        src = os.path.join(source_tab, panel)
        dst = os.path.join(mep_tab, panel)
        if not _copy_tree_replace(src, dst):
            missing.append("MEP:" + panel)

    # ARCH laikinas roadmap mygtukas
    icon_source = os.path.join(
        source_tab,
        "Nustatymai.panel",
        "Pagalba.pushbutton",
        "icon.png"
    )
    _write_arch_placeholder(arch_ext, icon_source)

    # Bendri dokumentai i Core pletini
    for doc_name in ["CHANGELOG.md", "SUPPORT_PLAYBOOK.md", "TOOLS_KNOWLEDGE_BASE.md"]:
        src_doc = os.path.join(source_dir, doc_name)
        if os.path.exists(src_doc):
            shutil.copy2(src_doc, os.path.join(core_ext, doc_name))

    return missing


def _update_legacy_structure(source_dir, ext_dir):
    """Senas vieno pletinio atnaujinimas (fallback suderinamumui)."""
    for src_dir, _, files in os.walk(source_dir):
        dst_dir = src_dir.replace(source_dir, ext_dir)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        for file_name in files:
            src_file = os.path.join(src_dir, file_name)
            dst_file = os.path.join(dst_dir, file_name)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as ex:
                print("Nepavyko perrasyti {}: {}".format(dst_file, ex))


def update_extension():
    res = forms.alert(
        "Ar tikrai norite atsisiusti ir idiegti naujausius irankiu atnaujinimus?",
        yes=True,
        no=True,
        title="Irankiu atnaujinimas"
    )
    if not res:
        return

    try:
        ext_dir = __file__.split(".extension")[0] + ".extension"
    except Exception:
        forms.alert("Nepavyko nustatyti pletinio aplanko.")
        return

    temp_zip = os.path.join(tempfile.gettempdir(), "Revit-MEP-Tools-master.zip")
    extract_dir = os.path.join(tempfile.gettempdir(), "pyrevit_update_temp")

    try:
        client = System.Net.WebClient()
        client.DownloadFile(URL, temp_zip)

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)

        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        source_dir = os.path.join(extract_dir, "Revit-MEP-Tools-master")

        install_root = os.path.dirname(ext_dir)
        split_mode = (
            os.path.basename(ext_dir).lower() == "prb_core.extension" or
            os.path.exists(os.path.join(install_root, "PRB_MEP.extension")) or
            os.path.exists(os.path.join(install_root, "PRB_ARCH.extension"))
        )

        if split_mode:
            missing = _update_split_structure(source_dir, ext_dir)
            if missing:
                forms.alert(
                    "Atnaujinimas atliktas, bet truksta kai kuriu paneliu:\n\n{}\n\n"
                    "Patikrinkite repozitorijos struktura.".format("\n".join(missing)),
                    title="Atnaujinta su ispėjimais"
                )
            else:
                forms.alert(
                    "Irankiai sekmingai atnaujinti (split Core/MEP/ARCH struktura)!\n\n"
                    "Dabar pyRevit persikraus, kad pritaikytu pakeitimus.",
                    title="Pavyko"
                )
        else:
            _update_legacy_structure(source_dir, ext_dir)
            forms.alert(
                "Irankiai sekmingai atnaujinti (legacy vieno pletinio struktura)!\n\n"
                "Dabar pyRevit persikraus, kad pritaikytu pakeitimus.",
                title="Pavyko"
            )

        try:
            os.remove(temp_zip)
            shutil.rmtree(extract_dir)
        except Exception:
            pass

        sessionmgr.reload_pyrevit()

    except Exception as e:
        forms.alert("Ivyko klaida bandant atnaujinti:\n\n{}".format(e), title="Klaida")


if __name__ == '__main__':
    update_extension()

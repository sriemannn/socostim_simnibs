import os
import pandas as pd
import numpy as np
from simnibs import sim_struct, run_simnibs, mni2subject_coords
from alive_progress import alive_it


basedir = os.path.join("/media", "Data02", "SoCoStim", "SimNIBS")
subs = os.listdir(basedir)
subs.sort()
subs = [sub for sub in subs if sub != "Code"]

PATH2XLSX = os.path.join(
    "/media", "MeinzerStudy", "03_SoCoStim", "Daten", "Data_VPT_umstrukturiert.xlsx"
)
VP_COL = "ID"
SITE_COL = "StimSite"
AGE_GROUP = "AgeGroup"
cols = [VP_COL, SITE_COL, AGE_GROUP]

stim_conditions = pd.read_excel(
    PATH2XLSX, index_col=None, usecols=cols, engine="openpyxl"
)

stim_conditions = stim_conditions.assign(
    ID="SoCoStim" + (stim_conditions.ID.astype(str).str.zfill(3))
)

stim_conditions = stim_conditions[stim_conditions["ID"].isin(subs)]

preprocessing_missing = np.sum(~stim_conditions["ID"].isin(subs))
print(f"Number of subjects with missing preprocessing: {preprocessing_missing}.")

simulation_cols = [VP_COL, SITE_COL]

old = stim_conditions.dropna()

young = stim_conditions.loc[stim_conditions[AGE_GROUP] == 0]
young_rTPJ = young.fillna("rTPJ")
young_dmPFC = young.fillna("dmPFC")
stim_conditions = pd.concat([young_dmPFC, young_rTPJ, old])

stim_conditions.to_csv("simulation_stim_conditions.csv", index=False)

stim_conditions = stim_conditions[simulation_cols].to_numpy()

ELECTRODETHICKNESS = 2
GELTHICKNESS = 1

ring_over_ear = [
    "SoCoStim001",
    "SoCoStim038",
    "SoCoStim066",
    "SoCoStim067",
    "SoCoStim072",
    "SoCoStim131",
]

for condition in alive_it(stim_conditions):
    sub, site = condition

    m2m_path = os.path.join(basedir, sub, f"m2m_SimNIBS4_{sub}")
    msh_path = os.path.join(m2m_path, f"SimNIBS4_{sub}.msh")
    output_path = os.path.join(basedir, sub, f"simnibs4_simulation_{site}")

    if not os.path.exists(msh_path):
        continue

    if os.path.exists(output_path) and not sub in ring_over_ear:
        continue

    elif os.path.exists(output_path) and sub in ring_over_ear and site == "dmPFC":
        continue

    elif os.path.exists(output_path) and sub in ring_over_ear and site == "rTPJ":
        output_path = os.path.join(
            basedir, sub, f"simnibs4_simulation_{site}_alternative_rTPJ_coordinate"
        )

    s = sim_struct.SESSION()
    s.map_to_fsavg = True
    s.map_to_MNI = True
    s.fields = "eEjJ"
    s.subpath = m2m_path
    s.pathfem = output_path
    s.open_in_gmsh = False

    if site == "rTPJ":
        CENTRE = "CP6"
        OUTERRING = 98
        INNERRING = 75

    elif site == "dmPFC":
        CENTRE = mni2subject_coords(
            coordinates=[0.51, 71.66, 46.09],
            m2m_folder=m2m_path,
        )
        OUTERRING = 110
        INNERRING = 90

    tdcslist = s.add_tdcslist()
    tdcslist.currents = [1.5e-3, -1.5e-3]

    anode = tdcslist.add_electrode()
    anode.centre = CENTRE
    anode.shape = "ellipse"
    anode.dimensions = [25, 25]
    anode.thickness = [GELTHICKNESS, ELECTRODETHICKNESS]
    anode.channelnr = 1

    cathode = tdcslist.add_electrode()
    cathode.centre = (
        mni2subject_coords(coordinates=[72.529, -47.867, 54.620], m2m_folder=m2m_path)
        if "alternative" in output_path
        else CENTRE
    )  # TODO
    cathode.shape = "ellipse"
    cathode.dimensions = [OUTERRING, OUTERRING]
    cathode.thickness = [GELTHICKNESS, ELECTRODETHICKNESS]
    cathode.channelnr = 2

    hole = cathode.add_hole()
    hole.shape = "ellipse"
    hole.dimensions = [INNERRING, INNERRING]
    hole.centre = [0, 0]

    run_simnibs(s, cpus=10)

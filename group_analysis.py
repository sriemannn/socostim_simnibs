import simnibs
import numpy as np
import pandas as pd
import os
import os.path as op
import seaborn as sns


def msh_path_creator(row):
    return op.join(
        basedir,
        row.ID,
        f"simnibs4_simulation_{row.StimSite}",
        "fsavg_overlays",
        f"SimNIBS4_{row.ID}_TDCS_1_scalar_fsavg.msh",
    )


def roi_creator(coordinates, msh_coords, radius=12.5):
    return np.linalg.norm(msh_coords - coordinates, axis=1) < radius


def get_mean_fields(field, roi):
    return np.average(field[roi], weights=results_fsavg.nodes_areas()[roi])


def get_roi_fields(coord, roi_radius=12.5):
    roi = roi_creator(
        coord,
        results_fsavg.nodes.node_coord,
        radius=roi_radius,
    )

    site_E_normal = [get_mean_fields(sub_field, roi) for sub_field in E_normal]
    site_E_magn = [get_mean_fields(sub_field, roi) for sub_field in E_magn]

    return site_E_normal, site_E_magn


coords = {
    "rTPJ": {
        "Wang_2016_average": [50, -60, 32],
        "Scrivener_2022": [62.43, -49.07, 37.65],
    },
    "dmPFC": {
        "Schurz_2014": [-1, 54, 24],
        "MNI_under_electrode": [0.56, 61.81, 36.91],
    },
}

basedir = os.path.join("/media", "Data02", "SoCoStim", "SimNIBS")

stim_conditions = pd.read_csv("simulation_stim_conditions.csv").sort_values("ID")

stim_conditions = stim_conditions.assign(
    msh_path=stim_conditions.apply(msh_path_creator, axis=1),
    msh_exists=lambda df: df.apply(lambda row: op.exists(row.msh_path), axis=1),
    age=np.where(stim_conditions.AgeGroup == 0, "young", "old"),
)

stim_conditions[~stim_conditions.msh_exists].to_csv("no_msh_file_created.csv")

data = stim_conditions

stim_conditions = stim_conditions.drop(columns="AgeGroup").to_numpy()

fields = {
    "E_magn_dmPFC_old": [],
    "E_magn_dmPFC_young": [],
    "E_magn_rTPJ_old": [],
    "E_magn_rTPJ_young": [],
    "E_normal_dmPFC_old": [],
    "E_normal_dmPFC_young": [],
    "E_normal_rTPJ_old": [],
    "E_normal_rTPJ_young": [],
}

subs = {
    "dmPFC_old": [],
    "dmPFC_young": [],
    "rTPJ_old": [],
    "rTPJ_young": [],
}

for conditions in stim_conditions:
    sub, site, msh_path, msh_file_exists, age_group = conditions

    if not msh_file_exists:
        continue

    results_fsavg = simnibs.read_msh(msh_path)
    fields[f"E_magn_{site}_{age_group}"].append(results_fsavg.field["E_magn"].value)
    fields[f"E_normal_{site}_{age_group}"].append(results_fsavg.field["E_normal"].value)
    subs[f"{site}_{age_group}"].append(sub)

fields = {key: np.vstack(value) for key, value in fields.items()}

results_fsavg.nodedata = []

for key, value in fields.items():
    results_fsavg.add_node_field(np.mean(value, axis=0), f"{key}_mean")
    results_fsavg.add_node_field(np.std(value, axis=0), f"{key}_std")

for key in [i.rsplit("_", 1)[0] for i in fields.keys()][::2]:
    results_fsavg.add_node_field(
        (
            np.mean(fields[f"{key}_young"], axis=0)
            - np.mean(fields[f"{key}_old"], axis=0)
        ),
        f"{key}_mean_contrast_young-old",
    )
    results_fsavg.add_node_field(
        (np.std(fields[f"{key}_young"], axis=0) - np.std(fields[f"{key}_old"], axis=0)),
        f"{key}_std_contrast_young-old",
    )

results_fsavg.view(visible_fields=list(fields.keys())[0]).show()

results_fsavg.add_node_field(
    roi_creator(coords["rTPJ"]["Wang_2016_average"], results_fsavg.nodes.node_coord),
    "rTPJ_Wang_2016",
)
results_fsavg.add_node_field(
    roi_creator(coords["rTPJ"]["Scrivener_2022"], results_fsavg.nodes.node_coord),
    "rTPJ_Scrivener_2022",
)
results_fsavg.add_node_field(
    roi_creator(coords["dmPFC"]["Schurz_2014"], results_fsavg.nodes.node_coord),
    "dmPFC_Schurz_2014",
)
results_fsavg.add_node_field(
    roi_creator(coords["dmPFC"]["MNI_under_electrode"], results_fsavg.nodes.node_coord),
    "dmPFC_MNI_under_electrode",
)

subjects = []
E_magn = []
E_normal = []
strat = []

for strata, subject in subs.items():
    for index, sub in enumerate(subject):
        subjects.append(sub)
        strat.append(strata)
        E_magn.append(fields[f"E_magn_{strata}"][index])
        E_normal.append(fields[f"E_normal_{strata}"][index])

E_magn = np.vstack(E_magn)
E_normal = np.vstack(E_normal)
subjects = np.vstack(subjects)


wang = get_roi_fields(coords["rTPJ"]["Wang_2016_average"])
scrievener = get_roi_fields(coords["rTPJ"]["Scrivener_2022"])
schurz = get_roi_fields(coords["dmPFC"]["Schurz_2014"])
mni = get_roi_fields(coords["dmPFC"]["MNI_under_electrode"])

mean_fields = pd.DataFrame(
    {
        "ID": subjects.reshape(-1),
        "strata": strat,
        "wang_E_normal": wang[0],
        "wang_E_magn": wang[1],
        "scrivener_E_normal": scrievener[0],
        "scrivener_E_magn": scrievener[1],
        "schurz_E_normal": schurz[0],
        "schurz_E_magn": schurz[1],
        "mni_E_normal": mni[0],
        "mni_E_magn": mni[1],
    }
)

mean_fields = mean_fields.assign(
    StimSite=mean_fields.strata.str.split("_", expand=True)[0],
).drop(columns="strata")

data = data.merge(mean_fields, on=["ID", "StimSite"], how="left").drop(
    ["msh_path", "age"], axis=1
)

data_plot = data.drop(data.columns[data.columns.str.endswith("E_normal")], axis=1)

data_plot.to_csv("SoCoStim_SimNIBS.csv", index=False)

ax = sns.pairplot(
    data=data_plot[data_plot.msh_exists].drop(["ID", "StimSite", "msh_exists"], axis=1),
    hue="AgeGroup",
    diag_kind="hist",
)

ax.savefig("SoCoStim_SimNIBS_pairplot_E_magn.png")

ax = sns.pairplot(
    data=data[data.msh_exists]
    .drop(data.columns[data.columns.str.endswith("E_magn")], axis=1)
    .drop(columns=["ID", "StimSite", "msh_exists"]),
    hue="AgeGroup",
    diag_kind="hist",
)

ax.savefig("SoCoStim_SimNIBS_pairplot_E_normal.png")

# -*- coding: utf-8 -*-

#pip install bstpp

import bstpp

#!pip install --upgrade scipy jax jaxlib

from bstpp.main import LGCP_Model, Hawkes_Model,  Point_Process_Model

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Try to import geopandas
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

import numpyro
import numpyro.distributions as dist

"""# **CONFIGURATION**"""

SEED = 42
np.random.seed(SEED)

# --- 1. Load Data ---
EBOLA_CSV = "/content/drive/MyDrive/data1/ebola/ebola_sierraleone_2014_processed.csv"
SIERRA_LEONE_SHP = "/content/drive/MyDrive/data1/ebola/shp/sle_admbnda_adm1_gov_ocha_20231215.shp"

OUTPUT_DIR = '/content/drive/MyDrive/data1/bstpp_ebola_analysis_results/results'
FIGURE_DIR = '/content/drive/MyDrive/data1/bstpp_ebola_analysis_results/figures'

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

"""#**DATA LOADING**"""

events_df = pd.read_csv(EBOLA_CSV)

# Clean NaNs
events_df = events_df.dropna()

print(events_df.head())

len(events_df)

events_df['T'].unique()

"""#**EDA**"""

plt.figure(figsize=(8, 6))
plt.hist(events_df['T'], bins=50, color='steelblue')
plt.xlabel("Time (Days)")
plt.ylabel("Event Count")
plt.title("Epidemic Curve (EDA-1)")
plt.savefig(f"{FIGURE_DIR}/EDA-1_epidemic_curve.png")
plt.show()

plt.figure(figsize=(8, 6))
sc = plt.scatter(events_df['X'], events_df['Y'], c=events_df['T'], cmap='viridis')
plt.colorbar(sc, label='Time (Days)')
plt.xlabel("Longitude (X)")
plt.ylabel("Latitude (Y)")
plt.title("Spatial Event Locations (EDA-2)")

# =======================
# EDA (Updated to plot shapefile + points together)
# =======================
plt.figure(figsize=(10, 8))

if HAS_GEOPANDAS and SIERRA_LEONE_SHP and os.path.exists(SIERRA_LEONE_SHP):
    boundaries = gpd.read_file(SIERRA_LEONE_SHP)
    ax = boundaries.plot(facecolor="none", edgecolor="black", linewidth=1)
    events_df.plot.scatter(x="X", y="Y", c=events_df["T"], colormap="viridis", ax=ax, alpha=0.7,label='Ebola Cases')
else:
    plt.scatter(events_df['X'], events_df['Y'], c=events_df['T'], cmap='viridis')
    plt.colorbar(label='Time (Days)')
    plt.gca().set_aspect('equal')

plt.xlabel("Longitude (X)")
plt.ylabel("Latitude (Y)")
plt.title("Spatial Event Locations over Sierra Leone Boundaries (EDA-2)")
plt.legend()
plt.savefig(f"{FIGURE_DIR}/EDA-2_spatial_scatter.png")
plt.show()

"""#**DOMAIN DEFINITION**"""

x_min, x_max = events_df['X'].min(), events_df['X'].max()
y_min, y_max = events_df['Y'].min(), events_df['Y'].max()

buffer_x = 0.01 * (x_max - x_min)
buffer_y = 0.01 * (y_max - y_min)

grid_bounds = np.array([[x_min - buffer_x, x_max + buffer_x],
                              [y_min - buffer_y, y_max + buffer_y]])

T_max = events_df['T'].max() + 1.0

print("Grid Bounds:", grid_bounds_ebola)
print("T_max:", T_max_ebola)

"""#**Helper Inference Function**"""

def run_inference(model, name, method, out_file, rng_key, **kwargs):
    if os.path.exists(out_file):
        try:
            model.load_rslts(out_file)
            print(f"[LOADED] {name} from {out_file}")
            return True
        except:
            pass

    print(f"[RUNNING] {method.upper()} for {name}")

    start = time.time()
    if method == "svi":
        model.run_svi(**kwargs)
    else:
        model.run_mcmc(**kwargs)

    elapsed = time.time() - start
    print(f"[DONE] {name} ({method}) took {elapsed:.2f} seconds")

    model.save_rslts(out_file)

    if method == "svi":
        plt.savefig(f"{FIGURE_DIR}/{name}_svi_loss.png")
        plt.close()

    return True

"""#**Priors**"""

priors = {
    "a_0": dist.Normal(1, 10),
    "alpha": dist.Beta(20, 60),
    "beta": dist.HalfNormal(2.0),
    "sigmax_2": dist.HalfNormal(0.25),
}

GRID_RESOLUTION = 25
MCMC_WARMUP = 500
MCMC_SAMPLES = 1500
MCMC_CHAINS = 1

"""#**MODEL FITTING**"""

hawkes = Hawkes_Model(events_df, grid_bounds, T_max, **priors)

hawkes.run_svi(num_steps=20000, lr=0.001, plot_loss=True)
hawkes.save_rslts(f"{OUTPUT_DIR}/hawkes_svi.pkl")

hawkes.expected_AIC()

hawkes.plot_prop_excitation()

hawkes.plot_trigger_posterior(trace=False)

hawkes.plot_spatial()

hawkes.plot_temporal()





"""# LGCP MODEL"""

lgcp_cov = LGCP_Model(events_df, grid_bounds, T_max, cov_grid_size=(GRID_RESOLUTION, GRID_RESOLUTION),
                  **priors)

print("Running LGCP SVI...")

lgcp_cov.run_svi(num_steps=20000, lr=0.001, plot_loss=True)
lgcp_cov.save_rslts(f"{OUTPUT_DIR}/lgcp_cov_svi.pkl")

print("SVI Completed and saved.")

lgcp_cov.expected_AIC()

lgcp_cov.plot_temporal()

lgcp_cov.plot_spatial()







"""# COX HAWKES MODEL"""

coxhawkes_cov = Hawkes_Model(events_df, grid_bounds, T_max, cox_background=True, **priors)

print("Running Cox-Hawkes SVI...")

coxhawkes_cov.run_svi(num_steps=20000, lr=0.001, plot_loss=True)
coxhawkes_cov.save_rslts(f"{OUTPUT_DIR}/coxhawkes_cov_svi.pkl")

print("SVI Completed and saved.")

coxhawkes_cov.expected_AIC()

coxhawkes_cov.plot_prop_excitation()

coxhawkes_cov.plot_trigger_posterior(trace=False)

coxhawkes_cov.plot_spatial()

coxhawkes_cov.plot_temporal()








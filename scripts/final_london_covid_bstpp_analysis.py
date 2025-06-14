# -*- coding: utf-8 -*-
#pip install bstpp

import bstpp

#pip install --upgrade scipy jax jaxlib

from bstpp.main import LGCP_Model, Hawkes_Model

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import numpyro.distributions as dist
from shapely.geometry import box

"""#**CONFIGURATION**"""

EVENTS_PATH = "/kaggle/input/coviduk/london_covid_events.csv"
COVARIATES_PATH = "/kaggle/input/coviduk/london_covid_covariates.csv"
OUTPUT_DIR = "/kaggle/working/"
FIGURE_DIR = "/kaggle/working/"
SHAPEFILE_PATH = "/kaggle/input/coviduk/Greater_London_Authority_(GLA).shp"  # Update path if available


SUBSET_SIZE = 10000

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

"""#**LOAD DATA**"""

events_df = pd.read_csv(EVENTS_PATH)
events_df = events_df.sample(n=SUBSET_SIZE, random_state=42).sort_values("T").reset_index(drop=True)
#events_df = events_df[events_df["T"] <= 40].copy()

print("Subset events data:")
print(events_df.head())

events_df['T'].unique()

len(events_df)

"""#**EDA - EXPLORATORY DATA ANALYSIS**"""

# Epidemic curve
plt.figure()
events_df["T"].hist(bins=50)
plt.xlabel("Time (T)")
plt.ylabel("Number of Events")
plt.title("Epidemic Curve (COVID Cases Over Time)")
plt.savefig(f"{FIGURE_DIR}/eda_epidemic_curve.png")
plt.show()

# Spatial plot colored by time
plt.figure()
plt.scatter(events_df["X"], events_df["Y"], c=events_df["T"], cmap="viridis", alpha=0.5)
plt.xlabel("Longitude (X)")
plt.ylabel("Latitude (Y)")
plt.title("Spatial Distribution of COVID Cases (colored by Time)")
plt.colorbar(label="Time (T)")
plt.savefig(f"{FIGURE_DIR}/eda_spatial_scatter.png")
plt.show()

if SHAPEFILE_PATH and os.path.exists(SHAPEFILE_PATH):
    # Load shapefile
    shp = gpd.read_file(SHAPEFILE_PATH)

    # Assign CRS if missing
    if shp.crs is None:
        shp = shp.set_crs("EPSG:27700")

    # Prepare events as GeoDataFrame
    events_gdf = gpd.GeoDataFrame(events_df, geometry=gpd.points_from_xy(events_df["X"], events_df["Y"]))
    events_gdf.crs = "EPSG:4326"
    events_gdf = events_gdf.to_crs(shp.crs)

    # Plot with larger figure and better points
    plt.figure(figsize=(12, 16))
    ax = shp.plot(color='white', edgecolor='black', linewidth=1)

    # Plot points, larger size and clearer colormap
    events_gdf.plot(ax=ax, column='T', cmap='plasma', markersize=80, alpha=0.8, legend=True)

    # Add titles and labels
    plt.title("Spatial Distribution of COVID Events (Subset)", fontsize=16)
    plt.xlabel("Longitude", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # Save and show
    plt.savefig(f"{FIGURE_DIR}/eda_spatial_on_shapefile.png", bbox_inches='tight')
    plt.show()

"""#**DEFINE SPATIAL DOMAIN**"""

x_min, x_max = events_df["X"].min() - 0.005, events_df["X"].max() + 0.005
y_min, y_max = events_df["Y"].min() - 0.005, events_df["Y"].max() + 0.005
grid_bounds = np.array([[x_min, x_max], [y_min, y_max]])

T_max = events_df["T"].max() + 7

priors = {
    "a_0": dist.Normal(1, 10),
    "alpha": dist.Beta(20, 60),
    "beta": dist.HalfNormal(2.0),
    "sigmax_2": dist.HalfNormal(0.25),
}

MCMC_WARMUP = 100
MCMC_SAMPLES = 400
MCMC_CHAINS = 1

SVI_STEPS = 15000
SVI_LR = 0.02
GRID_RESOLUTION = 0.5
SAMPLE_EVENTS = 10000

"""# LOAD + SAMPLE EVENTS"""

#events_df_full = pd.read_csv(EVENTS_PATH)

# Sample events
#events_df = events_df_full.sample(n=min(SAMPLE_EVENTS, len(events_df_full)), random_state=42).reset_index(drop=True)

#T_max = events_df["T"].max() + 7
#grid_bounds = np.array([
    #[events_df["X"].min() - 0.005, events_df["X"].max() + 0.005],
   # [events_df["Y"].min() - 0.005, events_df["Y"].max() + 0.005],
#])

# Prepare events GeoDataFrame
events_gdf = gpd.GeoDataFrame(events_df, geometry=gpd.points_from_xy(events_df.X, events_df.Y))
events_gdf.crs = "EPSG:4326"

"""# LOAD + SAMPLE SPATIAL COVARIATES"""

covariates_df_raw = pd.read_csv(COVARIATES_PATH).drop_duplicates(subset=["X", "Y"]).reset_index(drop=True)

covariates_gdf = gpd.GeoDataFrame(covariates_df_raw, geometry=gpd.points_from_xy(covariates_df_raw.X, covariates_df_raw.Y))
covariates_gdf.crs = "EPSG:4326"

covariates_gdf = covariates_gdf.to_crs("EPSG:27700")

# Create polygons
grid_size = 2000  # meters
polygons = []
for point in covariates_gdf.geometry:
    x, y = point.x, point.y
    polygons.append(box(x - grid_size/2, y - grid_size/2, x + grid_size/2, y + grid_size/2))

covariates_gdf['geometry'] = polygons
covariates_gdf.crs = "EPSG:27700"
covariates_gdf = covariates_gdf.to_crs("EPSG:4326")

spatial_cov = covariates_gdf

events_gdf.head()

spatial_cov.head()

"""# LGCP MODEL"""

spatial_cov.columns

lgcp_cov_priors = {
    "a_0": dist.Normal(0, 10)
}

covariate_columns = ['popdensity', 'covid_deaths', 'popn', 'houseprice']

lgcp_cov = LGCP_Model(events_gdf, grid_bounds, T_max,
                  cov_grid_size=(GRID_RESOLUTION, GRID_RESOLUTION),
                  spatial_cov=spatial_cov,
                  cov_names=covariate_columns,
                  **priors)

print("Running LGCP SVI...")

lgcp_cov.run_svi(num_steps=SVI_STEPS, lr=SVI_LR, plot_loss=True)
lgcp_cov.save_rslts(f"{OUTPUT_DIR}/lgcp_cov_svi.pkl")

print("SVI Completed and saved.")

lgcp_cov.expected_AIC()

lgcp_cov.plot_temporal()

lgcp_cov.plot_spatial()

lgcp_cov.plot_spatial(include_cov=True)

lgcp_cov.cov_weight_post_summary()

print("Running lgcp_cov MCMC...")

lgcp_cov.run_mcmc(num_warmup=MCMC_WARMUP, num_samples=MCMC_SAMPLES, num_chains=MCMC_CHAINS)
lgcp_cov.save_rslts(f"{OUTPUT_DIR}/lgcp_cov_mcmc.pkl")

print("MCMC Completed and saved.")

lgcp_cov.expected_AIC()

lgcp_cov.plot_temporal()

lgcp_cov.plot_spatial()

lgcp_cov.plot_spatial(include_cov=True)

print("Plotting LGCP Intensity maps...")

time_slices = np.linspace(0, T_max, 5)

for t in time_slices:
    plt.figure(figsize=(10, 6))
    lgcp_cov.plot_spatial(t)
    plt.title(f"LGCP_cov Intensity at t={int(t)}")
    plt.savefig(f"{FIGURE_DIR}/lgcp_cov_mcmc_intensity_t{int(t)}.png")
    plt.show()

lgcp_cov.cov_weight_post_summary()



"""# Cox-Hawkes

"""

# ---------------------------
# Define Priors for Cox-Hawkes
# ---------------------------

coxhawkes_cov_priors = {
     "a_0": dist.Normal(1, 10),
    "alpha": dist.Beta(20, 60),
    "beta": dist.HalfNormal(2.0),
    "sigmax_2": dist.HalfNormal(0.25)
}

# ---------------------------
# Initialize Cox-Hawkes Model
# ---------------------------

coxhawkes_cov = Hawkes_Model(events_gdf, grid_bounds, T_max,
                         cox_background=True,
                         spatial_cov=spatial_cov,
                         cov_names=covariate_columns,
                         **coxhawkes_cov_priors)

print("Initialized Cox-Hawkes model.")

# ---------------------------
# Run SVI
# ---------------------------

print("Running Cox-Hawkes SVI...")

coxhawkes_cov.run_svi(num_steps=SVI_STEPS, lr=SVI_LR, plot_loss=True)
coxhawkes_cov.save_rslts(f"{OUTPUT_DIR}/coxhawkes_cov_svi.pkl")

print("SVI Completed and saved.")

coxhawkes_cov.expected_AIC()

coxhawkes_cov.plot_prop_excitation()

coxhawkes_cov.plot_trigger_posterior(trace=False)

coxhawkes_cov.plot_spatial()

coxhawkes_cov.plot_spatial(include_cov=True)

coxhawkes_cov.plot_temporal()

coxhawkes_cov.cov_weight_post_summary(trace=True)

#---------------------------
# Run MCMC
# ---------------------------

print("Running coxhawkes_cov MCMC...")

coxhawkes_cov.run_mcmc(num_warmup=MCMC_WARMUP, num_samples=MCMC_SAMPLES, num_chains=MCMC_CHAINS)
coxhawkes_cov.save_rslts(f"{OUTPUT_DIR}/coxhawkes_cov_mcmc.pkl")

print("MCMC Completed and saved.")

coxhawkes_cov.expected_AIC()

coxhawkes_cov.plot_prop_excitation()

coxhawkes_cov.plot_trigger_posterior(trace=False)

coxhawkes_cov.plot_spatial()

coxhawkes_cov.plot_spatial(include_cov=True)

coxhawkes_cov.plot_temporal()

coxhawkes_cov.cov_weight_post_summary(trace=True)

"""# Hawkes

"""

priors = {
    "a_0": dist.Normal(1, 10),
    "alpha": dist.Beta(20, 60),
    "beta": dist.HalfNormal(2.0),
    "sigmax_2": dist.HalfNormal(0.25)
}
hawkes = Hawkes_Model(events_df, grid_bounds, T_max, **priors)

hawkes.run_mcmc(num_warmup=MCMC_WARMUP, num_samples=MCMC_SAMPLES, num_chains=MCMC_CHAINS)
hawkes.save_rslts(f"{OUTPUT_DIR}/hawkes_mcmc.pkl")

hawkes.expected_AIC()

hawkes.plot_prop_excitation()

hawkes.plot_trigger_posterior(trace=False)

hawkes.plot_trigger_time_decay()

hawkes.plot_spatial()

hawkes.plot_temporal()

hawkes.run_svi(num_steps=SVI_STEPS, lr=SVI_LR, plot_loss=True)
hawkes.save_rslts(f"{OUTPUT_DIR}/hawkes_svi.pkl")

hawkes.expected_AIC()

hawkes.plot_prop_excitation()

hawkes.plot_trigger_posterior(trace=False)

hawkes.plot_spatial()

hawkes.plot_temporal()





print("\n=== Loading Results and Calculating Expected AICs ===")

# Hawkes (MCMC)
hawkes.load_rslts(f"{OUTPUT_DIR}/hawkes_mcmc.pkl")
hawkes_MCMC_aic = hawkes.expected_AIC()
print("Expected AIC (Hawkes MCMC):", hawkes_MCMC_aic)

# Hawkes (SVI)
hawkes.load_rslts(f"{OUTPUT_DIR}/hawkes_svi.pkl")
hawkes_SVI_aic = hawkes.expected_AIC()
print("Expected AIC (Hawkes SVI:", hawkes_SVI_aic)

# LGCP_cov (SVI)
lgcp_cov.load_rslts(f"{OUTPUT_DIR}/lgcp_cov_svi.pkl")
lgcp_cov_svi_aic = lgcp_cov.expected_AIC()
print("Expected AIC (LGCP_cov SVI):", lgcp_cov_svi_aic)

# LGCP_cov (MCMC)
lgcp_cov.load_rslts(f"{OUTPUT_DIR}/lgcp_cov_mcmc.pkl")
lgcp_cov_mcmc_aic = lgcp_cov.expected_AIC()
print("Expected AIC (LGCP_cov MCMC):", lgcp_cov_mcmc_aic)


# Cox-Hawkes_cov (SVI)
coxhawkes_cov.load_rslts(f"{OUTPUT_DIR}/coxhawkes_cov_svi.pkl")
coxhawkes_cov_svi_aic = coxhawkes_cov.expected_AIC()
print("Expected AIC (Cox-Hawkes_cov SVI):", coxhawkes_cov_svi_aic)

# Cox-Hawkes_cov (MCMC)
coxhawkes_cov.load_rslts(f"{OUTPUT_DIR}/coxhawkes_cov_mcmc.pkl")
coxhawkes_cov_mcmc_aic = coxhawkes_cov.expected_AIC()
print("Expected AIC (Cox-Hawkes_cov MCMC):", coxhawkes_cov_mcmc_aic)

# -------------------------------
# Comparison + Best Model
# -------------------------------

print("\n=== Model Comparison (Expected AIC) ===")
model_aics = {
    "Hawkes (MCMC)": hawkes_MCMC_aic,
     "Hawkes (SVI)": hawkes_SVI_aic,
    "LGCP_cov (SVI)": lgcp_cov_svi_aic,
    "LGCP_cov (MCMC)": lgcp_cov_mcmc_aic,
    "Cox-Hawkes_cov (SVI)": coxhawkes_cov_svi_aic,
    "Cox-Hawkes_cov (MCMC)": coxhawkes_cov_mcmc_aic
}

# Sort models by AIC
sorted_aic = sorted(model_aics.items(), key=lambda x: x[1])

# Print nicely
for model_name, aic in sorted_aic:
    print(f"{model_name}: Expected AIC = {aic:.2f}")

# Best model
best_model = sorted_aic[0]
print(f"\nBest model based on Expected AIC: {best_model[0]} (AIC = {best_model[1]:.2f})")


# Bayesian Analysis of Spatio-Temporal Point Processes

This repository contains all the code and datasets used in the thesis "Bayesian Analysis of Spatio-Temporal Point Processes". The work focuses on implementing and comparing three models: the Log-Gaussian Cox Process (LGCP), the Hawkes Process, and the Cox-Hawkes Process, using real-world datasets from the COVID-19 outbreak in London and the Ebola epidemic in Sierra Leone.

## Repository Contents

- `final_london_covid_bstpp_analysis.py`: Full modeling pipeline using the `bstpp` package
- `london_covid_descriptive_analysis.py`: Code for descriptive spatial-temporal analysis and visualization
- `data/`: Contains preprocessed event and covariate datasets for both COVID-19 and Ebola case studies
- `notebooks/`: Jupyter Notebooks for model exploration and result interpretation

## 🧠 Models Implemented

- **Log-Gaussian Cox Process (LGCP)**  
  Captures latent spatial and temporal intensity through Gaussian processes

- **Hawkes Process**  
  Models self-exciting events through triggering kernels without a background component

- **Cox-Hawkes Process**  
  Combines latent background effects with event-based self-excitation for greater flexibility


## 🧰 Tools and Libraries

- [`bstpp`](https://github.com/imanring/BSTPP): Core package used for Bayesian inference in STPP models  
- `PyTorch`, `ArviZ`, `Matplotlib`, `Seaborn`, `GeoPandas`, `Numpy`, and `Pandas` for computation and visualization

## 📊 Datasets

- **COVID-19 Events in London**: Includes case times, coordinates, and district-level covariates
- **Ebola Incidence in Sierra Leone**: Temporal-spatial dataset used to demonstrate model transferability


## 📜 Citation

If you use this code, please cite the original `bstpp` package:

> Isaac Manring et al. (2025). *BSTPP: Bayesian Spatio-Temporal Point Process Modeling*. GitHub: [https://github.com/imanring/BSTPP](https://github.com/imanring/BSTPP)

---


## 📫 Contact

For questions about this repository or the thesis, feel free to reach out via GitHub Issues or email.


#!/usr/bin/env python
"""Photometric redshifts with Gaussian processes, on real SDSS galaxies.

Pull ugriz photometry plus spectroscopic redshift from SDSS, train an exact GP
on colors, and predict redshift with calibrated error bars. Evaluate with the
standard photo-z metrics and a PIT histogram.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from astroquery.sdss import SDSS
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import (ConstantKernel, Matern,
                                              WhiteKernel)

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# data: SDSS galaxies with clean photometry and a reliable spectroscopic z
# ---------------------------------------------------------------------------
QUERY = """
SELECT TOP 12000 modelMag_u, modelMag_g, modelMag_r, modelMag_i, modelMag_z, z
FROM SpecPhoto
WHERE class='GALAXY' AND zWarning=0 AND z BETWEEN 0.02 AND 0.35
AND modelMag_r BETWEEN 14 AND 19
"""
print("[photoz] querying SDSS ...")
tab = SDSS.query_sql(QUERY, timeout=300)
m = np.vstack([tab[f"modelMag_{b}"] for b in "ugriz"]).T.astype(float)
zspec = np.asarray(tab["z"], float)

# drop rows with bad magnitudes
good = np.all(np.isfinite(m), axis=1) & np.all(m > 10, axis=1) & np.all(m < 30, axis=1)
m, zspec = m[good], zspec[good]
print(f"[photoz] {len(zspec)} clean galaxies")

# features: four colors plus the r-band magnitude (a rough distance proxy)
colors = np.column_stack([m[:, 0] - m[:, 1],   # u-g
                          m[:, 1] - m[:, 2],   # g-r
                          m[:, 2] - m[:, 3],   # r-i
                          m[:, 3] - m[:, 4],   # i-z
                          m[:, 2]])            # r

# ---------------------------------------------------------------------------
# split: exact GP is O(n^3), so train on a subsample, test on the rest
# ---------------------------------------------------------------------------
idx = rng.permutation(len(zspec))
n_train = 1200
tr, te = idx[:n_train], idx[n_train:n_train + 4000]

scaler = StandardScaler().fit(colors[tr])
Xtr, Xte = scaler.transform(colors[tr]), scaler.transform(colors[te])
ytr, yte = zspec[tr], zspec[te]

kernel = (ConstantKernel(1.0) * Matern(length_scale=np.ones(Xtr.shape[1]), nu=1.5)
          + WhiteKernel(noise_level=1e-3))
gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=1)
print("[photoz] fitting GP ...")
gp.fit(Xtr, ytr)
print("[photoz] learned kernel:", gp.kernel_)

mu, sigma = gp.predict(Xte, return_std=True)

# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
dz = (mu - yte) / (1 + yte)
bias = np.mean(dz)
nmad = 1.4826 * np.median(np.abs(dz - np.median(dz)))
outlier = np.mean(np.abs(dz) > 0.15)
print(f"[photoz] bias        = {bias:+.4f}")
print(f"[photoz] sigma_NMAD  = {nmad:.4f}")
print(f"[photoz] outlier frac= {outlier:.3%}")

# PIT: if the predictive Gaussian is calibrated, these are uniform on [0,1]
pit = norm.cdf((yte - mu) / sigma)

# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 6))
hb = ax.hexbin(yte, mu, gridsize=45, bins="log", cmap="viridis", mincnt=1)
ax.plot([0, 0.35], [0, 0.35], "r--", lw=1)
ax.set_xlim(0.02, 0.35)
ax.set_ylim(0.02, 0.35)
ax.set_aspect("equal")
ax.set_xlabel("spectroscopic z")
ax.set_ylabel("photometric z (GP mean)")
ax.set_title("SDSS photo-z with a Gaussian process")
ax.text(0.04, 0.31,
        f"bias = {bias:+.4f}\nsigma_NMAD = {nmad:.4f}\noutliers = {outlier:.1%}",
        fontsize=9, va="top",
        bbox=dict(boxstyle="round", fc="white", alpha=0.8))
fig.colorbar(hb, ax=ax, label="log count")
fig.tight_layout()
fig.savefig("uploads/2026/06/photoz-gp-scatter.png", dpi=130)
print("[photoz] saved uploads/2026/06/photoz-gp-scatter.png")

fig2, ax2 = plt.subplots(figsize=(6.5, 4))
ax2.hist(pit, bins=20, range=(0, 1), color="#1e88e5",
         edgecolor="white", density=True)
ax2.axhline(1.0, color="r", ls="--", label="calibrated (uniform)")
ax2.set_xlabel("PIT = Phi((z_spec - mu) / sigma)")
ax2.set_ylabel("density")
ax2.set_title("PIT histogram: are the GP error bars honest?")
ax2.legend()
fig2.tight_layout()
fig2.savefig("uploads/2026/06/photoz-gp-pit.png", dpi=130)
print("[photoz] saved uploads/2026/06/photoz-gp-pit.png")

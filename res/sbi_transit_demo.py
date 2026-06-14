#!/usr/bin/env python
"""Simulation-based inference for exoplanet transits.

Train a neural posterior on synthetic Mandel-Agol transits with sbi, recover
parameters of a held-out transit, and check calibration with simulation-based
calibration (SBC).
"""
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import batman
from sbi.inference import NPE
from sbi.neural_nets import posterior_nn
from sbi.utils import BoxUniform
from sbi.analysis import pairplot

torch.manual_seed(0)
np.random.seed(0)

# ---------------------------------------------------------------------------
# simulator: a single transit, 4 free parameters
#   theta = [rp/rs, a/rs, b (impact param), t0]
# limb darkening and period are fixed and known.
# ---------------------------------------------------------------------------
N_TIME = 200
T = np.linspace(-0.15, 0.15, N_TIME)
PERIOD = 5.0
U_LD = [0.3, 0.2]
NOISE = 7e-4
LABELS = ["rp/rs", "a/rs", "b", "t0"]

_pm = batman.TransitParams()
_pm.per = PERIOD
_pm.ecc = 0.0
_pm.w = 90.0
_pm.limb_dark = "quadratic"
_pm.u = U_LD


def simulate_one(theta):
    rp, a, b, t0 = [float(v) for v in theta]
    _pm.rp = rp
    _pm.a = a
    _pm.t0 = t0
    _pm.inc = np.degrees(np.arccos(np.clip(b / a, 0, 1)))
    m = batman.TransitModel(_pm, T)
    flux = m.light_curve(_pm)
    flux = flux + np.random.normal(0, NOISE, N_TIME)
    return flux.astype(np.float32)


def simulator(theta_batch):
    theta_batch = np.atleast_2d(np.asarray(theta_batch))
    return torch.tensor(np.stack([simulate_one(t) for t in theta_batch]))


prior = BoxUniform(
    low=torch.tensor([0.05, 6.0, 0.0, -0.03]),
    high=torch.tensor([0.15, 14.0, 0.9, 0.03]),
)

# ---------------------------------------------------------------------------
# training data
# ---------------------------------------------------------------------------
N_SIM = 8000
theta = prior.sample((N_SIM,))
print(f"[sbi] simulating {N_SIM} transits ...")
x = simulator(theta)
print(f"[sbi] x shape {tuple(x.shape)}")


# ---------------------------------------------------------------------------
# 1D CNN embedding: compress the light curve before the flow
# ---------------------------------------------------------------------------
class CNNEmbed(nn.Module):
    def __init__(self, n_time, out_dim=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Unflatten(1, (1, n_time)),
            nn.Conv1d(1, 16, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(16, 32, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Flatten(),
            nn.LazyLinear(out_dim), nn.ReLU(),
        )

    def forward(self, x):
        return self.net(x)


density_estimator = posterior_nn(model="nsf", embedding_net=CNNEmbed(N_TIME))
inference = NPE(prior=prior, density_estimator=density_estimator)
inference.append_simulations(theta, x)
print("[sbi] training neural posterior ...")
inference.train()
posterior = inference.build_posterior()

# ---------------------------------------------------------------------------
# inference on a held-out transit
# ---------------------------------------------------------------------------
theta_true = torch.tensor([0.10, 10.0, 0.3, 0.0])
x_obs = simulator(theta_true.unsqueeze(0))[0]
samples = posterior.sample((20000,), x=x_obs)

med = samples.median(0).values
lo = samples.quantile(0.16, 0)
hi = samples.quantile(0.84, 0)
print("[sbi] parameter recovery (truth -> median [16-84%]):")
for i, name in enumerate(LABELS):
    print(f"  {name:6s} {theta_true[i]:+.4f} -> {med[i]:+.4f} "
          f"[{lo[i]:+.4f}, {hi[i]:+.4f}]")

fig, axes = pairplot(
    samples,
    points=theta_true.unsqueeze(0),
    labels=LABELS,
    points_colors="red",
    figsize=(8, 8),
)
fig.suptitle("NPE posterior for a held-out transit (red = truth)", y=1.0)
fig.savefig("uploads/2026/06/sbi-transit-posterior.png", dpi=130, bbox_inches="tight")
print("[sbi] saved uploads/2026/06/sbi-transit-posterior.png")

# ---------------------------------------------------------------------------
# calibration: simulation-based calibration
# ---------------------------------------------------------------------------
from sbi.diagnostics import run_sbc
from sbi.analysis import sbc_rank_plot

N_SBC = 300
theta_sbc = prior.sample((N_SBC,))
x_sbc = simulator(theta_sbc)
print(f"[sbi] running SBC on {N_SBC} draws ...")
ranks, _ = run_sbc(theta_sbc, x_sbc, posterior, num_posterior_samples=1000)

f, ax = sbc_rank_plot(ranks, num_posterior_samples=1000, plot_type="hist",
                      parameter_labels=LABELS)
fig2 = f if isinstance(f, plt.Figure) else plt.gcf()
fig2.suptitle("SBC rank histograms (flat = calibrated)", y=1.02)
fig2.savefig("uploads/2026/06/sbi-transit-sbc.png", dpi=130, bbox_inches="tight")
print("[sbi] saved uploads/2026/06/sbi-transit-sbc.png")

#!/usr/bin/env python
"""Matched filtering from scratch.

Injects a known pulse into white noise, recovers it with a matched filter,
then sweeps a bank of boxcar widths to show why pulse-search pipelines use a
filter bank. Produces two figures.
"""
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(20260608)

# ---------------------------------------------------------------------------
# core
# ---------------------------------------------------------------------------
def matched_filter(x, template):
    """Correlate x with a unit-energy, time-reversed template.

    np.correlate already does the time reversal, so we just normalize the
    template to unit energy. With white noise of variance sigma^2 the output
    at the true location has expected SNR = ||s|| / sigma.
    """
    t = template / np.linalg.norm(template)
    return np.correlate(x, t, mode="same")


def gaussian_pulse(width, n=64):
    t = np.arange(n) - n / 2
    p = np.exp(-0.5 * (t / width) ** 2)
    return p / p.max()


# ---------------------------------------------------------------------------
# figure 1: detection of a single pulse buried in noise
# ---------------------------------------------------------------------------
N = 4000
sigma = 1.0
amp = 1.2                 # peak amplitude -- comparable to the noise sigma
true_width = 6.0
loc = 2600               # sample index where the pulse is injected

pulse = amp * gaussian_pulse(true_width, n=64)
x = rng.normal(0, sigma, N)
x[loc - 32:loc + 32] += pulse

template = gaussian_pulse(true_width, n=64)
y = matched_filter(x, template)

# theoretical noise level at the filter output is sigma (template is unit energy)
snr = y / sigma
peak = int(np.argmax(snr))

print(f"[fig1] injected at {loc}, detected at {peak} (off by {peak - loc})")
print(f"[fig1] peak SNR = {snr[peak]:.2f}")

fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
ax[0].plot(x, lw=0.6, color="#444")
ax[0].axvspan(loc - 32, loc + 32, color="#ff7043", alpha=0.25)
ax[0].set_title("Raw signal: a pulse hidden in white noise (orange = true location)")
ax[0].set_ylabel("amplitude")

tt = np.arange(64) + loc - 32
ax[1].plot(tt, template, color="#1e88e5")
ax[1].set_title("Matched template (the known pulse shape)")
ax[1].set_ylabel("amplitude")

ax[2].plot(snr, lw=0.8, color="#444")
ax[2].axhline(0, color="k", lw=0.5)
ax[2].plot(peak, snr[peak], "o", color="#e53935")
ax[2].annotate(f"SNR = {snr[peak]:.1f}", (peak, snr[peak]),
               textcoords="offset points", xytext=(10, -4), color="#e53935")
ax[2].set_title("Matched filter output (SNR units): the pulse pops out")
ax[2].set_ylabel("SNR")
ax[2].set_xlabel("sample")
fig.tight_layout()
fig.savefig("uploads/2026/06/matched-filter-detection.png", dpi=130)
print("[fig1] saved uploads/2026/06/matched-filter-detection.png")

# ---------------------------------------------------------------------------
# figure 2: boxcar filter bank -- the pulse width is unknown in practice
# ---------------------------------------------------------------------------
# a real single-pulse search does not know the pulse width, so it runs a bank
# of boxcar matched filters and keeps the width that maximizes SNR.
widths = np.arange(1, 41)
recovered_snr = []
for w in widths:
    boxcar = np.ones(w)
    yb = matched_filter(x, boxcar)
    recovered_snr.append(np.max(yb) / sigma)
recovered_snr = np.array(recovered_snr)
best_w = widths[int(np.argmax(recovered_snr))]

# the gaussian pulse has an effective width ~ sqrt(2*pi)*true_width samples
eff_width = np.sqrt(2 * np.pi) * true_width
print(f"[fig2] best boxcar width = {best_w}, effective pulse width ~ {eff_width:.1f}")

fig2, ax2 = plt.subplots(figsize=(8, 4.5))
ax2.plot(widths, recovered_snr, "-o", ms=3, color="#1e88e5")
ax2.axvline(eff_width, color="#e53935", ls="--",
            label=f"effective pulse width ~ {eff_width:.0f}")
ax2.plot(best_w, recovered_snr.max(), "o", color="#e53935", ms=8)
ax2.set_xlabel("boxcar width (samples)")
ax2.set_ylabel("recovered SNR")
ax2.set_title("Boxcar filter bank: SNR peaks near the true pulse width")
ax2.legend()
fig2.tight_layout()
fig2.savefig("uploads/2026/06/matched-filter-boxcar-bank.png", dpi=130)
print("[fig2] saved uploads/2026/06/matched-filter-boxcar-bank.png")

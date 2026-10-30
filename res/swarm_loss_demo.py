#!/usr/bin/env python3
"""Small, reproducible check of the threat-level swarm loss.

The trainable parameters in this demonstration are assignment logits, not a
full GNN.  This isolates the loss function: softmax turns each interceptor's
logits into one-target probabilities, and gradient descent minimizes the
expected number of surviving threats.
"""

import argparse
import itertools
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


KILL = np.array(
    [
        [0.95, 0.80, 0.15, 0.10, 0.10],
        [0.94, 0.78, 0.20, 0.10, 0.10],
        [0.93, 0.15, 0.76, 0.10, 0.10],
        [0.92, 0.10, 0.10, 0.74, 0.20],
        [0.91, 0.10, 0.10, 0.20, 0.72],
    ],
    dtype=np.float64,
)


def softmax(logits, temperature=1.0):
    scaled = logits / temperature
    scaled -= scaled.max(axis=1, keepdims=True)
    exp = np.exp(scaled)
    return exp / exp.sum(axis=1, keepdims=True)


def expected_destroyed(probabilities, kill=KILL):
    """Expected number of distinct threats killed (option C)."""
    survival = np.prod(1.0 - probabilities * kill, axis=0)
    return float(np.sum(1.0 - survival))


def train(steps=1600, learning_rate=0.35, seed=7):
    rng = np.random.default_rng(seed)
    logits = 0.01 * rng.standard_normal(KILL.shape)
    history = []

    for step in range(steps):
        # Annealing makes the soft training decision approach deployed argmax.
        temperature = max(0.18, 1.2 * (0.9975**step))
        p = softmax(logits, temperature)
        miss = np.clip(1.0 - p * KILL, 1e-12, 1.0)
        survival = np.prod(miss, axis=0)
        loss = float(survival.sum())
        history.append(loss)

        # d(sum_j prod_i(1-p_ij*k_ij)) / dp_ij
        dloss_dp = -KILL * survival[np.newaxis, :] / miss

        # Row-wise softmax Jacobian-vector product, including temperature.
        row_average = np.sum(p * dloss_dp, axis=1, keepdims=True)
        dloss_dz = p * (dloss_dp - row_average) / temperature
        logits -= learning_rate * dloss_dz

    return logits, np.asarray(history)


def hard_matrix(assignment):
    p = np.zeros_like(KILL)
    p[np.arange(KILL.shape[0]), assignment] = 1.0
    return p


def exhaustive_optimum():
    best_assignment = None
    best_score = -np.inf
    for assignment in itertools.product(range(KILL.shape[1]), repeat=KILL.shape[0]):
        score = expected_destroyed(hard_matrix(np.asarray(assignment)))
        if score > best_score:
            best_score = score
            best_assignment = np.asarray(assignment)
    return best_assignment, best_score


def monte_carlo(assignment, trials=200_000, seed=11):
    rng = np.random.default_rng(seed)
    p = hard_matrix(assignment)
    successes = rng.random((trials,) + KILL.shape) < (p * KILL)
    killed = successes.any(axis=1).sum(axis=1)
    return float(killed.mean()), float(killed.std(ddof=1) / np.sqrt(trials))


def quantized_assignment(logits):
    """Symmetric int8 quantization, sufficient for the deployed argmax here."""
    scale = np.max(np.abs(logits)) / 127.0
    q = np.clip(np.rint(logits / scale), -127, 127).astype(np.int8)
    return q.argmax(axis=1), float(scale)


def make_plot(history, scores, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    ax1.plot(history, color="#49a6d8", linewidth=2)
    ax1.set_xlabel("gradient step")
    ax1.set_ylabel("expected surviving threats")
    ax1.set_title("Training objective")
    ax1.grid(alpha=0.25)

    names = list(scores)
    values = [scores[name] for name in names]
    bars = ax2.bar(names, values, color=["#cf6679", "#49a6d8", "#8bc34a"])
    ax2.set_ylim(0, KILL.shape[1])
    ax2.set_ylabel("expected distinct threats destroyed")
    ax2.set_title("Hard assignment after training")
    ax2.tick_params(axis="x", rotation=12)
    for bar, value in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(output, dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", type=Path, default=Path("swarm-threat-loss.png"))
    parser.add_argument("--json", type=Path, default=Path("/tmp/swarm-threat-loss.json"))
    args = parser.parse_args()

    logits, history = train()
    learned = logits.argmax(axis=1)
    per_interceptor = KILL.argmax(axis=1)  # option D as independent hard decisions
    optimum, optimum_score = exhaustive_optimum()
    quantized, quant_scale = quantized_assignment(logits)

    scores = {
        "per-interceptor": expected_destroyed(hard_matrix(per_interceptor)),
        "trained threat loss": expected_destroyed(hard_matrix(learned)),
        "exhaustive optimum": optimum_score,
    }
    mc_mean, mc_se = monte_carlo(learned)
    result = {
        "kill_matrix": KILL.tolist(),
        "per_interceptor_assignment_zero_based": per_interceptor.tolist(),
        "trained_assignment_zero_based": learned.tolist(),
        "exhaustive_assignment_zero_based": optimum.tolist(),
        "int8_assignment_zero_based": quantized.tolist(),
        "int8_scale": quant_scale,
        "expected_destroyed": scores,
        "training_loss": {"start": float(history[0]), "end": float(history[-1])},
        "monte_carlo": {"mean_destroyed": mc_mean, "standard_error": mc_se, "trials": 200_000},
        "trained_matches_exhaustive_score": bool(np.isclose(scores["trained threat loss"], optimum_score)),
        "int8_preserves_assignment": bool(np.array_equal(learned, quantized)),
    }

    make_plot(history, scores, args.plot)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

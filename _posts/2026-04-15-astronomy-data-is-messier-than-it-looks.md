---
title: "Astronomy Data Is Messier Than It Looks"
date: 2026-04-15 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/04/15/astronomy-data-is-messier-than-it-looks/
categories:
  - en-US
tags:
  - astronomy
  - data
  - machine-learning
  - python
  - comp
---

An astronomy catalog looks like the ideal machine-learning dataset. It has millions of rows, numeric columns and measurements produced by calibrated instruments. I loaded one into pandas, removed null values, trained a model and got a score that looked much better than it deserved.

That workflow can produce a model that is statistically impressive and scientifically wrong.

Astronomy data carries units, coordinate frames, observation epochs, quality flags, upper limits, repeated observations, survey selection effects and correlated uncertainties. Most of those did not fit naturally into the rectangular arrays I was using, so I wrote down how I handled them in one of my catalog experiments.

## A row is not necessarily an independent object

Before transforming the data, I identified what one row meant.

It might be:

- one astrophysical source
- one observation of a source
- one detector exposure
- one wavelength bin
- one candidate produced by a pipeline
- one cross-match pair

If the same source appears in several rows, a random train/test split leaks information. The model sees one observation of a star during training and another observation of the same star during testing. The reported score measures recognition of known objects, not generalization to new ones.

I started with an explicit data contract:

```python
DATA_CONTRACT = {
    "row_unit": "one observation of one source",
    "object_key": "source_id",
    "observation_key": "observation_id",
    "label": "target_class",
    "prediction_scope": "new sources",
}
```

The prediction scope determines the split. If the goal is new sources, group by `source_id`. If the goal is future observations, split by time. If the goal is a new instrument or field, hold out that domain.

## Preserve units from the first read

These columns are not interchangeable:

```text
frequency = 1420 MHz
frequency = 1420 Hz
parallax = 2 mas
parallax = 2 arcsec
```

I kept Astropy quantities while calculations crossed unit boundaries:

```python
import astropy.units as u

frequency = 1420.405751 * u.MHz
bandwidth = 2.5 * u.MHz
integration = 10.0 * u.s

channel_resolution = bandwidth / 4096

print(channel_resolution.to(u.kHz))
```

Units are executable documentation. A conversion error becomes an exception or an explicit `.to(...)`, not a silent factor of one thousand.

When the model finally needed a NumPy array, I chose and recorded canonical units:

```python
parallax_mas = table["parallax"].quantity.to_value(u.mas)
frequency_mhz = table["frequency"].quantity.to_value(u.MHz)
```

I only stripped units at the NumPy boundary. Before that, relying on a column name to remain accurate through several transformations was too easy to get wrong.

## Missing, masked and censored are different

Astronomy tables use several kinds of absent information:

- no measurement was attempted
- the pipeline failed
- the source was outside the footprint
- the value is below a detection limit
- the value was measured but rejected by a quality flag

These cases have different meanings.

I inspected Astropy masks before converting to pandas:

```python
import numpy as np

column = table["parallax"]

print(f"rows: {len(column)}")
print(f"masked: {np.count_nonzero(column.mask)}")
print(f"finite: {np.count_nonzero(np.isfinite(column.filled(np.nan)))}")
```

An upper limit is not an ordinary missing value. If a radio source has flux `< 0.2 mJy`, replacing it with the mean discards useful information and falsely treats the limit as a symmetric measurement.

A simple representation can keep both value and status:

```python
flux_value = np.asarray(table["flux"].filled(np.nan), dtype=float)
flux_detected = np.asarray(table["flux_detected"], dtype=np.int8)
flux_upper_limit = np.asarray(table["flux_upper_limit"], dtype=float)
```

For rigorous population analysis, use a likelihood that handles censoring. For a baseline classifier, at least preserve a detection flag so the model can distinguish a measured value from an imputed one.

## Quality flags are part of the measurement

A catalog value can be numeric and still be unreliable. Survey pipelines usually publish flags for saturation, blending, edge effects, astrometric quality, cosmic rays or fitting failures.

Make quality cuts explicit and count every step:

```python
selection_log = []


def record_cut(name, mask):
    selection_log.append({
        "cut": name,
        "kept": int(np.count_nonzero(mask)),
        "rejected": int(len(mask) - np.count_nonzero(mask)),
    })


finite = np.isfinite(df["parallax"])
record_cut("finite parallax", finite)

good_ruwe = df["ruwe"] < 1.4
record_cut("ruwe < 1.4", finite & good_ruwe)

clean = df[finite & good_ruwe].copy()
```

The exact RUWE threshold depended on the analysis. I kept the threshold in code, output counts and methodology instead of leaving it in a notebook cell that had been run once.

I did not remove every flagged row by reflex. A strict quality cut changed the population in the table; saturation flags, for example, preferentially removed bright nearby stars.

## Uncertainty is a column, not decoration

One comparison contained two parallaxes with the same `1 mas` value:

```text
1.0 +/- 0.02 mas
1.0 +/- 0.80 mas
```

I did not want them to have the same influence on a physical inference.

For the baseline, I included uncertainty-aware features:

```python
df["parallax_snr"] = df["parallax"] / df["parallax_error"]
df["flux_fractional_error"] = df["flux_error"] / df["flux"]
```

Be careful with ratios near zero. Clip or mask using a scientifically justified rule:

```python
valid_flux = (
    np.isfinite(df["flux"])
    & np.isfinite(df["flux_error"])
    & (df["flux"] > 0)
)

df.loc[valid_flux, "flux_fractional_error"] = (
    df.loc[valid_flux, "flux_error"]
    / df.loc[valid_flux, "flux"]
)
```

For regression, uncertainty can enter the loss as a sample weight. That is only correct when the weighting matches the assumed noise model. `1/sigma^2` is not a magic setting for every problem.

## Flux, magnitude and logarithms

Magnitudes are logarithmic. Averaging magnitudes is not the same as averaging fluxes. A color such as `BP-RP` is a difference of magnitudes and corresponds to a flux ratio.

I kept the physical representation explicit:

```python
def magnitude_to_relative_flux(magnitude):
    return 10.0 ** (-0.4 * magnitude)


g_flux_relative = magnitude_to_relative_flux(df["phot_g_mean_mag"])
```

For quantities involving additive energy, I worked in flux. Where the catalog's photometric system was the relevant representation, I retained magnitudes and recorded that choice.

Log transforms need a policy for zero and negative values:

```python
positive = df["flux"] > 0
df.loc[positive, "log10_flux"] = np.log10(df.loc[positive, "flux"])
```

I avoided an arbitrary epsilon because it created a visible pile-up that the model could learn as a class marker.

## Coordinates have frames and epochs

RA and Dec alone did not fully define my position comparison. I also needed the frame and epoch.

```python
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

gaia_coord = SkyCoord(
    ra=df["ra"].to_numpy() * u.deg,
    dec=df["dec"].to_numpy() * u.deg,
    pm_ra_cosdec=df["pmra"].to_numpy() * u.mas / u.yr,
    pm_dec=df["pmdec"].to_numpy() * u.mas / u.yr,
    obstime=Time("J2016.0"),
    frame="icrs",
)

coord_2025 = gaia_coord.apply_space_motion(
    new_obstime=Time("J2025.0")
)
```

This matters in cross-matching, especially for nearby high-proper-motion stars. A fixed one-arcsecond threshold can reject the correct counterpart or choose the wrong nearby source if epochs are ignored.

## Cross-match uncertainty enters the label

If labels come from one catalog and features from another, a bad match becomes label noise.

I kept match metadata in the training table:

```python
training["match_separation_arcsec"] = separation_arcsec
training["match_candidate_count"] = candidate_count
training["match_is_mutual"] = mutual_match
```

I then ran sensitivity tests:

```python
for limit in [0.25, 0.5, 1.0, 2.0]:
    subset = training[training["match_separation_arcsec"] <= limit]
    print(limit, len(subset), subset["target_class"].value_counts().to_dict())
```

Model performance changed with match radius, so I treated the cross-match as part of the uncertainty budget.

## The most common leakage: fitting preprocessing globally

My first preprocessing attempt was wrong:

```python
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)
```

The scaler has already seen test-set means and standard deviations.

I split first and kept preprocessing inside a pipeline:

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

model = Pipeline([
    ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(max_iter=2000)),
])

model.fit(X_train, y_train)
```

Every learned preprocessing step stays inside the pipeline and is fitted only on training data.

## Split by source, observation or time

For repeated observations, use grouped splitting:

```python
from sklearn.model_selection import GroupShuffleSplit

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.2,
    random_state=42,
)

train_index, test_index = next(
    splitter.split(X, y, groups=df["source_id"])
)

X_train = X[train_index]
X_test = X[test_index]
y_train = y[train_index]
y_test = y[test_index]
```

Verify the groups really are separate:

```python
train_sources = set(df.iloc[train_index]["source_id"])
test_sources = set(df.iloc[test_index]["source_id"])

assert train_sources.isdisjoint(test_sources)
```

For time-domain astronomy, a chronological split can be more honest:

```python
train = df[df["observation_time"] < "2025-01-01"]
test = df[df["observation_time"] >= "2025-01-01"]
```

This tests whether the model survives instrument drift, seasonal conditions and a changing RFI environment.

## Selection bias: the catalog is not the sky

A survey detects sources through a selection function. Faint objects are missing more often. Spectroscopic labels tend to exist for bright or scientifically interesting targets. A model trained on that labeled subset learns the subset.

I compared the labeled and unlabeled populations:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(
    df.loc[df["has_label"], "magnitude"],
    bins=40,
    histtype="step",
    density=True,
    label="labeled",
)
ax.hist(
    df.loc[~df["has_label"], "magnitude"],
    bins=40,
    histtype="step",
    density=True,
    label="unlabeled",
)
ax.set_xlabel("magnitude")
ax.set_ylabel("density")
ax.legend()
fig.tight_layout()
```

I repeated the comparison for sky position, color, S/N and observing program. The classifier could be accurate on the labeled test set and still unreliable on the unlabeled survey population because the two distributions differed.

## Class imbalance changes the question

In a heavily imbalanced case where 99.9% of events were RFI, a classifier that always predicted RFI had 99.9% accuracy and zero scientific value.

Report metrics connected to the use case:

```python
from sklearn.metrics import classification_report

print(classification_report(y_test, prediction, digits=3))
```

For rare-event searches, inspect:

- recall of the rare class
- precision among selected candidates
- false positives per observing hour
- performance as a function of S/N
- calibration of predicted probabilities
- the number of candidates a human must inspect

The operating threshold is part of the result.

## Duplicates can cross the split without sharing an ID

Catalogs may contain duplicate detections, blended components or the same physical source under different identifiers. Check coordinate neighborhoods and feature similarity.

For image or spectrum cutouts, hash exact duplicates:

```python
import hashlib


def array_hash(array):
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.tobytes()).hexdigest()
```

Exact hashes do not catch reprocessed or slightly shifted copies. Grouping by sky position, observation block or parent source is usually stronger.

## The provenance I saved

I saved the query and configuration beside the dataset:

```python
import json
from datetime import datetime, timezone

provenance = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "service": "Gaia TAP",
    "table": "gaiadr3.gaia_source",
    "query_file": "queries/training_sample.adql",
    "coordinate_frame": "ICRS",
    "coordinate_epoch": "J2016.0",
    "quality_cuts": [
        "parallax IS NOT NULL",
        "ruwe < 1.4",
    ],
    "random_seed": 42,
}

with open("training_sample.provenance.json", "w") as handle:
    json.dump(provenance, handle, indent=2)
```

Also record package versions:

```bash
python -m pip freeze > requirements-lock.txt
```

For the remote archive, I stored the exact ADQL, retrieval date and result checksum. The archive could change even when my code did not.

## The data audit I ran before modeling

```python
def audit_table(df, object_key, label):
    report = {
        "rows": len(df),
        "objects": df[object_key].nunique(),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_fraction": df.isna().mean().sort_values(ascending=False),
        "class_counts": df[label].value_counts(dropna=False),
    }
    return report


audit = audit_table(df, "source_id", "target_class")

print("rows", audit["rows"])
print("objects", audit["objects"])
print("duplicates", audit["duplicate_rows"])
print(audit["class_counts"])
print(audit["missing_fraction"].head(10))
```

Extend the audit with:

- unit checks
- allowed ranges
- flag distributions
- observations per object
- coordinate footprint
- time coverage
- label source
- cross-match separation
- train/test group overlap

I ran the audit every time I rebuilt the dataset.

## A defensible end-to-end skeleton

```python
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

FEATURES = [
    "phot_g_mean_mag",
    "bp_rp",
    "parallax_snr",
    "ruwe",
]

eligible = (
    df["target_class"].notna()
    & df["source_id"].notna()
)

sample = df.loc[eligible].copy()
X = sample[FEATURES].to_numpy(dtype=np.float64)
y = sample["target_class"].to_numpy()
groups = sample["source_id"].to_numpy()

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.2,
    random_state=42,
)
train_idx, test_idx = next(splitter.split(X, y, groups))

model = Pipeline([
    ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    )),
])

model.fit(X[train_idx], y[train_idx])
prediction = model.predict(X[test_idx])

print(classification_report(y[test_idx], prediction, digits=3))

assert set(groups[train_idx]).isdisjoint(set(groups[test_idx]))
```

The code is intentionally ordinary. A clean baseline with a correct split is more valuable than a sophisticated network trained on leaked or misinterpreted data.

Data cleaning is not the stage before science. It is where many scientific assumptions enter the analysis. A model cannot repair a wrong cross-match, an inconsistent unit or a leaked split. It will learn them efficiently and return a confident answer.

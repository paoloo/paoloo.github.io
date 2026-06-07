---
title: "Training an Astronomy Model from Scratch"
date: 2026-06-07 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/07/training-an-astronomy-model-from-scratch/
categories:
  - en-US
tags:
  - python
  - machine-learning
  - astronomy
  - comp
---

In the previous post, [Classifying Asteroids with CyberEther]({{ site.baseurl }}/2026/06/06/classifying-asteroids-with-cyberether/), I showed a live CyberEther flowgraph running an ONNX model on Gaia asteroid spectra. That post focused on the system: TAP input, inference, slices and plots.

This post is about the part that happens before that: training the model from scratch.

By "from scratch", I do not mean writing backpropagation by hand. I mean starting with public astronomy catalogs, downloading the data, building a labeled dataset, training a model, exporting it, and checking that the exported model works. That is the workflow students need to understand before they start worrying about bigger neural networks.

The example comes from:

```text
~/Workspace/SETI/cyberether-inference/scripts/train_asteroid_classifier.py
```

The goal is simple: train a classifier that receives a 16-point asteroid reflectance spectrum from Gaia DR3 and predicts a broad Bus-DeMeo taxonomic complex:

- `C`: carbonaceous types
- `S`: silicate-rich types
- `X`: metallic or primitive types
- `O`: other or rare types

We will build the whole thing in Python.

## The plan

The script follows this pipeline:

```text
Gaia DR3 asteroid spectra
        +
VizieR Bus-DeMeo taxonomy labels
        |
        v
cross-match by asteroid number
        |
        v
16-feature training matrix
        |
        v
StandardScaler + MLPClassifier
        |
        v
ONNX model
```

This is a useful pattern for many astronomy ML projects:

1. Find a large catalog with measurements.
2. Find a smaller catalog with labels.
3. Cross-match them.
4. Clean the data.
5. Train a model.
6. Export the model so another program can run it.

The labels are the scarce part. Gaia has many asteroid spectra. The taxonomy catalog has far fewer labeled asteroids. Most real astronomy ML projects look like this.

## Imports and paths

First we import the standard library modules and NumPy:

```python
#!/usr/bin/env python3

import sys
import pathlib
import urllib.parse
import urllib.request

import numpy as np
```

`urllib` is enough here because TAP queries are just HTTP requests. For a larger project I would probably use `pyvo` or `astroquery`, but using the standard library makes the mechanics visible.

Now we define the TAP endpoints and output path:

```python
GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

OUT_DIR = pathlib.Path(__file__).parent.parent / "resources"
OUT_ONNX = OUT_DIR / "asteroid_taxonomy.onnx"
```

There are two services:

- Gaia provides the asteroid reflectance spectra.
- VizieR provides the Bus-DeMeo taxonomy labels.

The model will be saved as `resources/asteroid_taxonomy.onnx`.

## TAP helper

TAP is the Table Access Protocol used by many astronomy archives. A TAP query sends ADQL to a remote database and gets a table back. Here we ask for CSV because it is easy to parse:

```python
def tap_query(endpoint: str, adql: str, maxrec: int = 200000) -> str:
    params = urllib.parse.urlencode({
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "MAXREC": str(maxrec),
        "QUERY": adql,
    }).encode()

    req = urllib.request.Request(endpoint, data=params)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode()
```

The important parameters are:

- `LANG=ADQL`: the query language
- `FORMAT=csv`: the output format
- `MAXREC`: the maximum number of rows
- `QUERY`: the ADQL query itself

Then we add a tiny CSV parser:

```python
def parse_csv(text: str) -> list[list[str]]:
    import csv
    import io

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    return [[c.strip() for c in row] for row in rows[1:]]
```

The first row is the header, so we skip it.

## Fetching Gaia asteroid spectra

Now we fetch the Gaia DR3 asteroid reflectance spectra:

```python
print("Fetching Gaia DR3 asteroid reflectance spectra...", flush=True)

csv = tap_query(
    GAIA_TAP,
    "SELECT source_id, wavelength, reflectance_spectrum "
    "FROM gaiadr3.sso_reflectance_spectrum "
    "ORDER BY source_id, wavelength",
    maxrec=1_100_000,
)

rows = parse_csv(csv)
print(f"  {len(rows):,} rows fetched", flush=True)
```

Each row is one wavelength measurement for one asteroid. A complete asteroid spectrum has 16 rows, one for each Gaia wavelength bin.

The query orders by `source_id, wavelength`. That matters because later we can append the values in order and get a clean 16-point vector.

Now we group the rows by Gaia `source_id`:

```python
spectra: dict[int, list[float]] = {}

for row in rows:
    if len(row) < 3 or not row[2]:
        continue

    try:
        sid = int(row[0])
        spectra.setdefault(sid, []).append(float(row[2]))
    except ValueError:
        pass
```

This creates a dictionary:

```text
source_id -> [r_0, r_1, ..., r_15]
```

Bad rows are skipped. This is normal catalog hygiene. Public catalogs are clean enough to use, but not clean enough to trust blindly.

Next we keep only complete spectra:

```python
spectra = {k: v for k, v in spectra.items() if len(v) == 16}
print(f"  {len(spectra):,} asteroids with 16-point spectra", flush=True)
```

Machine learning models expect fixed-size input. A 15-point spectrum and a 16-point spectrum cannot go into the same dense neural network without padding, masking or another representation. For this first model, we keep the clean case.

Then we build the full feature matrix:

```python
source_ids = np.array(list(spectra.keys()), dtype=np.int64)
X_all = np.array([spectra[sid] for sid in source_ids], dtype=np.float32)
```

`X_all` contains every complete Gaia spectrum, labeled or not. We will only train on the subset that has taxonomy labels, but keeping `X_all` is useful if we later want to run the model on all asteroids.

## Fetching taxonomy labels

The labels come from VizieR:

```python
print("Fetching asteroid taxonomy labels from VizieR...", flush=True)

csv_tax = tap_query(
    VIZIER_TAP,
    'SELECT "Number", "class" FROM "J/A+A/665/A26/asteroid"',
    maxrec=2000,
)

tax_rows = parse_csv(csv_tax)
```

The table contains asteroid numbers and Bus-DeMeo classes such as `S`, `C`, `Ch`, `Xk` and `V`.

Gaia uses `source_id`, while the VizieR taxonomy table uses the standard asteroid number. We need a bridge:

```python
csv_names = tap_query(
    GAIA_TAP,
    "SELECT source_id, number_mp FROM gaiadr3.sso_source ORDER BY number_mp",
    maxrec=100_000,
)

name_rows = parse_csv(csv_names)
```

`number_mp` is the minor-planet number. This lets us connect:

```text
Gaia source_id -> asteroid number -> taxonomy class
```

Now we build the mapping from Gaia source ID to asteroid number:

```python
sid_to_num: dict[int, int] = {}

for row in name_rows:
    if len(row) >= 2 and row[0] and row[1]:
        try:
            sid_to_num[int(row[0])] = int(row[1])
        except ValueError:
            pass
```

And the mapping from asteroid number to taxonomy class:

```python
tax: dict[int, str] = {}

for row in tax_rows:
    if len(row) >= 2 and row[0] and row[1]:
        try:
            tax[int(row[0])] = row[1].strip()
        except ValueError:
            pass
```

The two dictionaries are small, but they are the core of the dataset. Without this cross-match, we have spectra with no labels and labels with no spectra.

We print the counts:

```python
print(
    f"  {len(tax)} taxonomy labels, "
    f"{len(sid_to_num)} Gaia SSO source mappings",
    flush=True,
)
```

## Cross-matching spectra and labels

Now we attach a label to each Gaia spectrum when possible:

```python
labels: dict[int, str] = {}

for sid in source_ids:
    num = sid_to_num.get(int(sid))
    if num is not None:
        cls = tax.get(num)
        if cls:
            labels[int(sid)] = cls
```

This is a simple exact-ID cross-match. In other astronomy projects you may need a spatial cross-match using sky coordinates, but here the asteroid number gives us a cleaner join.

Then we check that we have enough labeled examples:

```python
print(
    f"  {len(labels)} asteroids with Bus-DeMeo labels after cross-match",
    flush=True,
)

if len(labels) < 20:
    print("ERROR: too few labeled samples for training. Check network access.")
    sys.exit(1)
```

The threshold is not a scientific rule. It is a guard against broken downloads or changed remote services. If we only got ten labels, training would run, but the result would be meaningless.

Now we build the labeled dataset:

```python
sid_list = sorted(labels.keys())
X_labeled = np.array([spectra[sid] for sid in sid_list], dtype=np.float32)
y_raw = [labels[sid] for sid in sid_list]
```

`X_labeled` is the input matrix for training. Each row has 16 numbers. `y_raw` contains the original Bus-DeMeo class strings.

## Collapsing detailed taxonomy into broad classes

Bus-DeMeo taxonomy has many classes. That is scientifically useful, but it is not ideal for a small training set. Some classes have too few examples.

So we collapse the detailed labels into four broad groups:

```python
COMPLEX = {
    "B": "C", "C": "C", "Cb": "C", "Cg": "C", "Cgh": "C", "Ch": "C",
    "S": "S", "Sa": "S", "Sq": "S", "Sr": "S", "Sv": "S",
    "Q": "S", "Qa": "S",
    "A": "S", "L": "S",
    "X": "X", "Xc": "X", "Xe": "X", "Xk": "X",
    "E": "X", "M": "X", "P": "X",
    "D": "O", "T": "O", "K": "O", "Ld": "O", "O": "O", "R": "O", "V": "O",
}

y_complex = [COMPLEX.get(c, "O") for c in y_raw]
```

This is a modeling decision. We trade detail for robustness. A model that predicts four broad classes reasonably well is more useful than a model that pretends to distinguish 25 classes with only a few samples per class.

Scikit-learn classifiers expect numeric labels, so we encode the class names:

```python
classes = sorted(set(y_complex))
class_idx = {c: i for i, c in enumerate(classes)}
y = np.array([class_idx[c] for c in y_complex], dtype=np.int64)
```

`classes` will usually be:

```python
["C", "O", "S", "X"]
```

The order matters because the ONNX model will output probabilities in this class order.

Print the distribution:

```python
print(f"  Classes: {classes}")

for c in classes:
    n = np.sum(y == class_idx[c])
    print(f"    {c}: {n}")
```

Always look at the class counts before training. If one class has 900 examples and another has 12, accuracy alone can lie to you.

## Splitting train and test data

Now we import the machine learning tools:

```python
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
```

Then we split the labeled data:

```python
X_tr, X_te, y_tr, y_te = train_test_split(
    X_labeled,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)
```

The test set is 20% of the labeled data. `random_state=42` makes the split reproducible. `stratify=y` keeps the class proportions similar in train and test.

That last part is important. If the class distribution is imbalanced, a random split can accidentally put too many rare-class examples in only one side.

## Building the model

The model is a scikit-learn pipeline:

```python
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        max_iter=500,
        random_state=42,
        early_stopping=True,
    )),
])
```

The first stage is `StandardScaler`. It subtracts the mean and divides by the standard deviation for each wavelength feature.

This matters because neural networks are sensitive to feature scaling. We want the model to learn spectral shape, not waste capacity adjusting to different numeric ranges in each wavelength bin.

The classifier is a small multilayer perceptron:

```text
16 inputs -> 64 hidden units -> 32 hidden units -> 4 class probabilities
```

This is intentionally small. The dataset has fewer labels than the full Gaia spectrum table, so a larger network would overfit more easily.

`early_stopping=True` tells scikit-learn to stop when validation performance stops improving. It is a simple guard against training too long.

## Training and evaluation

Training is just:

```python
print("\nTraining MLPClassifier...", flush=True)

pipe.fit(X_tr, y_tr)
acc = pipe.score(X_te, y_te)

print(f"  Test accuracy: {acc:.1%}  ({len(X_te)} samples)")
```

`fit()` trains both stages of the pipeline:

1. The scaler learns means and standard deviations from the training set.
2. The MLP learns weights from the scaled training data.

`score()` evaluates on the held-out test set.

For a real paper or mission workflow, I would also inspect a confusion matrix, per-class precision and recall, and examples of failed predictions. For teaching the basic pipeline, accuracy is enough to show whether the model learned anything.

## Exporting to ONNX

Training a model is not the end. If another program needs to run it, we need a portable format. For CyberEther, that format is ONNX.

First we import the ONNX converter:

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
```

Create the output directory:

```python
OUT_DIR.mkdir(parents=True, exist_ok=True)
```

Describe the model input:

```python
initial_types = [("float_input", FloatTensorType([None, 16]))]
```

This says:

- the input is named `float_input`
- the batch dimension is variable (`None`)
- each example has 16 float features

Now convert the scikit-learn pipeline:

```python
onnx_model = convert_sklearn(
    pipe,
    initial_types=initial_types,
    options={"zipmap": False},
)
```

`zipmap=False` is important. Without it, the converter may output a list of dictionaries mapping class labels to probabilities. That is convenient in Python, but awkward for a generic inference block. We want a dense tensor:

```text
[batch_size, number_of_classes]
```

By default, the exported model includes two outputs:

- `label`
- `probabilities`

CyberEther expects the probability tensor as output index 0, so we remove the label output:

```python
import onnx

graph = onnx_model.graph
label_output = next((o for o in graph.output if o.name == "label"), None)

if label_output is not None:
    graph.output.remove(label_output)
```

After this, `probabilities` becomes the first and only output.

Finally we save the model:

```python
with open(OUT_ONNX, "wb") as f:
    f.write(onnx_model.SerializeToString())

print(f"\nSaved: {OUT_ONNX}")
```

At this point we have a trained model file.

## Verifying the ONNX model

Never trust an exported model until you run it.

We use `onnxruntime`:

```python
import onnxruntime as ort

sess = ort.InferenceSession(str(OUT_ONNX))
inp = sess.get_inputs()[0]
outs = sess.get_outputs()
result = sess.run(None, {inp.name: X_te[:4]})
```

This loads the ONNX file and runs four test spectra through it.

Then we print the input and output metadata:

```python
print("\nONNX model verified:")
print(f"  inputName:  {inp.name}")
print(f"  inputShape: {inp.shape}")

for o in outs:
    print(f"  outputName: {o.name}  shape: {o.shape}")
```

Since we removed the `label` output, probabilities are in `result[0]`:

```python
probabilities = result[0]

print("  Sample probabilities (4 test asteroids):")

for i, row in enumerate(probabilities[:4]):
    pred = classes[int(np.argmax(row))]
    print(f"    asteroid {i}: {dict(zip(classes, row))}  predicted {pred}")
```

This is a sanity check. The values should look like probabilities, and each row should correspond to the class order printed at the end:

```python
print(f"\nClasses (index order): {classes}")
print("Use these names in the YAML config.")
```

If the model output has the wrong shape, wrong name, or wrong class order, it is better to discover that here than inside a GUI or embedded inference pipeline.

## The complete script

Here is the full script without the explanatory comments:

```python
#!/usr/bin/env python3

import sys
import pathlib
import urllib.parse
import urllib.request

import numpy as np

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

OUT_DIR = pathlib.Path(__file__).parent.parent / "resources"
OUT_ONNX = OUT_DIR / "asteroid_taxonomy.onnx"


def tap_query(endpoint: str, adql: str, maxrec: int = 200000) -> str:
    params = urllib.parse.urlencode({
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "MAXREC": str(maxrec),
        "QUERY": adql,
    }).encode()

    req = urllib.request.Request(endpoint, data=params)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode()


def parse_csv(text: str) -> list[list[str]]:
    import csv
    import io

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    return [[c.strip() for c in row] for row in rows[1:]]


print("Fetching Gaia DR3 asteroid reflectance spectra...", flush=True)

csv = tap_query(
    GAIA_TAP,
    "SELECT source_id, wavelength, reflectance_spectrum "
    "FROM gaiadr3.sso_reflectance_spectrum "
    "ORDER BY source_id, wavelength",
    maxrec=1_100_000,
)

rows = parse_csv(csv)
print(f"  {len(rows):,} rows fetched", flush=True)

spectra: dict[int, list[float]] = {}

for row in rows:
    if len(row) < 3 or not row[2]:
        continue

    try:
        sid = int(row[0])
        spectra.setdefault(sid, []).append(float(row[2]))
    except ValueError:
        pass

spectra = {k: v for k, v in spectra.items() if len(v) == 16}
print(f"  {len(spectra):,} asteroids with 16-point spectra", flush=True)

source_ids = np.array(list(spectra.keys()), dtype=np.int64)
X_all = np.array([spectra[sid] for sid in source_ids], dtype=np.float32)


print("Fetching asteroid taxonomy labels from VizieR...", flush=True)

csv_tax = tap_query(
    VIZIER_TAP,
    'SELECT "Number", "class" FROM "J/A+A/665/A26/asteroid"',
    maxrec=2000,
)

tax_rows = parse_csv(csv_tax)

csv_names = tap_query(
    GAIA_TAP,
    "SELECT source_id, number_mp FROM gaiadr3.sso_source ORDER BY number_mp",
    maxrec=100_000,
)

name_rows = parse_csv(csv_names)

sid_to_num: dict[int, int] = {}

for row in name_rows:
    if len(row) >= 2 and row[0] and row[1]:
        try:
            sid_to_num[int(row[0])] = int(row[1])
        except ValueError:
            pass

tax: dict[int, str] = {}

for row in tax_rows:
    if len(row) >= 2 and row[0] and row[1]:
        try:
            tax[int(row[0])] = row[1].strip()
        except ValueError:
            pass

print(
    f"  {len(tax)} taxonomy labels, "
    f"{len(sid_to_num)} Gaia SSO source mappings",
    flush=True,
)

labels: dict[int, str] = {}

for sid in source_ids:
    num = sid_to_num.get(int(sid))
    if num is not None:
        cls = tax.get(num)
        if cls:
            labels[int(sid)] = cls

print(
    f"  {len(labels)} asteroids with Bus-DeMeo labels after cross-match",
    flush=True,
)

if len(labels) < 20:
    print("ERROR: too few labeled samples for training. Check network access.")
    sys.exit(1)

sid_list = sorted(labels.keys())
X_labeled = np.array([spectra[sid] for sid in sid_list], dtype=np.float32)
y_raw = [labels[sid] for sid in sid_list]

COMPLEX = {
    "B": "C", "C": "C", "Cb": "C", "Cg": "C", "Cgh": "C", "Ch": "C",
    "S": "S", "Sa": "S", "Sq": "S", "Sr": "S", "Sv": "S",
    "Q": "S", "Qa": "S",
    "A": "S", "L": "S",
    "X": "X", "Xc": "X", "Xe": "X", "Xk": "X",
    "E": "X", "M": "X", "P": "X",
    "D": "O", "T": "O", "K": "O", "Ld": "O", "O": "O", "R": "O", "V": "O",
}

y_complex = [COMPLEX.get(c, "O") for c in y_raw]

classes = sorted(set(y_complex))
class_idx = {c: i for i, c in enumerate(classes)}
y = np.array([class_idx[c] for c in y_complex], dtype=np.int64)

print(f"  Classes: {classes}")

for c in classes:
    n = np.sum(y == class_idx[c])
    print(f"    {c}: {n}")


from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

X_tr, X_te, y_tr, y_te = train_test_split(
    X_labeled,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        max_iter=500,
        random_state=42,
        early_stopping=True,
    )),
])

print("\nTraining MLPClassifier...", flush=True)

pipe.fit(X_tr, y_tr)
acc = pipe.score(X_te, y_te)

print(f"  Test accuracy: {acc:.1%}  ({len(X_te)} samples)")


from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

OUT_DIR.mkdir(parents=True, exist_ok=True)

initial_types = [("float_input", FloatTensorType([None, 16]))]

onnx_model = convert_sklearn(
    pipe,
    initial_types=initial_types,
    options={"zipmap": False},
)

import onnx

graph = onnx_model.graph
label_output = next((o for o in graph.output if o.name == "label"), None)

if label_output is not None:
    graph.output.remove(label_output)

with open(OUT_ONNX, "wb") as f:
    f.write(onnx_model.SerializeToString())

print(f"\nSaved: {OUT_ONNX}")


import onnxruntime as ort

sess = ort.InferenceSession(str(OUT_ONNX))
inp = sess.get_inputs()[0]
outs = sess.get_outputs()
result = sess.run(None, {inp.name: X_te[:4]})
probabilities = result[0]

print("\nONNX model verified:")
print(f"  inputName:  {inp.name}")
print(f"  inputShape: {inp.shape}")

for o in outs:
    print(f"  outputName: {o.name}  shape: {o.shape}")

print("  Sample probabilities (4 test asteroids):")

for i, row in enumerate(probabilities[:4]):
    pred = classes[int(np.argmax(row))]
    print(f"    asteroid {i}: {dict(zip(classes, row))}  predicted {pred}")

print(f"\nClasses (index order): {classes}")
print("Use these names in the YAML config.")
```

## What students should take away

The model is not the hard part by itself. The hard part is the chain around it:

- choosing a measurable input
- finding labels
- cross-matching catalogs correctly
- cleaning incomplete data
- keeping train and test sets separate
- scaling features before training
- checking class imbalance
- exporting the model in a useful format
- verifying the exported model before using it elsewhere

That is the real workflow. The neural network in this example is small, but the pipeline is the same one you will use for larger astronomy models.

Start with a dataset you understand. Train the simplest model that can answer the question. Only make it more complex after you know what is failing.

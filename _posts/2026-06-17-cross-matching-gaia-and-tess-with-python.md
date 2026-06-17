---
title: "Cross-matching Gaia and TESS with Python"
date: 2026-06-17 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/17/cross-matching-gaia-and-tess-with-python/
categories:
  - en-US
tags:
  - python
  - astronomy
  - data
  - gaia
  - tess
---

Astronomy catalogs rarely contain everything I need in one place. TESS tells me which stars were observed for transits. Gaia adds positions, proper motions, parallaxes, colors and luminosity information. To study a TESS target as a physical star, I had to join the two catalogs.

That join is called a **cross-match**. It looks like a database join, but the key is not a string or integer. The key is a position on the sky, measured at a particular epoch and with an uncertainty.

I tested the process with a small field around an arbitrary sky position. I queried TESS and Gaia, matched their coordinates, inspected ambiguous results and saved the resulting table.

## What makes a sky match different

Two example catalog rows looked like this:

```text
catalog A: RA=120.123456, Dec=-18.123456
catalog B: RA=120.123520, Dec=-18.123410
```

They are not equal, but they may describe the same star. Coordinates differ because of measurement uncertainty, catalog epoch, proper motion and the way each survey determines its source centroid.

The right question is not "are the coordinates equal?" It is:

> Is the angular separation small enough, given the resolution, epoch and source density?

For two nearby positions, Astropy handles the spherical geometry for us with `SkyCoord`.

## The environment I used

I used a small virtual environment with the astronomy libraries I needed:

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy pandas astropy astroquery matplotlib
```

The example uses:

- `astroquery.mast.Catalogs` for the TESS Input Catalog (TIC)
- `astroquery.gaia.Gaia` for Gaia DR3
- `astropy.coordinates.SkyCoord` for spherical matching
- `astropy.units` so arcseconds do not become accidental degrees

## The field I used

I kept the center coordinate as an input instead of hard-coding a famous exoplanet. That made it easier to repeat the same test on fields with different source densities.

```python
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord

center = SkyCoord(
    ra=120.0 * u.deg,
    dec=-18.0 * u.deg,
    frame="icrs",
)

query_radius = 2.0 * u.arcmin
match_radius = 1.0 * u.arcsec
```

The query radius controlled the size of the field downloaded from each archive. The match radius controlled which pairs I accepted as possible counterparts. I kept them as separate variables because they solve different problems.

## My TESS Input Catalog query

MAST exposes the TIC through `astroquery`:

```python
from astroquery.mast import Catalogs

tic = Catalogs.query_region(
    center,
    radius=query_radius,
    catalog="TIC",
)

tic = tic[["ID", "ra", "dec", "Tmag"]]
coordinate_mask = (
    np.ma.getmaskarray(tic["ra"])
    | np.ma.getmaskarray(tic["dec"])
)
tic = tic[~coordinate_mask]

print(f"TIC sources: {len(tic)}")
```

The returned object is an Astropy `Table`, not a pandas DataFrame. That is useful because Astropy tables preserve units and masks.

I did not assume every row had coordinates. Some catalog columns were masked, and converting them directly into floats would have quietly created bad values.

## My Gaia DR3 query

Gaia provides a cone-search helper:

```python
from astroquery.gaia import Gaia

job = Gaia.cone_search_async(
    center,
    radius=query_radius,
    table_name="gaiadr3.gaia_source",
)

gaia = job.get_results()
gaia = gaia[[
    "source_id",
    "ra",
    "dec",
    "parallax",
    "pmra",
    "pmdec",
    "phot_g_mean_mag",
    "bp_rp",
    "ruwe",
]]

print(f"Gaia sources: {len(gaia)}")
```

`ruwe` is included because a close positional match is not automatically a good astrometric source. A large RUWE can indicate that Gaia's single-star astrometric model fits poorly. It is a quality clue, not a universal delete button.

## Convert both catalogs to coordinates

```python
tic_coord = SkyCoord(
    ra=tic["ra"],
    dec=tic["dec"],
    unit="deg",
    frame="icrs",
)

gaia_coord = SkyCoord(
    ra=gaia["ra"],
    dec=gaia["dec"],
    unit="deg",
    frame="icrs",
)
```

At this point both catalogs lived in the same coordinate frame, so Astropy could calculate great-circle separations correctly, including near the poles and across RA=0.

## Nearest-neighbor matching

For every TIC source, find the nearest Gaia source:

```python
idx, separation, _ = tic_coord.match_to_catalog_sky(gaia_coord)

accepted = separation <= match_radius

print(f"Accepted matches: {accepted.sum()} / {len(tic)}")
print(f"Median accepted separation: "
      f"{np.median(separation[accepted].to_value(u.arcsec)):.3f} arcsec")
```

`idx[i]` is the Gaia row nearest to TIC row `i`. This does **not** mean the match is valid. Nearest-neighbor algorithms always return something when the comparison catalog is non-empty. The radius cut is what turns a nearest neighbor into a candidate counterpart.

I assembled the accepted pairs into an output table:

```python
from astropy.table import Table

matched = Table()
matched["tic_id"] = tic["ID"][accepted]
matched["gaia_source_id"] = gaia["source_id"][idx[accepted]]
matched["separation_arcsec"] = separation[accepted].to_value(u.arcsec)
matched["tmag"] = tic["Tmag"][accepted]
matched["gmag"] = gaia["phot_g_mean_mag"][idx[accepted]]
matched["parallax_mas"] = gaia["parallax"][idx[accepted]]
matched["bp_rp"] = gaia["bp_rp"][idx[accepted]]
matched["ruwe"] = gaia["ruwe"][idx[accepted]]

matched.sort("separation_arcsec")
matched.write("tic_gaia_matches.ecsv", overwrite=True)
```

ECSV is a good default for intermediate astronomy products because it preserves metadata and units better than plain CSV.

## The first hidden problem: duplicate assignments

Nearest-neighbor matching is directional. Two TIC rows can choose the same Gaia source, especially in a crowded field.

```python
gaia_ids = np.asarray(matched["gaia_source_id"])
unique_ids, counts = np.unique(gaia_ids, return_counts=True)
duplicates = unique_ids[counts > 1]

print(f"Gaia sources assigned more than once: {len(duplicates)}")
```

When duplicates appeared, I inspected them and considered several responses:

- keep only the smallest-separation pair
- require mutual nearest neighbors
- solve a global one-to-one assignment problem
- use magnitude, color or catalog identifiers as additional evidence

There is no universal choice. The scientific question determines the matching policy.

## Mutual nearest neighbors

A simple stricter rule is to require the catalogs to choose each other:

```python
tic_to_gaia, sep_tg, _ = tic_coord.match_to_catalog_sky(gaia_coord)
gaia_to_tic, _, _ = gaia_coord.match_to_catalog_sky(tic_coord)

rows = np.arange(len(tic))
mutual = gaia_to_tic[tic_to_gaia] == rows
close = sep_tg <= match_radius
keep = mutual & close

print(f"Mutual matches: {keep.sum()}")
```

This rejects many ambiguous pairs, but it can also reject legitimate sources in blended or incomplete catalogs. Stricter is not automatically more correct.

## The second hidden problem: epoch and proper motion

Gaia DR3 positions are referenced to epoch J2016.0. A nearby fast-moving star can shift by more than an arcsecond over a few years. If the other catalog position belongs to a different epoch, propagate Gaia coordinates before matching.

```python
from astropy.time import Time

gaia_with_motion = SkyCoord(
    ra=gaia["ra"] * u.deg,
    dec=gaia["dec"] * u.deg,
    pm_ra_cosdec=gaia["pmra"] * u.mas / u.yr,
    pm_dec=gaia["pmdec"] * u.mas / u.yr,
    obstime=Time("J2016.0"),
    frame="icrs",
)

gaia_at_2020 = gaia_with_motion.apply_space_motion(
    new_obstime=Time("J2020.0")
)
```

This example omits radial velocity and distance, so it is an approximation. For ordinary distant stars and a short epoch baseline, it is often enough. For nearby high-proper-motion stars, use every available phase-space component and document the target epoch.

## The separation distribution I got

Rather than accepting `1 arcsec` only because it sounded reasonable, I plotted the separation distribution:

```python
import matplotlib.pyplot as plt

sep_arcsec = separation.to_value(u.arcsec)

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(sep_arcsec, bins=np.linspace(0, 5, 51))
ax.axvline(match_radius.to_value(u.arcsec), color="tab:red",
           label="adopted threshold")
ax.set_xlabel("nearest Gaia separation (arcsec)")
ax.set_ylabel("TIC sources")
ax.legend()
fig.tight_layout()
fig.savefig("tic_gaia_separations.png", dpi=150)
```

A real counterpart population often forms a narrow peak near zero, while chance alignments create a wider tail. Crowded Galactic-plane fields need more care than sparse high-latitude fields.

## Estimate false matches with a shifted catalog

For an empirical control, I shifted one catalog by an amount larger than the match radius and repeated the match. I treated those pairs as accidental.

```python
shifted_tic = SkyCoord(
    ra=tic_coord.ra + 1.0 * u.arcmin,
    dec=tic_coord.dec,
    frame="icrs",
)

_, shifted_sep, _ = shifted_tic.match_to_catalog_sky(gaia_coord)
false_matches = np.count_nonzero(shifted_sep <= match_radius)

print(f"Shifted-catalog matches inside threshold: {false_matches}")
```

This was not a complete contamination model, but it showed whether my threshold was producing many random associations.

## A compact reusable function

```python
def nearest_crossmatch(left, right, max_sep):
    idx, sep, _ = left.match_to_catalog_sky(right)
    keep = sep <= max_sep
    return np.flatnonzero(keep), idx[keep], sep[keep]


left_rows, right_rows, sep = nearest_crossmatch(
    tic_coord,
    gaia_coord,
    1.0 * u.arcsec,
)
```

I kept the function small and left quality cuts, epoch propagation and one-to-one logic as explicit steps around it. That kept the assumptions visible in the analysis.

## What I recorded with the result

I recorded the following details with the cross-match:

- catalog releases and table names
- query date or archive job identifier
- coordinate frame and epochs
- whether proper motion was applied
- matching algorithm
- maximum separation
- one-to-one or mutual-match policy
- quality filters
- number of sources before and after every cut
- an estimate of accidental-match contamination

The final table is not merely downloaded data. It is the result of a chain of scientific decisions.

I started this as a data-preparation step, but the test made it clear that cross-matching is part of the inference. A wrong counterpart gives me a perfectly valid parallax, color and proper motion for the wrong star, which is much harder to notice than a missing value.

---
title: "TAP for Astronomy Data"
date: 2026-05-20 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/05/20/tap-for-astronomy-data/
categories:
  - en-US
tags:
  - astronomy
  - data
  - python
  - tap
---

If you work with astronomy data for more than a few days, you eventually run into TAP.

TAP means **Table Access Protocol**. It is an IVOA standard for querying astronomical catalogs through web services. In practice, it lets archives expose their tables as remote relational databases, and you query them with **ADQL**, which is basically SQL with celestial-coordinate functions.

For a data astronomer, knowing TAP is very close to knowing SQL for normal data engineering. Gaia, NOIRLab Astro Data Lab, VizieR, MAST and several radio archives use it.

## The basic architecture

The shape is simple:

```text
Client (Python, TOPCAT, browser)
        |
        |  HTTP POST/GET
        v
TAP server  ---> relational database
        |
        v
Result (VOTable, FITS, CSV, JSON)
```

A TAP service usually exposes:

- `{base_url}/sync` for synchronous queries, good for small and fast requests
- `{base_url}/async` for asynchronous jobs, needed when the query is slow or large
- `{base_url}/tables` to inspect schemas and tables
- `{base_url}/capabilities` to see what the server supports

For quick tests, `/sync` is fine. For real catalog work, `/async` is safer.

## ADQL

ADQL is SQL-92 with astronomy extensions. The part that matters most is geometry:

| Function | Use |
|---|---|
| `POINT('ICRS', ra, dec)` | A point on the sky |
| `CIRCLE('ICRS', ra, dec, r)` | A cone centered at RA/Dec with radius in degrees |
| `BOX('ICRS', ra, dec, w, h)` | A rectangular sky region |
| `POLYGON('ICRS', ...)` | An arbitrary polygon |
| `CONTAINS(a, b)` | Returns 1 if one geometry contains the other |
| `INTERSECTS(a, b)` | Tests geometry intersection |
| `DISTANCE(a, b)` | Angular distance in degrees |

One thing that always bites people coming from SQL: use `TOP`, not `LIMIT`.

```sql
SELECT TOP 100 source_id, ra, dec, parallax
FROM gaiadr3.gaia_source
WHERE parallax > 10
```

Without `TOP` or a strong filter, it is very easy to request a huge table and hit a timeout.

## Cone search

A cone search is the standard "give me everything around this coordinate" query:

```sql
SELECT TOP 1000 *
FROM survey.catalog
WHERE CONTAINS(
        POINT('ICRS', ra, dec),
        CIRCLE('ICRS', 153.26, -1.61, 1.5)
      ) = 1
```

The radius is in degrees. If you want one arcsecond, use about `0.000278`.

## Cross-matching catalogs

Spatial joins are where TAP becomes really useful. For example, matching a DESI source to nearby Gaia sources:

```sql
SELECT d.targetid, d.rv_adop, g.source_id, g.pmra, g.pmdec,
       DISTANCE(POINT('ICRS', d.target_ra, d.target_dec),
                POINT('ICRS', g.ra, g.dec)) AS sep_deg
FROM desi_dr1.mws AS d
JOIN gaiadr3.gaia_source AS g
  ON CONTAINS(
       POINT('ICRS', g.ra, g.dec),
       CIRCLE('ICRS', d.target_ra, d.target_dec, 0.000278)
     ) = 1
WHERE CONTAINS(
        POINT('ICRS', d.target_ra, d.target_dec),
        CIRCLE('ICRS', 153.26, -1.61, 1.5)
      ) = 1
```

This kind of query is the backbone of a lot of data-driven astronomy: take one catalog, find counterparts in another, then build a physical picture from the combined measurements.

## Useful TAP servers

| Service | TAP URL | Main use |
|---|---|---|
| Gaia Archive | `https://gea.esac.esa.int/tap-server/tap` | Gaia DR3 and DR2 |
| NOIRLab Astro Data Lab | `https://datalab.noirlab.edu/tap` | DESI, DECaLS, NSC, DES |
| MAST | `https://mast.stsci.edu/tap` | HST, TESS, Kepler, K2 |
| VizieR | `https://tapvizier.cds.unistra.fr/TAPVizieR/tap` | Published catalogs |
| SIMBAD | `https://simbad.cds.unistra.fr/simbad/sim-tap` | Named objects and object types |
| CASDA | `https://casda.csiro.au/casda_vo_tools/tap` | ASKAP and Parkes data |
| ARI Gaia mirror | `https://gaia.ari.uni-heidelberg.de/tap` | Gaia mirror and distance tables |

## Python with astroquery

For day-to-day work I usually start with `astroquery`:

```python
from astroquery.utils.tap.core import TapPlus

tap = TapPlus(url="https://datalab.noirlab.edu/tap")

job = tap.launch_job("""
    SELECT TOP 100 targetid, rv_adop, feh
    FROM desi_dr1.mws
    WHERE success = 'True'
""")

df = job.get_results().to_pandas()
```

For large jobs, use async:

```python
job = tap.launch_job_async("""
    SELECT targetid, target_ra, target_dec, rv_adop, feh, logg, teff
    FROM desi_dr1.mws
    WHERE CONTAINS(
            POINT('ICRS', target_ra, target_dec),
            CIRCLE('ICRS', 153.26, -1.61, 1.5)
          ) = 1
      AND success = 'True'
      AND rvs_warn = 0
""")

job.wait_for_job_end()
df = job.get_results().to_pandas()
```

Gaia also has a dedicated helper:

```python
from astroquery.gaia import Gaia

Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"

job = Gaia.launch_job_async("""
    SELECT source_id, ra, dec, parallax, pmra, pmdec, phot_g_mean_mag
    FROM gaiadr3.gaia_source
    WHERE CONTAINS(
            POINT('ICRS', ra, dec),
            CIRCLE('ICRS', 153.26, -1.61, 1.5)
          ) = 1
      AND parallax < 0.5
""")

df = job.get_results().to_pandas()
```

## Python with pyvo

`pyvo` is lower level, but it is very useful when you want direct control over IVOA services:

```python
import pyvo

service = pyvo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")

results = service.search("""
    SELECT TOP 1000 source_id, ra, dec, parallax
    FROM gaiadr3.gaia_source
    WHERE parallax > 10
""")

df = results.to_table().to_pandas()
```

It also supports other VO protocols such as cone search, spectral access and image access.

## TOPCAT

TOPCAT is still one of the best tools for interactive catalog work. It has a TAP tab, autocompletes tables and columns, does spatial matching, plots results and exports FITS, CSV and VOTable files. If I am exploring a new archive, I often start in TOPCAT and move the final query to Python later.

## Common errors

| Error | Usual cause | Fix |
|---|---|---|
| `OverflowError: query exceeded row limit` | Result is too large | Add `TOP` or stronger filters |
| `400 Bad Request` | Invalid ADQL | Check quotes, geometry syntax and `TOP` |
| Timeout | Query is too slow | Use async TAP |
| Wrong coordinate column names | Table schemas vary | Inspect `/tables` first |
| `CONTAINS` gives no rows | Region is outside the footprint | Test with `TOP 10` without geometry first |

TAP is not glamorous, but it is one of those boring standards that quietly makes modern astronomy possible. Once you get comfortable with it, the web becomes a giant astronomical database.

---
title: Cleanup PDFs
date: 2024-12-10T22:00:43+00:00
author: paolo
layout: post
permalink: /2024/12/10/cleanup-pdfs/
categories:
  - en-US
tags:
  - comp
  - hacks
  - python
---

I've got a lot of pdfs with password and with a huge text with my name on every page. To fix both issues, I wrote the small code below:

```python

import pikepdf
import sys
import re

if len(sys.argv) < 2:
    print(f"syntax {sys.argv[0]} input-file.pdf\n")
    exit(1)

to_remove = ['TEXT TO REMOVE']
input_file = sys.argv[1]
output_file = f"clean_{input_file}"

with pikepdf.open(input_file, password='FILE-PASSWORD') as pdf:
    for page in pdf.pages:
        instructions = pikepdf.parse_content_stream(page)
        new_instructions = []
        for x in instructions:
            extracted = ''.join(m.group(1) for m in re.finditer(r'"([^"]+)"', str(x)))
            if not any(s in extracted for s in to_remove):
                new_instructions.append(x)

        new_content_stream = pikepdf.unparse_content_stream(new_instructions)
        page.Contents = pdf.make_stream(new_content_stream)
    pdf.save(output_file)

```

it worked for everything that I did try. Even multi-line text, just add more fields to the `to_remove` array.

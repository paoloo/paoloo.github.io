---
title: "A Neural Network on an 8-bit Machine"
date: 2026-06-13 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/13/a-neural-network-on-an-8-bit-machine/
categories:
  - en-US
tags:
  - retrocomputing
  - machine-learning
  - c64
  - assembly
---

This one is for fun, but it makes a serious point. If you can run inference on a 1 MHz 6502 with no multiply instruction and no floating point, you understand exactly what your model costs. This post trains a tiny MLP to recognize 5x5 digit glyphs, bakes it into fixed-point integers, and runs the forward pass in 6502 assembly on a Commodore 64. Here is the proof it works:

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/06/eightbit-nn-c64.png" alt="A Commodore 64 screen showing '8-BIT MLP ON A 6502' and 'DIGIT = 2'" /><figcaption>The C64 ran the network and classified the embedded glyph as digit 2. Correct.</figcaption></figure>

It is the same discipline as the [TinyML post]({{ site.baseurl }}/2026/06/09/tinyml-under-a-power-budget/), taken to the absurd extreme that I happen to enjoy.

## Train big, deploy tiny

All the hard work happens off the machine. I train a small MLP in Python on jittered copies of four 5x5 glyphs (digits 0 to 3), then throw the floating-point model away and keep only an integer version of the weights.

```python
clf = MLPClassifier(hidden_layer_sizes=(8,), activation="relu", max_iter=4000)
clf.fit(X, y)            # 25 inputs -> 8 hidden -> 4 classes
```

The network is deliberately tiny: 25 binary inputs, 8 hidden units, 4 outputs. The quantization is the interesting part, because the 6502 has to be able to do the arithmetic.

## An integer forward pass the 6502 can run

I define the exact integer arithmetic in Python first, as a golden reference, and only then translate it to assembly. Two design choices make it fit an 8-bit CPU.

First, the input is binary. A pixel is on or off, so the first layer never multiplies anything. The pre-activation of a hidden unit is just its bias plus the sum of the weights whose input pixel is lit:

```python
acc = B1[j]
for i in range(25):
    if xbits[i]:
        acc += W1[j, i]          # add-only, no multiply
acc = acc >> SHIFT1              # ReLU + downscale
h[j] = max(0, min(127, acc))
```

Second, the hidden activations are clamped to 0 to 127 and the second-layer weights to a small range, so every product fits in 16 bits and the layer-2 sums never overflow a signed 16-bit accumulator. That is the one place a real multiply is needed:

```python
for c in range(4):
    acc = B2[c]
    for j in range(8):
        acc += h[j] * W2[c, j]   # 8x8 -> 16-bit multiply
    o[c] = acc
```

On the host this is trivial. The point of the exercise is that on the 6502, that one line, `h[j] * W2[c, j]`, is not an instruction. It is a subroutine.

The integer network classifies all four clean glyphs correctly, which is the green light to write the assembly:

```
digit 0: pred 0  logits [198, -213, -141, -41]
digit 1: pred 1  logits [-231, 265, -101, -103]
digit 2: pred 2  logits [-124, -114, 286, -47]
digit 3: pred 3  logits [-181, -131, -113, 184]
```

## A multiply is a routine, not an instruction

The 6502 has no multiply. You build one from shifts and adds. This is the standard 8-bit-by-8-bit unsigned multiply, accumulating a 16-bit product:

```asm
mul8:
    lda #0
    sta RESLO
    sta RESHI
    ldx #8
mul8l:
    lsr MULB           ; next bit of the multiplier into carry
    bcc mul8na
    clc
    lda RESHI
    adc MULA
    sta RESHI
mul8na:
    ror RESHI          ; shift the 16-bit product right
    ror RESLO
    dex
    bne mul8l
    rts
```

The rest of the program is bookkeeping: a signed 16-bit accumulator for each layer, an arithmetic shift right for the ReLU downscale, and an argmax. I make the argmax simple by biasing every logit by +32768 (a single `eor #$80` on the high byte), which turns the signed comparison into an unsigned one. Layer-2 weights carry their sign separately, so the multiply itself only ever sees magnitudes.

The whole thing assembles with `cc65` into a 760-byte `.prg` with a BASIC stub, so `RUN` just works.

## How slow is slow

That is the lesson hiding in the screenshot. The 32 second-layer multiplies dominate the cost: each pass through `mul8` is roughly 200 cycles, so the multiplies alone are about 8000 cycles, and the whole forward pass lands on the order of 12 to 15 thousand cycles. At the C64's ~0.98 MHz that is around 15 milliseconds for a single inference of a 25-8-4 network.

Fifteen milliseconds. For a model so small it is barely a model. A modern laptop runs the identical integer arithmetic in well under a microsecond, four orders of magnitude faster, and you never feel it. The 6502 makes you feel every multiply, and that is the whole point.

## The serious bit

Extreme constraints are clarifying. The same instinct that makes you respect a 6502's cycle budget is the one that makes you measure an INA219 before claiming a model can fly. A forward pass is a fixed, countable amount of arithmetic; the only thing that changes between a C64 and a flight computer is how many of those operations you can afford per second and per milliwatt. That mindset, treating compute as a hard physical budget rather than an abstraction, is what I want the lab built on.

The same network ports to the Z80 with a different multiply routine, so the MSX is next.

## Full code

Trainer (Python), which also emits the `ca65` weight tables:

```python
#!/usr/bin/env python
"""Train a tiny MLP to recognize 5x5 digit glyphs, quantize it to integers, and
emit the weights as ca65 tables for the 6502.

The integer forward pass defined here is the GOLDEN reference: the 6502 assembly
reproduces this exact arithmetic. Binary input means layer 1 is add-only; layer 2
uses an 8-bit by 8-bit multiply.
"""
import numpy as np
from sklearn.neural_network import MLPClassifier

rng = np.random.default_rng(0)

GLYPHS = {
    0: ["01110", "10001", "10001", "10001", "01110"],
    1: ["00100", "01100", "00100", "00100", "01110"],
    2: ["11110", "00001", "01110", "10000", "11111"],
    3: ["11110", "00001", "01110", "00001", "11110"],
}
N_IN, N_HID, N_OUT = 25, 8, 4


def to_vec(rows):
    return np.array([int(c) for r in rows for c in r], dtype=np.float64)


templates = {k: to_vec(v) for k, v in GLYPHS.items()}

X, y = [], []
for label, vec in templates.items():
    for _ in range(80):
        v = vec.copy()
        flips = rng.choice(N_IN, size=rng.integers(0, 3), replace=False)
        v[flips] = 1 - v[flips]
        X.append(v); y.append(label)
X, y = np.array(X), np.array(y)

clf = MLPClassifier(hidden_layer_sizes=(N_HID,), activation="relu",
                    max_iter=4000, random_state=0)
clf.fit(X, y)
print("[train] float train accuracy:", clf.score(X, y))

W1f, W2f = clf.coefs_[0].T, clf.coefs_[1].T
b1f, b2f = clf.intercepts_[0], clf.intercepts_[1]

S1 = 64.0 / max(np.abs(W1f).max(), np.abs(b1f).max())
W1 = np.clip(np.round(W1f * S1), -127, 127).astype(np.int16)
B1 = np.round(b1f * S1).astype(np.int32)
SHIFT1 = 5

S2 = 31.0 / np.abs(W2f).max()
W2 = np.clip(np.round(W2f * S2), -31, 31).astype(np.int16)
B2 = np.round(b2f * S2).astype(np.int32)


def int_forward(xbits):
    h = np.zeros(N_HID, dtype=np.int32)
    for j in range(N_HID):
        acc = B1[j]
        for i in range(N_IN):
            if xbits[i]:
                acc += W1[j, i]
        acc = acc >> SHIFT1
        h[j] = max(0, min(127, acc))
    o = np.zeros(N_OUT, dtype=np.int32)
    for c in range(N_OUT):
        acc = B2[c]
        for j in range(N_HID):
            acc += h[j] * W2[c, j]
        o[c] = acc
    assert np.abs(o).max() < 32767, f"layer-2 overflows int16: {o}"
    return h, o


print("[quant] integer-net predictions on clean glyphs:")
ok = True
for label, vec in templates.items():
    _, o = int_forward(vec.astype(int))
    pred = int(np.argmax(o))
    ok &= (pred == label)
    print(f"  digit {label}: pred {pred}  logits {list(o)}")
assert ok, "integer net misclassifies a clean glyph -- retune scales/shift"

TEST_LABEL = 2
test_bits = templates[TEST_LABEL].astype(int)


def w16(v):
    return v & 0xFFFF


lines = ["; auto-generated by eightbit_nn_train.py -- do not edit",
         f"N_IN = {N_IN}", f"N_HID = {N_HID}", f"N_OUT = {N_OUT}",
         f"SHIFT1 = {SHIFT1}", f"EXPECTED = {TEST_LABEL}", "",
         "; input glyph (25 bytes, 0/1) -- digit %d" % TEST_LABEL, "INPUT:"]
for r in range(5):
    row = test_bits[r * 5:(r + 1) * 5]
    lines.append("    .byte " + ",".join(str(int(b)) for b in row))
lines += ["", "; W1[hidden][input] signed bytes, row-major (8 x 25)", "W1:"]
for j in range(N_HID):
    lines.append("    .byte " + ",".join(str(int(W1[j, i]) & 0xFF) for i in range(N_IN)))
lines += ["; B1 (8 x int16, little-endian)", "B1:",
          "    .word " + ",".join(str(w16(int(B1[j]))) for j in range(N_HID)),
          "; W2[out][hidden] signed bytes (4 x 8)", "W2:"]
for c in range(N_OUT):
    lines.append("    .byte " + ",".join(str(int(W2[c, j]) & 0xFF) for j in range(N_HID)))
lines += ["; B2 (4 x int16)", "B2:",
          "    .word " + ",".join(str(w16(int(B2[c]))) for c in range(N_OUT)), ""]

open("res/nn_weights.s", "w").write("\n".join(lines) + "\n")
print("[emit] wrote res/nn_weights.s ; expected class =", TEST_LABEL)
```

The 6502 assembly (`ca65` syntax). It `.include`s the generated `nn_weights.s`:

```asm
; A tiny MLP running inference on a 6502 (Commodore 64).
; Binary 5x5 input -> add-only layer 1 -> ReLU(shift) -> 8x8 multiply layer 2
; -> argmax -> print the predicted digit.

CHROUT = $FFD2
W1PTR = $FB        ; zero-page pointers (classically-free C64 bytes)
W2PTR = $FD

.segment "HDR"
    .word $0801                 ; .prg load address

.segment "CODE"
    .word stub_end              ; BASIC stub: 10 SYS 2061
    .word 10
    .byte $9E
    .byte "2061"
    .byte 0
stub_end:
    .word 0

start:
    lda #$93                    ; clear screen
    jsr CHROUT
    ldx #0
hmsg:
    lda HDRMSG,x
    beq l1init
    jsr CHROUT
    inx
    bne hmsg

; ---- Layer 1: hidden[j] = relu( (B1[j] + sum_set W1[j][i]) >> SHIFT1 ) ----
l1init:
    lda #<W1
    sta W1PTR
    lda #>W1
    sta W1PTR+1
    lda #0
    sta J
l1j:
    lda J                       ; ACC = B1[J]
    asl a
    tax
    lda B1,x
    sta ACCLO
    lda B1+1,x
    sta ACCHI
    ldy #0
l1i:
    lda INPUT,y
    beq l1skip
    lda (W1PTR),y               ; signed weight -> add (sign-extended)
    tax
    clc
    adc ACCLO
    sta ACCLO
    txa
    bpl l1pos
    lda #$FF
    bne l1hi
l1pos:
    lda #$00
l1hi:
    adc ACCHI
    sta ACCHI
l1skip:
    iny
    cpy #N_IN
    bne l1i
    ldx #SHIFT1                 ; arithmetic shift right by SHIFT1
l1sh:
    lda ACCHI
    cmp #$80
    ror ACCHI
    ror ACCLO
    dex
    bne l1sh
    lda ACCHI                   ; clamp 0..127
    bmi l1zero
    bne l1max
    lda ACCLO
    cmp #128
    bcc l1ok
l1max:
    lda #127
    jmp l1ok
l1zero:
    lda #0
l1ok:
    ldx J
    sta HID,x
    clc                         ; W1PTR += N_IN
    lda W1PTR
    adc #N_IN
    sta W1PTR
    lda W1PTR+1
    adc #0
    sta W1PTR+1
    inc J
    lda J
    cmp #N_HID
    beq l1end
    jmp l1j
l1end:

; ---- Layer 2: o[c] = B2[c] + sum_j hid[j]*W2[c][j] ----
    lda #<W2
    sta W2PTR
    lda #>W2
    sta W2PTR+1
    lda #0
    sta CIDX
l2c:
    lda CIDX                    ; ACC = B2[CIDX]
    asl a
    tax
    lda B2,x
    sta ACCLO
    lda B2+1,x
    sta ACCHI
    ldy #0
l2j:
    lda HID,y
    sta MULA
    lda (W2PTR),y               ; signed weight
    bpl l2pos
    eor #$FF                    ; MULB = -w, then subtract
    clc
    adc #1
    sta MULB
    jsr mul8
    sec
    lda ACCLO
    sbc RESLO
    sta ACCLO
    lda ACCHI
    sbc RESHI
    sta ACCHI
    jmp l2next
l2pos:
    sta MULB
    jsr mul8
    clc
    lda ACCLO
    adc RESLO
    sta ACCLO
    lda ACCHI
    adc RESHI
    sta ACCHI
l2next:
    iny
    cpy #N_HID
    bne l2j
    lda ACCHI                   ; bias by +$8000 (unsigned argmax)
    eor #$80
    sta ACCHI
    lda CIDX
    asl a
    tax
    lda ACCLO
    sta OBUF,x
    lda ACCHI
    sta OBUF+1,x
    clc                         ; W2PTR += N_HID
    lda W2PTR
    adc #N_HID
    sta W2PTR
    lda W2PTR+1
    adc #0
    sta W2PTR+1
    inc CIDX
    lda CIDX
    cmp #N_OUT
    beq l2end
    jmp l2c
l2end:

; ---- argmax over OBUF (unsigned 16-bit) ----
    lda #0
    sta BESTLO
    sta BESTHI
    sta BESTIX
    sta CIDX
amc:
    lda CIDX
    asl a
    tax
    lda BESTLO
    cmp OBUF,x
    lda BESTHI
    sbc OBUF+1,x
    bcs amnext                  ; BEST >= cand -> keep
    lda OBUF,x
    sta BESTLO
    lda OBUF+1,x
    sta BESTHI
    lda CIDX
    sta BESTIX
amnext:
    inc CIDX
    lda CIDX
    cmp #N_OUT
    bne amc

; ---- print "DIGIT = n" ----
    ldx #0
dmsg:
    lda DIGMSG,x
    beq dprint
    jsr CHROUT
    inx
    bne dmsg
dprint:
    lda BESTIX
    clc
    adc #$30
    jsr CHROUT
    lda #13
    jsr CHROUT
    rts

; ---- unsigned 8x8 -> 16 multiply: MULA*MULB -> RESHI:RESLO ----
mul8:
    lda #0
    sta RESLO
    sta RESHI
    ldx #8
mul8l:
    lsr MULB
    bcc mul8na
    clc
    lda RESHI
    adc MULA
    sta RESHI
mul8na:
    ror RESHI
    ror RESLO
    dex
    bne mul8l
    rts

.segment "RODATA"
HDRMSG: .byte "8-BIT MLP ON A 6502", 13, 0
DIGMSG: .byte 13, "DIGIT = ", 0
.include "nn_weights.s"

.segment "BSS"
HID:    .res 8
OBUF:   .res 8
ACCLO:  .res 1
ACCHI:  .res 1
MULA:   .res 1
MULB:   .res 1
RESLO:  .res 1
RESHI:  .res 1
BESTLO: .res 1
BESTHI: .res 1
BESTIX: .res 1
J:      .res 1
CIDX:   .res 1
```

The linker config (`c64prg.cfg`) and the build-and-run commands:

```
# c64prg.cfg
MEMORY {
    ZP:   start = $0002, size = $00FE, type = rw;
    HDR:  start = $07FF, size = $0002, file = %O;
    MAIN: start = $0801, size = $C7FF, file = %O;
}
SEGMENTS {
    HDR:    load = HDR,  type = ro;
    CODE:   load = MAIN, type = rw;
    RODATA: load = MAIN, type = ro, optional = yes;
    BSS:    load = MAIN, type = bss, define = yes, optional = yes;
}
```

```bash
python eightbit_nn_train.py            # writes nn_weights.s
ca65 nn.s -o nn.o
ld65 -C c64prg.cfg -o nn.prg nn.o
# run headless and grab the screenshot
x64sc -warp -limitcycles 8000000 -autostart nn.prg -exitscreenshot nn-c64.png
```

; ---------------------------------------------------------------------------
; A tiny MLP running inference on a 6502 (Commodore 64).
; Binary 5x5 input -> add-only layer 1 -> ReLU(shift) -> 8x8 multiply layer 2
; -> argmax -> print the predicted digit. Weights come from nn_weights.s,
; which the training script generated. ca65 syntax.
; ---------------------------------------------------------------------------

CHROUT = $FFD2

; zero-page pointers (the 4 classically-free C64 ZP bytes)
W1PTR = $FB        ; $FB/$FC
W2PTR = $FD        ; $FD/$FE

.segment "HDR"
    .word $0801                 ; .prg load address

.segment "CODE"
; ---- BASIC stub: 10 SYS 2061 ----
    .word stub_end              ; link to next line
    .word 10                    ; line number
    .byte $9E                   ; SYS token
    .byte "2061"                ; -> $080D
    .byte 0
stub_end:
    .word 0                     ; end of program
                                ; start lands at $080D = 2061

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
    lda J                       ; ACC = B1[J] (J*2 index)
    asl a
    tax
    lda B1,x
    sta ACCLO
    lda B1+1,x
    sta ACCHI
    ldy #0
l1i:
    lda INPUT,y
    beq l1skip                  ; input bit 0 -> no add
    lda (W1PTR),y               ; signed weight
    tax
    clc
    adc ACCLO
    sta ACCLO
    txa
    bpl l1pos
    lda #$FF                    ; sign-extend negative
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
    cmp #$80                    ; C = sign bit
    ror ACCHI
    ror ACCLO
    dex
    bne l1sh
    lda ACCHI                   ; clamp to 0..127
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
    eor #$FF                    ; MULB = -w
    clc
    adc #1
    sta MULB
    jsr mul8
    sec                         ; ACC -= RES
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
    clc                         ; ACC += RES
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
    lda ACCHI                   ; bias by +$8000 so argmax is unsigned
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
    lda BESTLO                  ; test BEST < cand
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
    adc #$30                    ; '0' + index
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

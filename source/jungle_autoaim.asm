    org $1ff400
    org $1ff400
filter_0:
    bsr.w is_pickup
    beq.s .allow
    jmp $450a0
.allow:
    movea.l $22(a5),a6
    jsr $44abc
    jmp $4508a
    org $1ff440
filter_1:
    bsr.w is_pickup
    beq.s .allow
    jmp $450e8
.allow:
    movea.l $22(a5),a6
    jsr $44abc
    jmp $450d2
    org $1ff480
is_pickup:
    ; Same pickup-kind byte used by original winch candidate search.
    tst.b $d(a5)
    rts

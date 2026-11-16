    org $1ffe00
    org $1ffe00
filter_0:
    bsr.w is_pickup
    beq.s .allow
    jmp $f91a
.allow:
    movea.l $22(a5),a6
    jsr $f310
    jmp $f904
    org $1ffe40
filter_1:
    bsr.w is_pickup
    beq.s .allow
    jmp $f962
.allow:
    movea.l $22(a5),a6
    jsr $f310
    jmp $f94c
    org $1ffe80
is_pickup:
    ; Same pickup-kind byte used by original winch candidate search.
    tst.b $d(a5)
    rts

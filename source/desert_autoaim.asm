    org $100000
    org $100000
filter_0:
    bsr.w is_pickup
    beq.s .allow
    jmp $d972
.allow:
    movea.l $28(a5),a6
    jsr $d468
    jmp $d95c
    org $100040
filter_1:
    bsr.w is_pickup
    beq.s .allow
    jmp $d9ba
.allow:
    movea.l $28(a5),a6
    jsr $d468
    jmp $d9a4
    org $100080
is_pickup:
    ; Same descriptor chain and pickup byte used by original winch at DFC2.
    move.l a6,-(sp)
    movea.l 8(a5),a6
    cmpa.l #0,a6
    beq.s .done
    movea.l (a6),a6
    cmpa.l #0,a6
    beq.s .done
    movea.l (a6),a6
    cmpa.l #0,a6
    beq.s .done
    tst.b $f(a6)
.done:
    movea.l (sp)+,a6
    rts

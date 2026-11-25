    org $2a3000
reserve_vram:
    cmpi.w #9,$ff139e
    bne.s .normal
    cmpa.l #$150566,a2
    beq.s .single
    cmpa.l #$130d14,a2
    beq.s .single
.normal:
    move.w 2(a2),d0
    jmp $3e282
.single:
    move.w $42(a1),$44(a1)
    move.l $32(a1),$36(a1)
    clr.l $3e(a1)
    move.l (sp)+,d0
    cmpi.l #$4339e,d0
    beq.s .init
    jmp $43296
.init:
    jmp $433b6

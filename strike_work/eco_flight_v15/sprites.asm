    org $2dd000
reserve_vram:
    cmpi.w #9,$ff139e
    bne.s .normal
    move.l a3,-(sp)
    lea $2dd100,a3
.scan:
    tst.l (a3)
    beq.s .normal_pop
    cmpa.l (a3)+,a2
    bne.s .scan
    movea.l (sp)+,a3
    bra.s .single
.normal_pop:
    movea.l (sp)+,a3
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

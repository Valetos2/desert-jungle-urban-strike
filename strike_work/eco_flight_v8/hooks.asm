    org $27a000
select_campaign:
    jsr $3ec8e
    btst #8,d0
    beq.s released
    bset #0,$ff1097
    bne.s done
    addq.l #1,$ff10b0
    cmpi.l #10,$ff10b0
    blo.s redraw
    clr.l $ff10b0
redraw:
    addq.l #4,sp
    jmp $39450
released:
    bclr #0,$ff1097
done:
    tst.b d0
    rts

    org $27a080
start_supplies:
    move.w #99,$ff10ce
    move.w #9999,$ff10c6
    move.w #9999,$ff10d4
    movea.l #$ff1650,a1
    rts

    org $27a0c0
protect_armor:
    cmpa.l $ff29e8,a5
    beq.s .skip
    btst #1,$f(a5)
    jmp $41934
.skip:
    rts

    org $27a100
protect_slot:
    move.l d1,-(sp)
    move.l 4(a5),d1
    beq.s .original
    cmp.l $ff29e8,d1
    beq.s .skip
.original:
    move.l (sp)+,d1
    btst #6,8(a5)
    jmp $41768
.skip:
    move.l (sp)+,d1
    rts

    org $27a140
fuel:
    tst.w $ff10c6
    rts

    org $27a180
markers:
    cmpi.w #9,$ff139e
    bne.s original
    move.l d0,-(sp)
    move.w $ff1022,d0
    beq.s restore
    tst.w $ff041c
    bne.s hidden
    add.w d0,d0
    move.l a0,-(sp)
    lea $ff10d8,a0
    tst.w (a0,d0.w)
    movea.l (sp)+,a0
    bmi.s restore
hidden:
    move.l (sp)+,d0
    rts
restore:
    move.l (sp)+,d0
original:
    movem.l d0-d7/a0-a5,-(sp)
    move.w $ff1022,d0
    jmp $3978e

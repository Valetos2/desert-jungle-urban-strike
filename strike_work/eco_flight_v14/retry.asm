    org $2be000
    jsr $274000
    move.w sr,-(sp)
    movem.l d0-d7/a0-a6,-(sp)
    cmpi.w #9,$ff139e
    bne.s .done
    moveq #0,d0
    move.w $ff128a,d0
    divu.w $210226,d0
    swap d0
    tst.w d0
    beq.s .done
    add.w d0,d0
    movea.l $21024c,a0
    lea $fffba6,a2
    adda.w (a0,d0.w),a2
    tst.l (a2)
    beq.s .done
    tst.l 4(a2)
    bne.s .done
    jsr $4143a
.done:
    movem.l (sp)+,d0-d7/a0-a6
    move.w (sp)+,ccr
    rts

    org $2be100
; The DOS objective-two script destroys an invisible signal of group 22.
completed:
    movem.l (sp)+,d0-d2
    cmpi.w #9,$ff139e
    bne.s .continue
    cmpi.w #2,d0
    bne.s .continue
    movem.l d0-d7/a0-a6,-(sp)
    moveq #22,d0
    moveq #1,d1
    jsr $3bbfc
    movem.l (sp)+,d0-d7/a0-a6
.continue:
    jsr $4499c
    jmp $44a98


    org $1ff200
pad_preserve:
    movem.l d1,-(sp)
    jsr $9be0
    movem.l (sp)+,d1
    btst #1,$ff05f1
    rts
pad_detect:
    movem.l d0-d1/a0,-(sp)
    clr.l $ff10b4
    move.b #$40,$a10003
    move.w #2047,d0
.wait:
    dbra d0,.wait
    jsr $9a32
    tst.b $ff46ef
    bne.s .done
    move.l #1,$ff10b4
.done:
    movem.l (sp)+,d0-d1/a0
    rts

    org $1ff260
movie_enter:
    movem.l d0-d7/a0-a6,-(sp)
    move.w sr,-(sp)
    move.l $ff2f02,-(sp)
    move.w #$2700,sr
    move.l #$7d7a,$ff2f02
    move.w #$2300,sr
    move.l #$ff55de,$ff55d6
    jmp $bfa
movie_leave:
    move.w #$2700,sr
    move.l (sp)+,$ff2f02
    move.w (sp)+,sr
    movem.l (sp)+,d0-d7/a0-a6
    rts

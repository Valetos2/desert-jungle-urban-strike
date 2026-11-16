    org $1ff500
menu_resources:
    ; Entry replaces6FB8..6FE0. Preserve caller interrupt context around menu.
    move.w sr,-(sp)
    move.l $ff2f02,-(sp)
    move.w #$2700,sr
    move.l #$7d7a,$ff2f02
    move.w #$2300,sr
    move.w #0,$ff1306
    move.l #$ff55de,$ff55d6
    move.l #$fffb56,$ff55da
    jsr $a4cc
    jsr $a5be
    jsr $1f40
    move.w #$2700,sr
    move.l (sp)+,$ff2f02
    move.w (sp)+,sr
    jmp $6fe4

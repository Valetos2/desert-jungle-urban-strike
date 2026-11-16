    org $1ff300
sound_adjust:
    cmpi.b #3,$ff045a
    beq.s .sound
    movem.l d0-d2/a0-a2,-(sp)
    ext.l d1
    jmp $2f02
.sound:
    movem.l d0-d7/a0-a6,-(sp)
    jsr $1ff6a0
    nop
    ext.l d1
    add.l $ff10b8,d1
    cmpi.l #1,d1
    bge.s .upper
    moveq #1,d1
.upper:
    cmpi.l #53,d1
    ble.s .store
    moveq #53,d1
.store:
    move.l d1,$ff10b8
    moveq #3,d0
    movea.l #$ff10ac,a1
    movea.l #$7cb1e,a2
    jsr $2e98
    move.l #$fffffff1,$ff045c
    movem.l (sp)+,d0-d7/a0-a6
    rts
sound_play:
    movem.l d0-d7/a0-a6,-(sp)
    move.l $ff10b8,d0
    subq.l #1,d0
    lsl.w #2,d0
    lea sound_table(pc),a0
    adda.w d0,a0
    move.w (a0),d1
    move.l a0,-(sp)
    jsr $72c
    movea.l (sp)+,a0
    moveq #0,d0
    move.w 2(a0),d0
    jsr $7cdc
    movem.l (sp)+,d0-d7/a0-a6
    jmp $1d5a
sound_restore:
    movem.l d0-d7/a0-a6,-(sp)
    moveq #0,d0
    jsr $7d02
    moveq #3,d1
    jsr $72c
    movem.l (sp)+,d0-d7/a0-a6
    rts
sound_leave_row:
    cmpi.b #3,$ff045a
    bne.s .normal
    bsr.w $1ff6a0
.normal:
    move.l d3,-(sp)
    move.b #$20,d3
    jmp $1c6e
sound_leave_menu:
    bsr.w $1ff6a0
    bclr #0,$ff10a0
    rts
sound_table:
    include "sound_table.asm"

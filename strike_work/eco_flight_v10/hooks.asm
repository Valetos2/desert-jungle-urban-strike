    org $27f000
init_persistent_wires:
    jsr $278200
    cmpi.w #9,$ff139e
    bne.s .done
    movem.l d0-d7/a0-a6,-(sp)
    lea $27f100,a6
    moveq #5,d7
.loop:
    movea.l (a6)+,a4
    jsr $40916
    movea.l $1e(a4),a2
    lea $ff29cc,a1
    jsr $3dfca
    addq.w #1,$ff29ca
    dbra d7,.loop
    movem.l (sp)+,d0-d7/a0-a6
.done:
    rts

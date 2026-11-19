    org $278000
entry:
    cmpi.w #9,$ff139e
    bne.w native
split:
    ; A single native blit increments linearly through VRAM. Split the
    ; rectangle at each 64-tile seam, keeping source and collision offsets.
    move.l d7,-(sp)
    move.w d0,d7
    andi.w #63,d7
    neg.w d7
    addi.w #64,d7
    cmp.w d2,d7
    bge.s vertical
    move.w d7,-(sp)
    move.l 2(sp),d7
    movem.l d0-d7/a0-a6,-(sp)
    move.w 60(sp),d2
    bsr.w split
    movem.l (sp)+,d0-d7/a0-a6
    move.w (sp)+,d7
    add.w d7,d0
    add.w d7,d4
    sub.w d7,d2
vertical:
    move.w d1,d7
    andi.w #63,d7
    neg.w d7
    addi.w #64,d7
    cmp.w d3,d7
    bge.s ready
    move.w d7,-(sp)
    move.l 2(sp),d7
    movem.l d0-d7/a0-a6,-(sp)
    move.w 60(sp),d3
    bsr.s native
    movem.l (sp)+,d0-d7/a0-a6
    move.w (sp)+,d7
    add.w d7,d1
    add.w d7,d5
    sub.w d7,d3
ready:
    move.l (sp)+,d7
native:
    cmpa.l #0,a6
    beq.s clear_native
    cmpi.w #$1a,$10(a6)
    jmp $3fd2c
clear_native:
    move.w sr,-(sp)
    move.l $ff1632,-(sp)
    jmp $3ff92
    org $278100
clear:
    cmpi.w #9,$ff139e
    beq.w split
    bra.w clear_native
    org $278120
camera:
    jsr $40160
    cmpi.w #9,$ff139e
    bne.s setup
    cmpi.w #40,$ff1234
    bne.s setup
    moveq #0,d3
setup:
    jmp $40608
    org $278150
water:
    cmpi.w #9,$ff139e
    bne.s stock_water
    ; Keep the original phase timer and rotate between two free CRAM indices.
    move.w #$8f02,$c00004
    move.l #$c03a0000,$c00004
    lea $2781c0,a0
    move.w (a0,d1.w),$c00000
    addq.w #2,d1
    cmpi.w #6,d1
    blo.s phase_ok
    moveq #0,d1
phase_ok:
    move.l #$c03e0000,$c00004
    move.w (a0,d1.w),$c00000
    jmp $3de0a
stock_water:
    addq.l #6,a0
    move.l #$c006,d2
    jmp $3ddde
    org $2781c0
    dc.w $0640,$0660,$0862
    org $278200
init_static:
    jsr $44516
    jsr $4094c
    cmpi.w #9,$ff139e
    bne.s init_done
    movem.l d0-d7/a0-a6,-(sp)
    ; Platform 42 crosses two sector edges. Keep one live entry for the
    ; whole platform rather than removing it with the anchor sector.
    movea.l #$2503e8,a4
    jsr $40916
    movea.l $1e(a4),a2
    lea $ff29cc,a1
    jsr $3dfca
    addq.w #1,$ff29ca
    movem.l (sp)+,d0-d7/a0-a6
init_done:
    rts

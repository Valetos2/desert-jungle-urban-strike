    org $272000
entry:
    cmpa.l #$260100,a6
    bne.s native
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
    bsr.s entry
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
    cmpi.w #$1a,$10(a6)
    jmp $3fd2c

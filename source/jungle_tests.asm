    include "jungle_tests_constants.asm"
    org $200000
menu:
    movem.l d0-d7/a0-a6,-(sp)
    suba.l #32,sp
    movea.l sp,a6
    move.l $ff10a0,(a6)
    move.l $ff10a4,4(a6)
    move.l $ff10a8,8(a6)
    move.l #1,12(a6)
    clr.l 16(a6)
    clr.l 20(a6)
    clr.b $ff0452
    bsr.w draw
loop:
    bclr #0,$ff0420
.wait:
    btst #0,$ff0420
    beq.s .wait
    jsr $3ec8e
    btst #7,d0
    beq.s .nav
    btst #7,$ff1636
    beq.w exit_menu
.nav:
    tst.b d0
    bne.s .held
    clr.l $ff0454
    bra.w loop
.held:
    tst.l $ff0454
    blt.w loop
    btst #0,d0
    bne.w up
    btst #1,d0
    bne.w down
    btst #2,d0
    bne.w left
    btst #3,d0
    bne.w right
    cmpi.b #3,$ff0452
    beq.w sound_keys
    cmpi.b #4,$ff0452
    beq.w movie_keys
    bra.w loop
up:
    bsr.w stop_if_sound
    jsr $39022
    subq.b #1,$ff0452
    bpl.s cursor
    move.b #4,$ff0452
    bra.s cursor
down:
    bsr.w stop_if_sound
    jsr $39022
    addq.b #1,$ff0452
    cmpi.b #5,$ff0452
    bne.s cursor
    clr.b $ff0452
cursor:
    jsr $39016
    bra.w delay
left:
    moveq #-1,d1
    bra.s adjust
right:
    moveq #1,d1
adjust:
    moveq #0,d0
    move.b $ff0452,d0
    cmpi.w #3,d0
    bne.s .get
    bsr.w stop_if_test
.get:
    move.w d0,d2
    lsl.w #2,d2
    move.l (a6,d2.w),d3
    add.l d1,d3
    moveq #0,d4
    cmpi.w #3,d0
    bne.s .limit
    moveq #1,d4
.limit:
    lea limits(pc),a0
    move.w d0,d5
    add.w d5,d5
    cmp.l d4,d3
    bge.s .upper
    move.l d4,d3
.upper:
    moveq #0,d5
    move.w d0,d5
    add.w d5,d5
    move.w (a0,d5.w),d5
    cmp.l d5,d3
    ble.s .store
    move.l d5,d3
.store:
    move.l d3,(a6,d2.w)
    bsr.w sync
    movea.l a6,a1
    lea $202000,a2
    jsr $3a0b4
    bsr.w hints
    bra.w delay
sound_keys:
    btst #4,d0
    beq.s .stop
    btst #4,$ff1636
    bne.w loop
    bsr.w stop_sound
    move.l #1,20(a6)
    movem.l d0-d1/a0,-(sp)
    moveq #1,d0
    jsr $3e5c4
    move.l 12(a6),d0
    subq.w #1,d0
    lea $203000,a0
    move.b (a0,d0.w),d0
    andi.w #255,d0
    jsr $3e598
    movem.l (sp)+,d0-d1/a0
    bra.w delay
.stop:
    btst #5,d0
    beq.w loop
    bsr.w stop_sound
    bra.w delay
movie_keys:
    btst #4,d0
    beq.w loop
    btst #4,$ff1636
    bne.w loop
    bsr.w movie
    bra.w delay
delay:
    move.l #-15,$ff0454
    bra.w loop
exit_menu:
    bsr.w stop_if_test
    bsr.w sync
    bclr #0,$ff1094
    clr.w $ff0480
    adda.l #32,sp
    movem.l (sp)+,d0-d7/a0-a6
    rts
sync:
    move.l (a6),$ff10a0
    move.l 4(a6),$ff10a4
    move.l 8(a6),$ff10a8
    rts
stop_if_sound:
    cmpi.b #3,$ff0452
    bne.s .done
    bsr.w stop_if_test
.done:
    rts
stop_if_test:
    tst.l 20(a6)
    beq.s .done
    clr.l 20(a6)
    bsr.w stop_sound
.done:
    rts
stop_sound:
    move.l d0,-(sp)
    moveq #0,d0
    jsr $3e598
    move.l (sp)+,d0
    rts
limits:
    dc.w 2,1,1,SOUND_COUNT,MOVIE_COUNT-1

    org $200400
draw:
    movem.l d0-d7/a0-a5,-(sp)
    jsr $3e4d2
    clr.w $ff0474
    clr.w $ff0476
    move.w #1,$ff0480
    bclr #0,$ff1094
    lea $202800,a2
    jsr $384fe
    bset #0,$ff1094
    movea.l a6,a1
    lea $202000,a2
    move.l #-1,$ff0470
    jsr $3a0d6
    bsr.w hints
    jsr $39016
    clr.l $ff0454
    movem.l (sp)+,d0-d7/a0-a5
    rts
hints:
    movem.l d0/a2,-(sp)
    bclr #0,$ff1094
    move.l (a6),d0
    tst.l 8(a6)
    beq.s .three
    addq.l #4,d0
.three:
    lsl.w #2,d0
    lea $202900,a2
    movea.l (a2,d0.w),a2
    jsr $384fe
    bset #0,$ff1094
    movem.l (sp)+,d0/a2
    rts

    org $200600
movie:
    clr.l 20(a6)
    movem.l d0-d7/a0-a6,-(sp)
    move.w $ff139e,-(sp)
    move.l $ff283c,-(sp)
    bsr.w stop_sound
    move.l 16(a6),d0
    lsl.w #3,d0
    lea $203100,a0
    adda.w d0,a0
    move.w 4(a0),d0
    move.w d0,$ff139e
    lsl.w #2,d0
    lea $19292e,a1
    move.l (a1,d0.w),$ff283c
    bclr #0,$ff1094
    clr.l $ff1288
    movea.l (a0),a0
    jsr $11e0
    bsr.w stop_sound
    jsr $3b66c
    move.w sr,-(sp)
    move.w #$2700,sr
    jsr $3baa6
    jsr $3e1e0
    jsr $3e2d2
    move.l #$528,$ff046c
    move.w (sp)+,sr
    move.l (sp)+,$ff283c
    move.w (sp)+,$ff139e
    movem.l (sp)+,d0-d7/a0-a6
    jsr $392b0
rebuilt:
    move.b #4,$ff0452
    bsr.w draw
    rts

    org $200800
background_ready:
    cmpi.l #rebuilt,(sp)
    bne.s .normal
    rts
.normal:
    movem.l d2-d3/a2-a3,-(sp)
    movea.l #$7e2e2,a2
    jmp $3931c
    org $200840
value_draw:
    ; The new movie value uses the stock small font.
    cmpa.l #$fffba6,a1
    blo.s .normal
    cmpa.l a6,a1
    beq.s .normal
    movem.l d0/a0,-(sp)
    lea 16(a6),a0
    cmpa.l a0,a1
    movem.l (sp)+,d0/a0
    bne.s .normal
    addi.l #$80,d1
    bclr #0,$ff1094
    jsr $3846a
    bset #0,$ff1094
    jmp $3a0aa
.normal:
    jsr $3846a
    jmp $3a0aa

    org $200900
number_draw:
    move.l a0,-(sp)
    lea 12(a6),a0
    cmpa.l a0,a1
    movea.l (sp)+,a0
    beq.s .custom
    jsr $3846a
    movea.l a3,a2
    jmp $3a050
.custom:
    movem.l d1-d4/a2-a3,-(sp)
    movea.l a2,a3
    move.l #$aa4,d1
    lea blanks(pc),a2
    jsr $3846a
    moveq #0,d3
.count:
    move.b (a3)+,d4
    beq.s .render
    cmpi.b #32,d4
    beq.s .render
    addq.w #2,d3
    cmpi.b #49,d4
    bne.s .count
    subq.w #1,d3
    bra.s .count
.render:
    movea.l 16(sp),a2
    move.l #$ab0,d1
    add.w d3,d3
    sub.w d3,d1
    jsr $3846a
    movem.l (sp)+,d1-d4/a2-a3
    movea.l a3,a2
    jmp $3a050
blanks:
    dc.b '   ',0


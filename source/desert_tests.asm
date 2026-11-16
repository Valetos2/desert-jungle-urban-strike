    include "desert_tests_constants.asm"
    org $101000
menu:
    movem.l d0-d7/a0-a6,-(sp)
    suba.l #32,sp
    movea.l sp,a6
    move.l $ff1084,(a6)
    move.l $ff1088,4(a6)
    move.l $ff108c,8(a6)
    move.l #1,12(a6)
    clr.l 16(a6)
    clr.l 20(a6)
    clr.b $ff0252
    bsr.w draw
loop:
    bclr #0,$ff0220
.wait:
    btst #0,$ff0220
    beq.s .wait
    bsr.w animate
    jsr $8e66
    btst #7,d0
    beq.s .nav
    btst #7,$ff1c78
    beq.w exit_menu
.nav:
    tst.b d0
    bne.s .held
    clr.l $ff0254
    bra.w loop
.held:
    tst.l $ff0254
    blt.w loop
    btst #0,d0
    bne.w up
    btst #1,d0
    bne.w down
    btst #2,d0
    bne.w left
    btst #3,d0
    bne.w right
    cmpi.b #3,$ff0252
    beq.w sound_keys
    cmpi.b #4,$ff0252
    beq.w movie_keys
    bra.w loop
up:
    bsr.w stop_if_sound
    subq.b #1,$ff0252
    bpl.s cursor
    move.b #4,$ff0252
    bra.s cursor
down:
    bsr.w stop_if_sound
    addq.b #1,$ff0252
    cmpi.b #5,$ff0252
    bne.s cursor
    clr.b $ff0252
cursor:
    jsr $3306
    bra.w delay
left:
    moveq #-1,d1
    bra.s adjust
right:
    moveq #1,d1
adjust:
    moveq #0,d0
    move.b $ff0252,d0
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
    lea $102000,a2
    jsr $47fe
    bsr.w hints
    bra.w delay
sound_keys:
    btst #4,d0
    beq.s .stop
    btst #4,$ff1c78
    bne.w loop
    bsr.w stop_sound
    move.l #1,20(a6)
    movem.l d0-d1/a0,-(sp)
    moveq #1,d0
    jsr $89a6
    move.l 12(a6),d0
    subq.w #1,d0
    lea $103000,a0
    add.w d0,d0
    move.w (a0,d0.w),d0
    bsr.w play_sound
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
    btst #4,$ff1c78
    bne.w loop
    bsr.w movie
    bra.w delay
delay:
    move.l #-15,$ff0254
    bra.w loop
exit_menu:
    bsr.w stop_if_test
    bsr.w sync
    bclr #0,$ff107c
    clr.w $ff027c
    adda.l #32,sp
    movem.l (sp)+,d0-d7/a0-a6
    rts
sync:
    move.l (a6),$ff1084
    move.l 4(a6),$ff1088
    move.l 8(a6),$ff108c
    rts
stop_if_sound:
    cmpi.b #3,$ff0252
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
    movem.l d0-d7/a0-a6,-(sp)
    moveq #0,d0
    jsr $890e
    moveq #2,d0
    jsr $89a6
    bsr.w hard_mute
    movem.l (sp)+,d0-d7/a0-a6
    rts
play_sound:
    btst #15,d0
    beq.s .music
    andi.w #$7fff,d0
    jmp $88c8
.music:
    jmp $890e
limits:
    dc.w 2,2,1,SOUND_COUNT,MOVIE_COUNT-1

    org $101400
draw:
    movem.l d0-d7/a0-a5,-(sp)
    jsr $8832
    move.w #2,$ff0270
    move.w #2,$ff0272
    move.w #1,$ff027c
    bclr #0,$ff107c
    lea $102800,a2
    jsr $45dc
    bset #0,$ff107c
    movea.l a6,a1
    lea $102000,a2
    move.l #-1,$ff026c
    jsr $4820
    bsr.w hints
    jsr $3306
    clr.l $ff0254
    movem.l (sp)+,d0-d7/a0-a5
    rts
hints:
    movem.l d0/a2,-(sp)
    bclr #0,$ff107c
    move.l (a6),d0
    tst.l 8(a6)
    beq.s .three
    addq.l #4,d0
.three:
    lsl.w #2,d0
    lea $102900,a2
    movea.l (a2,d0.w),a2
    jsr $45dc
    bset #0,$ff107c
    movem.l (sp)+,d0/a2
    rts

    org $101600
movie:
    clr.l 20(a6)
    movem.l d0-d7/a0-a6,-(sp)
    move.w $ff1b10,-(sp)
    move.l $ff1038,-(sp)
    bsr.w stop_sound
    move.l 16(a6),d0
    move.l d0,-(sp)
    bclr #0,$ff107c
    jsr $5d1c
    jsr $851e
    jsr $8608
    move.l (sp)+,d0
    tst.w d0
    bne.s movie_list
    jsr $8832
    jsr $ff8ca
intro_done:
    bra.w return_movie
movie_list:
    cmpi.w #9,d0
    bge.w preview_result
    cmpi.w #4,d0
    beq.s .ending
    bgt.s .brief
    subq.w #1,d0
    lsl.w #2,d0
    lea $103100,a0
    movea.l (a0,d0.w),a0
    jsr $ffa8e
    bra.s return_movie
.ending:
    moveq #$16,d0
    jsr $5d36
    btst #7,$ff1c79
    bne.s return_movie
    moveq #$1a,d0
    jsr $5d36
    bra.s return_movie
.brief:
    subq.w #5,d0
    move.w d0,$ff1b10
    bclr #0,$ff1038
    moveq #$e,d0
    jsr $5d36
return_movie:
    bsr.w stop_sound
    move.w sr,-(sp)
    move.w #$2700,sr
    jsr $5d1c
    jsr $851e
    jsr $8608
    move.l #$528,$ff0268
    move.w (sp)+,sr
    move.l (sp)+,$ff1038
    move.w (sp)+,$ff1b10
    jsr $371e
rebuilt:
    movem.l (sp)+,d0-d7/a0-a6
    move.b #4,$ff0252
    bsr.w draw
    rts
    org $101800
background_ready:
    cmpi.l #rebuilt,(sp)
    bne.s .normal
    rts
.normal:
    jsr $8832
    movea.l #$409,a2
    jmp $374a
    org $101840
value_draw:
    movem.l d0/a0,-(sp)
    lea 16(a6),a0
    cmpa.l a0,a1
    movem.l (sp)+,d0/a0
    bne.s .normal
    addi.l #$80,d1
    bclr #0,$ff107c
    jsr $4572
    bset #0,$ff107c
    jmp $47f4
.normal:
    jsr $4572
    jmp $47f4

    org $101900
number_draw:
    move.l a0,-(sp)
    lea 12(a6),a0
    cmpa.l a0,a1
    movea.l (sp)+,a0
    beq.s .custom
    jsr $4572
    movea.l a3,a2
    jmp $479a
.custom:
    movem.l d1-d4/a2-a3,-(sp)
    movea.l a2,a3
    move.l #$9a4,d1
    lea blanks(pc),a2
    jsr $4572
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
    move.l #$9b0,d1
    add.w d3,d3
    sub.w d3,d1
    jsr $4572
    movem.l (sp)+,d1-d4/a2-a3
    movea.l a3,a2
    jmp $479a
blanks:
    dc.b '   ',0

    org $101a00
hard_mute:
    move.w sr,-(sp)
    move.w #$2700,sr
    move.w #$100,$a11100
.bus:
    btst #0,$a11100
    bne.s .bus
    lea $a04000,a0
    moveq #$40,d1
.tl:
    move.b d1,(a0)
    bsr.s .wait
    move.b #$7f,1(a0)
    bsr.s .wait
    move.b d1,2(a0)
    bsr.s .wait
    move.b #$7f,3(a0)
    bsr.s .wait
    addq.w #1,d1
    cmpi.w #$50,d1
    bne.s .tl
    move.b #$2b,(a0)
    bsr.s .wait
    clr.b 1(a0)
    bsr.s .wait
    move.b #$9f,$c00011
    move.b #$bf,$c00011
    move.b #$df,$c00011
    move.b #$ff,$c00011
    move.w #0,$a11100
    move.w (sp)+,sr
    rts
.wait:
    moveq #32,d2
.delay:
    dbra d2,.delay
    rts

    org $101b00
intro_chain:
    cmpi.l #intro_done,(sp)
    bne.s .normal
    rts
.normal:
    tst.w $fffb1a
    beq.s .done
    jmp $ffa82
.done:
    rts
animate:
    tst.l $ff0258
    blt.s .done
    movem.l d0-d7/a0-a6,-(sp)
    jsr $35bc
    movem.l (sp)+,d0-d7/a0-a6
.done:
    rts
preview_result:
    cmpi.w #9,d0
    bne.s .death
    moveq #$16,d0
    jsr $5d36
    bra.w return_movie
.death:
    lea $103180,a0
    jsr $ffa8e
    bra.w return_movie

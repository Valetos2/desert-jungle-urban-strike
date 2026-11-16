    org $1ff500
read_router:
    tst.l $ff10a8
    bne.w read_six
    movem.l d1/a0,-(sp)
    lea $a10003,a0
    jmp $3ebfc
    org $1ff540
init_pad:
    movem.l d0-d3/a0,-(sp)
    move.w sr,-(sp)
    move.w #$2700,sr
    clr.l $ff10a8
    move.b #$40,$a10009
    move.b #$40,$a10003
    move.w #2047,d0
.wait:
    dbra d0,.wait
    bsr.w read_six
    btst #15,d0
    beq.s .done
    move.l #1,$ff10a8
.done:
    move.w (sp)+,sr
    movem.l (sp)+,d0-d3/a0
    rts
    org $1ff5a0
read_six:
    movem.l d1-d3/a0,-(sp)
    lea $a10003,a0
    moveq #0,d0
    moveq #0,d3
    move.w #$100,$a11100
.bus:
    btst #0,$a11100
    bne.s .bus
    bsr.w phase
    asl.b #2,d0
    andi.w #$c0,d0
    andi.w #$3f,d1
    or.w d1,d0
    not.b d0
    move.w d0,d2
    bsr.w phase
    bsr.w phase
    andi.b #$f,d0
    bne.s .three
    bsr.w phase
    not.b d1
    andi.w #$f,d1
    lsl.w #8,d1
    ori.w #$8000,d1
    move.w d1,d3
.three:
    move.b #$40,(a0)
    move.w #0,$a11100
    move.w d2,d0
    move.w d0,d1
    andi.w #$f,d1
    andi.w #$f0,d0
    lea $3ebd6,a0
    or.b (a0,d1.w),d0
    or.w d3,d0
    movem.l (sp)+,d1-d3/a0
    rts
phase:
    move.b #$40,(a0)
    nop
    nop
    nop
    move.b (a0),d1
    move.b #0,(a0)
    nop
    nop
    nop
    move.b (a0),d0
    rts
    org $1ff680
strafe:
    move.w $ff101a,d2
    tst.l $ff10a8
    beq.s .done
    move.w #10,d2
    btst #11,d0
    beq.s .done
    move.w #11,d2
.done:
    jmp $3ecca
    org $1ff6b0
hellfire:
    move.w $ff101a,d2
    tst.l $ff10a8
    bne.s .six
    jmp $3d00a
.six:
    btst d2,d0
    beq.s .done
    btst d2,$ff126d
    bne.s .done
    movea.l $3c(a0),a3
    clr.l $c(a3)
    clr.l $ff12a0
    jsr $45042
.done:
    jmp $3d052
    org $1ff700
help_index:
    move.l $ff10a0,d0
    tst.l $ff10a8
    beq.s .done
    addq.l #4,d0
.done:
    rts
    org $1ff720
help_refresh:
    bsr.w help_index
    jmp $39210

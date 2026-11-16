    org $100300
read_router:
    move.l d1,-(sp)
    move.w sr,-(sp)
    move.w #$2700,sr
    tst.l $ff108c
    bne.s .six
    jmp $8e6e
.six:
    move.b $ff1c79,$ff1c78
    bsr.w read_six
    jmp $8ebc
    org $100340
init_pad:
    movem.l d0-d3/a0,-(sp)
    move.w sr,-(sp)
    move.w #$2700,sr
    clr.l $ff108c
    move.b #$40,$a10009
    move.b #$40,$a10003
    move.w #2047,d0
.wait:
    dbra d0,.wait
    bsr.w read_six
    btst #15,d0
    beq.s .done
    move.l #1,$ff108c
.done:
    move.w (sp)+,sr
    movem.l (sp)+,d0-d3/a0
    rts
    org $1003a0
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
    or.w d3,d0
    btst #11,d0
    beq.s .no_mode
    bset #10,d0
.no_mode:
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
    org $100480
strafe:
    move.w $ff100c,d2
    tst.l $ff108c
    beq.s .done
    move.w #10,d2
.done:
    jmp $8eee
    org $1004c0
hellfire:
    move.w $ff100c,d2
    tst.l $ff108c
    bne.s .six
    jmp $6f1e
.six:
    btst d2,d0
    beq.s .done
    btst d2,$ff19d3
    bne.s .done
    movea.l $ff251c,a0
    movea.l $42(a0),a3
    clr.l $c(a3)
    clr.l $ff1a08
    jsr $d914
.done:
    jmp $6f68

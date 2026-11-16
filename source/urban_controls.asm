    org $1ff600
strafe:
    tst.l $ff10b4
    bne.s .six
    jmp $9cbc
.six:
    btst #11,d0
    beq.s .done
    bset #10,d0
.done:
    rts
    org $1ff640
hellfire:
    move.w $ff1024,d2
    tst.l $ff10b4
    bne.s .six
    jmp $65be
.six:
    bclr d2,$ff46eb
    btst d2,d0
    beq.s .done
    btst d2,$ff129b
    bne.s .done
    movea.l $3c(a0),a3
    cmpa.l #0,a3
    beq.s .done
    clr.l $c(a3)
    jsr $f8bc
.done:
    jmp $65dc

    org $1ff6a0
stop_test:
    bclr #7,$ff10a0
    beq.s .done
    jmp $1ff39e
.done:
    rts
    org $1ff6c0
play_test:
    bset #7,$ff10a0
    movem.l d0-d7/a0-a6,-(sp)
    move.l $ff10b8,d0
    jmp $1ff372
    org $1ff700
help_index:
    move.l $ff10ac,d0
    tst.l $ff10b4
    beq.s .done
    addq.l #4,d0
.done:
    rts

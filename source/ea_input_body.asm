    org EA_BASE
ea_poll:
    move.l d2,-(sp)
    move.b #$40,$a10009
    move.b #$40,$a1000b
    move.b #$40,$a10003
    move.b #$40,$a10005
    ; >2.5 ms at NTSC 68000 clock: let either six-button pad reset its handshake.
    move.w #2000,d2
.wait:
    dbra d2,.wait
    move.l (sp)+,d2
    jmp EA_POLL_TAIL
    org EA_BASE+$80
ea_skip:
    or.b d1,d0
    andi.w #$f0,d0
    beq.s .released
    tst.b $ff0000
    beq.s .ignore
    jmp EA_EXIT
.released:
    move.b #1,$ff0000
.ignore:
    moveq #0,d0
    moveq #0,d1
    jmp EA_CONTINUE

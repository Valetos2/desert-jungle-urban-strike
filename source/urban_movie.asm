    org $1ff900
movie_dispatch:
    cmpi.b #4,$ff045a
    beq.s .movie
    cmpi.b #2,$ff045a
    beq.s .hint
    cmpi.b #0,$ff045a
.hint:
    jmp $1eca
.movie:
    btst #4,$ff46e5
    bne movie_wait
    btst #4,d0
    beq movie_wait
    movem.l d0-d7/a0-a6,-(sp)
    move.l $ff10ac,-(sp)
    move.l $ff10b0,-(sp)
    move.l $ff10b4,-(sp)
    move.l $ff10b8,-(sp)
    move.l $ff10bc,-(sp)
    move.l $ff10c0,-(sp)
    move.w $ff13e4,-(sp)
    move.l $ff4542,-(sp)
    moveq #1,d1
    jsr $72c
    move.l $ff10bc,d0
    lsl.w #3,d0
    lea movie_table(pc),a0
    adda.w d0,a0
    move.w 4(a0),d0
    move.w d0,$ff13e4
    lsl.w #2,d0
    movea.l #$1a4b9e,a1
    move.l (a1,d0.w),$ff4542
    bclr #0,$ff10a0
    clr.l $ff1136
    movea.l (a0),a0
    jsr $bec
    jsr $1ff39e
    jsr $4e32
    ; Full sequences can retain resource allocations. Match startup cleanup.
    jsr $a4cc
    jsr $a5be
    move.l (sp)+,$ff4542
    move.w (sp)+,$ff13e4
    move.l (sp)+,$ff10c0
    move.l (sp)+,$ff10bc
    move.l (sp)+,$ff10b8
    move.l (sp)+,$ff10b4
    move.l (sp)+,$ff10b0
    move.l (sp)+,$ff10ac
    movem.l (sp)+,d0-d7/a0-a6
    move.l #$528,$ff047c
    addq.l #4,sp
    jsr $1f92
movie_rebuilt:
    jsr $1cb6
movie_options_return:
    jmp $217c
movie_wait:
    jmp $1d5a
movie_table:
    include "movie_table.asm"
debrief_win:
    dc.l $ac156,0
debrief_lose:
    dc.l $ac1c6,0

    org $1ffc00
movie_value_draw:
    cmpa.l #$ff10bc,a1
    bne.s .normal
    bclr #0,$ff10a0
    addi.l #$80,d1 ; one tile row below the large label top
    jsr $fd4
    bset #0,$ff10a0
    jmp $2e8e
.normal:
    jsr $fd4
    jmp $2e8e

; Fixed entry addresses keep release hooks independent of table size.
    cnop 0,2
    org $1ffd00
; JSR1F92 reaches this hook with our continuation on top of stack.
; Normal main-menu entry still executes the displaced instructions.
movie_background_ready:
    cmpi.l #movie_rebuilt,(sp)
    bne.s .normal
    rts
.normal:
    movem.l d2-d3/a2-a3,-(sp)
    movea.l #$7ca2c,a2
    jmp $2006
    org $1ffd40
options_initial_row:
    bclr #7,$ff10a0
    move.b #0,$ff045a
    cmpi.l #movie_options_return,16(sp)
    bne.s .done
    move.b #4,$ff045a
.done:
    jmp $1d40
    org $1ffd80
options_wrap:
    movem.l d0,-(sp)
    move.b $ff045a,d0
    bpl.s .bottom
    move.b $ff045b,d0
    bra.s .done
.bottom:
    cmp.b $ff045b,d0
    ble.s .done
    moveq #0,d0
.done:
    jmp $1c96

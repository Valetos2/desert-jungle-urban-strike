    org $211000
setup_flight:
    move.w #99,$ff10ce
    move.w #9999,$ff10c6
    move.w #9999,$ff10d4
    movea.l #$ff1650,a1
    rts

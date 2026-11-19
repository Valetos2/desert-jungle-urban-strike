    org $211100
water_palette:
    cmpi.w #9,$ff139e
    bne.s stock
    adda.l #$32,a0
    move.l #$c032,d2
    rts
stock:
    adda.l #6,a0
    move.l #$c006,d2
    rts

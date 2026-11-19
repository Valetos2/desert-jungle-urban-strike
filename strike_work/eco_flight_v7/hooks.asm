    org $279000
water:
    cmpi.w #9,$ff139e
    bne.s stock_water
    ; 13 is the static sea color. Only pixels tagged 15 cycle.
    move.w #$8f02,$c00004
    move.l #$c03e0000,$c00004
    lea waves(pc),a0
    move.w (a0,d1.w),$c00000
    jmp $3de0a
stock_water:
    addq.l #6,a0
    move.l #$c006,d2
    jmp $3ddde
waves:
    dc.w $0640,$0660,$0862
    org $279080
ammo:
    cmpi.w #9,$ff139e
    bne.s consume
    cmpa.l $ff29e8,a0
    beq.s done
consume:
    subq.w #1,$12(a3)
done:
    rts

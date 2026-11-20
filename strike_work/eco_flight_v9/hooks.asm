    org $27b000
; The boot reader at $3ea already provides standard A/B/C/Start bits.
; A button becomes eligible after a neutral sample on that button and port.
; One held input cannot block unrelated buttons or a controller on the other port.
ea_skip:
    andi.w #$f0,d0
    andi.w #$f0,d1
    lsl.w #8,d1
    or.w d1,d0
    move.w d0,d1
    and.w $ff0000,d1
    bne.s .skip
    not.w d0
    or.w d0,$ff0000
    moveq #0,d0
    moveq #0,d1
    jmp $3be
.skip:
    jmp $3d2

    org $27b080
; The stock function also draws a separate selected-category overlay.
; In Eco Threat only the existing numbered-target path should draw dots.
map_targets:
    cmpi.w #9,$ff139e
    bne.s .draw
    tst.w $ff1022
    beq.s .skip
.draw:
    jmp $27a180
.skip:
    rts

    org $27b0c0
map_player:
    cmpi.w #9,$ff139e
    beq.s .targets
    movea.l #$18e0f0,a0
    jmp $39b82
.targets:
    jmp $39bd2

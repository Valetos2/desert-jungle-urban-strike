 org $274000
debug_z:
 movem.l d0-d7/a0-a6,-(sp)
 cmpi.w #9,$ff139e
 bne.s done
 btst #8,d0
 beq.s released
 bset #0,$ff4080
 bne.s done
 lea $ff10da,a0
 moveq #0,d0
scan:
 move.w (a0)+,d1
 bmi.s found
 addq.w #1,d0
 cmpi.w #8,d0
 bne.s scan
 bra.s done
found:
 neg.w d1
 addq.w #1,d0
 jsr $44a30
 bra.s done
released:
 bclr #0,$ff4080
done:
 movem.l (sp)+,d0-d7/a0-a6
 move.b $ff1637,$ff126c
 rts
 org $274100
scroll:
 cmpi.w #9,$ff139e
 bne.s orig
 movem.l d0-d7/a0-a6,-(sp)
 movea.l #$ff3c0c,a5
 jsr $4099e
 movem.l (sp)+,d0-d7/a0-a6
orig:
 lea 16(a2),a0
 lea (a2),a1
 rts
 org $274180
camera:
 jsr $40160
 cmpi.w #9,$ff139e
 bne.s setup
 ; Begin inside the northern shore and converge on the player at Y=40.
 cmpi.w #96,d3
 bge.s setup
 move.w #96,d3
setup:
 jmp $40608

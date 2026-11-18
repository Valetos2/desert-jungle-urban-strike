/* Preview adapter for the project's Genesis Plus GX md_ntsc filter. */
#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include <stdio.h>
#define CUSTOM_BLITTER
#include "md_ntsc.c"
#undef MD_NTSC_IN_FORMAT
#define MD_NTSC_IN_FORMAT MD_NTSC_BGR9
void preview(const unsigned short *in, unsigned short *out, int width, int height) {
    md_ntsc_t *filter = malloc(sizeof(*filter));
    md_ntsc_init(filter, &md_ntsc_composite);
    for(int y=0;y<height;y++) {
        const unsigned short *p=in+y*width;
        unsigned short *q=out+y*width*2;
        MD_NTSC_BEGIN_ROW(filter,0,p[0],p[1],p[2]);
        p+=3;
        for(int x=0;x<width/4-1;x++) {
            MD_NTSC_COLOR_IN(0,filter,*p++); MD_NTSC_RGB_OUT(0,*q++); MD_NTSC_RGB_OUT(1,*q++);
            MD_NTSC_COLOR_IN(1,filter,*p++); MD_NTSC_RGB_OUT(2,*q++); MD_NTSC_RGB_OUT(3,*q++);
            MD_NTSC_COLOR_IN(2,filter,*p++); MD_NTSC_RGB_OUT(4,*q++); MD_NTSC_RGB_OUT(5,*q++);
            MD_NTSC_COLOR_IN(3,filter,*p++); MD_NTSC_RGB_OUT(6,*q++); MD_NTSC_RGB_OUT(7,*q++);
        }
        MD_NTSC_COLOR_IN(0,filter,*p++); MD_NTSC_RGB_OUT(0,*q++); MD_NTSC_RGB_OUT(1,*q++);
        MD_NTSC_COLOR_IN(1,filter,0); MD_NTSC_RGB_OUT(2,*q++); MD_NTSC_RGB_OUT(3,*q++);
        MD_NTSC_COLOR_IN(2,filter,0); MD_NTSC_RGB_OUT(4,*q++); MD_NTSC_RGB_OUT(5,*q++);
        MD_NTSC_COLOR_IN(3,filter,0); MD_NTSC_RGB_OUT(6,*q++); MD_NTSC_RGB_OUT(7,*q++);
    }
    free(filter);
}

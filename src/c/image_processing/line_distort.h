#ifndef LINE_DISTORT_H
#define LINE_DISTORT_H

#include "utils.h"
#include <stdint.h>

typedef struct {
    uint8_t *image;
    int *segment_count_ptr;
    int width;
    int height;
    int rows;
    int *max_y;
} LineDistortParams;


SegmentArray *line_distort(LineDistortParams *params);

#endif // LINE_DISTORT_H

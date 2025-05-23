#ifndef WAVE_H
#define WAVE_H

#include <stdint.h>
#include "utils.h"

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

typedef struct {
    uint8_t *image_arr;
    int *segments_array_count_ptr;
    int width;
    int height;
    int ystep;
    double xstep;
    double xsmooth;
    double stroke_width;
} WaveParams;

SegmentArray *wave(WaveParams *params);
void write_wave_segments_to_file(SegmentArray *segment_ptr, int count, char *file_path);

#endif // WAVE_H

#ifndef UTILS_H
#define UTILS_H

#define _USE_MATH_DEFINES
#include <math.h>  // for M_PI
#include <stdlib.h> // for free()
#include <stdint.h>

typedef struct {
    double *segment_arr;
    int segment_count;
    int segment_size;
    int segments_allocated;
} SegmentArray;

float radian(float angle);
void free_mem(int *ptr);
void free_segments_array(SegmentArray *arr, int count);
void get_min_max(uint8_t *arr, int width, int height, float *min, float *max);
float map(float value, float in_min, float in_max, float out_min, float out_max);

#endif // UTILS_H

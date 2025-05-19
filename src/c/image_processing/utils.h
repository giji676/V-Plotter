#ifndef UTILS_H
#define UTILS_H

#define _USE_MATH_DEFINES
#include <math.h>  // for M_PI
#include <stdlib.h> // for free()

typedef struct {
    double* segment_arr;
    int segment_count;
    int segment_size;
    int segments_allocated;
} SegmentArray;

float radian(float angle);
void free_mem(int* ptr);
void free_segments_array(SegmentArray* arr, int count);

#endif // UTILS_H

#ifndef CROSS_HATCHING_H
#define CROSS_HATCHING_H

#include <stdint.h>

typedef struct {
    uint8_t* image;
    int* segment_count_ptr;
    int width;
    int height;
    int layers;
    int layer;
    int spacing;
    float starting_angle;
    float delta_angle;
} CrossHatchParams;

void write_segments_to_file(int* segments_ptr, int segment_count, int segment_size, char* file_path);
int* cross_hatch(CrossHatchParams* params);

#endif // CROSS_HATCHING_H


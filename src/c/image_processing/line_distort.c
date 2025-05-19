#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "line_distort.h"
#include "utils.h"

void line_distort(LineDistortParams *params) {
    uint8_t *image = params->image;
    int width = params->width;
    int height = params->height;
    int rows = params->rows;

    float y_scaler = (float)height/rows;
    int max_height = (int)y_scaler*2; // Z height will be scaled to this. Line distort will not go over this value
    float min;
    float max;
    /* TODO: only go over the values that are part of the row, not every y */
    get_min_max(image, width, height, &min, &max);

    SegmentArray* segment_arrays = malloc(rows * sizeof(SegmentArray) * 2);

    for (int y = 0; y < rows; y++) {
        for (int x = 0; x < width; x++) {
            int index = (int)(y * y_scaler * width + x);
            uint8_t z = (uint8_t)(image[index]);
            float scaled_z = map(z, min, max, 0, max_height);
        }
    }
}

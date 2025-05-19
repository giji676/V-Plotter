#include <minwindef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <synchapi.h>
#include <windows.h>
#include <stdlib.h>

typedef struct {
    uint8_t *image;
    int *segment_count_ptr;
    int width;
    int height;
    int rows;
    int *max_y;
} LineDistortParams;

typedef struct {
    double* segment_arr;
    int segment_count;
    int segment_size;
    int segments_allocated;
} SegmentArray;

void getMinMax(uint8_t *arr, int width, int height, float *min, float *max);
float mapRange(float value, float in_min, float in_max, float out_min, float out_max);

void lineDistort(LineDistortParams *params) {
    uint8_t *image = params->image;
    int width = params->width;
    int height = params->height;
    int rows = params->rows;

    float y_scaler = (float)height/rows;
    int max_height = (int)y_scaler*2; // Z height will be scaled to this. Line distort will not go over this value
    float min;
    float max;
    /* TODO: only go over the values that are part of the row, not every y */
    getMinMax(image, width, height, &min, &max);

    SegmentArray* segment_arrays = malloc(rows * sizeof(SegmentArray) * 2);

    for (int y = 0; y < rows; y++) {
        for (int x = 0; x < width; x++) {
            int index = (int)(y * y_scaler * width + x);
            uint8_t z = (uint8_t)(image[index]);
            float scaled_z = mapRange(z, min, max, 0, max_height);
        }
    }
}

void getMinMax(uint8_t *arr, int width, int height, float *min, float *max) {
    if (width <= 0 || height <= 0 || arr == NULL || min == NULL || max == NULL) return;

    *min = arr[0];
    *max = arr[0];

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            if (arr[y*width+x] < *min) *min = arr[y*width+x];
            if (arr[y*width+x] > *max) *max = arr[y*width+x];
        }
    }
}

float mapRange(float value, float in_min, float in_max, float out_min, float out_max) {
    if (in_max == in_min) return out_min;  // Avoid divide-by-zero
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

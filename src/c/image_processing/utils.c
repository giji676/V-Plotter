#include "utils.h"

float radian(float angle) {
    return angle * M_PI / 180.0;
}

void free_mem(int *ptr) {
    free(ptr);
}

void free_segments_array(SegmentArray *arr, int count) {
    for (int i = 0; i < count; i++) {
        if (arr[i].segment_arr != NULL) {
            free(arr[i].segment_arr);
        }
    }
    free(arr);
}

void get_min_max(uint8_t *arr, int width, int height, float *min, float *max) {
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

float map(float value, float in_min, float in_max, float out_min, float out_max) {
    if (in_max == in_min) return out_min;  // Avoid divide-by-zero
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

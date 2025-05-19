#include "utils.h"

float radian(float angle) {
    return angle * M_PI / 180.0;
}

void free_mem(int* ptr) {
    free(ptr);
}

void free_segments_array(SegmentArray* arr, int count) {
    for (int i = 0; i < count; i++) {
        if (arr[i].segment_arr != NULL) {
            free(arr[i].segment_arr);
        }
    }
    free(arr);
}

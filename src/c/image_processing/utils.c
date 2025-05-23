#include <stdio.h>
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

void init_segments_array(SegmentArray *segment_ptr, int count) {
    segment_ptr->segment_count = 0;
    segment_ptr->segment_arr = malloc(sizeof(double) * count);
    if (segment_ptr->segment_arr == NULL) {
        printf("Failed to allocate memory for SegmentArray\n");
        exit(-1);
    }
    segment_ptr->segments_allocated = count;
}

void append_segments_array(SegmentArray *segment_ptr, double value) {
    if (segment_ptr->segment_count >= segment_ptr->segments_allocated) {
        double *temp = realloc(segment_ptr->segment_arr, sizeof(double) * segment_ptr->segments_allocated * 2);
        if (temp == NULL) {
            printf("Failed to expand memory for SegmentArray\n");
            exit(-1);
        }
        segment_ptr->segment_arr = temp;
        segment_ptr->segments_allocated *= 2;
    }
    segment_ptr->segment_arr[segment_ptr->segment_count] = value;
    segment_ptr->segment_count++;
}

void reverse_array(double arr[], int start, int end) {
    double temp;
    while (start < end) {
        temp = arr[start];
        arr[start] = arr[end];
        arr[end] = temp;
        start++;
        end--;
    }
}

void write_segments_to_file(SegmentArray *segment_ptr, int count, char *file_path) {
    FILE *fptr = fopen(file_path, "w");

    if (!fptr) {
        perror("Error opening file");
        return;
    }

    SegmentArray x_points;
    SegmentArray y_points;
    for (int i = 0; i < count; i+=2) {
        x_points = segment_ptr[i+0];
        y_points = segment_ptr[i+1];
        for (int j = 0; j < x_points.segment_count; j++) {
            double x = x_points.segment_arr[j];
            double y = y_points.segment_arr[j];
            fprintf(fptr, "%f %f\n", x, y);
        }
    }
    fclose(fptr);
}

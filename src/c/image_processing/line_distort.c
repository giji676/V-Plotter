#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include "line_distort.h"
#include "utils.h"

SegmentArray *line_distort(LineDistortParams *params) {
    uint8_t *image = params->image;
    int *segment_count_ptr = params->segment_count_ptr;
    int width = params->width;
    int height = params->height;
    int rows = params->rows;
    float distort_mult = params->distort_mult;
    int *max_y_ptr = params->max_y;

    float y_scaler = (float)height/rows;
    int max_height = (int)y_scaler*distort_mult; // Z height will be scaled to this. Line distort will not go over this value
    float min;
    float max;
    /* TODO: only go over the values that are part of the row, not every y */
    get_min_max(image, width, height, &min, &max);
    *max_y_ptr = height+max_height;

    SegmentArray* segment_arrays = malloc(rows * sizeof(SegmentArray) * 2);

    int idx = 0;
    bool segment_start = false;
    bool reverse_row = false;

    for (int y = 0; y < rows; y++) {
        int iy = (int)y*y_scaler;
        SegmentArray *x_points = &segment_arrays[idx+0];
        SegmentArray *y_points = &segment_arrays[idx+1];
        int start_points_count = 0;
        int points_count = 0;
        int end_points_count = 0;

        init_segments_array(x_points, width);
        init_segments_array(y_points, width);

        for (int x = 0; x < width; x++) {
            int index = (iy * width + x);
            uint8_t z = (uint8_t)(image[index]);
            double scaled_z = map(z, min, max, 0, max_height);
            if (x == 0) {
                append_segments_array(x_points, x);
                append_segments_array(y_points, scaled_z + iy);
                segment_start = true;
            } else {
                if (segment_start) {
                    append_segments_array(x_points, x);
                    append_segments_array(y_points, scaled_z + iy);
                    segment_start = false;
                } else if (x-1 > 0) {
                    if (x_points->segment_arr[x-1] == x &&
                        y_points->segment_arr[x-1] == scaled_z + iy) {
                        x_points->segment_arr[x] = x;
                        y_points->segment_arr[x] = scaled_z + iy;
                        segment_start = false;
                    } else {
                        append_segments_array(x_points, x);
                        append_segments_array(y_points, scaled_z + iy);
                        segment_start = false;
                    }
                }
            }
        }
        if (reverse_row) {
            reverse_array(x_points->segment_arr, 0, width-1);
            reverse_array(y_points->segment_arr, 0, width-1);
        }
        reverse_row = !reverse_row;
        segment_start = false;
        idx+=2;
    }
    *segment_count_ptr = idx;

    return segment_arrays;
}

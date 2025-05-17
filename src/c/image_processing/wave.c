#include <minwindef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

// 0.488secs default params

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

typedef struct {
    uint8_t* image_arr;
    int* segments_array_count_ptr;
    int width;
    int height;
    int ystep;
    int xsmooth;
    float xstep;
    float stroke_width;
} WaveParams;

typedef struct {
    float* segment_arr;
    int segment_count;
    int segment_size;
    int segments_allocated;
} SegmentArray;

void initSegmentsArray(SegmentArray* segment_ptr, int count);
void appendSegmentsArray(SegmentArray* arr, float value);
void freeArray(SegmentArray* arr);
void reverseArray(float arr[], int start, int end);

SegmentArray* wave(WaveParams* params) {
    float TWO_PI = 2 * M_PI;
    float HALF_PI = 0.5 * M_PI;
    float IMAGE_SCALE_UP = 3;

    uint8_t *image_arr = params->image_arr;
    int* segments_array_count_ptr = params->segments_array_count_ptr;
    int width = params->width;
    int height = params->height;
    int ystep = params->ystep;
    float xsmooth = params->xsmooth;
    float xstep = params->xstep;
    float stroke_width = params->stroke_width;

    float min_phase_incr = 10 * TWO_PI / (width / xstep);
    float max_phase_incr =  TWO_PI * xstep / stroke_width;

    float scaled_y_step = (float)height / ystep;
    float ymult = IMAGE_SCALE_UP * 2;

    bool odd_row = FALSE;
    bool final_row = FALSE;
    bool reverse_row = FALSE;

    int l_x = -1;
    int l_y = -1;

    SegmentArray* segment_arrays = malloc(ystep * sizeof(SegmentArray) * 2);
    if (segment_arrays == NULL) {
        printf("Failed to allocate memory for segment arrays\n");
        return NULL;
    }

    int idx = 0;
    for (float y = 0; (int)y < height-1; y+=scaled_y_step) {
        SegmentArray *x_points = &segment_arrays[idx+0];
        SegmentArray *y_points = &segment_arrays[idx+1];
        int start_points_count = 0;
        int points_count = 0;
        int end_points_count = 0;
        x_points->segment_size = 2;
        y_points->segment_size = 2;

        initSegmentsArray(x_points, width*x_points->segment_size);
        initSegmentsArray(y_points, width*y_points->segment_size);

        odd_row = !odd_row;

        if (y + scaled_y_step >= height) {
            final_row = TRUE;
            reverse_row = !odd_row;
        }

        if (reverse_row) {
            if (y == 0) {
                appendSegmentsArray(x_points, width + 0.1 * xstep);
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                start_points_count++;
            }
            appendSegmentsArray(x_points, width);
            appendSegmentsArray(y_points, y + scaled_y_step/2);
            start_points_count++;
        } else {
            if (y == 0) {
                appendSegmentsArray(x_points, -(0.1 * xstep));
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                start_points_count++;
            }
            appendSegmentsArray(x_points, 0);
            appendSegmentsArray(y_points, y + scaled_y_step/2);
            start_points_count++;
        }

        float phase = 0;
        float last_phase = 0;
        float last_ampl = 0;
        bool final_step = FALSE;

        float x = 0;
        float last_x = 0;

        while (!final_step) {
            x += xstep;
            final_step = (x + xstep) >= width;

            int img_x = (int)x;
            int img_y = (int)y;
            if (img_x >= width || img_y >= height || img_x < 0 || img_y < 0) {
                printf("OVERSHOOT");
                break;  // or continue / skip as needed
            }
            float z = image_arr[img_y * width + img_x];
            float r = z / ystep * ymult;

            float df = z / xsmooth;
            df = MAX(df, min_phase_incr);
            df = MIN(df, max_phase_incr);

            phase += df;

            float delta_x = x - last_x;
            float delta_ampl = r - last_ampl;
            float delta_phase = phase - last_phase;

            if (!final_step) {
                if (delta_phase > HALF_PI) {
                    int vertex_count = floor(delta_phase / HALF_PI);
                    int integer_part = (vertex_count * HALF_PI) / delta_phase;

                    float delta_x_truncate = delta_x * integer_part;

                    float x_per_vertex =  delta_x_truncate / vertex_count;
                    float ampl_per_vertex = (integer_part * delta_ampl) / vertex_count;

                    for (int i = 0; i < vertex_count; i++) {
                        last_x = last_x + x_per_vertex;
                        last_phase = last_phase + HALF_PI;
                        last_ampl = last_ampl + ampl_per_vertex;
                        if (l_x == -1 && l_y == -1) {
                            l_x = last_x;
                            l_y = scaled_y_step/2 + (y + sin(last_phase) * last_ampl);
                        }
                        appendSegmentsArray(x_points, last_x);
                        appendSegmentsArray(y_points, scaled_y_step/2 + (y + sin(last_phase) * last_ampl));
                        points_count++;
                    }
                }
            }
        }
        if (reverse_row) {
            /*reverseArray(x_points->segment_arr, start_points_count, start_points_count + points_count - 1);*/
            /*reverseArray(y_points->segment_arr, start_points_count, start_points_count + points_count - 1);*/

            appendSegmentsArray(x_points, 0);
            appendSegmentsArray(y_points, y + scaled_y_step/2);
            end_points_count++;
            if (final_row) {
                appendSegmentsArray(x_points, -(0.1 * xstep));
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                end_points_count++;
            }
        } else {
            appendSegmentsArray(x_points, width);
            appendSegmentsArray(y_points, y + scaled_y_step/2);
            end_points_count++;
            if (final_row) {
                appendSegmentsArray(x_points, width + 0.1 * xstep);
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                end_points_count++;
            }
        }

        if (!final_row) {
            if (reverse_row) {
                appendSegmentsArray(x_points, -(0.1 * xstep));
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                end_points_count++;
            } else {
                appendSegmentsArray(x_points, width + 0.1 * xstep);
                appendSegmentsArray(y_points, y + scaled_y_step/2);
                end_points_count++;
            }
        }
        idx+=2;
    }
    *segments_array_count_ptr = idx;

    return segment_arrays;
}

void initSegmentsArray(SegmentArray* segment_ptr, int count) {
    segment_ptr->segment_count = 0;
    segment_ptr->segment_arr = malloc(sizeof(float) * count * segment_ptr->segment_size);
    if (segment_ptr->segment_arr == NULL) {
        printf("Failed to allocate memory for SegmentArray\n");
        exit(-1);
    }
    segment_ptr->segments_allocated = count * segment_ptr->segment_size;
}

void appendSegmentsArray(SegmentArray* segment_ptr, float value) {
    if (segment_ptr->segment_count >= segment_ptr->segments_allocated) {
        float *temp = realloc(segment_ptr->segment_arr, sizeof(float) * segment_ptr->segments_allocated * 2);
        if (temp == NULL) {
            printf("Failed to expand memory for SegmentArray\n");
            exit(-1);
        }
        segment_ptr->segment_arr = temp;
        segment_ptr->segments_allocated *= 2;
    }
    /*printf("%f\n", value);*/
    segment_ptr->segment_arr[segment_ptr->segment_count] = value;
    segment_ptr->segment_count++;
}

void reverseArray(float arr[], int start, int end) {
    float temp;
    while (start < end) {
        temp = arr[start];
        arr[start] = arr[end];
        arr[end] = temp;
        start++;
        end--;
    }
}

void freeAllSegments(SegmentArray* arr, int count) {
    for (int i = 0; i < count; i++) {
        if (arr[i].segment_arr != NULL) {
            free(arr[i].segment_arr);
        }
    }
    free(arr);
}

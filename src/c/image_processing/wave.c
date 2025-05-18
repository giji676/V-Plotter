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
    double xstep;
    double xsmooth;
    double stroke_width;
} WaveParams;

typedef struct {
    double* segment_arr;
    int segment_count;
    int segment_size;
    int segments_allocated;
} SegmentArray;

void initSegmentsArray(SegmentArray* segment_ptr, int count);
void appendSegmentsArray(SegmentArray* arr, double value);
void freeArray(SegmentArray* arr);
void reverseArray(double arr[], int start, int end);
void writeWaveSegmentsToFile(SegmentArray* segment_ptr, int count, char* file_path);

SegmentArray* wave(WaveParams* params) {
    double TWO_PI = 2 * M_PI;
    double HALF_PI = 0.5 * M_PI;
    double IMAGE_SCALE_UP = 3;

    uint8_t *image_arr = params->image_arr;
    int* segments_array_count_ptr = params->segments_array_count_ptr;
    int width = params->width;
    int height = params->height;
    int ystep = params->ystep;
    double xstep = params->xstep;
    double xsmooth = params->xsmooth;
    double stroke_width = params->stroke_width;

    double min_phase_incr = 10 * TWO_PI / (width / xstep);
    double max_phase_incr =  TWO_PI * xstep / stroke_width;

    double scaled_y_step = (double)height / ystep;
    double ymult = IMAGE_SCALE_UP * 2;

    bool odd_row = FALSE;
    bool final_row = FALSE;
    bool reverse_row = FALSE;

    bool l_set = FALSE;
    double l_x;
    double l_y;

    SegmentArray* segment_arrays = malloc(ystep * sizeof(SegmentArray) * 2);
    if (segment_arrays == NULL) {
        printf("Failed to allocate memory for segment arrays\n");
        return NULL;
    }

    int idx = 0;
    for (double y = 0; (int)y < height - 1; y += scaled_y_step) {
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
        }
        reverse_row = !odd_row;

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

        double phase = 0;
        double last_phase = 0;
        double last_ampl = 0;
        bool final_step = FALSE;

        double x = 1;
        double last_x = 1;

        while (!final_step) {
            x += xstep;
            final_step = (x + xstep) >= width;

            double z = image_arr[(int)y * width + (int)x];
            double r = z / ystep * ymult;

            double df = z / xsmooth;
            df = MAX(df, min_phase_incr);
            df = MIN(df, max_phase_incr);

            phase += df;

            double delta_x = x - last_x;
            double delta_ampl = r - last_ampl;
            double delta_phase = phase - last_phase;

            if (!final_step) {
                if (delta_phase > HALF_PI) {
                    double vertex_count = floor(delta_phase / HALF_PI);
                    double integer_part = (vertex_count * HALF_PI) / delta_phase;

                    double delta_x_truncate = delta_x * integer_part;

                    double x_per_vertex =  delta_x_truncate / vertex_count;
                    double ampl_per_vertex = (integer_part * delta_ampl) / vertex_count;

                    for (int i = 0; i < (int)vertex_count; i++) {
                        last_x = last_x + x_per_vertex;
                        last_phase = last_phase + HALF_PI;
                        last_ampl = last_ampl + ampl_per_vertex;
                        if (!l_set) {
                            l_x = last_x;
                            l_y = scaled_y_step/2 + (y + sin(last_phase) * last_ampl);
                            l_set = TRUE;
                        }
                        appendSegmentsArray(x_points, last_x);
                        appendSegmentsArray(y_points, scaled_y_step/2 + (y + sin(last_phase) * last_ampl));
                        points_count++;
                    }
                }
            }
        }
        if (reverse_row) {
            reverseArray(x_points->segment_arr, start_points_count, start_points_count + points_count - 1);
            reverseArray(y_points->segment_arr, start_points_count, start_points_count + points_count - 1);

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
    segment_ptr->segment_arr = malloc(sizeof(double) * count);
    if (segment_ptr->segment_arr == NULL) {
        printf("Failed to allocate memory for SegmentArray\n");
        exit(-1);
    }
    segment_ptr->segments_allocated = count;
}
void appendSegmentsArray(SegmentArray* segment_ptr, double value) {
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

void reverseArray(double arr[], int start, int end) {
    double temp;
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

void writeWaveSegmentsToFile(SegmentArray* segment_ptr, int count, char* file_path) {
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

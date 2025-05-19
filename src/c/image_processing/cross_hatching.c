#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <stdlib.h>
#include "cross_hatching.h"
#include "utils.h"

int *cross_hatch(CrossHatchParams *params) {
    uint8_t *image = params->image;
    int *segment_count_ptr = params->segment_count_ptr;
    int width = params->width;
    int height = params->height;
    int layers = params->layers;
    int layer = params->layer;
    int spacing = params->spacing;
    float starting_angle = params->starting_angle;
    float delta_angle = params->delta_angle;

    float angle_deg = starting_angle + layer * delta_angle;
    float angle_rad = radian(angle_deg);
    int color_scaler = 255/(layers+1);

    // Direction of the hatching lines
    float dx = cos(angle_rad);
    float dy = sin(angle_rad);

    // Perpendicular direction for spacing
    float pdx = -dy;
    float pdy = dx;

    // Maximum distance to cover the image diagonally
    int diag = (int)hypot(width, height);
    float step_size = 0.5;

    int segment_size = 4; // Size of a sinalge segment (x1,y1,x2,y2)
    int segments_allocation_increment = 400;
    int segments_allocated = segments_allocation_increment;
    int *segments_ptr = malloc(segment_size * segments_allocated * sizeof(int));
    if (segments_ptr == NULL) {
        printf("Failed to allocate memory for segments\n");
        return NULL;
    }
    int segment_count = -1;

    int layer_offset = (rand() % (2 * spacing + 1)) - spacing;

    for (int i = -diag/2; i <= diag/2; i+=spacing) {
        float cx = width/2.0 + pdx*i - dx*diag/2 + layer_offset;
        float cy = height/2.0 + pdy*i - dy*diag/2 + layer_offset;

        bool started = false;
        for (int j = 0; j <= (int)diag/step_size; j++) {
            cx += dx*step_size;
            cy += dy*step_size;
            if (cx < 0 || cx >= width || cy < 0 || cy >= height) {
                continue;
            }
            int index = (int)cy * width + (int)cx;
            uint8_t color = (uint8_t)(image[index]);
            if (color / color_scaler <= layer) {
                if (!started) {
                    segment_count++;

                    if (segment_count == segments_allocated) {
                        // If allocated memory is full, allocate space for segments_allocation_increment more segments
                        int *temp = realloc(segments_ptr,
                                            (segments_allocated + segments_allocation_increment) * segment_size * sizeof(int));
                        if (temp == NULL) {
                            printf("Failed to reallocate memory for segments\n");
                            return NULL;
                        }
                        segments_ptr = temp;
                        segments_allocated += segments_allocation_increment;
                    }

                    started = true;
                    segments_ptr[segment_count*segment_size+0] = (int)cx;
                    segments_ptr[segment_count*segment_size+1] = (int)cy;
                }
                segments_ptr[segment_count*segment_size+2] = (int)cx;
                segments_ptr[segment_count*segment_size+3] = (int)cy;
            } else if (started) {
                started = false;
            }
        }
    }
    *segment_count_ptr = segment_count;

    return segments_ptr;
}

void write_segments_to_file(int *segments_ptr, int segment_count, int segment_size, char *file_path) {
    int base;
    int x1, y1, x2, y2;
    FILE *fptr = fopen(file_path, "w");

    if (!fptr) {
        perror("Error opening file");
        return;
    }

    for (int i = 0; i < segment_count; i++) {
        base = i * segment_size;
        x1 = segments_ptr[base + 0];
        y1 = segments_ptr[base + 1];
        x2 = segments_ptr[base + 2];
        y2 = segments_ptr[base + 3];
        fprintf(fptr, "%d %d\n", x1, y1);
        fprintf(fptr, "PENDOWN\n");
        fprintf(fptr, "%d %d\n", x2, y2);
        fprintf(fptr, "PENUP\n");
    }
    fclose(fptr);
}

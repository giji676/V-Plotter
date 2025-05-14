#include <stdio.h>

unsigned char* process_image(unsigned char* data, int width, int height) {
    printf("Image (%dx%d):\n", width, height);
    printf("PTR ADDR: %p:\n", data);
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            int idx = (y * width + x)*3;
            int r = idx + 0;
            int g = idx + 1;
            int b = idx + 2;
            printf("(%d %d %d)", data[r], data[g], data[b]);
            data[r] += 2;
            data[g] += 2;
            data[b] += 2;
        }
        printf("\n");
    }
    return data;
}

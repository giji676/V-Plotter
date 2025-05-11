# Compiler and flags
CC = x86_64-w64-mingw32-gcc
CFLAGS = -shared -fPIC   # Generate position-independent code for DLLs
LDFLAGS = -shared

# Directories
SRC_DIR = src/c/image_processing
BUILD_DIR = build_c
OUTPUT_DIR = output
OUT_NAME = image.dll

# Source and object files
SRC_FILES := $(wildcard $(SRC_DIR)/*.c)
OBJ_FILES := $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(SRC_FILES))

# Default target
all: $(OUTPUT_DIR)/$(OUT_NAME)

# Link object files into DLL
$(OUTPUT_DIR)/$(OUT_NAME): $(OBJ_FILES) | $(OUTPUT_DIR)
	@echo "Linking object files into DLL..."
	$(CC) $(LDFLAGS) -o $@ $^

# Compile C files into object files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -o $@ -c $<

# Create build and output directories if they don't exist
$(BUILD_DIR):
	@mkdir -p $@

$(OUTPUT_DIR):
	@mkdir -p $@

# Clean rule
clean:
	@echo "Cleaning..."
	rm -rf $(BUILD_DIR) $(OUTPUT_DIR)

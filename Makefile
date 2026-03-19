CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lpthread -lrt

TARGET  = timer_threads

.PHONY: all clean run

all: $(TARGET)

$(TARGET): timer_threads.c
	$(CC) $(CFLAGS) -o $(TARGET) timer_threads.c $(LDFLAGS)
	@echo "Build successful: ./$(TARGET)"

clean:
	rm -f $(TARGET) time_and_interval.txt freq.txt interval_analysis.png

run: all
	@echo "Starting C program in background..."
	./$(TARGET) &
	@echo "Starting frequency changer script..."
	bash change_freq.sh

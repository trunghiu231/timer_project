#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <stdint.h>

/*Chương trình này dùng để đo: thời gian thực tế mỗi lần gọi clock_nanosleep() tốn bao nhiêu ns
Compile: gcc -O2 -o measure_sleep_overhead measure_sleep_overhead.c
chạy với quyền run_time: sudo ./measure_sleep_overhead
*/

/* ─── Helper: lấy thời gian ns ───────────────────────────── */
static inline long long get_time_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

/* ─── Main đo overhead ───────────────────────────────────── */
int main(void)
{
/* ─── Lấy mốc thời gian ban đầu ───────────────────────────── */

    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);

    long long t0 = get_time_ns();

    const int N = 10000;

    for (int i = 0; i < N; i++) {
        /* tăng deadline thêm 1µs */
        ts.tv_nsec += 1000;
        /*Chuẩn hóa nanosecond*/
        if (ts.tv_nsec >= 1000000000LL) {
            ts.tv_nsec -= 1000000000LL;
            ts.tv_sec++;
        }

        /* sleep theo thời gian tuyệt đối */
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
    }

    long long t1 = get_time_ns(); //tổng thời gian toàn bộ vòng lặp

    long long avg = (t1 - t0) / N; //thời gian trung bình mỗi vòng lặp

    printf("clock_nanosleep avg = %lld ns\n", avg);

    return 0;
}
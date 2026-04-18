/*
 * Cần định nghĩa trước khi include để mở khoá POSIX clock API
 * và GNU extension (pthread_setaffinity_np, CPU_SET, ...)
 */
#define _GNU_SOURCE

/*
 * timer_threads.c
 * Linux Programming Assignment - gNodeB 5G VHT
 *
 * 3 threads:
 *   - SAMPLE:  Đọc thời gian hệ thống (ns) vào biến T với chu kì X ns
 *   - INPUT:   Theo dõi file "freq.txt", cập nhật chu kì X
 *   - LOGGING: Khi T được cập nhật, ghi T và interval vào "time_and_interval.txt"
 *
 * Compile: gcc -o timer_threads timer_threads.c -lpthread -lrt
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <stdint.h>
#include <signal.h>
#include <sched.h>      /* SCHED_FIFO, sched_param, pthread_setaffinity_np */
#include <errno.h>

/* ─── Shared state ────────────────────────────────────────────────────── */

/* Mutex + condvar bảo vệ biến T và flag new_sample */
static pthread_mutex_t  lock       = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t   cond_new_T = PTHREAD_COND_INITIALIZER;

static volatile long long T_ns    = 0;   /* thời gian hiện tại (ns) */
static volatile int       new_sample = 0;/* flag: T vừa được cập nhật */

/* Chu kì X (ns) – được bảo vệ bằng mutex riêng để INPUT cập nhật an toàn */
static pthread_mutex_t  period_lock = PTHREAD_MUTEX_INITIALIZER;
static volatile long long period_ns = 1000000LL; /* mặc định 1 ms */

/* Flag dừng chương trình */
static volatile int running = 1;

/* ─── Helper: đọc thời gian hệ thống (CLOCK_REALTIME) tính theo ns ─── */
static long long get_time_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

/* ─── Helper: sleep chính xác (ns) dùng clock_nanosleep ──────────────── */
static void sleep_relative_ns(long long ns)
{
    struct timespec req;
    req.tv_sec  = ns / 1000000000LL;
    req.tv_nsec = ns % 1000000000LL;
    /* loop lại nếu bị interrupt bởi signal */
    while (clock_nanosleep(CLOCK_MONOTONIC, 0, &req, &req) != 0)
        ;
}
/* ─── Helper: sleep chính xác tuyệt đối dùng clock_nanosleep với TIMER_ABSTIME ─── */
static void sleep_until(struct timespec *ts)
{
    while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, ts, NULL) != 0) {
        if (errno != EINTR) {
            perror("[SAMPLE] clock_nanosleep failed");
            break;
        }
        /* Nếu bị EINTR (signal), tiếp tục ngủ đến thời điểm tuyệt đối */
    }
}

/* ═══════════════════════════════════════════════════════════════════════
 * Thread SAMPLE
 * Cải tiến:
 *   1. SCHED_FIFO priority 99: thread không bị preempt bởi tiến trình thường
 *   2. CPU affinity core 1: tránh migration giữa các core, giảm cache miss
 *   3. Absolute deadline (next_wake): tránh drift tích luỹ
 * ═══════════════════════════════════════════════════════════════════════ */
static void *thread_sample(void *arg)
{
    (void)arg;

    /* ── Hướng 1: Đặt real-time scheduling policy SCHED_FIFO ── */
    struct sched_param sp;
    sp.sched_priority = 99;  /* mức cao nhất (1–99) */
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp) != 0) {
        perror("[SAMPLE] pthread_setschedparam (cần chạy sudo)");
    } else {
        printf("[SAMPLE] SCHED_FIFO priority 99 OK\n");
    }

    /* ── Hướng 2: Ghim thread vào CPU core 1 (CPU affinity) ── */
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(1, &cpuset);     /* core 1: tránh core 0 hay bận xử lý interrupt */
    if (pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset) != 0) {
        perror("[SAMPLE] pthread_setaffinity_np");
    } else {
        printf("[SAMPLE] CPU affinity → core 1 OK\n");
    }

    printf("[SAMPLE] Thread started.\n");

    /* Khởi tạo thời điểm tuyệt đối đầu tiên */
    struct timespec next_ts;
    clock_gettime(CLOCK_MONOTONIC, &next_ts);
    
    while (running) {
        /* 1. Đọc thời gian hệ thống */
        long long t = get_time_ns();

        /* 2. Cập nhật biến T và báo cho LOGGING */
        pthread_mutex_lock(&lock);
        T_ns       = t;
        new_sample = 1;
        pthread_cond_signal(&cond_new_T);
        pthread_mutex_unlock(&lock);

        /* 3. Đọc chu kì hiện tại */
        pthread_mutex_lock(&period_lock);
        long long X = period_ns;
        pthread_mutex_unlock(&period_lock);

        /* 4. Cập nhật deadline tuyệt đối (tránh drift) */
        next_ts.tv_nsec += X;
        while (next_ts.tv_nsec >= 1000000000LL) {
            next_ts.tv_nsec -= 1000000000LL;
            next_ts.tv_sec++;
        }

        /* 5. Ngủ tuyệt đối đến next_ts */
        sleep_until(&next_ts);
    }

    printf("[SAMPLE] Thread exiting.\n");
    return NULL;
}

/* ═══════════════════════════════════════════════════════════════════════
 * Thread INPUT
 * Kiểm tra file "freq.txt" mỗi 100 ms, cập nhật chu kì X nếu thay đổi
 * ═══════════════════════════════════════════════════════════════════════ */
static void *thread_input(void *arg)
{
    (void)arg;
    printf("[INPUT]  Thread started. Watching freq.txt ...\n");

    long long last_period = -1;   /* giá trị X lần đọc trước */

    while (running) {
        FILE *fp = fopen("freq.txt", "r");
        if (fp) {
            long long new_period;
            if (fscanf(fp, "%lld", &new_period) == 1 && new_period > 0) {
                if (new_period != last_period) {
                    pthread_mutex_lock(&period_lock);
                    period_ns = new_period;
                    pthread_mutex_unlock(&period_lock);
                    printf("[INPUT]  Period updated: %lld ns\n", new_period);
                    last_period = new_period;
                }
            }
            fclose(fp);
        }
        /* Kiểm tra mỗi 100 ms */
        sleep_relative_ns(100000000LL);
    }

    printf("[INPUT]  Thread exiting.\n");
    return NULL;
}

/* ═══════════════════════════════════════════════════════════════════════
 * Thread LOGGING
 * Chờ T được cập nhật rồi ghi ra "time_and_interval.txt"
 * ═══════════════════════════════════════════════════════════════════════ */
static void *thread_logging(void *arg)
{
    (void)arg;
    printf("[LOGGING] Thread started. Writing to time_and_interval.txt ...\n");

    FILE *fp = fopen("time_and_interval.txt", "w");
    if (!fp) {
        perror("[LOGGING] fopen");
        return NULL;
    }

    /* Header */
    fprintf(fp, "%-25s %-20s\n", "T (ns)", "Interval (ns)");
    fprintf(fp, "%-25s %-20s\n",
            "-------------------------", "--------------------");
    fflush(fp);

    long long prev_T = 0;
    int       first  = 1;

    while (running) {
        /* Chờ SAMPLE báo có mẫu mới */
        pthread_mutex_lock(&lock);
        while (!new_sample && running)
            pthread_cond_wait(&cond_new_T, &lock);

        if (!running) {
            pthread_mutex_unlock(&lock);
            break;
        }

        long long t = T_ns;
        new_sample  = 0;
        pthread_mutex_unlock(&lock);

        /* Tính interval */
        long long interval = first ? 0 : (t - prev_T);
        first = 0;
        prev_T = t;

        /* Ghi ra file */
        fprintf(fp, "%-25lld %-20lld\n", t, interval);
        fflush(fp);
    }

    fclose(fp);
    printf("[LOGGING] Thread exiting.\n");
    return NULL;
}

/* ─── Signal handler: Ctrl+C dừng chương trình gọn gàng ──────────────── */
static void handle_sigint(int sig)
{
    (void)sig;
    printf("\n[MAIN] SIGINT received, stopping...\n");
    running = 0;
    /* Đánh thức LOGGING khỏi cond_wait */
    pthread_mutex_lock(&lock);
    pthread_cond_broadcast(&cond_new_T);
    pthread_mutex_unlock(&lock);
}

/* ═══════════════════════════════════════════════════════════════════════
 * main
 * ═══════════════════════════════════════════════════════════════════════ */
int main(void)
{
    /* Tạo file freq.txt mặc định nếu chưa có */
    {
        FILE *f = fopen("freq.txt", "r");
        if (!f) {
            f = fopen("freq.txt", "w");
            if (f) { fprintf(f, "1000000\n"); fclose(f); }
        } else {
            fclose(f);
        }
    }

    signal(SIGINT, handle_sigint);

    pthread_t t_sample, t_input, t_logging;

    pthread_create(&t_logging, NULL, thread_logging, NULL);
    pthread_create(&t_input,   NULL, thread_input,   NULL);
    pthread_create(&t_sample,  NULL, thread_sample,  NULL);

    printf("[MAIN]   All threads running. Press Ctrl+C to stop.\n");

    pthread_join(t_sample,  NULL);
    pthread_join(t_input,   NULL);

    /* Đánh thức LOGGING một lần nữa đề phòng */
    pthread_mutex_lock(&lock);
    pthread_cond_broadcast(&cond_new_T);
    pthread_mutex_unlock(&lock);

    pthread_join(t_logging, NULL);

    printf("[MAIN]   Done. Results in time_and_interval.txt\n");
    return 0;
}
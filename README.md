# Linux Programming Assignment – Timer Threads

## Cấu trúc file

```
.
├── docs/
|   ├── linux_programming_interface_book.md
|   ├── linux_programming_interface_book/
|       ├── ch23_timers_and_sleeping.md
|       ├── ch29_threads_introduction.md
├── timer_threads.c       ← Chương trình C chính (3 threads)
├── change_freq.sh        ← Shell script đổi chu kì mỗi 1 phút
├── analyze_intervals.py  ← Script Python vẽ đồ thị phân tích
├── Makefile              ← Build helper
└── README.md             ← File này
```

## 1. Biên dịch chương trình C

```bash
make
# hoặc thủ công:
gcc -Wall -O2 -std=c11 -o timer_threads timer_threads.c -lpthread -lrt
```

## 2. Chạy chương trình (5 phút)

cd ~/Documents/timer_project
sudo ./timer_threads &
bash change_freq.sh

## 3. Phân tích kết quả

Cài thư viện Python (1 lần):
```bash
pip install matplotlib numpy
```

Vẽ đồ thị:
```bash
python3 analyze_intervals.py time_and_interval.txt
```

Kết quả: file `interval_analysis.png` với 5 subplot, mỗi subplot tương ứng một chu kì X.

## Kiến trúc chương trình

```
┌─────────────┐   clock_gettime()   ┌──────────────────────────┐
│   SAMPLE    │ ──────────────────▶ │  T_ns (global, ns)       │
│  (chu kì X) │                     └───────────┬──────────────┘
└─────────────┘                                 │ mutex + condvar
                                                ▼
                                     ┌──────────────────────────┐
                                     │   LOGGING                │
                                     │  ghi T + interval →      │
                                     │  time_and_interval.txt   │
                                     └──────────────────────────┘
┌─────────────┐   đọc freq.txt
│   INPUT     │ ─────────────▶  period_ns (global, ns)
│  (100 ms)   │                  ▲
└─────────────┘                  │ SAMPLE đọc chu kì từ đây
                                 │
                           echo X > freq.txt  ← người dùng / script
```

## Lưu ý kỹ thuật

| Vấn đề | Giải pháp |
|---|---|
| Đọc thời gian ns | `clock_gettime(CLOCK_REALTIME, &ts)` |
| Sleep chính xác ns | `clock_nanosleep(CLOCK_MONOTONIC, ...)` |
| Đồng bộ SAMPLE↔LOGGING | `pthread_mutex` + `pthread_cond_wait` |
| Đồng bộ INPUT↔SAMPLE | `pthread_mutex` riêng bảo vệ `period_ns` |
| Dừng sạch | `SIGINT` handler đặt `running=0` + broadcast condvar |
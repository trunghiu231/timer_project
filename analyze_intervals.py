#!/usr/bin/env python3
"""
analyze_intervals.py
Đọc file time_and_interval.txt, vẽ đồ thị interval theo từng chu kì X.

Cách dùng:
    python3 analyze_intervals.py [time_and_interval.txt]

Yêu cầu: pip install matplotlib numpy pandas
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ─── 1. Đọc dữ liệu ────────────────────────────────────────────────────
fname = sys.argv[1] if len(sys.argv) > 1 else "time_and_interval.txt"

T_list        = []
interval_list = []

with open(fname, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("T") or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            T_list.append(int(parts[0]))
            interval_list.append(int(parts[1]))
        except ValueError:
            continue

T        = np.array(T_list,        dtype=np.int64)
interval = np.array(interval_list, dtype=np.int64)

# Bỏ sample đầu (interval = 0)
mask     = interval > 0
T        = T[mask]
interval = interval[mask]

if len(T) == 0:
    print("Không có dữ liệu hợp lệ trong file.")
    sys.exit(1)

# ─── 2. Phân chia theo chu kì X (5 giai đoạn × 1 phút) ────────────────
# Mỗi giai đoạn kéo dài 60 giây = 60e9 ns
T0          = T[0]
PERIOD_SECS = 60
NS_PER_PERIOD = PERIOD_SECS * 1_000_000_000

PERIOD_LABELS = {
    0: "X = 1,000,000 ns (1 ms)",
    1: "X = 100,000 ns (100 µs)",
    2: "X = 10,000 ns (10 µs)",
    3: "X = 1,000 ns (1 µs)",
    4: "X = 100 ns (100 ns)",
}
EXPECTED_NS = [1_000_000, 100_000, 10_000, 1_000, 100]
COLORS      = ['steelblue', 'darkorange', 'green', 'red', 'purple']

phase = ((T - T0) // NS_PER_PERIOD).clip(0, 4)

# ─── 3. Vẽ đồ thị ───────────────────────────────────────────────────────
fig, axes = plt.subplots(5, 1, figsize=(14, 18))
fig.suptitle("Interval theo từng chu kì lấy mẫu X\n(Linux Timer Threads Assignment)",
             fontsize=14, fontweight='bold', y=0.98)

for p in range(5):
    ax  = axes[p]
    idx = phase == p
    if not np.any(idx):
        ax.set_title(f"{PERIOD_LABELS[p]}  — không có dữ liệu")
        continue

    t_rel = (T[idx] - T[idx][0]) / 1e6   # ms
    iv    = interval[idx] / 1e3           # µs

    ax.plot(t_rel, iv, color=COLORS[p], linewidth=0.6, alpha=0.8)
    ax.axhline(EXPECTED_NS[p] / 1e3, color='black', linestyle='--',
               linewidth=1.0, label=f"Lý thuyết = {EXPECTED_NS[p]/1e3:.0f} µs")

    mean_iv = np.mean(iv)
    std_iv  = np.std(iv)
    ax.axhline(mean_iv, color='red', linestyle=':', linewidth=1.0,
               label=f"Mean = {mean_iv:.2f} µs  |  Std = {std_iv:.2f} µs")

    ax.set_title(PERIOD_LABELS[p], fontsize=11, fontweight='bold')
    ax.set_xlabel("Thời gian tương đối (ms)")
    ax.set_ylabel("Interval (µs)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Clip trục Y để dễ nhìn (bỏ outlier cực lớn)
    p95 = np.percentile(iv, 95)
    ax.set_ylim(0, max(p95 * 2, EXPECTED_NS[p] / 1e3 * 3))

plt.tight_layout(rect=[0, 0, 1, 0.97])
out_file = "interval_analysis.png"
plt.savefig(out_file, dpi=150, bbox_inches='tight')
print(f"[PLOT] Saved → {out_file}")

# ─── 4. In thống kê ─────────────────────────────────────────────────────
print("\n{'─'*65}")
print(f"{'Giai đoạn':<30} {'N':>7} {'Mean (ns)':>12} {'Std (ns)':>12} {'Max (ns)':>12}")
print("─" * 65)
for p in range(5):
    idx = phase == p
    if not np.any(idx):
        print(f"{PERIOD_LABELS[p]:<30} {'N/A':>7}")
        continue
    iv_ns = interval[idx]
    print(f"{PERIOD_LABELS[p]:<30} {np.sum(idx):>7} "
          f"{np.mean(iv_ns):>12.0f} {np.std(iv_ns):>12.0f} {np.max(iv_ns):>12.0f}")
print("─" * 65)
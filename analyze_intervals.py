#!/usr/bin/env python3
"""
analyze_intervals.py - Full version (fixed + optimized)
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ─── 1. Đọc dữ liệu ────────────────────────────────────────────────────
fname = sys.argv[1] if len(sys.argv) > 1 else "time_and_interval.txt"

T_list = []
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

T = np.array(T_list, dtype=np.int64)
interval = np.array(interval_list, dtype=np.int64)

# Bỏ interval = 0
mask = interval > 0
T = T[mask]
interval = interval[mask]

if len(T) == 0:
    print("Không có dữ liệu hợp lệ.")
    sys.exit(1)

# ─── 2. Phân chia theo chu kỳ ──────────────────────────────────────────
T0 = T[0]
NS_PER_PERIOD = 60 * 1_000_000_000

PERIOD_LABELS = {
    0: "X = 1,000,000 ns (1 ms)",
    1: "X = 100,000 ns   (100 µs)",
    2: "X = 10,000 ns    (10 µs)",
    3: "X = 1,000 ns     (1 µs)",
    4: "X = 100 ns       (100 ns)",
}

EXPECTED_NS = [1_000_000, 100_000, 10_000, 1_000, 100]
COLORS = ['steelblue', 'darkorange', 'green', 'red', 'purple']

phase = ((T - T0) // NS_PER_PERIOD).clip(0, 4)

# ─── 3. Vẽ đồ thị ──────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 20))
gs = fig.add_gridspec(5, 2, height_ratios=[1, 1, 1, 1, 1])

axes = [fig.add_subplot(gs[i, 0]) for i in range(5)]
hist_axes = [fig.add_subplot(gs[i, 1]) for i in range(5)]

fig.suptitle(
    "Phân tích Interval theo từng chu kỳ X\n(Linux Thread Sampling Assignment)",
    fontsize=16, fontweight='bold', y=0.98
)

# ─── LOOP CHÍNH ────────────────────────────────────────────────────────
for p in range(5):
    ax = axes[p]
    hax = hist_axes[p]
    idx = phase == p

    if not np.any(idx):
        ax.set_title(f"{PERIOD_LABELS[p]} — Không có dữ liệu")
        continue

    iv_full = interval[idx]
    t_rel_full = T[idx] - T[idx][0]

    # ─── Downsample để tránh bị Killed ───────────────────────────────
    MAX_POINTS = 20000
    if len(iv_full) > MAX_POINTS:
        step = len(iv_full) // MAX_POINTS
        iv = iv_full[::step]
        t_rel = t_rel_full[::step]
    else:
        iv = iv_full
        t_rel = t_rel_full

    # ─── Metric (LUÔN dùng full data) ───────────────────────────────
    mean_iv = np.mean(iv_full)
    std_iv  = np.std(iv_full, ddof=1)
    min_iv  = np.min(iv_full)
    max_iv  = np.max(iv_full)
    target  = EXPECTED_NS[p]

    # ─── LINE PLOT ──────────────────────────────────────────────────
    ax.plot(t_rel, iv, color=COLORS[p], linewidth=0.7, alpha=0.85)

    ax.axhline(target, color='black', linestyle='--', linewidth=1.2,
               label=f'Target = {target:,} ns')

    ax.axhline(mean_iv, color='red', linestyle=':', linewidth=1.2,
               label=f'Mean = {mean_iv:,.0f} ns | Std = {std_iv:,.1f} ns')

    ax.axhline(min_iv, color='blue', linestyle='-.', linewidth=1.0,
               label=f'Min = {min_iv:,.0f} ns')

    ax.axhline(max_iv, color='darkred', linestyle='-.', linewidth=1.0,
               label=f'Max = {max_iv:,.0f} ns')

    ax.set_title(PERIOD_LABELS[p], fontsize=11, fontweight='bold')
    ax.set_xlabel("Thời gian tương đối (ns)")
    ax.set_ylabel("Interval (ns)")
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.3)

    p95 = np.percentile(iv_full, 95)
    ax.set_ylim(0, max(p95 * 2.5, target * 4))

    # ─── HISTOGRAM ─────────────────────────────────────────────────
<<<<<<< HEAD
    # Dùng p0.5–p99.5 để zoom tự động vừa khít dữ liệu mỗi giai đoạn.
    # Tránh range quá rộng (chỉ 1 cột to) khi dữ liệu tập trung hẹp.
    p1  = np.percentile(iv_full, 1)
    p99 = np.percentile(iv_full, 99)
    spread = p99 - p1
    if p <= 1:
        x_min = target * 0.9
        x_max = target * 1.1
    else:
        x_min = p1 - spread * 0.3
        x_max = p99 + spread * 0.3
    iv_hist = iv_full[(iv_full >= x_min) & (iv_full <= x_max)]

    hax.hist(iv_hist, bins=80, color=COLORS[p], alpha=0.75,
             edgecolor='black', linewidth=0.3)
=======
    # Lọc dữ liệu theo range TRƯỚC khi vẽ — tránh set_xlim sau hist()
    # vì set_xlim sau khi vẽ sẽ khiến matplotlib tính lại ylim dựa trên
    # dữ liệu bị cắt → cột cao nhất (nằm trong range) bị clip mất ngọn.
    p99 = np.percentile(iv_full, 99)
    x_max = max(p99 * 1.5, target * 3)
    iv_hist = iv_full[iv_full <= x_max]

    hax.hist(iv_hist, bins=50, color=COLORS[p], alpha=0.75,
             edgecolor='black', linewidth=0.5)
>>>>>>> main

    hax.axvline(target, color='black', linestyle='--', linewidth=1)
    hax.axvline(mean_iv, color='red', linestyle='--', linewidth=1)

    hax.set_title(f"Histogram - {PERIOD_LABELS[p]}", fontsize=10)
    hax.set_xlabel("Interval (ns)")
    hax.set_ylabel("Count")
    hax.grid(True, alpha=0.3)

    # Annotation dùng tọa độ tương đối trên trục Y (0–1)
    # để không ảnh hưởng đến ylim của histogram.
    hax.text(mean_iv, 0.92, f"Mean\n{mean_iv:,.0f}",
             color='red', ha='center', fontsize=8,
             transform=hax.get_xaxis_transform())
    hax.text(target, 0.77, f"Target\n{target:,}",
             color='black', ha='center', fontsize=8,
             transform=hax.get_xaxis_transform())
<<<<<<< HEAD
=======

# ─── Histogram tổng ───────────────────────────────────────────────────
hist_ax_total.hist(interval, bins=100, alpha=0.7,
                   color='gray', edgecolor='black')

hist_ax_total.set_title("Histogram tổng hợp tất cả giai đoạn",
                        fontsize=12, fontweight='bold')
hist_ax_total.set_xlabel("Interval (ns)")
hist_ax_total.set_ylabel("Count")
hist_ax_total.grid(True, alpha=0.3)
>>>>>>> main

# ─── Layout & Save ────────────────────────────────────────────────────
plt.subplots_adjust(hspace=0.5, wspace=0.3, top=0.95)
plt.savefig("interval_analysis.png", dpi=120, bbox_inches='tight')

print("[PLOT] Đã lưu → interval_analysis.png")

# ─── 4. In thống kê ───────────────────────────────────────────────────
print("\n" + "="*110)
print(f"{'Giai đoạn':<32} {'N':>6} {'Mean':>12} {'Std':>12} {'Min':>12} {'Max':>12} {'Range':>12} {'95th':>12}")
print("="*110)

for p in range(5):
    idx = phase == p
    if not np.any(idx):
        print(f"{PERIOD_LABELS[p]:<32} {'N/A':>6}")
        continue

    iv_ns = interval[idx]
    mean_val = np.mean(iv_ns)
    std_val  = np.std(iv_ns, ddof=1)
    min_val  = np.min(iv_ns)
    max_val  = np.max(iv_ns)
    p95_val  = np.percentile(iv_ns, 95)

    print(f"{PERIOD_LABELS[p]:<32} {len(iv_ns):>6} "
          f"{mean_val:>12.0f} {std_val:>12.1f} "
          f"{min_val:>12.0f} {max_val:>12.0f} "
          f"{(max_val-min_val):>12.0f} {p95_val:>12.0f}")

print("="*110)
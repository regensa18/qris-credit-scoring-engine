def revenue_stability(passed: bool, cv: float, limit: float) -> str:
    if passed:
        return (f"Pendapatan harian stabil: fluktuasi di luar pola tren dan hari "
                f"dalam seminggu sekitar {cv:.0%} (batas {limit:.0%}).")
    return (f"Pendapatan harian kurang stabil: fluktuasi di luar pola tren dan hari "
            f"dalam seminggu sekitar {cv:.0%}, melebihi batas {limit:.0%}.")

def trend_direction(passed: bool, monthly_change: float, limit: float) -> str:
    if passed:
        return (f"Tren pendapatan stabil atau naik: perubahan sekitar "
                f"{monthly_change:+.1%} per bulan (batas penurunan {abs(limit):.0%} per bulan).")
    return (f"Tren pendapatan menurun: sekitar {monthly_change:+.1%} per bulan, "
            f"lebih buruk dari batas penurunan {abs(limit):.0%} per bulan.")

def shock_not_applicable() -> str:
    return "Tidak ada penutupan sementara yang terdeteksi; penilaian pemulihan usaha tidak diterapkan."

def shock_recovery_passed(shock_count: int, ratio: float | None) -> str:
    if ratio is None:
        return f"Terdeteksi {shock_count} penutupan sementara, dalam batas wajar."
    level = "level semula atau lebih" if ratio >= 1 else f"sekitar {ratio:.0%} dari level semula"
    return (f"Usaha pulih setelah {shock_count} penutupan sementara: "
            f"penjualan kembali ke {level}.")

def shock_recovery_failed(shock_count, max_shocks, ratio, min_ratio, too_many, low_recovery) -> str:
    parts = []
    if too_many:
        parts.append(f"usaha tutup sementara berulang kali ({shock_count} kali, batas {max_shocks} kali)")
    if low_recovery:
        parts.append(f"penjualan setelah penutupan hanya sekitar {ratio:.0%} dari level sebelumnya "
                     f"(minimum {min_ratio:.0%})")
    return "Pemulihan usaha kurang memadai: " + "; ".join(parts) + "."

def irregularity_passed(share, limit, longest, max_longest) -> str:
    return (f"Kontinuitas usaha baik: hari tanpa penjualan yang tidak terjelaskan {share:.0%} "
            f"(batas {limit:.0%}), jeda terpanjang {longest} hari (batas {max_longest} hari).")

def irregularity_failed(share, limit, longest, max_longest, share_bad, longest_bad) -> str:
    parts = []
    if share_bad:
        parts.append(f"hari tanpa penjualan yang tidak terjelaskan {share:.0%}, melebihi batas {limit:.0%}")
    if longest_bad:
        parts.append(f"jeda tanpa penjualan terpanjang {longest} hari, melebihi batas {max_longest} hari")
    return "Kontinuitas usaha kurang memadai: " + "; ".join(parts) + "."

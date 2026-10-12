import math
import statistics
from dataclasses import dataclass
from typing import Callable, List, Tuple

from core.sections import CircularBeam, IBeam, RectangularBeam
from frontend.models import (
    CircularDimensions,
    IBeamDimensions,
    PointLoadState,
    RectangularDimensions,
    SupportState,
    UDLLoadState,
    UVLLoadState,
)
from frontend.state_manager import StateManager


@dataclass(slots=True)
class AccuracyResult:
    parameter: str
    position_x: float
    depth_y: float
    calculated: float
    expected: float
    absolute_error: float
    accuracy_percentage: float


@dataclass(slots=True)
class BeamTestReport:
    beam_name: str
    results: list[AccuracyResult]
    mean_accuracy: float
    median_accuracy: float
    sf_mean_acc: float
    bm_mean_acc: float
    bs_mean_acc: float
    ss_mean_acc: float


def compute_accuracy(calc: float, expected: float, scale: float = 1.0) -> float:
    """Calculates accuracy percentage comparing calculated and analytical values."""
    abs_err = abs(calc - expected)
    if abs(expected) > 1e-4:
        rel_err = abs_err / abs(expected)
        return max(0.0, min(100.0, (1.0 - rel_err) * 100.0))
    else:
        # Near zero: scale based on characteristic parameter magnitude
        rel_err = abs_err / max(scale, 1e-4)
        return max(0.0, min(100.0, (1.0 - rel_err) * 100.0))


def run_rectangular_beam_test() -> BeamTestReport:
    """Test Case 1: Rectangular Beam (10m span) with Point Load, UDL, and UVL."""
    span = 10.0
    w_mm = 200.0
    h_mm = 400.0
    w_m = w_mm / 1000.0
    h_m = h_mm / 1000.0
    I = (w_m * h_m**3) / 12.0

    state = StateManager()
    state.beam_type = "Rectangular"
    state.beam_length = span
    state.beam_dimensions = RectangularDimensions(width_mm=w_mm, height_mm=h_mm)
    state.supports = [SupportState("Pin", 0.0), SupportState("Roller", span)]

    # Loads: Point (50kN @ 4m), UDL (20kN/m from 1 to 6m), UVL (10 to 40kN/m from 5 to 9m)
    state.loads = [
        PointLoadState(magnitude_kn=50.0, position_m=4.0),
        UDLLoadState(intensity_kn_m=20.0, start_position_m=1.0, end_position_m=6.0),
        UVLLoadState(
            start_intensity_kn_m=10.0,
            end_intensity_kn_m=40.0,
            start_position_m=5.0,
            end_position_m=9.0,
        ),
    ]
    state.solve()

    # Analytical equation solvers
    R1 = 121.0
    R2 = 129.0

    def exact_sf(x: float) -> float:
        if x >= span:
            return 0.0
        v = R1
        if x >= 4.0:
            v -= 50.0
        # UDL [1, 6] @ 20kN/m
        if x > 1.0:
            udl_span = min(x, 6.0) - 1.0
            v -= 20.0 * udl_span
        # UVL [5, 9] from 10 to 40kN/m (slope 7.5)
        if x > 5.0:
            u = min(x, 9.0) - 5.0
            v -= 10.0 * u + 3.75 * u**2
        return v

    def exact_bm(x: float) -> float:
        if x <= 0.0 or x >= span:
            return 0.0
        m = R1 * x
        if x > 4.0:
            m -= 50.0 * (x - 4.0)
        # UDL [1, 6]
        if x > 1.0:
            if x <= 6.0:
                m -= 10.0 * (x - 1.0) ** 2
            else:
                m -= 100.0 * (x - 3.5)
        # UVL [5, 9]
        if x > 5.0:
            if x <= 9.0:
                u = x - 5.0
                m -= 5.0 * u**2 + 1.25 * u**3
            else:
                m -= 100.0 * (x - 7.4)
        return m

    # Max scales for zero normalization
    max_sf_scale = 129.0
    max_bm_scale = 395.0
    max_bs_scale = (395.0 * (h_m / 2.0)) / (I * 1000.0)
    max_ss_scale = 1.5 * 129.0 / (w_m * h_m * 1000.0)

    results: list[AccuracyResult] = []

    # Check at 1m intervals along span (0m to 10m)
    for i in range(int(span) + 1):
        x = float(i)
        state.cross_section_x = x

        # 1. Shear Force
        calc_v = state.get_shear_force(x)
        exp_v = exact_sf(x)
        acc_v = compute_accuracy(calc_v, exp_v, max_sf_scale)
        results.append(
            AccuracyResult("Shear Force", x, 0.0, calc_v, exp_v, abs(calc_v - exp_v), acc_v)
        )

        # 2. Bending Moment
        calc_m = state.get_bending_moment(x)
        exp_m = exact_bm(x)
        acc_m = compute_accuracy(calc_m, exp_m, max_bm_scale)
        results.append(
            AccuracyResult("Bending Moment", x, 0.0, calc_m, exp_m, abs(calc_m - exp_m), acc_m)
        )

        # 3. Bending Stress at depth y = h/4 = 0.1m
        y_test = h_m / 4.0
        state.cross_section_y_meters = y_test
        calc_bs = state.get_bending_stress(y_test)
        exp_bs = (exp_m * y_test) / (I * 1000.0)
        acc_bs = compute_accuracy(calc_bs, exp_bs, max_bs_scale)
        results.append(
            AccuracyResult("Bending Stress", x, y_test, calc_bs, exp_bs, abs(calc_bs - exp_bs), acc_bs)
        )

        # 4. Shear Stress at neutral axis y = 0m
        y_na = 0.0
        state.cross_section_y_meters = y_na
        calc_ss = state.get_shear_stress(y_na)
        Q_na = (w_m * h_m**2) / 8.0
        exp_ss = (exp_v * Q_na) / (I * w_m * 1000.0)
        acc_ss = compute_accuracy(calc_ss, exp_ss, max_ss_scale)
        results.append(
            AccuracyResult("Shear Stress", x, y_na, calc_ss, exp_ss, abs(calc_ss - exp_ss), acc_ss)
        )

    sf_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Force"]
    bm_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Moment"]
    bs_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Stress"]
    ss_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Stress"]
    all_accs = [r.accuracy_percentage for r in results]

    return BeamTestReport(
        beam_name="Rectangular Beam (10m)",
        results=results,
        mean_accuracy=statistics.mean(all_accs),
        median_accuracy=statistics.median(all_accs),
        sf_mean_acc=statistics.mean(sf_accs),
        bm_mean_acc=statistics.mean(bm_accs),
        bs_mean_acc=statistics.mean(bs_accs),
        ss_mean_acc=statistics.mean(ss_accs),
    )


def run_circular_beam_test() -> BeamTestReport:
    """Test Case 2: Circular Beam (8m span) with Point Load, UDL, and UVL."""
    span = 8.0
    d_mm = 300.0
    d_m = d_mm / 1000.0
    R = d_m / 2.0
    I = (math.pi * d_m**4) / 64.0

    state = StateManager()
    state.beam_type = "Circular"
    state.beam_length = span
    state.beam_dimensions = CircularDimensions(diameter_mm=d_mm)
    state.supports = [SupportState("Pin", 0.0), SupportState("Roller", span)]

    # Loads: Point (40kN @ 3m), UDL (15kN/m from 2 to 6m), UVL (20 to 50kN/m from 4 to 7m)
    state.loads = [
        PointLoadState(magnitude_kn=40.0, position_m=3.0),
        UDLLoadState(intensity_kn_m=15.0, start_position_m=2.0, end_position_m=6.0),
        UVLLoadState(
            start_intensity_kn_m=20.0,
            end_intensity_kn_m=50.0,
            start_position_m=4.0,
            end_position_m=7.0,
        ),
    ]
    state.solve()

    R1 = 85.0
    R2 = 120.0

    def exact_sf(x: float) -> float:
        if x >= span:
            return 0.0
        v = R1
        if x >= 3.0:
            v -= 40.0
        if x > 2.0:
            v -= 15.0 * (min(x, 6.0) - 2.0)
        if x > 4.0:
            u = min(x, 7.0) - 4.0
            v -= 20.0 * u + 5.0 * u**2
        return v

    def exact_bm(x: float) -> float:
        if x <= 0.0 or x >= span:
            return 0.0
        m = R1 * x
        if x > 3.0:
            m -= 40.0 * (x - 3.0)
        if x > 2.0:
            if x <= 6.0:
                m -= 7.5 * (x - 2.0) ** 2
            else:
                m -= 60.0 * (x - 4.0)
        if x > 4.0:
            if x <= 7.0:
                u = x - 4.0
                m -= 10.0 * u**2 + (5.0 / 3.0) * u**3
            else:
                m -= 105.0 * (x - (40.0 / 7.0))
        return m

    max_sf_scale = 120.0
    max_bm_scale = 270.0
    max_bs_scale = (270.0 * R) / (I * 1000.0)
    max_ss_scale = (4.0 * 120.0) / (3.0 * (math.pi * R**2) * 1000.0)

    results: list[AccuracyResult] = []

    for i in range(int(span) + 1):
        x = float(i)
        state.cross_section_x = x

        # 1. Shear Force
        calc_v = state.get_shear_force(x)
        exp_v = exact_sf(x)
        acc_v = compute_accuracy(calc_v, exp_v, max_sf_scale)
        results.append(AccuracyResult("Shear Force", x, 0.0, calc_v, exp_v, abs(calc_v - exp_v), acc_v))

        # 2. Bending Moment
        calc_m = state.get_bending_moment(x)
        exp_m = exact_bm(x)
        acc_m = compute_accuracy(calc_m, exp_m, max_bm_scale)
        results.append(AccuracyResult("Bending Moment", x, 0.0, calc_m, exp_m, abs(calc_m - exp_m), acc_m))

        # 3. Bending Stress at depth y = R/2 = 0.075m
        y_test = R / 2.0
        state.cross_section_y_meters = y_test
        calc_bs = state.get_bending_stress(y_test)
        exp_bs = (exp_m * y_test) / (I * 1000.0)
        acc_bs = compute_accuracy(calc_bs, exp_bs, max_bs_scale)
        results.append(AccuracyResult("Bending Stress", x, y_test, calc_bs, exp_bs, abs(calc_bs - exp_bs), acc_bs))

        # 4. Shear Stress at neutral axis y = 0m
        y_na = 0.0
        state.cross_section_y_meters = y_na
        calc_ss = state.get_shear_stress(y_na)
        Q_na = (d_m**3) / 12.0
        b_na = d_m
        exp_ss = (exp_v * Q_na) / (I * b_na * 1000.0)
        acc_ss = compute_accuracy(calc_ss, exp_ss, max_ss_scale)
        results.append(AccuracyResult("Shear Stress", x, y_na, calc_ss, exp_ss, abs(calc_ss - exp_ss), acc_ss))

    sf_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Force"]
    bm_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Moment"]
    bs_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Stress"]
    ss_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Stress"]
    all_accs = [r.accuracy_percentage for r in results]

    return BeamTestReport(
        beam_name="Circular Beam (8m)",
        results=results,
        mean_accuracy=statistics.mean(all_accs),
        median_accuracy=statistics.median(all_accs),
        sf_mean_acc=statistics.mean(sf_accs),
        bm_mean_acc=statistics.mean(bm_accs),
        bs_mean_acc=statistics.mean(bs_accs),
        ss_mean_acc=statistics.mean(ss_accs),
    )


def run_ibeam_test() -> BeamTestReport:
    """Test Case 3: I-Beam (6m span) with Point Load, UDL, and UVL."""
    span = 6.0
    h_mm = 300.0
    fw_mm = 150.0
    ft_mm = 20.0
    wt_mm = 10.0

    h_m = h_mm / 1000.0
    fw_m = fw_mm / 1000.0
    ft_m = ft_mm / 1000.0
    wt_m = wt_mm / 1000.0
    hw_m = h_m - 2.0 * ft_m

    I = (fw_m * h_m**3) / 12.0 - ((fw_m - wt_m) * hw_m**3) / 12.0

    state = StateManager()
    state.beam_type = "I-Beam"
    state.beam_length = span
    state.beam_dimensions = IBeamDimensions(
        height_mm=h_mm,
        flange_width_mm=fw_mm,
        flange_thickness_mm=ft_mm,
        web_thickness_mm=wt_mm,
    )
    state.supports = [SupportState("Pin", 0.0), SupportState("Roller", span)]

    # Loads: Point (30kN @ 2m), UDL (25kN/m from 1 to 4m), UVL (15 to 45kN/m from 3 to 5m)
    state.loads = [
        PointLoadState(magnitude_kn=30.0, position_m=2.0),
        UDLLoadState(intensity_kn_m=25.0, start_position_m=1.0, end_position_m=4.0),
        UVLLoadState(
            start_intensity_kn_m=15.0,
            end_intensity_kn_m=45.0,
            start_position_m=3.0,
            end_position_m=5.0,
        ),
    ]
    state.solve()

    R1 = 492.5 / 6.0  # 82.08333 kN
    R2 = 165.0 - R1   # 82.91667 kN

    def exact_sf(x: float) -> float:
        if x >= span:
            return 0.0
        v = R1
        if x >= 2.0:
            v -= 30.0
        if x > 1.0:
            v -= 25.0 * (min(x, 4.0) - 1.0)
        if x > 3.0:
            u = min(x, 5.0) - 3.0
            v -= 15.0 * u + 7.5 * u**2
        return v

    def exact_bm(x: float) -> float:
        if x <= 0.0 or x >= span:
            return 0.0
        m = R1 * x
        if x > 2.0:
            m -= 30.0 * (x - 2.0)
        if x > 1.0:
            if x <= 4.0:
                m -= 12.5 * (x - 1.0) ** 2
            else:
                m -= 75.0 * (x - 2.5)
        if x > 3.0:
            if x <= 5.0:
                u = x - 3.0
                m -= 7.5 * u**2 + 2.5 * u**3
            else:
                m -= 60.0 * (x - (25.0 / 6.0))
        return m

    max_sf_scale = 82.91667
    max_bm_scale = 166.25
    max_bs_scale = (166.25 * (h_m / 2.0)) / (I * 1000.0)
    Q_na = fw_m * ft_m * (h_m / 2.0 - ft_m / 2.0) + (wt_m / 2.0) * (hw_m / 2.0) ** 2
    max_ss_scale = (max_sf_scale * Q_na) / (I * wt_m * 1000.0)

    results: list[AccuracyResult] = []

    for i in range(int(span) + 1):
        x = float(i)
        state.cross_section_x = x

        # 1. Shear Force
        calc_v = state.get_shear_force(x)
        exp_v = exact_sf(x)
        acc_v = compute_accuracy(calc_v, exp_v, max_sf_scale)
        results.append(AccuracyResult("Shear Force", x, 0.0, calc_v, exp_v, abs(calc_v - exp_v), acc_v))

        # 2. Bending Moment
        calc_m = state.get_bending_moment(x)
        exp_m = exact_bm(x)
        acc_m = compute_accuracy(calc_m, exp_m, max_bm_scale)
        results.append(AccuracyResult("Bending Moment", x, 0.0, calc_m, exp_m, abs(calc_m - exp_m), acc_m))

        # 3. Bending Stress at flange surface y = h/2 = 0.15m
        y_test = h_m / 2.0
        state.cross_section_y_meters = y_test
        calc_bs = state.get_bending_stress(y_test)
        exp_bs = (exp_m * y_test) / (I * 1000.0)
        acc_bs = compute_accuracy(calc_bs, exp_bs, max_bs_scale)
        results.append(AccuracyResult("Bending Stress", x, y_test, calc_bs, exp_bs, abs(calc_bs - exp_bs), acc_bs))

        # 4. Shear Stress at neutral axis y = 0m (in web)
        y_na = 0.0
        state.cross_section_y_meters = y_na
        calc_ss = state.get_shear_stress(y_na)
        exp_ss = (exp_v * Q_na) / (I * wt_m * 1000.0)
        acc_ss = compute_accuracy(calc_ss, exp_ss, max_ss_scale)
        results.append(AccuracyResult("Shear Stress", x, y_na, calc_ss, exp_ss, abs(calc_ss - exp_ss), acc_ss))

    sf_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Force"]
    bm_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Moment"]
    bs_accs = [r.accuracy_percentage for r in results if r.parameter == "Bending Stress"]
    ss_accs = [r.accuracy_percentage for r in results if r.parameter == "Shear Stress"]
    all_accs = [r.accuracy_percentage for r in results]

    return BeamTestReport(
        beam_name="I-Beam (6m)",
        results=results,
        mean_accuracy=statistics.mean(all_accs),
        median_accuracy=statistics.median(all_accs),
        sf_mean_acc=statistics.mean(sf_accs),
        bm_mean_acc=statistics.mean(bm_accs),
        bs_mean_acc=statistics.mean(bs_accs),
        ss_mean_acc=statistics.mean(ss_accs),
    )


def run_all_tests() -> list[BeamTestReport]:
    reports = [
        run_rectangular_beam_test(),
        run_circular_beam_test(),
        run_ibeam_test(),
    ]
    return reports


if __name__ == "__main__":
    reports = run_all_tests()
    for report in reports:
        print("=" * 70)
        print(f"REPORT: {report.beam_name}")
        print("=" * 70)
        print(f"Mean Accuracy:   {report.mean_accuracy:.2f}%")
        print(f"Median Accuracy: {report.median_accuracy:.2f}%")
        print(f" - Shear Force Mean Accuracy:    {report.sf_mean_acc:.2f}%")
        print(f" - Bending Moment Mean Accuracy:  {report.bm_mean_acc:.2f}%")
        print(f" - Bending Stress Mean Accuracy: {report.bs_mean_acc:.2f}%")
        print(f" - Shear Stress Mean Accuracy:   {report.ss_mean_acc:.2f}%")
        print("-" * 70)
        print(f"{'Param':<16} {'x(m)':<5} {'y(m)':<6} {'Calc':<12} {'Exact':<12} {'AbsErr':<10} {'Accuracy':<8}")
        print("-" * 70)
        for r in report.results:
            print(
                f"{r.parameter:<16} {r.position_x:<5.1f} {r.depth_y:<6.3f} {r.calculated:<12.4f} "
                f"{r.expected:<12.4f} {r.absolute_error:<10.4e} {r.accuracy_percentage:>6.2f}%"
            )
        print()

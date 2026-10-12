from core.types import LoadFunction


class RombergIntegrator:
    """Numerical integrator using Romberg Integration with the composite trapezoidal rule.

    Successively halves the trapezoidal mesh:
        R(k, 0) = 0.5 * R(k-1, 0) + h_k * sum_{i=1}^{2^{k-1}} f(a + (2i - 1) * h_k)
    and applies Richardson extrapolation:
        R(k, j) = R(k, j-1) + (R(k, j-1) - R(k-1, j-1)) / (4^j - 1)
    Terminates early as soon as successive diagonal approximations agree within the
    target tolerance (default 0.1 for accuracy down to 1 decimal place).
    """

    DEFAULT_TOLERANCE: float = 0.1  # Accuracy down to 1 decimal place
    MAX_STEPS: int = 6

    @classmethod
    def integrate(
        cls,
        function: LoadFunction,
        start: float,
        end: float,
        tolerance: float = DEFAULT_TOLERANCE,
        max_steps: int = MAX_STEPS,
    ) -> float:
        if start >= end:
            return 0.0

        h = end - start
        # Initial step: trapezoidal rule with 1 interval
        r: list[list[float]] = [[0.5 * h * (function(start) + function(end))]]

        for k in range(1, max_steps):
            h /= 2.0
            n_midpoints = 1 << (k - 1)  # 2^(k-1)
            midpoint_sum = 0.0
            for i in range(1, n_midpoints + 1):
                midpoint_sum += function(start + (2 * i - 1) * h)

            trapezoid_val = 0.5 * r[k - 1][0] + h * midpoint_sum
            row = [trapezoid_val]

            pow_4 = 1
            for j in range(1, k + 1):
                pow_4 *= 4  # 4^j
                extrapolated = row[j - 1] + (row[j - 1] - r[k - 1][j - 1]) / (pow_4 - 1)
                row.append(extrapolated)

            r.append(row)

            # Check convergence down to 1 decimal place
            if abs(r[k][k] - r[k - 1][k - 1]) <= tolerance:
                return r[k][k]

        return r[-1][-1]


class SimpsonIntegrator:
    """Numerical integrator using Simpson's 1/3 rule with Richardson error reduction."""

    DEFAULT_SUBDIVISIONS: int = 10
    MIN_SUBDIVISIONS: int = 4
    MAX_SUBDIVISIONS: int = 60

    @classmethod
    def integrate_simpson_one_third(
        cls,
        function: LoadFunction,
        start: float,
        end: float,
        intervals: int = 10,
    ) -> float:
        if start >= end:
            return 0.0

        n = max(cls.MIN_SUBDIVISIONS, intervals)
        if n % 2 != 0:
            n += 1

        h1 = (end - start) / n
        s_n_sum = function(start) + function(end)
        for i in range(1, n):
            x = start + i * h1
            s_n_sum += (4.0 if i % 2 != 0 else 2.0) * function(x)
        s_n = (h1 / 3.0) * s_n_sum

        n2 = 2 * n
        h2 = (end - start) / n2
        s_2n_sum = function(start) + function(end)
        for i in range(1, n2):
            x = start + i * h2
            s_2n_sum += (4.0 if i % 2 != 0 else 2.0) * function(x)
        s_2n = (h2 / 3.0) * s_2n_sum

        error_reduction = (s_2n - s_n) / 15.0
        return s_2n + error_reduction

    @classmethod
    def integrate(
        cls,
        function: LoadFunction,
        start: float,
        end: float,
        step_size: float = 0.01,
    ) -> float:
        if start >= end:
            return 0.0

        if step_size > 0:
            raw_n = int((end - start) / step_size)
            intervals = max(cls.MIN_SUBDIVISIONS, min(cls.MAX_SUBDIVISIONS, raw_n))
        else:
            intervals = cls.DEFAULT_SUBDIVISIONS

        return cls.integrate_simpson_one_third(function, start, end, intervals=intervals)


def romberg_integral(
    function: LoadFunction,
    start: float,
    end: float,
    tolerance: float = RombergIntegrator.DEFAULT_TOLERANCE,
) -> float:
    """Computes integral using Romberg integration with trapezoidal rule down to 1 decimal place."""
    return RombergIntegrator.integrate(function, start, end, tolerance=tolerance)


def simpson_one_third(
    function: LoadFunction,
    start: float,
    end: float,
    intervals: int = SimpsonIntegrator.DEFAULT_SUBDIVISIONS,
) -> float:
    return SimpsonIntegrator.integrate_simpson_one_third(function, start, end, intervals=intervals)


def simpsonIntegral(
    function: LoadFunction,
    start: float,
    end: float,
    step_size: float = 0.01,
) -> float:
    return SimpsonIntegrator.integrate(function, start, end, step_size=step_size)

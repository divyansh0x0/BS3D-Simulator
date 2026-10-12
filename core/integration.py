from core.types import LoadFunction


class SimpsonIntegrator:
    """Numerical integrator using Simpson's 1/3 rule with Richardson error reduction.

    The error reduction formula:
        I_corrected = S_{2n} + (S_{2n} - S_n) / 15
    provides O(h^6) accuracy, drastically reducing the required number of evaluations
    while eliminating higher-order truncation errors.
    """

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

        # 1. Compute S_n with step h
        h1 = (end - start) / n
        s_n_sum = function(start) + function(end)
        for i in range(1, n):
            x = start + i * h1
            s_n_sum += (4.0 if i % 2 != 0 else 2.0) * function(x)
        s_n = (h1 / 3.0) * s_n_sum

        # 2. Compute S_{2n} with step h / 2 (double the intervals)
        n2 = 2 * n
        h2 = (end - start) / n2
        s_2n_sum = function(start) + function(end)
        for i in range(1, n2):
            x = start + i * h2
            s_2n_sum += (4.0 if i % 2 != 0 else 2.0) * function(x)
        s_2n = (h2 / 3.0) * s_2n_sum

        # 3. Apply Richardson error reduction formula (O(h^6) accuracy)
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

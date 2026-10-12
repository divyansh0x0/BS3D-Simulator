from core.types import LoadFunction


def simpsonIntegral(function: LoadFunction, start: float, end: float, step_size: float) -> float:
    if start >= end:
        return 0
    n = int((end - start) / step_size)
    n = max(3, n + (3 - n % 3) % 3)
    step_size = (end - start) / n
    x1 = start
    x2 = end
    y1 = function(x1)
    y2 = function(x2)

    sum = 0
    for i in range(1, n):
        if i % 3 == 0:
            y = function(x1 + step_size * i)
            sum += y * 2
        else:
            y = function(x1 + step_size * i)
            sum += y * 3
    return 3 * step_size / 8 * (y1 + y2 + sum)

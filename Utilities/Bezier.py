from collections.abc import Callable
from bisect import bisect

def cube(p1:float,  p2:float, t:float) -> float:
    return cubic_bezier(0.0, p1, p2, 1.0, t)

def cubic_bezier(p0:float, p1:float, p2:float, p3:float, t:float) -> float:
    return linear_bezier(quadratic_bezier(p0, p1, p2, t), quadratic_bezier(p1, p2, p3, t), t)

def quadratic_bezier(p0:float, p1:float, p2:float, t:float) -> float:
    return linear_bezier(linear_bezier(p0, p1, t), linear_bezier(p1, p2, t), t)

def linear_bezier(p0:float, p1:float, t:float) -> float:
    return (1.0 - t) * p0 + t * p1

def prepare_curve(x1:float, y1:float, x2:float, y2:float) -> Callable[[float,float,float],float]:
    def get_function(p1:float, p2:float, time:float) -> float:
        index1 = bisect(plot[0], time)
        if time > 1.0 or time < 0.0: raise ValueError("Time value outside of valid range [0.0, 1.0]!")
        if time == plot[1][index1-1]: return linear_bezier(p1, p2, plot[1][index1-1])
        index2 = index1
        index1 -= 1
        time1 = plot[0][index1]; time2 = plot[0][index2]
        delta_time = time2 - time1 # between pre-point and post-point
        trailing_time = time - time1 # between pre-point and point
        progress = trailing_time / delta_time
        return linear_bezier(p1, p2, linear_bezier(plot[1][index1], plot[1][index2], progress))
    delta_time = 1 / RESOLUTION
    x_values:list[float] = []
    y_values:list[float] = []
    for i in range(RESOLUTION + 1): # +1 to be inclusive of edge
        time = delta_time * i
        x = cube(x1, x2, time)
        y = cube(y1, y2, time)
        x_values.append(x)
        y_values.append(y)
    plot = (x_values, y_values)
    return get_function

RESOLUTION = 16
ease = prepare_curve(0.25, 0.1, 0.25, 1.0)
ease_out = prepare_curve(0.0, 0.0, 0.58, 1.0)
ease_in = prepare_curve(0.42, 0.0, 1.0, 1.0)
ease_in_out = prepare_curve(0.42, 0.0, 0.59, 1.0)

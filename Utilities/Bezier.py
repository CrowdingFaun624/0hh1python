def cube(p1:float,  p2:float, t:float) -> float:
    return cubic_bezier(0, p1, p2, 1, t)

def cubic_bezier(p0:float, p1:float, p2:float, p3:float, t:float) -> float:
    return linear_bezier(quadratic_bezier(p0, p1, p2, t), quadratic_bezier(p1, p2, p3, t), t)

def quadratic_bezier(p0:float, p1:float, p2:float, t:float) -> float:
    return linear_bezier(linear_bezier(p0, p1, t), linear_bezier(p1, p2, t), t)

def linear_bezier(p0:float, p1:float,  t:float) -> float:
    return (1 - t) * p0 + t * p1

def cube_2d(x1:float, y1:float, x2:float, y2:float, t:float) -> float:
    return cube(y1, y2, cube(x1, x2, t))

def ease(p1:float, p2:float, t:float) -> float:
    return linear_bezier(p1, p2, cube_2d(0.25, 0.1, 0.25, 1.0, t))

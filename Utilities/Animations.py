from collections.abc import Callable

# try:
#     import Utilities.Bezier as Bezier
# except ImportError:
#     import Bezier

wiggle = { # angle (degrees)
    0.0: 3.0,
    0.1: -3.0,
    0.2: 3.0,
    0.3: -3.0,
    0.4: 3.0,
    0.5: -3.0,
    0.6: 3.0,
    0.7: -3.0,
    0.8: 3.0,
    0.9: -3.0,
    1.0: 0.0
}
subtle_hint = { # y position (%)
    0.0: 0.0,
    0.25: -0.08,
    0.5: 0.0,
    0.75: -0.08,
    1.0: 0.0
}

flash = { # opacity
    0.0: 0.3,
    0.5: 1.0,
    1.0: 0.3
}

def animate(animation:dict[float,float], duration:float, bezier_function:Callable[[float,float,float],float], time:float, infinite:bool=False) -> float:
    time = time % duration
    time_fraction = time / duration
    anim_time = time_fraction
    if anim_time in animation: return animation[anim_time]
    min_time = 0.0
    max_time = 1.0
    for period in reversed(list(animation.keys())):
        if period < anim_time: min_time = period; break
    for period in animation:
        if period > anim_time: max_time = period; break
    inter_period = max_time - min_time
    if inter_period == 0: return animation[max_time]
    past_min = anim_time - min_time
    if infinite: max_time = max_time % 1.0
    return bezier_function(animation[min_time], animation[max_time], past_min / inter_period)

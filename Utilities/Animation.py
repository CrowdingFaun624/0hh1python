import time
from collections.abc import Callable

import pygame

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

class Animation():
    def __init__(self, current_value:float, start_value:float|None, duration:float, bezier_function:Callable[[float,float,float],float], current_time:float|None=None) -> None:
        self.next_value = current_value
        if start_value is None: start_value = current_value
        self.current_value = start_value
        self.previous_value = start_value
        self.duration = duration
        self.bezier_function = bezier_function
        self.change_time = time.time() if current_time is None else current_time
        self.get_direction()
    
    def get_direction(self) -> int:
        '''Returns 1 or -1 based on which way the current value is going.'''
        if self.previous_value > self.next_value: self.direction = -1
        else: self.direction = 1

    def is_finished(self, current_time:float|None=None) -> bool:
        if current_time is None: current_time = time.time()
        return current_time - self.change_time >= self.duration

    def get(self, current_time:float|None=None) -> float:
        if current_time is None: current_time = time.time()
        if current_time - self.change_time >= self.duration: self.current_value = self.next_value
        elif current_time < self.change_time: self.current_value = self.previous_value
        else:
            if self.direction == 1:
                self.current_value = self.bezier_function(self.previous_value, self.next_value, (current_time - self.change_time) / self.duration)
            else:
                self.current_value = self.bezier_function(self.previous_value, self.next_value, (current_time - self.change_time) / self.duration)
        return self.current_value
    
    def set(self, value:float, new_duration:float|None=None, current_time:float|None=None) -> None:
        if new_duration is not None: self.duration = new_duration
        if current_time is None: current_time = time.time()
        self.previous_value = self.current_value
        self.next_value = value
        self.get_direction()
        self.change_time = time.time()
    
    def __str__(self) -> str:
        direction_string = "down" if self.direction == -1 else "up"
        current_time = time.time()
        return "Anim %s from %f to %f in %f seconds (%f ago); at %f" % (direction_string, self.previous_value, self.next_value, self.duration, current_time - self.change_time, self.get(current_time))

class MultiAnimation(Animation):
    '''Animates using multiple values at the same time in a tuple.'''
    def __init__(self, current_value:tuple[float], start_value:tuple[float]|None, duration:float, bezier_function:Callable[[float,float,float],float], current_time:float|None=None) -> None:
        if start_value is None: start_value = current_value
        assert len(current_value) == len(start_value)
        self.direction = [None] * len(current_value)
        super().__init__(current_value, start_value, duration, bezier_function, current_time)

    def get_direction(self) -> tuple[int]:
        for index in range(len(self.current_value)):
            if self.previous_value > self.next_value: self.direction[index] = -1
            else: self.direction[index] = 1
    
    def get(self, current_time:float|None=None) -> float:
        if current_time is None: current_time = time.time()
        if current_time - self.change_time >= self.duration: self.current_value = self.next_value
        elif current_time < self.change_time: self.current_value = self.previous_value
        else:
            new_value:list[float] = []
            for index in range(len(self.current_value)):
                if self.direction[index] == 1:
                    new_value.append(self.bezier_function(self.previous_value[index], self.next_value[index], (current_time - self.change_time) / self.duration))
                else:
                    new_value.append(self.bezier_function(self.previous_value[index], self.next_value[index], (current_time - self.change_time) / self.duration))
            self.current_value = tuple(new_value)
        return self.current_value

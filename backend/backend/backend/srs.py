import math
from datetime import datetime, timedelta

def calculate_sm2(interval: int, ease_factor: float, repetitions: int, quality: int) -> tuple[int, float, int]:
    """
    Calculate the next interval, ease factor, and repetitions using the SM-2 algorithm.
    
    Quality scoring (0 to 5):
    5 - perfect response
    4 - correct response after a hesitation
    3 - correct response recalled with serious difficulty
    2 - incorrect response; where the correct one seemed easy to recall
    1 - incorrect response; the correct one remembered
    0 - complete blackout
    
    Returns:
        (new_interval, new_ease_factor, new_repetitions)
    """
    # Clip quality to 0-5
    quality = max(0, min(5, quality))
    
    # If the response was incorrect (quality < 3), restart repetitions from 0 and set interval to 1 day
    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        # Correct response
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = int(math.ceil(interval * ease_factor))
        new_repetitions = repetitions + 1
        
    # Adjust ease factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    # Keep ease factor at a minimum of 1.3
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3
        
    return new_interval, new_ease_factor, new_repetitions

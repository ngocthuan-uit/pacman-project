import json
import os
from core.constants import *

"""Persistence layer for the all-time high score."""

def load_high_score():

    """Read the high score from the JSON file defined by HIGH_SCORE_FILE.

    Attempts to open and parse the file. Returns 0 if the file does not
    exist, is empty, or contains malformed JSON.

    Returns:
        int: The stored high score, or 0 on any failure.
    """

    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except Exception:
            return 0
    return 0

def save_high_score(score):

    """Write score to the JSON file defined by HIGH_SCORE_FILE.

    Overwrites any previous value. Silently ignores all I/O and
    serialisation errors so a failed write never crashes the game.

    Args:
        score (int): The score value to persist.
    """

    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": score}, f)
    except Exception:
        pass

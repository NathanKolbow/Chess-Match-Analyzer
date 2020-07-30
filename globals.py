BG_COLOR = "#69a4b5"
CANVAS_SIZE = 800

BEST_MOVE = 0
BRILLIANT = 1
EXCELLENT = 2
GOOD = 3
INACCURACY = 4
MISTAKE = 5
BLUNDER = 6

BEST_MOVE_COLOR = '#FFFFFF'
BRILLIANT_COLOR = '#779ECB'
EXCELLENT_COLOR = '#80CEE1'
GOOD_COLOR = '#77DD77'
INACCURACY_COLOR = '#FFFF4F'
MISTAKE_COLOR = '#FF5050'
BLUNDER_COLOR = '#990000'

DEFAULT_FONT = "Calibri 12"
DEFAULT_FONT_BOLD = "Calibri\ Bold 12"

DEPTH = 18


def RatingToStr(rating):
    if rating == 0:
        return 'Best move'
    elif rating == 1:
        return 'Brilliant'
    elif rating == 2:
        return 'Excellent'
    elif rating == 3:
        return 'Good'
    elif rating == 4:
        return 'Inaccuracy'
    elif rating == 5:
        return 'Mistake'
    else:
        return 'Blunder'


def StrToRating(rating):
    rating = rating.upper()
    if rating == 'BEST MOVE':
        return 0
    elif rating == 'BRILLIANT':
        return 1
    elif rating == 'EXCELLENT':
        return 2
    elif rating == 'GOOD':
        return 3
    elif rating == 'INACCURACY':
        return 4
    elif rating == 'MISTAKE':
        return 5
    else:
        return 6
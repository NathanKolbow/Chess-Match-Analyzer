BG_COLOR = "#69a4b5"
CANVAS_SIZE = 800

BAR_MAX_PERCENT = 0.95

OVERVIEW_SIZE = [400, -1]
OVERVIEW_WIDTH_MULTIPLIER = 0.9
OVERVIEW_MAX_WIDTH = (OVERVIEW_SIZE[0]/2) * OVERVIEW_WIDTH_MULTIPLIER
OVERVIEW_TEXT_ADJUSTMENT = 10
OVERVIEW_COLUMN_SIZE = (400, 800)
OVERVIEW_PER_SCORE_MULTIPLIER = 25
OVERVIEW_COLOR = 'red'
OVERVIEW_LINE_WIDTH = 2
OVERVIEW_POINT_SIZE = 3
OVERVIEW_POINT_COLOR = 'black'
OVERVIEW_CENTER_COLOR = '#A6A6A6'
OVERVIEW_CENTER_WIDTH = 2
OVERVIEW_GRAPH_DIVISOR = 1

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
DEFAULT_FONT_MEDIUM_SMALL = "Calibri 14"
DEFAULT_FONT_LARGE = "Calibri 24"
DEFAULT_FONT_LARGE_BOLD = "Calibri\ Bold 24"
DEFAULT_FONT_MEDIUM = "Calibri 17"
DEFAULT_FONT_MEDIUM_BOLD = "Calibri\ Bold 17"
DEFAULT_FONT_SMALL = "Calibri 9"

DEPTH = 23

SWITCH_SIZE = (59, 30)


def RatingToColor(rating):
    if rating == 0:
        return BEST_MOVE_COLOR
    elif rating == 1:
        return BRILLIANT_COLOR
    elif rating == 2:
        return EXCELLENT_COLOR
    elif rating == 3:
        return GOOD_COLOR
    elif rating == 4:
        return INACCURACY_COLOR
    elif rating == 5:
        return MISTAKE_COLOR
    else:
        return BLUNDER_COLOR


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
import sys

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 8):
	print("Python version 3.8 or later required.")
	sys.exit(1)


import PySimpleGUI as sg
import board_utils as butil
import analysis
import builder
from globals import *
from tkinter import TclError
import clipboard
from math import floor
import mathemagics


"""
    TODO: Analyze all of the FENs in all of the 160,000 games collected on ZenGen AND KEEP TRACK OF HOW MANY TIMES EACH OF THEM OCCURS (along w/ score, move, depth obvs)
"""
WINDOW = None

_SCORES = []
_RATINGS = []

_CURR_INDEX = 0

_OVERVIEW_TEXT = []
_PLAYER = 'w'

def run():
    global _SCORES
    global _RATINGS
    global WINDOW
    global _CURR_INDEX
    global _PLAYER

    try:
        clip = clipboard.paste()
        ret = butil.PGNToFENList(clip)
        if not ret:
            raise EOFError # just some random error
    except:
        paste_button = sg.Button('Paste PGN', key='paste')
        failure_text = sg.Text('Invalid PGN; make sure you have the PGN copied to your clipboard.', visible=False, justification='center')

        window = sg.Window("Paste PGN Data", [[sg.Column([[paste_button], [failure_text]], justification='center', element_justification='center')]], background_color=BG_COLOR)

        while True:
            event, _ = window.read()

            if event == sg.WIN_CLOSED:
                _close(window)
                return
            else:
                try:
                    clip = clipboard.paste()
                    ret = butil.PGNToFENList(clip)

                    if ret:
                        _close(window)
                        break
                except TclError:
                    # Probably caused by a clipboard error
                    pass

                failure_text.Update(visible=True)
        del window

    #butil.PGNToFENList("1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. Nxe5 Qd4 6. Nf3 Qxe4+ 7. Qe2 Qxe2+ 8. Kxe2 Nf6")

    bar = sg.ProgressBar(len(butil._PGN_DATA), orientation='horizontal', size=(20, 20), key='progbar')
    window = sg.Window("Loading Analyses", [[bar]], background_color=BG_COLOR)
    window.Finalize()

    for i in range(len(butil._PGN_DATA)):
        event, _ = window.read(timeout=0)
        if event == sg.WIN_CLOSED:
            _close(window)
            return
        
        try:
            if butil._PGN_DATA[i][0] != []:
                score, bestmove = analysis.SyncAnalysis(butil._PGN_DATA[i][0])
                _SCORES.append((score, bestmove))
                bar.update_bar(i)
        except IndexError:
            break

    _close(window)
    del window

    for i in range(0, len(_SCORES)):
        try:
            score_before = _SCORES[i][0]
            score_after = -_SCORES[i+1][0] if type(_SCORES[i+1][0]) == int else _SCORES[i+1][0].replace('-', '') if '-' in _SCORES[i+1][0] else _SCORES[i+1][0].replace('+', '-')
            
            if _SCORES[i][1] == butil._xy_to_rank_file(butil._PGN_DATA[i][1][0][0], butil._PGN_DATA[i][1][0][1]) + butil._xy_to_rank_file(butil._PGN_DATA[i][1][1][0], butil._PGN_DATA[i][1][1][1]):
                _RATINGS.append(BEST_MOVE)
            else:
                _RATINGS.append(analysis._categorize_move(score_before, score_after))
        except IndexError:
            break


    # TODO:
    # ((1. Build window with board
    #       this should be done by modularizing the board window building process
    # ((2. Set board to current FEN
    # ((3. Draw a red arrow where the bad move was
    # ((4. Take new move input and analyze each input move (gonna have to remodel board_utils for this)
    # ((5. Worry about the exterior panel on the right side that displays information
    #       once 1-3 are done

    print("_RATINGS: %s\n_SCORES: %s" % (_RATINGS, _SCORES))

    board = builder.BoardElements()
    analysis_menu, columns = builder.AnalysisMenuElements(_RATINGS)
    analysis_bar, analysis_text = builder.AnalysisBarElements()
    analysis_bar_column = sg.Column([[analysis_bar], [analysis_text]], background_color=BG_COLOR, pad=((0, 0), (32, 0)), element_justification='center')
    overview = builder.MatchOverviewGraph([i for (i, j) in _SCORES])

    thresh = INACCURACY*2 + (0 if _PLAYER == 'w' else 1)
    window = sg.Window("Match Analysis", [ 
                                            [  
                                                analysis_bar_column,
                                                sg.Column(board, background_color=BG_COLOR), 
                                                sg.Column(analysis_menu, background_color=BG_COLOR), 
                                                sg.Column([[overview]],
                                                            background_color=BG_COLOR, pad=((0, 0), (32, 0)), justification='center', element_justification='center', size=OVERVIEW_COLUMN_SIZE,
                                                            scrollable=OVERVIEW_SIZE[1] > OVERVIEW_COLUMN_SIZE[1] or OVERVIEW_SIZE[0] > OVERVIEW_COLUMN_SIZE[0], 
                                                            vertical_scroll_only=OVERVIEW_COLUMN_SIZE[0] >= OVERVIEW_SIZE[0])
                                            ] 
                                        ], background_color=BG_COLOR)
    WINDOW = window
    window.Finalize()
    window.TKroot.bind("<<Eval-Waiting>>", _eval_waiting)
    window.TKroot.bind("<<Eval-Done-Best Move>>", _eval_done_best_move)
    window.TKroot.bind("<<Eval-Done-Brilliant>>", _eval_done_brilliant)
    window.TKroot.bind("<<Eval-Done-Excellent>>", _eval_done_excellent)
    window.TKroot.bind("<<Eval-Done-Good>>", _eval_done_good)
    window.TKroot.bind("<<Eval-Done-Inaccuracy>>", _eval_done_inaccuracy)
    window.TKroot.bind("<<Eval-Done-Mistake>>", _eval_done_mistake)
    window.TKroot.bind("<<Eval-Done-Blunder>>", _eval_done_blunder)

    columns[thresh].Update(visible=True)
    callbacks = builder.PostFinalization(window, overview_hover_func=_overview_hover, overview_hover_text=_OVERVIEW_TEXT, overview_click=_overview_click, overview_release=_overview_release)

    butil.Init(window, CANVAS_SIZE)
    butil.FocusCurrentPosition(True)
    butil.RateEachMove(True)
    butil.LockBoard()
    butil.SetPosFromFEN(butil._STARTING_POS_FEN)
    butil.AnalysisEvent(None)
    butil.UpdateBoard()

    while True:
        event, _ = window.read()
        if butil._PROMOTING:
            continue

        switch_names = [ 'BUTTON-PLAYTHRU', 'BUTTON-RATE-EACH-MOVE', 'BUTTON-ANALYSIS-BAR', 'BUTTON-SHOW-BEST-MOVE' ]

        if event == sg.WIN_CLOSED:
            break
        elif type(event) == str and 'RETRY-BUTTON' in event:
            split = event.split('.')
            index = int(split[0])*2 if split[1] == 'w' else int(split[0])*2 + 1
            _switch_to_move(index)
        elif event == 'threshold-dropdown':
            new_thresh = window['threshold-dropdown'].Get()
            new_thresh = StrToRating(new_thresh) * 2 + (0 if _PLAYER == 'w' else 1)

            columns[thresh].Update(visible=False)
            columns[new_thresh].Update(visible=True)

            thresh = new_thresh
        elif event == 'RETRY-MOVE':
            _switch_to_move(_CURR_INDEX)
        elif event == 'BACK-A-MOVE':
            if _CURR_INDEX != 0:
                _switch_to_move(_CURR_INDEX - 1)
        elif event == 'FORWARD-A-MOVE':
            if _CURR_INDEX != len(_RATINGS) - 1:
                _switch_to_move(_CURR_INDEX + 1)
        elif event in switch_names:
            info = window[event].__dict__
            print(info['metadata'])
            if not '.disabled' in info['metadata']:
                if 'on' in info['metadata']:
                    # Flipping switch off
                    window[event].Update(image_data=builder._button_off_data(True))
                    info['metadata'] = info['metadata'].replace('n', 'ff')

                    if event == 'BUTTON-PLAYTHRU':
                        window['BUTTON-RATE-EACH-MOVE'].__dict__['metadata'] = 'on.disabled'
                        window['BUTTON-RATE-EACH-MOVE'].Update(image_data=builder._button_on_data(False))

                        _wait_for_move()
                        butil.FocusCurrentPosition(True)
                        butil.RateEachMove(True)
                        butil.LockBoard()
                    elif event == 'BUTTON-ANALYSIS-BAR':
                        analysis_bar.Update(visible=False)
                        analysis_text.Update(visible=False)
                    elif event == 'BUTTON-RATE-EACH-MOVE':
                        _eval_blank()
                        butil.RateEachMove(False)
                    elif event == 'BUTTON-SHOW-BEST-MOVE':
                        butil.ShowBest(False)
                        butil.UpdateBoard()
                else:
                    # Flipping switch on
                    window[event].Update(image_data=builder._button_on_data(True))
                    info['metadata'] = info['metadata'].replace('ff', 'n')

                    if event == 'BUTTON-PLAYTHRU':
                        window['BUTTON-RATE-EACH-MOVE'].__dict__['metadata'] = 'on'
                        window['BUTTON-RATE-EACH-MOVE'].Update(image_data=builder._button_on_data(True))
                        
                        window['RETRY-MOVE'].Update(disabled=True)

                        butil.ResetWrongMove()
                        butil.UpdateBoard()

                        _eval_blank()
                        butil.FocusCurrentPosition(False)
                        butil.UnlockBoard()
                    elif event == 'BUTTON-ANALYSIS-BAR':
                        analysis_bar.Update(visible=True)
                        analysis_text.Update(visible=True)
                    elif event == 'BUTTON-RATE-EACH-MOVE':
                        _wait_for_move()
                        butil.RateEachMove(True)
                    elif event == 'BUTTON-SHOW-BEST-MOVE':
                        print("Showing best move")
                        butil.ShowBest(True)
                        butil.UpdateBoard()



        for callback in callbacks:
            callback(window)


            #print("_RATINGS: %s" % (_RATINGS))
            #new_menu = builder.AnalysisMenuElements([(_RATINGS[i], i) for i in range(0, len(_RATINGS)) if _RATINGS[i] >= new_thresh])
            #window['ratings-column'].Layout(new_menu)
            #window['ratings-column'].Update(visible=True)


        i += 1

    _close(window)


_CLICKED_INDEX = -1
def _overview_click(event):
    global _CLICKED_INDEX
    y_step = max(OVERVIEW_PER_SCORE_MULTIPLIER, OVERVIEW_SIZE[1]/len(_SCORES))
    _CLICKED_INDEX = int((event.y+y_step/2) // y_step)
    print("CLICKED %s" % (_CLICKED_INDEX))


def _overview_release(event):
    global _CLICKED_INDEX

    y_step = max(OVERVIEW_PER_SCORE_MULTIPLIER, OVERVIEW_SIZE[1]/len(_SCORES))
    index = int((event.y+y_step/2) // y_step)
    print("RELEASED %s" % (index))
    if index == _CLICKED_INDEX:
        _switch_to_move(index)

    _CLICKED_INDEX = -1


def _overview_hover(event):
    global _OVERVIEW_TEXT
    global _SCORES
    
    if _OVERVIEW_TEXT == []:
        return

    y_step = max(OVERVIEW_PER_SCORE_MULTIPLIER, OVERVIEW_SIZE[1]/len(_SCORES))
    index = int((event.y+y_step/2) // y_step)

    try:
        score = _OVERVIEW_TEXT[0].__dict__['metadata'][index]
        x = mathemagics.Transform(score/100) * OVERVIEW_MAX_WIDTH + OVERVIEW_SIZE[0]/2 + (OVERVIEW_TEXT_ADJUSTMENT if index % 2 == 0 else -OVERVIEW_TEXT_ADJUSTMENT)

        _OVERVIEW_TEXT[0].Widget.coords(_OVERVIEW_TEXT[1], (x, index * y_step))
        display_score = _SCORES[index][0]
        if type(display_score) == str:
            if '-' in display_score:
                display_score = display_score.replace('+', '')
            
            if index % 2 != 0:
                if '-' in display_score:
                    display_score = display_score.replace('-', '+')
                else:
                    display_score = display_score.replace('+', '-')
        else:
            display_score = display_score/100 if index % 2 == 0 else -display_score/100
            display_score = str(display_score)

        _OVERVIEW_TEXT[0].Widget.itemconfig(_OVERVIEW_TEXT[1], 
                                            text=str(index//2 + 1)) #+ ('W' if index % 2 == 0 else 'B') + ' ' + display_score)
    except IndexError:
        pass


def _eval_waiting(event):
    _update_menu_graph('EVALUATING', 'white', 'gray', DEFAULT_FONT_LARGE_BOLD)


def _eval_done_best_move(event):
    _update_menu_graph('BEST MOVE', 'black', BEST_MOVE_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('BEST MOVE')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_brilliant(event):
    _update_menu_graph('BRILLIANT', 'white', BRILLIANT_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('BRILLIANT')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_excellent(event):
    _update_menu_graph('EXCELLENT', 'white', EXCELLENT_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('EXCELLENT')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_good(event):
    _update_menu_graph('GOOD', 'white', GOOD_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('GOOD')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_inaccuracy(event):
    _update_menu_graph('INACCURACY', 'white', INACCURACY_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('INACCURACY')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_mistake(event):
    _update_menu_graph('MISTAKE', 'white', MISTAKE_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('MISTAKE')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _eval_done_blunder(event):
    _update_menu_graph('BLUNDER', 'white', BLUNDER_COLOR, DEFAULT_FONT_LARGE_BOLD)
    _update_current_button('BLUNDER')
    if 'off' in WINDOW['BUTTON-PLAYTHRU'].__dict__['metadata']:
        WINDOW['RETRY-MOVE'].Update(disabled=False)


def _wait_for_move():
    _update_menu_graph('WAITING FOR A MOVE', 'white', BG_COLOR, DEFAULT_FONT_MEDIUM_BOLD)
    WINDOW['RETRY-MOVE'].Update(disabled=True)


def _eval_blank():
    _update_menu_graph('', 'white', BG_COLOR, DEFAULT_FONT)
    WINDOW['RETRY-MOVE'].Update(disabled=True)


def _update_menu_graph(text, text_color, bg_color, font):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=bg_color)
    WINDOW['menu-graph'].DrawText(text, (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font=font, color=text_color)
    WINDOW.TKroot.update()


def _update_current_button(rating):
    global _CURR_INDEX
    rating = StrToRating(rating)
    print("_CURR_INDEX: %s, _RATINGS[_CURR_INDEX]: %s" % (_CURR_INDEX, _RATINGS[_CURR_INDEX]))
    for j in range(0, _RATINGS[_CURR_INDEX] + 1):
        rows = WINDOW['%s-ratings-column-%s' % (_PLAYER, j)].__dict__['Rows']
        for button in rows:
            button = button[0]

            if rating <= button.__dict__['metadata'] and int(button.__dict__['Key'].split('.')[0]) == int(_CURR_INDEX // 2):
                button.Update(button_color=('white', RatingToColor(rating)))
                button.__dict__['metadata'] = rating


def _switch_to_move(index):
    global _SCORES
    global _RATINGS
    global _CURR_INDEX
    global _PLAYER
    _CURR_INDEX = index

    print("_PLAYER: %s; index: %s" % (_PLAYER, index))
    print(_PLAYER == 'w' and index % 2 == 0)
    print(_PLAYER == 'b' and index % 2 == 1)
    if (_PLAYER == 'w' and index % 2 == 1) or (_PLAYER == 'b' and index % 2 == 0):
        print("Flip floop")
        butil._flip_board()
    _PLAYER = 'w' if index % 2 == 0 else 'b'

    if 'on' in WINDOW['BUTTON-RATE-EACH-MOVE'].__dict__['metadata']:
        _wait_for_move()

    butil.SetPosFromFEN(butil._PGN_DATA[index][0])
    butil.AnalysisEvent(None)

    if index - 1 >= 0:
        butil.SetLastMove(butil._PGN_DATA[index-1][1][0], butil._PGN_DATA[index-1][1][1])
    else:
        butil.ResetLastMove()
    if 'on' in WINDOW['BUTTON-RATE-EACH-MOVE'].__dict__['metadata']:
        butil.SetWrongMove(butil._PGN_DATA[index][1][0], butil._PGN_DATA[index][1][1], _RATINGS[index])
    
    butil.UpdateBoard()
    butil.UnlockBoard()


def _close(window):
    analysis.SaveStorage()
    analysis.Close()

    window.close()



if __name__ == '__main__':
    run()
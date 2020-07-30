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
import traceback


DEPTH = 15
WINDOW = None


def run():
    global WINDOW

    paste_button = sg.Button('Paste PGN', key='paste')
    failure_text = sg.Text('Invalid PGN; make sure you have the PGN copied to your clipboard.', visible=False, justification='center')

    window = sg.Window("Paste PGN Data", [[sg.Column([[paste_button], [failure_text]], justification='center', element_justification='center')]], background_color=BG_COLOR)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            window.close()
            return
        elif event == 'paste':
            try:
                clip = clipboard.paste()
                ret = butil.PGNToFENList(clip)

                if ret:
                    window.close()
                    break
            except TclError:
                # Probably caused by a clipboard error
                pass

            failure_text.Update(visible=True)

    del window
    bar = sg.ProgressBar(len(butil._PGN_DATA), orientation='horizontal', size=(20, 20), key='progbar')
    window = sg.Window("Loading Analyses", [[bar]], background_color=BG_COLOR)
    window.Finalize()

    _SCORES = []
    for i in range(len(butil._PGN_DATA)):
        event, values = window.read(timeout=0)
        if event == sg.WIN_CLOSED:
            window.close()
            return
        
        try:
            if butil._PGN_DATA[i][0] != []:
                score, bestmove = analysis.SyncAnalysis(butil._PGN_DATA[i][0])
                _SCORES.append((score, bestmove))
                bar.update_bar(i)
        except IndexError:
            break

    window.close()
    del window

    player = 'b'
    _RATINGS = []
    for i in range(0 if player == 'w' else 1, len(_SCORES), 2):
        try:
            score_before = _SCORES[i][0]
            score_after = -_SCORES[i+1][0] if type(_SCORES[i+1][0]) == int else _SCORES[i+1][0].replace('-', '+') if '-' in _SCORES[i+1][0] else _SCORES[i+1][0].replace('+', '-')
            
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
    # 4. Take new move input and analyze each input move (gonna have to remodel board_utils for this)
    # 5. Worry about the exterior panel on the right side that displays information
    #       once 1-3 are done

    board = builder.BoardElements()
    analysis_menu, columns = builder.AnalysisMenuElements(_RATINGS)

    thresh = INACCURACY
    window = sg.Window("Title", [ [sg.Column(board, background_color=BG_COLOR), sg.Column(analysis_menu, background_color=BG_COLOR)] ], background_color=BG_COLOR)
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
    builder.PostFinalization(window)

    butil.Init(window, CANVAS_SIZE)
    butil.FocusCurrentPosition(True)

    _switch_to_move(0 if player == 'w' else 1, _RATINGS)

    while True:
        event, values = window.read(timeout=0)

        if event == sg.WIN_CLOSED:
            break
        elif type(event) == str and 'RETRY-BUTTON' in event:
            index = int(event.split('.')[0])*2 if player == 'w' else int(event.split('.')[0])*2 + 1
            _switch_to_move(index, _RATINGS)
        elif event == 'threshold-dropdown':
            new_thresh = window['threshold-dropdown'].Get()
            new_thresh = StrToRating(new_thresh)

            columns[thresh].Update(visible=False)
            columns[new_thresh].Update(visible=True)

            thresh = new_thresh
        elif event == 'RETRY-MOVE':
            print("Retrying move")
            butil.RetryMove()
        elif event == '<Eval-Waiting>':
            print("WAITING FOR EVAL")
        elif type(event) == str and '<Eval-Done-' in event:
            print("EVAL DONE: %s" % (event))


            #print("_RATINGS: %s" % (_RATINGS))
            #new_menu = builder.AnalysisMenuElements([(_RATINGS[i], i) for i in range(0, len(_RATINGS)) if _RATINGS[i] >= new_thresh])
            #window['ratings-column'].Layout(new_menu)
            #window['ratings-column'].Update(visible=True)


        i += 1

    window.close()


def _eval_waiting(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color='gray')
    WINDOW['menu-graph'].DrawText('EVALUATING...', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_best_move(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=BEST_MOVE_COLOR)
    WINDOW['menu-graph'].DrawText('BEST MOVE', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='black')
    WINDOW.TKroot.update()


def _eval_done_brilliant(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=BRILLIANT_COLOR)
    WINDOW['menu-graph'].DrawText('BRILLIANT', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_excellent(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=EXCELLENT_COLOR)
    WINDOW['menu-graph'].DrawText('EXCELLENT', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_good(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=GOOD_COLOR)
    WINDOW['menu-graph'].DrawText('GOOD', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_inaccuracy(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=INACCURACY_COLOR)
    WINDOW['menu-graph'].DrawText('INACCURACY', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_mistake(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=MISTAKE_COLOR)
    WINDOW['menu-graph'].DrawText('MISTAKE', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _eval_done_blunder(event):
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=BLUNDER_COLOR)
    WINDOW['menu-graph'].DrawText('BLUNDER', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 24', color='white')
    WINDOW.TKroot.update()


def _wait_for_move():
    WINDOW['menu-graph'].Erase()
    WINDOW['menu-graph'].Update(background_color=BG_COLOR)
    WINDOW['menu-graph'].DrawText('WAITING FOR A MOVE', (50, 50), text_location=sg.TEXT_LOCATION_CENTER, font='Calibri\ Bold 17', color='white')
    WINDOW.TKroot.update()


def _switch_to_move(index, _RATINGS):
    _wait_for_move()
    rating_index = floor(index / 2)

    butil.SetPosFromFEN(butil._PGN_DATA[index][0])
    if rating_index - 1 >= 0:
        butil.SetLastMove(butil._PGN_DATA[index-1][1][0], butil._PGN_DATA[index-1][1][1])
    else:
        butil.ResetLastMove()
    butil.SetWrongMove(butil._PGN_DATA[index][1][0], butil._PGN_DATA[index][1][1], _RATINGS[rating_index])
    butil.UpdateBoard()


if __name__ == '__main__':
    run()
"""

    NEW ANALYSIS SETUP:
        * Initialize with an Init() function
        * One function to update the FEN that is being analyzed
        * One function for any importer to obtain the current analysis of the position
        * Close everything with Close()
    The above is the ONLY outside interaction that importers have with this module

"""

import threading
import subprocess
import tkinter
import sys
from time import sleep
from globals import *
import traceback


_READ_THREAD = None
_WRITE_THREAD = None
_ALIVE = False

_PROC = None
_UCI_ENGINE_LOC = "engines/stockfish11_win_64.exe"
_ROOT = None

_STORAGE = {}
_INITIATED = False


def Init(root):
    global analysis_thread
    global _PROC
    global _UCI_ENGINE_LOC
    global _ROOT
    global _ALIVE

    _ALIVE = True
    _ROOT = root

    LoadStorage()

    _PROC = subprocess.Popen([_UCI_ENGINE_LOC], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    _READ_THREAD = threading.Thread(target=_reading_thread_run, args=())
    _WRITE_THREAD = threading.Thread(target=_writing_thread_run, args=())

    _READ_THREAD.start()
    _WRITE_THREAD.start()


def Close():
    global _PROC
    global _READ_THREAD
    global _WRITE_THREAD
    global _ANALYZING
    global _NEW_FEN_BOOL
    global _ALIVE

    _write('quit\n', _PROC)

    _ALIVE = False
    _ANALYZING = False
    _NEW_FEN_BOOL = False
    _PROC.terminate()

    _WAITING_FOR_UPDATE_READ.acquire()
    _WAITING_FOR_UPDATE_READ.notify()
    _WAITING_FOR_UPDATE_READ.release()

    _WAITING_FOR_UPDATE_WRITE.acquire()
    _WAITING_FOR_UPDATE_WRITE.notify()
    _WAITING_FOR_UPDATE_WRITE.release()


def SaveStorage():
    global _STORAGE

    with open('.storage', 'w+') as f:
        for item in _STORAGE:
            f.write(item + ':' + str(_STORAGE[item][0]) 
                        + ':' + str(_STORAGE[item][1]) + ':' + str(_STORAGE[item][2]) + '\n')


"""
    Format of .storage as it stands is just lines of the following format:
        FEN:evaluation score:best move:search depth
"""
def LoadStorage():
    global _STORAGE

    with open('.storage', 'r') as f:
        lines = f.read().split('\n')

    for line in lines:
        ele = line.split(':')
        if ele == ['']:
            break
        try:
            _STORAGE[ele[0]] = (int(ele[1]), ele[2], int(ele[3]))
        except:
            # Evaluation was a mate, so ele[1] is a string
            _STORAGE[ele[0]] = (ele[1], ele[2], int(ele[3]))


_WAITING_FOR_UPDATE_READ = threading.Condition()
_WAITING_FOR_UPDATE_WRITE = threading.Condition()
_NEW_FEN_BOOL = False
_PRIMED_FEN = ""
_WRITING_FEN = ""
_READING_FEN = ""
_CURR_EVAL = 0
_CURR_DEPTH = 0
_CURR_BEST_MOVE = ""
_ANALYZING = False
_READ_FEN_COUNT = 0
_WRITTEN_FEN_COUNT = 0
def _writing_thread_run():
    global _PROC
    global _WAITING_FOR_UPDATE_WRITE
    global _PRIMED_FEN
    global _WRITING_FEN
    global _ANALYZING
    global _NEW_FEN_BOOL
    global _WRITTEN_FEN_COUNT

    _write('uci\n', _PROC)

    while _ALIVE:
        while not _NEW_FEN_BOOL:
            _WAITING_FOR_UPDATE_WRITE.acquire()
            if _ALIVE == False:
                _WAITING_FOR_UPDATE_WRITE.release()
                sys.exit(0)
            
            _WAITING_FOR_UPDATE_WRITE.wait()
            _WAITING_FOR_UPDATE_WRITE.release()

        _WRITING_FEN = _PRIMED_FEN

        # We have a new FEN now
        _write('stop\n', _PROC)

        _WRITING_FEN = _PRIMED_FEN
        _NEW_FEN_BOOL = False

        _write('position fen ' + _WRITING_FEN + '\n', _PROC)
        _write('go depth ' + str(DEPTH) + '\n', _PROC)


        _WAITING_FOR_UPDATE_READ.acquire()
        _WAITING_FOR_UPDATE_READ.notify()
        _WAITING_FOR_UPDATE_READ.release()

    sys.exit(0)


def _reading_thread_run():
    global _PROC
    global _READING_FEN
    global _PRIMED_FEN
    global _CURR_EVAL
    global _CURR_BEST_MOVE
    global _CURR_DEPTH
    global _WRITTEN_FEN_COUNT
    global _READ_FEN_COUNT
    global _STORAGE

    while _ALIVE:
        while _WRITTEN_FEN_COUNT == _READ_FEN_COUNT:
            _WAITING_FOR_UPDATE_READ.acquire()
            if _ALIVE == False:
                _WAITING_FOR_UPDATE_READ.release()
                sys.exit(0)

            _WAITING_FOR_UPDATE_READ.wait()
            _WAITING_FOR_UPDATE_READ.release()

        try:
            _CURR_EVAL = _STORAGE[_PRIMED_FEN][0]
            _CURR_BEST_MOVE = _STORAGE[_PRIMED_FEN][1]
            _READING_FEN = _PRIMED_FEN

            _raise_event()
            _READ_FEN_COUNT += 1
        except KeyError:
            while _WRITTEN_FEN_COUNT != _READ_FEN_COUNT:
                try:
                    if _PRIMED_FEN != _READING_FEN:
                        _STORAGE[_PRIMED_FEN]
                        break
                except KeyError:
                    pass
                _READING_FEN = _PRIMED_FEN
                
                out = str(_PROC.stdout.read1(-1))[2:-1].replace('\\r', '').split('\\n')

                for item in out:
                    # Split the output so it can be easily parsed
                    split = item.split(' ')

                    if split[0] == "" and _PROC.poll() == 0:
                        # Output isn't being read anymore and the main proc is closed
                        return
                    elif split[0] == "uciok":
                        pass
                    elif split[0] == "info":
                        _index = 1

                        # Parse the line
                        while _index < len(split):
                            if split[_index] == "score":
                                if split[_index+1] == "cp":
                                    _CURR_EVAL = int(split[_index+2])
                                    _index += 3
                                elif split[_index+1] == "mate":
                                    _CURR_EVAL = 'MATE+' + split[_index+2]
                                    _index += 3
                            elif split[_index] == "pv":
                                _CURR_BEST_MOVE = split[_index+1]
                                _index += 2
                            elif split[_index] == "bestmove":
                                _CURR_BEST_MOVE = split[_index+1]
                                _index += 2
                            elif split[_index] == "depth":
                                _CURR_DEPTH = split[_index+1]
                                _index += 2
                            else:
                                _index += 1
                    elif split[0] == "bestmove":
                        _CURR_BEST_MOVE = split[1]
                        _READ_FEN_COUNT += 1
                        
                        _STORAGE[_READING_FEN] = (_CURR_EVAL, _CURR_BEST_MOVE, _CURR_DEPTH)
                
                _raise_event()

    sys.exit(0)


def _raise_event():
    try:
        _ROOT.event_generate("<<Analysis-Update>>")
    except:
        sys.exit(0)


def SyncAnalysis(FEN):
    global _STORAGE
    if _STORAGE == {}:
        LoadStorage()

    if FEN in _STORAGE and _STORAGE[FEN][2] >= DEPTH:
        return _STORAGE[FEN][0], _STORAGE[FEN][1]

    proc = subprocess.Popen([_UCI_ENGINE_LOC], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    _write('uci\n', proc)
    _write('setoption name Threads value 4\n', proc)
    _write('position fen ' + FEN + '\n', proc)
    _write('go depth ' + str(DEPTH) + '\n', proc)

    score, best_move = _get_sync_score(proc)
    _STORAGE[FEN] = (score, best_move, DEPTH)

    proc.kill()
    return score, best_move


def _get_sync_score(proc):
    running = True
    curr_eval = 0
    best_move = ""
    while running:
        out = str(proc.stdout.read1(-1))[2:-1].replace('\\r', '').split('\\n')

        for item in out:
            # Split the output so it can be easily parsed
            split = item.split(' ')

            if split[0] == "" and proc.poll() == 0:
                # Output isn't being read anymore and the main proc is closed
                return
            elif split[0] == "uciok":
                pass
            elif split[0] == "info":
                _index = 1

                # Parse the line
                while _index < len(split):
                    if split[_index] == "score":
                        if split[_index+1] == "cp":
                            curr_eval = int(split[_index+2])
                            _index += 3
                        elif split[_index+1] == "mate":
                            curr_eval = 'MATE+' + split[_index+2]
                            _index += 3
                    else:
                        _index += 1
            elif split[0] == "bestmove":
                best_move = split[1]
                running = False

    return curr_eval, best_move


def CurrentAnalysis():
    global _CURR_EVAL
    global _CURR_BEST_MOVE
    global _READING_FEN
    global _ALIVE

    if not _ALIVE:
        return None

    return _CURR_EVAL, _CURR_BEST_MOVE, _READING_FEN


def SetFen(FEN):
    global _NEW_FEN_BOOL
    global _WAITING_FOR_UPDATE_WRITE
    global _WRITTEN_FEN_COUNT
    global _PRIMED_FEN
    global _STORAGE
    global _CURR_EVAL
    global _CURR_BEST_MOVE
    global _READING_FEN
    global _ALIVE

    if not _ALIVE:
        return

    _PRIMED_FEN = FEN
    _NEW_FEN_BOOL = True
    _WRITTEN_FEN_COUNT += 1
    _WAITING_FOR_UPDATE_WRITE.acquire()
    _WAITING_FOR_UPDATE_WRITE.notify()
    _WAITING_FOR_UPDATE_WRITE.release()


def _write(str, proc):
    proc.stdin.write(str.encode())
    proc.stdin.flush()


# Takes the raw analysis value from before and after the move BOTH RELATIVE
# TO THE PERSON THAT MADE THE MOVE, this should ONLY be run if the move was
# NOT the best move in the position
def _categorize_move(score_before, score_after):
    if type(score_after) == str and '0' in score_after:
        if '0' in score_after:
            return BEST_MOVE


    if type(score_before) == str:
        if '+' in score_before:
            if type(score_after) == str:
                if '+' in score_after:
                    # TODO: check numbers
                    return EXCELLENT
                else:
                    # TODO: check numbers
                    return BLUNDER
            else:
                if score_after > 450:
                    return MISTAKE
                else:
                    return BLUNDER
        elif '-' in score_before:
            if type(score_after) == str:
                if '-' in score_after:
                    div = int(score_before.split('-')[1]) / int(score_after.split('-')[1])
                    if div == 1:
                        return BEST_MOVE
                    elif div > 1.1:
                        return EXCELLENT
                    elif div > 1.5:
                        return GOOD
                    elif div > 1.9:
                        return INACCURACY
                    else:
                        return MISTAKE
            else:
                return EXCELLENT


    if type(score_after) == str:
        # only hits here if score_before was not a str (i.e. there was not a mating situation before this)
        if '-' in score_after:
            return BLUNDER
        else:
            return BRILLIANT

    diff = score_after - score_before
    if diff < -250:
        return BLUNDER
    elif diff < -130:
        return MISTAKE
    elif diff < -90:
        return INACCURACY
    elif diff < -65:
        return GOOD
    elif diff <= 10:
        return EXCELLENT
    else:
        return BRILLIANT
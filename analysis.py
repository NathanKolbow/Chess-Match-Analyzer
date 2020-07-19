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
import sys

_READ_THREAD = None
_WRITE_THREAD = None
_DEPTH = 18
_ALIVE = True

_PROC = None
_UCI_ENGINE_LOC = "engines/stockfish11_win_64.exe"
_ROOT = None

def Init(root):
    global analysis_thread
    global _PROC
    global _UCI_ENGINE_LOC
    global _ROOT

    _ROOT = root

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

    _write('quit\n')

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


_WAITING_FOR_UPDATE_READ = threading.Condition()
_WAITING_FOR_UPDATE_WRITE = threading.Condition()
_NEW_FEN_BOOL = False
_PRIMED_FEN = ""
_WRITING_FEN = ""
_READING_FEN = ""
_CURR_EVAL = 0
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

    _write('uci\n')

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
        _write('stop\n')

        _WRITING_FEN = _PRIMED_FEN
        _NEW_FEN_BOOL = False
        _WRITTEN_FEN_COUNT += 1

        _write('position fen ' + _WRITING_FEN + '\n')
        _write('go depth ' + str(_DEPTH) + '\n')


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
    global _WRITTEN_FEN_COUNT
    global _READ_FEN_COUNT

    while _ALIVE:
        while _WRITTEN_FEN_COUNT == _READ_FEN_COUNT:
            _WAITING_FOR_UPDATE_READ.acquire()
            if _ALIVE == False:
                _WAITING_FOR_UPDATE_READ.release()
                sys.exit(0)

            _WAITING_FOR_UPDATE_READ.wait()
            _WAITING_FOR_UPDATE_READ.release()


        # Get the line output and change it from bytes to a legible string
        while _WRITTEN_FEN_COUNT != _READ_FEN_COUNT:
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
                        else:
                            _index += 1
                elif split[0] == "bestmove":
                    _CURR_BEST_MOVE = split[1]
                    _READ_FEN_COUNT += 1
            
            _ROOT.event_generate("<<Analysis-Update>>")

    sys.exit(0)


def CurrentAnalysis():
    global _CURR_EVAL
    global _CURR_BEST_MOVE
    global _READING_FEN

    return _CURR_EVAL, _CURR_BEST_MOVE, _READING_FEN


def SetFen(FEN):
    global _NEW_FEN_BOOL
    global _WAITING_FOR_UPDATE_WRITE
    global _PRIMED_FEN

    _PRIMED_FEN = FEN
    _NEW_FEN_BOOL = True
    _WAITING_FOR_UPDATE_WRITE.acquire()
    _WAITING_FOR_UPDATE_WRITE.notify()
    _WAITING_FOR_UPDATE_WRITE.release()


def _write(str):
    global _PROC

    _PROC.stdin.write(str.encode())
    _PROC.stdin.flush()
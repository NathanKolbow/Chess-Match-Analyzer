import PySimpleGUI as sg
import tkinter
import analysis
import threading
from math import sqrt, acos, floor, cos, sin
import sys, traceback
from PIL import Image
from globals import *
import base64
from io import BytesIO
import mathemagics

_STARTING_POS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_IMG_FOLDER = "img/pieces_wooden"
_IMG_DIM = -1 # dimension of the piece images, i.e. 100x100

_PERSPECTIVE = 'w'
_BOARD_GRAPH = None

# _CURR_DATA contains ALL of the information necessary to the current position on the board
# i.e. _CURR_DATA is roughly equivalent to an FEN, NOT a PGN
## _CURR_DATA {
## 		board: 2d array of the current board layout
##		turn: 'w' or 'b' depending on whose turn it is
##		castling: string containing kqKQ with info on who can castle which way
##		en passant: if a pawn was moved 2 spaced last turn, this is the square that that pawn can be en passanted on (in (x, y) form)
##		move counts: as per FEN standards
##      fen: the FEN string of the current position, mostly just stored so that analysis.py can use it
## }
_CURR_DATA = {}


# list of legal moves for the currently selected piece
_LEGAL_MOVES = ()
# current piece being moved
_MOVING_PIECE = None
_MOVING_FROM = None

__ANALYSIS_GRAPH__ = None
__ANALYSIS_RECT__ = None
__RECT_Y__ = -1
__RECT_TARGET_Y__ = -1
__ANALYSIS_TEXT__ = "0.0"

_ROOT = None
_WINDOW = None
_SIZE = 0

_FOCUS_CURRENT = False
_RATE_EACH = False
_BOARD_LOCK = False

_PROMOTING = False


def Init(window, size):
	global _ROOT
	global _WINDOW
	_WINDOW = window
	print("_WINDOW_1: %s" % (_WINDOW))
	_ROOT = window.TKroot

	window['board-graph'].Widget.bind("<Motion>", _board_motion_event)
	window['board-graph'].Widget.bind("<Button-1>", _board_mouse_one)
	window['board-graph'].Widget.bind("<B1-Motion>", _board_mouse_one_drag)
	window['board-graph'].Widget.bind("<ButtonRelease-1>", _board_mouse_one_release)
	window['board-graph'].Widget.bind("<Button-3>", _board_mouse_three)

	global _BOARD_GRAPH
	global _CURR_DATA
	_BOARD_GRAPH = window['board-graph']


	global __ANALYSIS_GRAPH__
	global __ANALYSIS_RECT__
	global __ANALYSIS_TEXT__
	global _SIZE
	global _IMG_DIM
	global __RECT_Y__
	global __RECT_TARGET_Y__
	__RECT_Y__ = size / 2
	__RECT_TARGET_Y__ = size / 2
	_SIZE = size
	_IMG_DIM = int(_SIZE / 8)

	
	__ANALYSIS_GRAPH__ = window.FindElement('analysis-graph', silent_on_error=True)
	if __ANALYSIS_GRAPH__ != None:
		__ANALYSIS_GRAPH__.DrawRectangle((0, 0), (50, size), fill_color='white', line_color='black')
		__ANALYSIS_RECT__ = __ANALYSIS_GRAPH__.DrawRectangle((0, size), (50, size/2), fill_color='gray')
		__ANALYSIS_GRAPH__.DrawRectangle((0, size/2+1), (50, size/2), fill_color='black', line_color='black')
		__ANALYSIS_TEXT__ = __ANALYSIS_GRAPH__.DrawText("0.0", (17, 10), text_location=sg.TEXT_LOCATION_BOTTOM_LEFT, font='Courier 9')

		_ROOT.bind("<<Analysis-Update>>", AnalysisEvent)
		_ROOT.bind("<<Bar-Animation>>", _set_bar_height)
	

_ANIMATING = False
def _set_bar_height(y):
	global __ANALYSIS_GRAPH__
	global __ANALYSIS_RECT__
	global __RECT_Y__
	global __RECT_TARGET_Y__
	global _ANIMATING
	global _ROOT

	try:
		if type(y) == float or type(y) == int:
			__RECT_TARGET_Y__ = y

			while abs(__RECT_TARGET_Y__ - __RECT_Y__) > 1:
				diff = __RECT_TARGET_Y__ - __RECT_Y__
				abs_diff = abs(diff)
				parity = diff / abs_diff

				if abs_diff >= 200:
					__RECT_Y__ += parity * 0.7
				elif abs_diff >= 30:
					__RECT_Y__ += parity * 0.3
				else:
					__RECT_Y__ += parity * 0.075

				__ANALYSIS_GRAPH__.Widget.coords(__ANALYSIS_RECT__, (0, 0, 50, __RECT_Y__))

				_ROOT.update()

			__RECT_Y__ = __RECT_TARGET_Y__
			__ANALYSIS_GRAPH__.Widget.coords(__ANALYSIS_RECT__, (0, 0, 50, __RECT_Y__))
			_ANIMATING = False
	except tkinter.TclError:
		pass





def _get_curr_fen():
	global _CURR_DATA

	out = ""
	blank_count = 0
	for j in reversed(range(0, 8)):
		for i in range(0, 8):
			piece = _get_piece(i, j)
			if piece == '':
				blank_count = blank_count + 1
			else:
				if blank_count != 0:
					out = out + str(blank_count)
					blank_count = 0
				out = out + piece
		if blank_count != 0:
			out = out + str(blank_count)
			blank_count = 0
		if j != 0:
			out = out + "/"

	out = out + " " + _CURR_DATA['turn'] + " " + ('-' if _CURR_DATA['castling'] == '' else _CURR_DATA['castling']) + " "
	if _CURR_DATA['en passant'] == '-':
		out = out + "- "
	else:
		out = out + _xy_to_rank_file(_CURR_DATA['en passant'][0], _CURR_DATA['en passant'][1]) + " "

	out = out + str(_CURR_DATA['move counts'][0]) + " " + str(_CURR_DATA['move counts'][1])
	return out

def SetPosFromFEN(FEN):
	global _CURR_DATA
	_CURR_DATA = _data_from_fen(FEN)
	_draw_board()

	ResetLastMove()

def _x_to_file(x):
	if x == 0:
		file = "a"
	elif x == 1:
		file = "b"
	elif x == 2:
		file = "c"
	elif x == 3:
		file = "d"
	elif x == 4:
		file = "e"
	elif x == 5:
		file = "f"
	elif x == 6:
		file = "g"
	elif x == 7:
		file = "h"
	return file

def _file_to_x(x):
	x = x.lower()
	if x == 'a':
		row = 0
	elif x == 'b':
		row = 1
	elif x == 'c':
		row = 2
	elif x == 'd':
		row = 3
	elif x == 'e':
		row = 4
	elif x == 'f':
		row = 5
	elif x == 'g':
		row = 6
	elif x == 'h':
		row = 7
	return row


def _xy_to_rank_file(x, y):
	return "%s%s" % (_x_to_file(x), y+1)


def _rank_file_to_xy(rankfile):
	if rankfile == '-':
		return '-'
	return (_file_to_x(rankfile[0]), int(rankfile[1])-1)


def _board_image_coords_to_xy(x, y):
	y = _SIZE-y
	# 0-indexed
	if _PERSPECTIVE == 'w':
		return int(x // (_SIZE/8)), int(y // (_SIZE/8))
	else:
		return int(7 - x // (_SIZE/8)), int(7 - y // (_SIZE/8))


def _xy_to_board_image_coords(row, column):
	# 0-indexed
	return (row * (_SIZE/8), (_SIZE/8) + column * (_SIZE/8))


def AnalysisEvent(event):
	eval, best_move, fen = analysis.CurrentAnalysis()

	if fen != _CURR_DATA['fen']:
		# possible edge case due to multithreading
		return
	
	_adjust_bar(eval)


def _adjust_text(string, loc): 
	__ANALYSIS_GRAPH__.Widget.itemconfig(__ANALYSIS_TEXT__, text=string)
	__ANALYSIS_GRAPH__.Widget.coords(__ANALYSIS_TEXT__, loc)


def _adjust_bar(eval):
	global _SIZE

	if type(eval) == str:
		if '-' in eval:
			if _CURR_DATA['turn'] == 'w':
				""" CORRECT """
				_adjust_text("M" + eval.split('+')[1], (7, 20))
				_set_bar_height(_SIZE)
			else:
				""" CORRECT """
				_adjust_text("M+" + eval.split('-')[1], (7, 790))
				_set_bar_height(0)
		else:
			if int(eval.split('+')[1]) == 0:
				if _CURR_DATA['turn'] == 'w':
					""" CORRECT """
					_adjust_text('0-1', (7, 20))
					_set_bar_height(_SIZE)
				else:
					""" CORRECT """
					_adjust_text('1-0', (7, 790))
					_set_bar_height(0)
			elif _CURR_DATA['turn'] == 'w':
				""" CORRECT """
				_adjust_text("M+" + eval.split('+')[1], (7, 790))
				_set_bar_height(0)
			else:
				""" CORRECT """
				_adjust_text("M-" + eval.split('+')[1], (7, 20))
				_set_bar_height(_SIZE)
	else:
		adjusted_eval = eval/100 if _CURR_DATA['turn'] == 'w' else -eval/100
		_adjust_text(str(adjusted_eval), 
						(7, 20) if adjusted_eval < 0 else (7, 790))
		
		proportion = mathemagics.Transform(eval/100 if _CURR_DATA['turn'] == 'b' else -eval/100, 17)
		_set_bar_height(_SIZE * proportion)


def _data_from_fen(FEN):
	str = FEN.split(' ')

	board_state = []

	lines = str[0].split('/')
	for row in reversed(range(0, 8)):
		temp = []
		for char in lines[row]:
			if char.isnumeric():
				for i in range(0, int(char)):
					temp.append('')
			else:
				temp.append(char)

		board_state.append(temp)

	data = {}
	data['board'] = board_state
	data['turn'] = str[1]
	data['castling'] = str[2]
	data['en passant'] = _rank_file_to_xy(str[3])
	data['move counts'] = [int(str[4]), int(str[5])]
	data['fen'] = FEN

	return data


def _set_piece(x, y, piece):
	global _CURR_DATA
	_CURR_DATA['board'][y][x] = piece

def _get_piece(x, y):
	global _CURR_DATA
	return _CURR_DATA['board'][y][x]


def _layer_legal_moves():
	global _BOARD_GRAPH
	global _LEGAL_MOVES

	for move in _LEGAL_MOVES:
		if _PERSPECTIVE == 'w':
			loc = (move[0]*(_SIZE/8), (move[1]+1)*(_SIZE/8))
		else:
			loc = ((_SIZE * 7/8) - move[0]*(_SIZE/8), _SIZE - move[1]*(_SIZE/8))
		_BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/move_dot.png", location=loc)

def _draw_board():
	global _BOARD_GRAPH
	global _CURR_DATA
	global _LAST_MOVE_FROM
	global _LAST_MOVE_TO
	global _WRONG_FROM
	global _WRONG_TO
	global _WRONG_TYPE
	global _SOLUTION_FROM
	global _SOLUTION_TO
	global _SOLUTION_PIECE

	if _BOARD_GRAPH == None:
		return
	
	_BOARD_GRAPH.erase()
	# _BOARD_GRAPH is necessarily the 800x800 board used in run()
	"""
		Method for reading in images, resizing, then drawing to the graph, will be useful in late-game development

	board_img = Image.open(_IMG_FOLDER + "/board.png")
	board_img = board_img.resize((400, 400))

	buffered = BytesIO()
	board_img.save(buffered, format="PNG")
	img_str = base64.b64encode(buffered.getvalue())

	_BOARD_GRAPH.DrawImage(data=img_str, location=(0, _SIZE))
	"""
	_BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/board.png", location=(0, _SIZE))

	# Draw last move squares
	if _LAST_MOVE_FROM != (-1, -1):
		bottom_corner_from = _xy_to_board_image_coords(_LAST_MOVE_FROM[0], _LAST_MOVE_FROM[1])
		bottom_corner_to = _xy_to_board_image_coords(_LAST_MOVE_TO[0], _LAST_MOVE_TO[1])

		_BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/last_move.png", location=bottom_corner_from)
		_BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/last_move.png", location=bottom_corner_to)


	# Draw pieces
	board = _CURR_DATA['board']
	transparent = (-1, -1) if not dragging else (_MOVING_FROM[0], _MOVING_FROM[1])
	for i in range(0, 8): # ranks, starting from the 8th rank
		for j in range(0, 8): # files, starting from the a file

			if not board[i][j] == '':
				if _PERSPECTIVE == 'w':
					locx, locy = _xy_to_board_image_coords(j, i)
				else:
					locx, locy = _xy_to_board_image_coords(7-j, 7-i)

				if _SOLUTION_TO == (j, i) and _SOLUTION_PIECE != None:
					_draw_piece(_SOLUTION_PIECE, (locx, locy), False)
				elif transparent == (j, i):
					_draw_piece(board[i][j], (locx, locy), False)
				else:
					_draw_piece(board[i][j], (locx, locy), True)


	# Draw wrong move arrow
	if _WRONG_FROM != (-1, -1):
		if _WRONG_TYPE == BEST_MOVE:
			color = BEST_MOVE_COLOR
		elif _WRONG_TYPE == BRILLIANT:
			color = BRILLIANT_COLOR
		elif _WRONG_TYPE == EXCELLENT:
			color = EXCELLENT_COLOR
		elif _WRONG_TYPE == GOOD:
			color = GOOD_COLOR
		elif _WRONG_TYPE == INACCURACY:
			color = INACCURACY_COLOR
		elif _WRONG_TYPE == MISTAKE:
			color = MISTAKE_COLOR
		elif _WRONG_TYPE == BLUNDER:
			color = BLUNDER_COLOR
		else:
			# This should never be reached
			color = 'black'

		_draw_arrow(_WRONG_FROM, _WRONG_TO, color)

	if _SOLUTION_FROM != (-1, -1):
		_draw_arrow(_SOLUTION_FROM, _SOLUTION_TO, BEST_MOVE_COLOR)

		

def _draw_arrow(from_xy, to_xy, color):
	global _IMG_DIM
	global _BOARD_GRAPH

	from_point = _xy_to_board_image_coords(from_xy[0], from_xy[1])
	from_point = (from_point[0] + _IMG_DIM / 2, from_point[1] - _IMG_DIM / 2)

	to_point = _xy_to_board_image_coords(to_xy[0], to_xy[1])
	to_point = (to_point[0] + _IMG_DIM / 2, to_point[1] - _IMG_DIM / 2)

	# Draw arrow head
	angle = _angle((to_point[0] - from_point[0], to_point[1] - from_point[1]), (1, 0))
	if to_point[1] - from_point[1] < 0:
		angle *= -1

	p1theta = 0 + angle
	p2theta = 2.1 + angle
	p3theta = 4.2 + angle
	

	r = 10

	p1x = r * cos(p1theta)
	p1y = r * sin(p1theta)
	p2x = r * cos(p2theta)
	p2y = r * sin(p2theta)
	p3x = r * cos(p3theta)
	p3y = r * sin(p3theta)

	p1 = (p1x + to_point[0], p1y + to_point[1])
	p2 = (p2x + to_point[0], p2y + to_point[1])
	p3 = (p3x + to_point[0], p3y + to_point[1])

	# Draw colors
	_BOARD_GRAPH.DrawPolygon([p1, p2, p3], fill_color=color)
	_BOARD_GRAPH.DrawLine(from_point, to_point, color=color, width=5)

	
"""
	Following functions from https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
"""
def _dotproduct(v1, v2):
	return sum((a*b) for a, b in zip(v1, v2))


def _length(v):
	return sqrt(_dotproduct(v, v))


def _angle(v1, v2):
	return acos(_dotproduct(v1, v2) / (_length(v1) * _length(v2)))
"""
"""


def FocusCurrentPosition(boolean):
	global _FOCUS_CURRENT
	_FOCUS_CURRENT = boolean


def LockBoard():
	global _BOARD_LOCK
	_BOARD_LOCK = True


def UnlockBoard():
	global _BOARD_LOCK
	_BOARD_LOCK = False


def RateEachMove(boolean):
	global _RATE_EACH
	_RATE_EACH = boolean


def RetryMove():
	global _BOARD_LOCK
	_BOARD_LOCK = False


def _draw_piece(piece, loc, opaque):
	global _BOARD_GRAPH

	if piece == 'p':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/pawn_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'r':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/rook_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'n':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/knight_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'b':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/bishop_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'k':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/king_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'q':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/queen_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'P':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/pawn_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'R':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/rook_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'N':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/knight_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'B':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/bishop_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'K':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/king_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'Q':
		return _BOARD_GRAPH.DrawImage(filename=_IMG_FOLDER + "/queen_white" + ("" if opaque else "_trans") + ".png", location=loc)

def _flip_board():
	global _PERSPECTIVE
	if _PERSPECTIVE == 'w':
		_PERSPECTIVE = 'b'
	else:
		_PERSPECTIVE = 'w'

	_draw_board()



_LAST_X = 0
_LAST_Y = 0
def _board_motion_event(event):
	global _LAST_X
	global _LAST_Y

	_LAST_X = event.x
	_LAST_Y = event.y

dragging = False
dragging_image = None
def _board_mouse_one_drag(event):
	global _BOARD_LOCK
	if _BOARD_LOCK:
		return

	global _LAST_X
	global _LAST_Y

	if dragging:
		_BOARD_GRAPH.Widget.coords(dragging_image, (_LAST_X - (_IMG_DIM / 2), _LAST_Y - (_IMG_DIM / 2)))

	_LAST_X = event.x
	_LAST_Y = event.y

def _board_mouse_one(event):
	global _BOARD_LOCK
	if _BOARD_LOCK:
		return

	x, y = _board_image_coords_to_xy(_LAST_X, _LAST_Y)
	
	global _LEGAL_MOVES
	global _MOVING_PIECE
	global _CURR_DATA
	global _MOVING_FROM
	global dragging

	if (_get_piece(x, y).islower() and _CURR_DATA['turn'] == 'b') or (_get_piece(x, y).isupper() and _CURR_DATA['turn'] == 'w'):
		dragging = True
		_MOVING_FROM = (x, y)
		_MOVING_PIECE = _get_piece(x, y)

		_LEGAL_MOVES = _get_legal_moves(x, y)

	_draw_board()
	_layer_legal_moves()
	if dragging:
		_layer_dragged_piece(_get_piece(x, y))

def _layer_dragged_piece(piece):
	global dragging_image

	dragging_image = _draw_piece(piece, (_LAST_X - (_IMG_DIM / 2), _SIZE + (_IMG_DIM / 2) - _LAST_Y), True)


def _board_mouse_three(event):
	# right-click
	#_flip_board()
	pass

def _board_mouse_one_release(event):
	global _BOARD_LOCK
	if _BOARD_LOCK:
		return

	x, y = _board_image_coords_to_xy(_LAST_X, _LAST_Y)

	global _LEGAL_MOVES
	global _MOVING_PIECE
	global _CURR_DATA
	global _MOVING_FROM
	global dragging

	dragging = False

	if _LEGAL_MOVES != None and (x, y) in _LEGAL_MOVES:
		_make_move(_MOVING_FROM, (x, y))
		analysis.SetFen(_CURR_DATA['fen'])
	else:
		_LEGAL_MOVES = ()
		_MOVING_PIECE = None
		_MOVING_FROM = None

	UpdateBoard()


_LAST_MOVE_FROM = (-1, -1)
_LAST_MOVE_Y = (-1, -1)
def _make_move(moving_from, moving_to, promotion=None):
	global _BOARD_LOCK
	global _FOCUS_CURRENT
	if _BOARD_LOCK:
		print("How did you get here?")
		return
	
	if _FOCUS_CURRENT:
		_BOARD_LOCK = True

	x = moving_to[0]
	y = moving_to[1]

	moving_piece = _get_piece(moving_from[0], moving_from[1])
	# Update the value for en passant
	if moving_piece == 'p' or moving_piece == 'P':
		if abs(y - moving_from[1]) == 2:
			_CURR_DATA['en passant'] = (moving_from[0], moving_from[1]+1 if moving_piece == 'P' else moving_from[1]-1)
		else:
			if _CURR_DATA['en passant'] != '-' and _CURR_DATA['en passant'][0] == x and _CURR_DATA['en passant'][1] == y:
				if moving_piece == 'p':
					_set_piece(x, y+1, '')
				else:
					_set_piece(x, y-1, '')
	
			_CURR_DATA['en passant'] = '-'
		

	# Increment the move counts
	if moving_piece.islower():
		_CURR_DATA['move counts'][1] = _CURR_DATA['move counts'][1] + 1
	if _get_piece(x, y) != '' or moving_piece == 'p' or moving_piece == 'P':
		_CURR_DATA['move counts'][0] = 0
	else:
		_CURR_DATA['move counts'][0] = _CURR_DATA['move counts'][0] + 1

	
	# Move the actual piece (if anything is taken, it's overwritten in this process)
	_set_piece(x, y, moving_piece)
	_set_piece(moving_from[0], moving_from[1], '')
	# Remove castling rights if necessary
	if moving_piece == 'R':
		if 'Q' in _CURR_DATA['castling'] and moving_from[0] == 0 and moving_from[1] == 0:
			_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('Q', '')
		elif 'K' in _CURR_DATA['castling'] and moving_from[0] == 7 and moving_from[1] == 0:
			_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('K', '')
	elif moving_piece == 'r':
		if 'q' in _CURR_DATA['castling'] and moving_from[0] == 0 and moving_from[1] == 7:
			_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('q', '')
		elif 'k' in _CURR_DATA['castling'] and moving_from[0] == 7 and moving_from[1] == 7:
			_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('k', '')
	# Special case for castling
	elif moving_piece == 'k':
		_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('k', '').replace('q', '')
		if abs(moving_from[0] - x) == 2:
			if x == 2:
				_set_piece(0, 7, '')
				_set_piece(3, 7, 'r')
			else:
				_set_piece(7, 7, '')
				_set_piece(5, 7, 'r')
	elif moving_piece == 'K':
		_CURR_DATA['castling'] = _CURR_DATA['castling'].replace('K', '').replace('Q', '')
		if abs(moving_from[0] - x) == 2:
			if x == 2:
				_set_piece(0, 0, '')
				_set_piece(3, 0, 'R')
			else:
				_set_piece(7, 0, '')
				_set_piece(5, 0, 'R')
	elif (moving_piece == 'p' and y == 0) or (moving_piece == 'P' and y == 7):
		# Promote the pawn
		global _SIZE

		if promotion == None:
			global _PROMOTING
			_PROMOTING = True
			button_layout = [
				[	
					sg.Button("", image_filename=(_IMG_FOLDER + "/queen_" + ("white" if _CURR_DATA['turn'] == 'w' else "black") + ".png"), 
					key='Q' if _CURR_DATA['turn'] == 'w' else 'q', auto_size_button=False, size=(_IMG_DIM, _IMG_DIM)),
					sg.Button("", image_filename=(_IMG_FOLDER + "/rook_" + ("white" if _CURR_DATA['turn'] == 'w' else "black") + ".png"), 
					key='R' if _CURR_DATA['turn'] == 'w' else 'r', auto_size_button=False, size=(_IMG_DIM, _IMG_DIM)),
					sg.Button("", image_filename=(_IMG_FOLDER + "/knight_" + ("white" if _CURR_DATA['turn'] == 'w' else "black") + ".png"), 
					key='N' if _CURR_DATA['turn'] == 'w' else 'n', auto_size_button=False, size=(_IMG_DIM, _IMG_DIM)),
					sg.Button("", image_filename=(_IMG_FOLDER + "/bishop_" + ("white" if _CURR_DATA['turn'] == 'w' else "black") + ".png"), 
					key='B' if _CURR_DATA['turn'] == 'w' else 'b', auto_size_button=False, size=(_IMG_DIM, _IMG_DIM))
				]
			]

			promotion_window = sg.Window('Promotion', button_layout)
			while True:
				button, _ = promotion_window.read()
				if button is None or button == "__TIMEOUT__":
					pass
				elif button == sg.WIN_CLOSED:
					# TODO: Fix this shit guy, it shouldn't just auto-queen, it should go back, but then again I think the whole
					#		promotion system should probably just be revamped
					promotion = 'Q' if _CURR_DATA['turn'] == 'w' else 'q'
					break
				else:
					promotion = button
					break

			promotion_window.Close()

		_set_piece(x, y, promotion)

	_PROMOTING = False
	global _LAST_MOVE_FROM
	global _LAST_MOVE_TO
	_LAST_MOVE_FROM = moving_from
	_LAST_MOVE_TO = moving_to

	prev_fen = _CURR_DATA['fen']
	# Update whose turn it is
	_CURR_DATA['turn'] = 'b' if _CURR_DATA['turn'] == 'w' else 'w'
	_CURR_DATA['fen'] = _get_curr_fen()

	_LEGAL_MOVES = ()
	_MOVING_PIECE = None
	_MOVING_FROM = None

	global dragging
	if not _FOCUS_CURRENT:
		ResetWrongMove()
	
	if _RATE_EACH:
		UpdateBoard()
		_ROOT.event_generate("<<Eval-Waiting>>")

		old_score, best_move = analysis.SyncAnalysis(prev_fen) # should already be stored, so this should go immediately
		print("best_move: %s" % (best_move))
		print("rank file transforms: %s%s" % (_xy_to_rank_file(_LAST_MOVE_FROM[0], _LAST_MOVE_FROM[1]), _xy_to_rank_file(_LAST_MOVE_TO[0], _LAST_MOVE_TO[1])))
		if best_move[:2] == _xy_to_rank_file(_LAST_MOVE_FROM[0], _LAST_MOVE_FROM[1]) and best_move[2:4] == _xy_to_rank_file(_LAST_MOVE_TO[0], _LAST_MOVE_TO[1]) and	(len(best_move) == 4 or best_move[4] == promotion.lower()):
				_ROOT.event_generate("<<Eval-Done-Best Move>>")
		else:
			new_score, _ = analysis.SyncAnalysis(_CURR_DATA['fen'])
			_ROOT.event_generate("<<Eval-Done-%s>>" % (RatingToStr(analysis._categorize_move(old_score, -new_score 
												if type(new_score) == int else new_score.replace('-', '+') if '-' in new_score else new_score.replace('+', '-')))))


def ResetWrongMove():
	global _WRONG_FROM
	global _WRONG_TO
	global _WRONG_TYPE

	_WRONG_FROM = (-1, -1)
	_WRONG_TO = (-1, -1)
	_WRONG_TYPE = ""


def ResetLastMove():
	global _LAST_MOVE_FROM
	global _LAST_MOVE_TO

	_LAST_MOVE_FROM = (-1, -1)
	_LAST_MOVE_TO = (-1, -1)


def SetLastMove(last_from, last_to):
	global _LAST_MOVE_FROM
	global _LAST_MOVE_TO

	_LAST_MOVE_FROM = last_from
	_LAST_MOVE_TO = last_to


_WRONG_FROM = (-1, -1)
_WRONG_TO = (-1, -1)
_WRONG_TYPE = ""
def SetWrongMove(wrong_from, wrong_to, wrong_type):
	global _WRONG_FROM
	global _WRONG_TO
	global _WRONG_TYPE

	_WRONG_FROM = wrong_from
	_WRONG_TO = wrong_to
	_WRONG_TYPE = wrong_type


_SOLUTION_FROM = (-1, -1)
_SOLUTION_TO = (-1, -1)
_SOLUTION_PIECE = None
def SetSolution(str):
	global _SOLUTION_FROM
	global _SOLUTION_TO
	global _SOLUTION_PIECE

	_SOLUTION_FROM = _rank_file_to_xy(str[:2])
	_SOLUTION_TO = _rank_file_to_xy(str[2:4])

	if len(str) == 5:
		_SOLUTION_PIECE = str[4]


def ResetSolution():
	global _SOLUTION_FROM
	global _SOLUTION_TO

	_SOLUTION_FROM = (-1, -1)
	_SOLUTION_TO = (-1, -1)


def UpdateBoard():
	_draw_board()
	_ROOT.update()


def _get_legal_moves(x, y):
	global _CURR_DATA

	moves = _get_moves(x, y)
	_LEGAL_MOVES = []
	piece = _get_piece(x, y)

	for move in moves:
		taken_piece = _get_piece(move[0], move[1])
		_set_piece(move[0], move[1], piece)
		_set_piece(x, y, '')

		if (piece.isupper() and not _is_in_check('w')) or (piece.islower() and not _is_in_check('b')):
			_LEGAL_MOVES.append(move)
		_set_piece(x, y, piece)
		_set_piece(move[0], move[1], taken_piece)

	return _LEGAL_MOVES

# THIS FUNCTION DOES NOT CHECK THE LEGALITY OF THE MOVES IT RETURNS
def _get_moves(x, y):
	# 0-indexed, does NOT take input as rank/file
	global _CURR_DATA
	board = _CURR_DATA['board']

	piece = _get_piece(x, y)
	moves = []

	if piece == '':
		return moves
	elif piece == 'P':
		if y == 7:
			# weird edge case
			return []
		if _get_piece(x, y+1) == '':
			moves.append((x, y+1))
			if y == 1 and _get_piece(x, y+2) == '':
				moves.append((x, y+2))
		if x > 0 and _get_piece(x-1, y+1).islower():
			moves.append((x-1, y+1))
		if x < 7 and _get_piece(x+1, y+1).islower():
			moves.append((x+1, y+1))
		if _CURR_DATA['en passant'] != '-':
			en_square = _CURR_DATA['en passant']
			if abs(en_square[0] - x) == 1 and y - en_square[1] == -1:
				moves.append(en_square)

		return moves
	elif piece == 'p':
		if y == 0:
			# weird edge case
			return []
		if _get_piece(x, y-1) == '':
			moves.append((x, y-1))
			if y == 6 and _get_piece(x, y-2) == '':
				moves.append((x, y-2))
		if x > 0 and _get_piece(x-1, y-1).isupper():
			moves.append((x-1, y-1))
		if x < 7 and _get_piece(x+1, y-1).isupper():
			moves.append((x+1, y-1))
		if _CURR_DATA['en passant'] != '-':
			en_square = _CURR_DATA['en passant']
			if abs(en_square[0] - x) == 1 and y - en_square[1] == 1:
				moves.append(en_square)

		return moves
	elif piece == 'r':
		for i in range(x+1, 8):
			if _get_piece(i, y).islower():
				break
			elif _get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if _get_piece(i, y).islower():
				break
			elif _get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if _get_piece(x, j).islower():
				break
			if _get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if _get_piece(x, j).islower():
				break
			if _get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'R':
		for i in range(x+1, 8):
			if _get_piece(i, y).isupper():
				break
			elif _get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if _get_piece(i, y).isupper():
				break
			elif _get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if _get_piece(x, j).isupper():
				break
			if _get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if _get_piece(x, j).isupper():
				break
			if _get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'n':
		if y < 7:
			if x > 1 and not _get_piece(x-2, y+1).islower():
				moves.append((x - 2, y + 1))
			if x < 6 and not _get_piece(x+2, y+1).islower():
				moves.append((x + 2, y + 1))
			if y < 6:
				if x > 0 and not _get_piece(x-1, y+2).islower():
					moves.append((x - 1, y + 2))
				if x < 7 and not _get_piece(x+1, y+2).islower():
					moves.append((x + 1, y + 2))

		if y > 0:
			if x > 1 and not _get_piece(x-2, y-1).islower():
				moves.append((x - 2, y - 1))
			if x < 6 and not _get_piece(x+2, y-1).islower():
				moves.append((x + 2, y - 1))
			if y > 1:
				if x > 0 and not _get_piece(x-1, y-2).islower():
					moves.append((x - 1, y - 2))
				if x < 7 and not _get_piece(x+1, y-2).islower():
					moves.append((x + 1, y - 2))

		return moves
	elif piece == 'N':
		if y < 7:
			if x > 1 and not _get_piece(x-2, y+1).isupper():
				moves.append((x - 2, y + 1))
			if x < 6 and not _get_piece(x+2, y+1).isupper():
				moves.append((x + 2, y + 1))
			if y < 6:
				if x > 0 and not _get_piece(x-1, y+2).isupper():
					moves.append((x - 1, y + 2))
				if x < 7 and not _get_piece(x+1, y+2).isupper():
					moves.append((x + 1, y + 2))

		if y > 0:
			if x > 1 and not _get_piece(x-2, y-1).isupper():
				moves.append((x - 2, y - 1))
			if x < 6 and not _get_piece(x+2, y-1).isupper():
				moves.append((x + 2, y - 1))
			if y > 1:
				if x > 0 and not _get_piece(x-1, y-2).isupper():
					moves.append((x - 1, y - 2))
				if x < 7 and not _get_piece(x+1, y-2).isupper():
					moves.append((x + 1, y - 2))

		return moves
	elif piece == 'B':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		return moves
	elif piece == 'b':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		return moves
	elif piece == 'Q':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if _get_piece(i, j).isupper():
				break
			elif _get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))


		for i in range(x+1, 8):
			if _get_piece(i, y).isupper():
				break
			elif _get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if _get_piece(i, y).isupper():
				break
			elif _get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if _get_piece(x, j).isupper():
				break
			if _get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if _get_piece(x, j).isupper():
				break
			if _get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'q':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if _get_piece(i, j).islower():
				break
			elif _get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))


		for i in range(x+1, 8):
			if _get_piece(i, y).islower():
				break
			elif _get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if _get_piece(i, y).islower():
				break
			elif _get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if _get_piece(x, j).islower():
				break
			if _get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if _get_piece(x, j).islower():
				break
			if _get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'K':
		if 'K' in _CURR_DATA['castling'] and _get_piece(5, 0) == '' and _get_piece(6, 0) == '':
			_set_piece(5, 0, 'K')
			_set_piece(6, 0, 'K')

			if not _is_in_check('w'):
				moves.append((6, 0))

			_set_piece(5, 0, '')
			_set_piece(6, 0, '')
		if 'Q' in _CURR_DATA['castling'] and _get_piece(1, 0) == '' and _get_piece(2, 0) == '' and _get_piece(3, 0) == '':
			_set_piece(1, 0, 'K')
			_set_piece(2, 0, 'K')
			_set_piece(3, 0, 'K')

			if not _is_in_check('w'):
				moves.append((2, 0))

			_set_piece(1, 0, '')
			_set_piece(2, 0, '')
			_set_piece(3, 0, '')

		prelim = []
		prelim.append((x, y+1))
		prelim.append((x, y-1))
		prelim.append((x+1, y))
		prelim.append((x-1, y))
		prelim.append((x+1, y+1))
		prelim.append((x+1, y-1))
		prelim.append((x-1, y+1))
		prelim.append((x-1, y-1))
		for move in prelim:
			try:
				if not _get_piece(move[0], move[1]).isupper():
					moves.append(move)
			except IndexError:
				pass

		return moves
	elif piece == 'k':
		if 'k' in _CURR_DATA['castling'] and _get_piece(5, 7) == '' and _get_piece(6, 7) == '':
			moves.append((6, 7))
		if 'q' in _CURR_DATA['castling'] and _get_piece(1, 7) == '' and _get_piece(2, 7) == '' and _get_piece(3, 7) == '':
			moves.append((2, 7))

		prelim = []
		prelim.append((x, y+1))
		prelim.append((x, y-1))
		prelim.append((x+1, y))
		prelim.append((x-1, y))
		prelim.append((x+1, y+1))
		prelim.append((x+1, y-1))
		prelim.append((x-1, y+1))
		prelim.append((x-1, y-1))
		for move in prelim:
			try:
				if not _get_piece(move[0], move[1]).islower():
					moves.append(move)
			except IndexError:
				pass

	return moves


# Side is either 'b' or 'w'
def _is_in_check(side):
	side = 'k' if side == 'b' else 'K'
	king = None

	for i in range(0, 8):
		for j in range(0, 8):
			if _get_piece(i, j) == side:
				king = (i, j)
				break
			if not king == None:
				break

	for i in range(0, 8):
		for j in range(0, 8):
			if (_get_piece(i, j).isupper() and side == 'k') or (_get_piece(i, j).islower() and side == 'K'):
				if king in _get_moves(i, j):
					return True

	return False


_PGN_INDEX = 0
def PGNNext():
	global _PGN_INDEX
	global _PGN_DATA

	if _PGN_INDEX + 1 < len(_PGN_DATA):
		_PGN_INDEX += 1
		SetPosFromFEN(_PGN_DATA[_PGN_INDEX])
		analysis.SetFen(_PGN_DATA[_PGN_INDEX])


def PGNBack():
	global _PGN_INDEX
	global _PGN_DATA
	
	if _PGN_INDEX > 0:
		_PGN_INDEX -= 1
		SetPosFromFEN(_PGN_DATA[_PGN_INDEX])
		analysis.SetFen(_PGN_DATA[_PGN_INDEX])



def PGNToFENList(PGN):
	try:
		return _pgn_to_fen_helper(PGN)
	except:
		print("Exception in user code:")
		traceback.print_exc(file=sys.stdout)
		return False


_PGN_DATA = []
def _pgn_to_fen_helper(PGN):
	PGN = PGN + ' '
	PGN = PGN.replace('\n', ' ').replace('\r', '')

	global _PGN_DATA

	SetPosFromFEN(_STARTING_POS_FEN)
	_PGN_DATA.append([])
	_PGN_DATA[0].append(_CURR_DATA['fen'])

	i = 0
	move_index = 0
	white = True
	while i < len(PGN):
		if PGN[i] == '{':
			while PGN[i] != '}':
				i += 1
		elif PGN[i] == '(':
			""" Possible TODO: Implement reading nested lines instead of ignoring them """
			while PGN[i] != ')':
				i+= 1
		elif PGN[i] == ';':
			while PGN[i] != '\n':
				i += 1
		elif PGN[i] == '[':
			while PGN[i] != ']':
				""" TODO: Implement reading the tag info here; all used tags are listed on https://en.wikipedia.org/wiki/Portable_Game_Notation#Tag_pairs """
				i += 1
		elif PGN[i] == '\n':
			print("Caught newline")
			pass
		elif PGN[i] == ' ':
			pass
		elif _is_int(PGN[i]) or PGN[i] == '.':
			pass
		else:
			_index = 0
			move = ""
			while i < len(PGN) and PGN[i] != ' ':
				move += PGN[i]
				i += 1

			if 'O-O' in move:
				if move == 'O-O':
					if white:
						_make_move((4, 0), (6, 0))
						move = ((4, 0), (6, 0))
					else:
						_make_move((4, 7), (6, 7))
						move = ((4, 7), (6, 7))
				elif move == 'O-O-O':
					if white:
						_make_move((4, 0), (2, 0))
						move = ((4, 0), (2, 0))
					else:
						_make_move((4, 7), (2, 7))
						move = ((4, 7), (2, 7))
			elif '-' in move:
				return True
			else:
				if '+' in move:
					move = move.split('+')[0]
				elif '#' in move:
					move = move.split('#')[0]

				if move[_index] == 'K':
					moving_piece = 'K'
				elif move[_index] == 'Q':
					moving_piece = 'Q'
				elif move[_index] == 'R':
					moving_piece = 'R'
				elif move[_index] == 'N':
					moving_piece = 'N'
				elif move[_index] == 'B':
					moving_piece = 'B'
				else:
					moving_piece = 'P'
					_index -= 1 # counteract the coming += 1
				_index += 1

				move = move[_index:len(move)]
				if not white:
					moving_piece = moving_piece.lower()

				promotion = ""
				if '=' in move:
					move = move.split('=')
					promotion = move[1] if white else move[1].lower()
					move = move[0]

				from_rank = None
				from_file = None
				if 'x' in move:
					move = move.split('x')
					take_from = move[0]
					move = move[1]
					if len(take_from) == 1:
						if _is_int(take_from):
							from_rank = int(take_from)
						else:
							from_file = take_from
				elif len(move) == 3:
					if _is_int(move[0]):
						from_rank = int(move[0])
					else:
						from_file = move[0]
					move = move[1:3]
					
				to_x, to_y = _rank_file_to_xy(move)

				move = _make_pgn_move(moving_piece, (to_x, to_y), from_rank, from_file, promotion)
				if move == None:
					_PGN_DATA = []
					return False
			
			_PGN_DATA.append([])

			_PGN_DATA[move_index+1].append(_CURR_DATA['fen'])
			_PGN_DATA[move_index].append(move)

			move_index += 1
			white = not white
				
		i += 1

	return True


def _is_int(string):
	try:
		int(string)
		return True
	except ValueError:
		return False


def _make_pgn_move(moving_piece, loc, from_rank, from_file, promotion):
	if from_file != None:
		for j in range(0, 8):
			if _get_piece(_file_to_x(from_file), j) == moving_piece:
				if loc in _get_legal_moves(_file_to_x(from_file), j):
					_make_move((_file_to_x(from_file), j), loc, promotion=promotion)
					return ((_file_to_x(from_file), j), loc)

	elif from_rank != None:
		from_rank += -1
		for i in range(0, 8):
			if _get_piece(i, from_rank) == moving_piece:
				if loc in _get_legal_moves(i, from_rank):
					_make_move((i, from_rank), loc, promotion=promotion)
					return ((i, from_rank), loc)

	else:
		for i in range(0, 8):
			for j in range(0, 8):
				if _get_piece(i, j) == moving_piece:
					if loc in _get_legal_moves(i, j):
						_make_move((i, j), loc, promotion=promotion)
						return ((i, j), loc)

	print("Help me, I'm lost! Info:\n\tmoving_piece:\t %s\n\tloc:\t(%s, %s)\n\tfrom_rank:\t%s\n\tfrom_file:\t%s\n\tpromotion:\t%s\n"
			% (moving_piece, loc[0], loc[1], from_rank, from_file, promotion))
	return None
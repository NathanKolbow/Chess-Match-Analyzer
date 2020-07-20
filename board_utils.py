import PySimpleGUI as sg
import tkinter
import analysis
import threading
from math import sqrt

_STARTING_POS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_IMG_FOLDER = "pieces_wooden"
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
_SIZE = 0

def Init(graph, bar, root, size):
	global _ROOT
	_ROOT = root

	graph.Widget.bind("<Motion>", _board_motion_event)
	graph.Widget.bind("<Button-1>", _board_mouse_one)
	graph.Widget.bind("<B1-Motion>", _board_mouse_one_drag)
	graph.Widget.bind("<ButtonRelease-1>", _board_mouse_one_release)
	graph.Widget.bind("<Button-3>", _board_mouse_three)

	global _BOARD_GRAPH
	global _CURR_DATA
	_BOARD_GRAPH = graph


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
	_IMG_DIM = _SIZE / 8

	__ANALYSIS_GRAPH__ = bar
	__ANALYSIS_GRAPH__.DrawRectangle((0, 0), (50, size), fill_color='white', line_color='black')
	__ANALYSIS_RECT__ = __ANALYSIS_GRAPH__.DrawRectangle((0, size), (50, 0), fill_color='gray')
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
		if type(y) == float:
			__RECT_TARGET_Y__ = y

			"""		if not _ANIMATING:
						_ANIMATING = True
						_ROOT.update()
						_ROOT.event_generate("<<Bar-Animation>>")

				else:
					print("ELSE")"""

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

	out = out + " " + _CURR_DATA['turn'] + " " + _CURR_DATA['castling'] + " "
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

def _board_image_coords(row, column):
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
	""" TODO: Check to make sure the settings for mates are correct (they probably aren't) """
	global _SIZE

	if type(eval) == str:
		if '-' in eval:
			if _CURR_DATA['turn'] == 'w':
				print('1')
				_adjust_text("M" + eval.split('+')[1], (7, 20))
				_set_bar_height(_SIZE)
			else:
				print('2')
				_adjust_text("M+" + eval.split('-')[1], (7, 790))
				_set_bar_height(0)
		else:
			if int(eval.split('+')[1]) == 0:
				if _CURR_DATA['turn'] == 'w':
					print('3')
					_adjust_text('0-1', (7, 20))
					_set_bar_height(0)
				else:
					print('4')
					_adjust_text('1-0', (7, 790))
					_set_bar_height(_SIZE)
			elif _CURR_DATA['turn'] == 'w':
				print('5')
				_adjust_text("M+" + eval.split('+')[1], (7, 790))
				_set_bar_height(0)
			else:
				print('6')
				_adjust_text("M-" + eval.split('+')[1], (7, 20))
				_set_bar_height(_SIZE)
	else:
		adjusted_eval = eval/100 if _CURR_DATA['turn'] == 'w' else -eval/100
		_adjust_text(str(adjusted_eval), 
						(7, 20) if adjusted_eval < 0 else (7, 790))
		
		proportion = _transform(eval/100)
		_set_bar_height(_SIZE * proportion)
		


def _transform(eval):
	if _CURR_DATA['turn'] == 'w':
		eval = -eval

	if eval > 17:
		return 0.95
	else:
		return max(min(0.98 * pow(2.72, -((pow(eval - 13.5, 2))/263)) + 0.01, 0.95), 0.05)


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
		_BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/move_dot.png", location=loc)

def _draw_board():
	global _BOARD_GRAPH
	global _CURR_DATA

	_BOARD_GRAPH.erase()
	# _BOARD_GRAPH is necessarily the 800x800 board used in run()
	_BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/board.png", location=(0, _SIZE))

	board = _CURR_DATA['board']
	transparent = (-1, -1) if not dragging else (_MOVING_FROM[0], _MOVING_FROM[1])
	for i in range(0, 8): # ranks, starting from the 8th rank
		for j in range(0, 8): # files, starting from the a file

			if not board[i][j] == '':
				if _PERSPECTIVE == 'w':
					locx, locy = _board_image_coords(j, i)
				else:
					locx, locy = _board_image_coords(7-j, 7-i)

				if transparent == (j, i):
					_draw_piece(board[i][j], (locx, locy), False)
				else:
					_draw_piece(board[i][j], (locx, locy), True)




def _draw_piece(piece, loc, opaque):
	global _BOARD_GRAPH

	if piece == 'p':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/pawn_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'r':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/rook_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'n':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/knight_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'b':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/bishop_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'k':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/king_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'q':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/queen_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'P':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/pawn_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'R':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/rook_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'N':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/knight_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'B':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/bishop_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'K':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/king_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'Q':
		return _BOARD_GRAPH.DrawImage(filename="img/" + _IMG_FOLDER + "/queen_white" + ("" if opaque else "_trans") + ".png", location=loc)

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
	global _LAST_X
	global _LAST_Y

	if dragging:
		_BOARD_GRAPH.Widget.coords(dragging_image, (_LAST_X - (_IMG_DIM / 2), _LAST_Y - (_IMG_DIM / 2)))

	_LAST_X = event.x
	_LAST_Y = event.y

def _board_mouse_one(event):
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
	x, y = _board_image_coords_to_xy(_LAST_X, _LAST_Y)

	global _LEGAL_MOVES
	global _MOVING_PIECE
	global _CURR_DATA
	global _MOVING_FROM
	global dragging

	if _LEGAL_MOVES != None and (x, y) in _LEGAL_MOVES:
		fen_before = _CURR_DATA['fen']

		_make_move(_MOVING_FROM, (x, y))

		_CURR_DATA['fen'] = _get_curr_fen()

		_ROOT.after(10, analysis.RateMove, fen_before, _CURR_DATA['fen'])

		analysis.SetFen(_CURR_DATA['fen'])

		_LEGAL_MOVES = ()
		_MOVING_PIECE = None
		_MOVING_FROM = None
	else:
		_LEGAL_MOVES = ()
		_MOVING_PIECE = None
		_MOVING_FROM = None

	dragging = False
	_draw_board()


def _make_move(moving_from, moving_to, promotion='q'):
	print("MAKING MOVE: (%s, %s) to (%s, %s)" % (moving_from[0], moving_from[1], moving_to[0], moving_to[1]))
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
		_set_piece(x, y, promotion.lower() if moving_piece == 'p' else promotion.upper())

	# Update whose turn it is
	_CURR_DATA['turn'] = 'b' if _CURR_DATA['turn'] == 'w' else 'w'
	_CURR_DATA['fen'] = _get_curr_fen()



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


_PGN_DATA = []
def _pgn_to_fen_list(PGN):
	SetPosFromFEN(_STARTING_POS_FEN)
	_PGN_DATA.append(_CURR_DATA['fen'])

	i = 0
	white = True
	while i < len(PGN):
		print('i at: %s/%s' % (i, len(PGN) - 1))
		if PGN[i] == '{':
			while PGN[i] != '}':
				i += 1
		elif PGN[i] == ';':
			while PGN[i] != '\n':
				i += 1
		elif PGN[i] == '[':
			print("Skipping...")
			while PGN[i] != ']':
				print("looping...")
				""" TODO: Implement actually reading the tag info here; all used tags are listed on https://en.wikipedia.org/wiki/Portable_Game_Notation#Tag_pairs """
				i += 1
		elif PGN[i] == '\n':
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
					else:
						_make_move((4, 7), (6, 7))
				elif move == 'O-O-O':
					if white:
						_make_move((4, 0), (2, 0))
					else:
						_make_move((4, 7), (2, 7))
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

				_make_pgn_move(moving_piece, (to_x, to_y), from_rank, from_file, promotion)
				
			_PGN_DATA.append(_CURR_DATA['fen'])
			white = not white
				
		i += 1

	print('Done loading PGN.')


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
					return

	elif from_rank != None:
		from_rank += -1
		for i in range(0, 8):
			if _get_piece(i, from_rank) == moving_piece:
				if loc in _get_legal_moves(i, from_rank):
					_make_move((i, from_rank), loc, promotion=promotion)
					return

	else:
		for i in range(0, 8):
			for j in range(0, 8):
				if _get_piece(i, j) == moving_piece:
					if loc in _get_legal_moves(i, j):
						_make_move((i, j), loc, promotion=promotion)
						return

	print("Help me, I'm lost! Info:\n\tmoving_piece:\t %s\n\tloc:\t(%s, %s)\n\tfrom_rank:\t%s\n\tfrom_file:\t%s\n\tpromotion:\t%s\n"
			% (moving_piece, loc[0], loc[1], from_rank, from_file, promotion))
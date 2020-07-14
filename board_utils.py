import PySimpleGUI as sg
import analysis

img_folder = "pieces_wooden"
img_dim = 100 # dimension of the piece images, i.e. 100x100

perspective = 'w'
board_graph = None

# curr_data contains ALL of the information necessary to the current position on the board
# i.e. curr_data is roughly equivalent to an FEN, NOT a PGN
## curr_data {
## 		board: 2d array of the current board layout
##		turn: 'w' or 'b' depending on whose turn it is
##		castling: string containing kqKQ with info on who can castle which way
##		en passant: if a pawn was moved 2 spaced last turn, this is the square that that pawn can be en passanted on (in (x, y) form)
##		move counts: as per FEN standards
##      fen: the FEN string of the current position, mostly just stored so that analysis.py can use it
## }
curr_data = {}


# list of legal moves for the currently selected piece
legal_moves = ()
# current piece being moved
moving_piece = None
moving_from = None

def Init(graph, bar):
	graph.Widget.bind("<Motion>", board_motion_event)
	graph.Widget.bind("<Button-1>", board_mouse_one)
	graph.Widget.bind("<B1-Motion>", board_mouse_one_drag)
	graph.Widget.bind("<ButtonRelease-1>", board_mouse_one_release)
	graph.Widget.bind("<Button-3>", board_mouse_three)

	global board_graph
	global curr_data
	board_graph = graph

	analysis.Init(bar)
	analysis.init_background_analysis()

def get_curr_fen():
	global curr_data

	out = ""
	blank_count = 0
	for j in reversed(range(0, 8)):
		for i in range(0, 8):
			piece = get_piece(i, j)
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

	out = out + " " + curr_data['turn'] + " " + curr_data['castling'] + " "
	if curr_data['en passant'] == '-':
		out = out + "- "
	else:
		out = out + xy_to_rank_file(curr_data['en passant'][0], curr_data['en passant'][1]) + " "

	out = out + str(curr_data['move counts'][0]) + " " + str(curr_data['move counts'][1])
	return out

def set_pos_from_fen(FEN):
	global curr_data
	curr_data = data_from_fen(FEN)
	#analysis.background_analysis(FEN, curr_data['turn'])
	_draw_board()

def xy_to_rank_file(x, y):
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

	return "%s%s" % (file, y+1)

def rank_file_to_xy(rankfile):
	if rankfile == '-':
		return '-'
	if rankfile[0] == 'a':
		row = 0
	elif rankfile[0] == 'b':
		row = 1
	if rankfile[0] == 'c':
		row = 2
	elif rankfile[0] == 'd':
		row = 3
	if rankfile[0] == 'e':
		row = 4
	elif rankfile[0] == 'f':
		row = 5
	if rankfile[0] == 'g':
		row = 6
	elif rankfile[0] == 'h':
		row = 7

	return (row, int(rankfile[1])-1)

def board_image_coords_to_xy(x, y):
	y = 800-y
	# 0-indexed
	if perspective == 'w':
		return x // 100, y // 100
	else:
		return 7 - x // 100, 7 - y // 100

def board_image_coords(row, column):
	# 0-indexed
	return (row * 100, 100 + column * 100)

def data_from_fen(FEN):
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
	data['en passant'] = rank_file_to_xy(str[3])
	data['move counts'] = [int(str[4]), int(str[5])]

	print('board: ')
	print(data['board'])
	return data


def set_piece(x, y, piece):
	global curr_data
	curr_data['board'][y][x] = piece

def get_piece(x, y):
	global curr_data
	return curr_data['board'][y][x]


def _layer_legal_moves():
	global board_graph
	global legal_moves

	for move in legal_moves:
		if perspective == 'w':
			loc = (move[0]*100, (move[1]+1)*100)
		else:
			loc = (700 - move[0]*100, 800 - move[1]*100)
		board_graph.DrawImage(filename="img/" + img_folder + "/move_dot.png", location=loc)

def _draw_board():
	global board_graph
	global curr_data

	board_graph.erase()
	# board_graph is necessarily the 800x800 board used in run()
	board_graph.DrawImage(filename="img/" + img_folder + "/board.png", location=(0, 800))

	board = curr_data['board']
	transparent = (-1, -1) if not dragging else (moving_from[0], moving_from[1])
	for i in range(0, 8): # ranks, starting from the 8th rank
		for j in range(0, 8): # files, starting from the a file

			if not board[i][j] == '':
				if perspective == 'w':
					locx, locy = board_image_coords(j, i)
				else:
					locx, locy = board_image_coords(7-j, 7-i)

				if transparent == (j, i):
					_draw_piece(board[i][j], (locx, locy), False)
				else:
					_draw_piece(board[i][j], (locx, locy), True)




def _draw_piece(piece, loc, opaque):
	global board_graph

	if piece == 'p':
		return board_graph.DrawImage(filename="img/" + img_folder + "/pawn_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'r':
		return board_graph.DrawImage(filename="img/" + img_folder + "/rook_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'n':
		return board_graph.DrawImage(filename="img/" + img_folder + "/knight_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'b':
		return board_graph.DrawImage(filename="img/" + img_folder + "/bishop_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'k':
		return board_graph.DrawImage(filename="img/" + img_folder + "/king_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'q':
		return board_graph.DrawImage(filename="img/" + img_folder + "/queen_black" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'P':
		return board_graph.DrawImage(filename="img/" + img_folder + "/pawn_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'R':
		return board_graph.DrawImage(filename="img/" + img_folder + "/rook_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'N':
		return board_graph.DrawImage(filename="img/" + img_folder + "/knight_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'B':
		return board_graph.DrawImage(filename="img/" + img_folder + "/bishop_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'K':
		return board_graph.DrawImage(filename="img/" + img_folder + "/king_white" + ("" if opaque else "_trans") + ".png", location=loc)
	elif piece == 'Q':
		return board_graph.DrawImage(filename="img/" + img_folder + "/queen_white" + ("" if opaque else "_trans") + ".png", location=loc)

def flip_board():
	global perspective
	if perspective == 'w':
		perspective = 'b'
	else:
		perspective = 'w'

	_draw_board()



last_X = 0
last_Y = 0
def board_motion_event(event):
	global last_X
	global last_Y

	last_X = event.x
	last_Y = event.y

dragging = False
dragging_image = None
def board_mouse_one_drag(event):
	global last_X
	global last_Y

	board_graph.Widget.coords(dragging_image, (last_X - (img_dim / 2), last_Y - (img_dim / 2)))

	last_X = event.x
	last_Y = event.y

def board_mouse_one(event):
	x, y = board_image_coords_to_xy(last_X, last_Y)
	
	global legal_moves
	global moving_piece
	global curr_data
	global moving_from
	global dragging

	if (get_piece(x, y).islower() and curr_data['turn'] == 'b') or (get_piece(x, y).isupper() and curr_data['turn'] == 'w'):
		dragging = True
		moving_from = (x, y)
		moving_piece = get_piece(x, y)

		legal_moves = _get_legal_moves(x, y)

	_draw_board()
	_layer_legal_moves()
	if dragging:
		_layer_dragged_piece(get_piece(x, y))

def _layer_dragged_piece(piece):
	global dragging_image

	dragging_image = _draw_piece(piece, (last_X - (img_dim / 2), 800 + (img_dim / 2) - last_Y), True)


def board_mouse_three(event):
	# right-click
	flip_board()

def board_mouse_one_release(event):
	x, y = board_image_coords_to_xy(last_X, last_Y)
	print('Released on (%s, %s)' % (x, y))

	global legal_moves
	global moving_piece
	global curr_data
	global moving_from
	global dragging

	if legal_moves != None and (x, y) in legal_moves:
		# Update the value for en passant
		curr_data['en passant'] = "-"
		if moving_piece == 'p' or moving_piece == 'P':
			if abs(y - moving_from[1]) == 2:
				curr_data['en passant'] = (moving_from[0], moving_from[1]+1 if moving_piece == 'P' else moving_from[1]-1)
				print("En passant is now: ", curr_data['en passant'])	

		# Increment the move counts
		if moving_piece.islower():
			curr_data['move counts'][1] = curr_data['move counts'][1] + 1
		if get_piece(x, y) != '' or moving_piece == 'p' or moving_piece == 'P':
			curr_data['move counts'][0] = 0
		else:
			curr_data['move counts'][0] = curr_data['move counts'][0] + 1


		# Move the actual piece (if anything is taken, it's overwritten in this process)
		set_piece(x, y, moving_piece)
		set_piece(moving_from[0], moving_from[1], '')
		# Remove castling rights if necessary
		if moving_piece == 'R':
			if 'Q' in curr_data['castling'] and moving_from[0] == 0 and moving_from[1] == 0:
				curr_data['castling'] = curr_data['castling'].replace('Q', '')
			elif 'K' in curr_data['castling'] and moving_from[0] == 7 and moving_from[1] == 0:
				curr_data['castling'] = curr_data['castling'].replace('K', '')
		elif moving_piece == 'r':
			if 'q' in curr_data['castling'] and moving_from[0] == 0 and moving_from[1] == 7:
				curr_data['castling'] = curr_data['castling'].replace('q', '')
			elif 'k' in curr_data['castling'] and moving_from[0] == 7 and moving_from[1] == 7:
				curr_data['castling'] = curr_data['castling'].replace('k', '')
		# Special case for castling
		elif moving_piece == 'k':
			curr_data['castling'] = curr_data['castling'].replace('k', '').replace('q', '')
			if abs(moving_from[0] - x) == 2:
				if x == 2:
					set_piece(0, 7, '')
					set_piece(3, 7, 'r')
				elif x == 6:
					set_piece(5, 7, 'r')
					set_piece(7, 7, '')
		elif (moving_piece == 'p' and y == 0) or (moving_piece == 'P' and y == 7):
			# Auto-queen
			set_piece(x, y, 'q' if moving_piece == 'p' else 'Q')

		# Update whose turn it is
		curr_data['turn'] = 'b' if curr_data['turn'] == 'w' else 'w'

		ffeenn = get_curr_fen()
		print('Set curr_data[\'fen\'] to the new FEN: %s.' % (get_curr_fen()))
		curr_data['fen'] = get_curr_fen()
		analysis.update_fen(curr_data['fen'])

		legal_moves = ()
		moving_piece = None
		moving_from = None
	else:
		legal_moves = ()
		moving_piece = None
		moving_from = None

	dragging = False
	_draw_board()


def _get_legal_moves(x, y):
	global curr_data

	moves = get_moves(x, y)
	legal_moves = []
	piece = get_piece(x, y)

	for move in moves:
		taken_piece = get_piece(move[0], move[1])
		set_piece(move[0], move[1], piece)
		set_piece(x, y, '')

		if (piece.isupper() and not is_in_check('w')) or (piece.islower() and not is_in_check('b')):
			legal_moves.append(move)
		set_piece(x, y, piece)
		set_piece(move[0], move[1], taken_piece)

	return legal_moves

# THIS FUNCTION DOES NOT CHECK THE LEGALITY OF THE MOVES IT RETURNS
def get_moves(x, y):
	# 0-indexed, does NOT take input as rank/file
	global curr_data
	board = curr_data['board']

	piece = get_piece(x, y)
	moves = []

	if piece == '':
		return moves
	elif piece == 'P':
		if y == 7:
			# weird edge case
			return []
		if get_piece(x, y+1) == '':
			moves.append((x, y+1))
			if y == 1 and get_piece(x, y+2) == '':
				moves.append((x, y+2))
		if x > 0 and get_piece(x-1, y+1).islower():
			moves.append((x-1, y+1))
		if x < 7 and get_piece(x+1, y+1).islower():
			moves.append((x+1, y+1))
		if curr_data['en passant'] != '-':
			en_square = curr_data['en passant']
			if abs(en_square[0] - x) == 1 and y - en_square[1] == -1:
				moves.append(en_square)

		return moves
	elif piece == 'p':
		if y == 0:
			# weird edge case
			return []
		if get_piece(x, y-1) == '':
			moves.append((x, y-1))
			if y == 6 and get_piece(x, y-2) == '':
				moves.append((x, y-2))
		if x > 0 and get_piece(x-1, y-1).isupper():
			moves.append((x-1, y-1))
		if x < 7 and get_piece(x+1, y-1).isupper():
			moves.append((x+1, y-1))
		if curr_data['en passant'] != '-':
			en_square = curr_data['en passant']
			if abs(en_square[0] - x) == 1 and y - en_square[1] == 1:
				moves.append(en_square)

		return moves
	elif piece == 'r':
		for i in range(x+1, 8):
			if get_piece(i, y).islower():
				break
			elif get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if get_piece(i, y).islower():
				break
			elif get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if get_piece(x, j).islower():
				break
			if get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if get_piece(x, j).islower():
				break
			if get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'R':
		for i in range(x+1, 8):
			if get_piece(i, y).isupper():
				break
			elif get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if get_piece(i, y).isupper():
				break
			elif get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if get_piece(x, j).isupper():
				break
			if get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if get_piece(x, j).isupper():
				break
			if get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'n':
		if y < 7:
			if x > 1 and not get_piece(x-2, y+1).islower():
				moves.append((x - 2, y + 1))
			if x < 6 and not get_piece(x+2, y+1).islower():
				moves.append((x + 2, y + 1))
			if y < 6:
				if x > 0 and not get_piece(x-1, y+2).islower():
					moves.append((x - 1, y + 2))
				if x < 7 and not get_piece(x+1, y+2).islower():
					moves.append((x + 1, y + 2))

		if y > 0:
			if x > 1 and not get_piece(x-2, y-1).islower():
				moves.append((x - 2, y - 1))
			if x < 6 and not get_piece(x+2, y-1).islower():
				moves.append((x + 2, y - 1))
			if y > 1:
				if x > 0 and not get_piece(x-1, y-2).islower():
					moves.append((x - 1, y - 2))
				if x < 7 and not get_piece(x+1, y-2).islower():
					moves.append((x + 1, y - 2))

		return moves
	elif piece == 'N':
		if y < 7:
			if x > 1 and not get_piece(x-2, y+1).isupper():
				moves.append((x - 2, y + 1))
			if x < 6 and not get_piece(x+2, y+1).isupper():
				moves.append((x + 2, y + 1))
			if y < 6:
				if x > 0 and not get_piece(x-1, y+2).isupper():
					moves.append((x - 1, y + 2))
				if x < 7 and not get_piece(x+1, y+2).isupper():
					moves.append((x + 1, y + 2))

		if y > 0:
			if x > 1 and not get_piece(x-2, y-1).isupper():
				moves.append((x - 2, y - 1))
			if x < 6 and not get_piece(x+2, y-1).isupper():
				moves.append((x + 2, y - 1))
			if y > 1:
				if x > 0 and not get_piece(x-1, y-2).isupper():
					moves.append((x - 1, y - 2))
				if x < 7 and not get_piece(x+1, y-2).isupper():
					moves.append((x + 1, y - 2))

		return moves
	elif piece == 'B':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		return moves
	elif piece == 'b':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		return moves
	elif piece == 'Q':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if get_piece(i, j).isupper():
				break
			elif get_piece(i, j).islower():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))


		for i in range(x+1, 8):
			if get_piece(i, y).isupper():
				break
			elif get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if get_piece(i, y).isupper():
				break
			elif get_piece(i, y).islower():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if get_piece(x, j).isupper():
				break
			if get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if get_piece(x, j).isupper():
				break
			if get_piece(x, j).islower():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'q':
		for i, j in zip(range(x+1, 8), range(y+1, 8)):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(range(x+1, 8), reversed(range(0, y))):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), range(y+1, 8)):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))

		for i, j in zip(reversed(range(0, x)), reversed(range(0, y))):
			if get_piece(i, j).islower():
				break
			elif get_piece(i, j).isupper():
				moves.append((i, j))
				break
			else:
				moves.append((i, j))


		for i in range(x+1, 8):
			if get_piece(i, y).islower():
				break
			elif get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for i in reversed(range(0, x)):
			if get_piece(i, y).islower():
				break
			elif get_piece(i, y).isupper():
				moves.append((i, y))
				break
			else:
				moves.append((i, y))

		for j in range(y+1, 8):
			if get_piece(x, j).islower():
				break
			if get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		for j in reversed(range(0, y)):
			if get_piece(x, j).islower():
				break
			if get_piece(x, j).isupper():
				moves.append((x, j))
				break
			else:
				moves.append((x, j))

		return moves
	elif piece == 'K':
		if 'K' in curr_data['castling'] and get_piece(5, 0) == '' and get_piece(6, 0) == '':
			set_piece(5, 0, 'K')
			set_piece(6, 0, 'K')

			if not is_in_check('w'):
				moves.append((6, 0))

			set_piece(5, 0, '')
			set_piece(6, 0, '')
		if 'Q' in curr_data['castling'] and get_piece(1, 0) == '' and get_piece(2, 0) == '' and get_piece(3, 0) == '':
			set_piece(1, 0, 'K')
			set_piece(2, 0, 'K')
			set_piece(3, 0, 'K')

			if not is_in_check('w'):
				moves.append((2, 0))

			set_piece(1, 0, '')
			set_piece(2, 0, '')
			set_piece(3, 0, '')

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
				if not get_piece(move[0], move[1]).isupper():
					moves.append(move)
			except IndexError:
				pass

		return moves
	elif piece == 'k':
		if 'k' in curr_data['castling'] and get_piece(5, 7) == '' and get_piece(6, 7) == '':
			moves.append((6, 7))
		if 'q' in curr_data['castling'] and get_piece(1, 7) == '' and get_piece(2, 7) == '' and get_piece(3, 7) == '':
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
				if not get_piece(move[0], move[1]).islower():
					moves.append(move)
			except IndexError:
				pass

	return moves


# Side is either 'b' or 'w'
def is_in_check(side):
	side = 'k' if side == 'b' else 'K'
	king = None

	for i in range(0, 8):
		for j in range(0, 8):
			if get_piece(i, j) == side:
				king = (i, j)
				break
			if not king == None:
				break

	for i in range(0, 8):
		for j in range(0, 8):
			if (get_piece(i, j).isupper() and side == 'k') or (get_piece(i, j).islower() and side == 'K'):
				if king in get_moves(i, j):
					return True

	return False
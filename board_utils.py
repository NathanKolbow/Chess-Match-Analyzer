import PySimpleGUI as sg

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
## }
curr_data = None


# list of legal moves for the currently selected piece
legal_moves = ()
# current piece being moved
moving_piece = None
moving_from = None


def Init(graph):
	graph.Widget.bind("<Motion>", board_motion_event)
	graph.Widget.bind("<Button-1>", board_mouse_one)
	graph.Widget.bind("<B1-Motion>", board_mouse_one_motion)
	graph.Widget.bind("<ButtonRelease-1>", board_mouse_one_release)
	graph.Widget.bind("<Button-3>", board_mouse_three)

	global board_graph
	board_graph = graph

def set_pos_from_fen(FEN):
	global curr_data
	curr_data = data_from_fen(FEN)
	draw_board()


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
	return (20 + row * 100, 80 + column * 100)

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
	data['move counts'] = (int(str[4]), int(str[5]))

	print('board: ')
	print(data['board'])
	return data


def set_piece(x, y, piece):
	global curr_data
	curr_data['board'][y][x] = piece

def get_piece(x, y):
	global curr_data
	return curr_data['board'][y][x]


def draw_legal_moves():
	global board_graph
	global legal_moves

	for move in legal_moves:
		board_graph.DrawImage(filename="img/pieces_default/move_dot.png", location=(move[0]*100, (move[1]+1)*100))

def draw_board():
	global board_graph
	global curr_data

	board_graph.erase()
	# board_graph is necessarily the 800x800 board used in run()
	board_graph.DrawImage(filename="img/pieces_default/board.png", location=(0, 800))

	board = curr_data['board']
	for i in range(0, 8): # ranks, starting from the 8th rank
		for j in range(0, 8): # files, starting from the a file
			if not board[i][j] == '':
				if perspective == 'w':
					locx, locy = board_image_coords(j, i)
				else:
					locx, locy = board_image_coords(7-j, 7-i)

				if board[i][j] == 'p':
					board_graph.DrawImage(filename="img/pieces_default/pawn_black.png", location=(locx, locy))
				elif board[i][j] == 'r':
					board_graph.DrawImage(filename="img/pieces_default/rook_black.png", location=(locx, locy))
				elif board[i][j] == 'n':
					board_graph.DrawImage(filename="img/pieces_default/knight_black.png", location=(locx, locy))
				elif board[i][j] == 'b':
					board_graph.DrawImage(filename="img/pieces_default/bishop_black.png", location=(locx, locy))
				elif board[i][j] == 'k':
					board_graph.DrawImage(filename="img/pieces_default/king_black.png", location=(locx, locy))
				elif board[i][j] == 'q':
					board_graph.DrawImage(filename="img/pieces_default/queen_black.png", location=(locx, locy))
				elif board[i][j] == 'P':
					board_graph.DrawImage(filename="img/pieces_default/pawn_white.png", location=(locx, locy))
				elif board[i][j] == 'R':
					board_graph.DrawImage(filename="img/pieces_default/rook_white.png", location=(locx, locy))
				elif board[i][j] == 'N':
					board_graph.DrawImage(filename="img/pieces_default/knight_white.png", location=(locx, locy))
				elif board[i][j] == 'B':
					board_graph.DrawImage(filename="img/pieces_default/bishop_white.png", location=(locx, locy))
				elif board[i][j] == 'K':
					board_graph.DrawImage(filename="img/pieces_default/king_white.png", location=(locx, locy))
				elif board[i][j] == 'Q':
					board_graph.DrawImage(filename="img/pieces_default/queen_white.png", location=(locx, locy))

def flip_board():
	global perspective
	if perspective == 'w':
		perspective = 'b'
	else:
		perspective = 'w'

	draw_board()





last_X = 0
last_Y = 0
def board_motion_event(event):
	global last_X
	global last_Y

	last_X = event.x
	last_Y = event.y

def board_mouse_one(event):
	x, y = board_image_coords_to_xy(last_X, last_Y)
	
	global legal_moves
	global moving_piece
	global curr_data
	global moving_from

	if legal_moves != None and (x, y) in legal_moves:
		# Update the value for en passant
		curr_data['en passant'] = "-"
		if moving_piece == 'p' or moving_piece == 'P':
			if abs(y - moving_from[1]) == 2:
				curr_data['en passant'] = (moving_from[0], moving_from[1]+1 if moving_piece == 'P' else moving_from[1]-1)
				print("En passant is now: ", curr_data['en passant'])

		# Move the actual piece (if anything is taken, it's overwritten in this process)
		set_piece(x, y, moving_piece)
		set_piece(moving_from[0], moving_from[1], '')
		# Remove castling rights if necessary
		if moving_piece == 'R':
			if 'Q' in curr_data['castling'] and moving_from[0] == 0 and moving_from[1] == 0:
				curr_data['castling'] = curr_data['castling'].replace('Q', '')
			elif 'K' in curr_data['castling'] and moving_from[0] == 7 and moving_from[1] == 0:
				curr_data['castling'] = curr_data['castling'].replace('K', '')
		if moving_piece == 'r':
			if 'q' in curr_data['castling'] and moving_from[0] == 0 and moving_from[1] == 7:
				curr_data['castling'] = curr_data['castling'].replace('q', '')
			elif 'k' in curr_data['castling'] and moving_from[0] == 7 and moving_from[1] == 7:
				curr_data['castling'] = curr_data['castling'].replace('k', '')
		# Special case for castling
		if moving_piece == 'k':
			print("king move")
			curr_data['castling'] = curr_data['castling'].replace('k', '').replace('q', '')
			if abs(moving_from[0] - x) == 2:
				print("castle")
				if x == 2:
					set_piece(0, 7, '')
					set_piece(3, 7, 'r')
				elif x == 6:
					set_piece(5, 7, 'r')
					set_piece(7, 7, '')

		# Update whose turn it is
		curr_data['turn'] = 'b' if curr_data['turn'] == 'w' else 'w'

		legal_moves = ()
		moving_piece = None
		moving_from = None
	elif moving_from == (x, y):
		legal_moves = ()
		moving_piece = None
		moving_from = None
	else:
		if not ((curr_data['turn'] == 'b' and get_piece(x, y).isupper()) or (curr_data['turn'] == 'w' and get_piece(x, y).islower())):
			legal_moves = get_legal_moves(x, y)
			moving_piece = get_piece(x, y)
			moving_from = (x, y)

	draw_board()
	draw_legal_moves()




def board_mouse_three(event):
	# right-click
	flip_board()

def board_mouse_one_motion(event):
	global last_X
	global last_Y

	last_X = event.x
	last_Y = event.y

def board_mouse_one_release(event):
	pass


def get_legal_moves(x, y):
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
			moves.append((6, 0))
		if 'Q' in curr_data['castling'] and get_piece(1, 0) == '' and get_piece(2, 0) == '' and get_piece(3, 0) == '':
			moves.append((2, 0))

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
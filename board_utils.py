import PySimpleGUI as sg

perspective = "white"
board_graph = None
# curr_data contains ALL of the information necessary to the current position on the board
# i.e. curr_data is roughly equivalent to an FEN, NOT a PGN
curr_data = None

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
	draw_from_data(curr_data)


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
	if perspective == 'white':
		return (x // 100, y // 100)
	else:
		return (7 - x // 100, 7 - y // 100)

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
	data['en passant'] = str[3]
	data['move counts'] = (int(str[4]), int(str[5]))

	print('board: ')
	print(data['board'])
	return data


def get_piece(x, y):
	global curr_data
	return curr_data['board'][y][x]


def draw_from_data(data):
	global board_graph

	# board_graph is necessarily the 800x800 board used in run()
	board_graph.DrawImage(filename="img/pieces_default/board.png", location=(0, 800))

	board = data['board']
	for i in range(0, 8): # ranks, starting from the 8th rank
		for j in range(0, 8): # files, starting from the a file
			if not board[i][j] == '':
				if perspective == 'white':
					loc = board_image_coords(j, i)
				else:
					loc = board_image_coords(7-j, 7-i)

				if board[i][j] == 'p':
					board_graph.DrawImage(filename="img/pieces_default/pawn_black.png", location=loc)
				elif board[i][j] == 'r':
					board_graph.DrawImage(filename="img/pieces_default/rook_black.png", location=loc)
				elif board[i][j] == 'n':
					board_graph.DrawImage(filename="img/pieces_default/knight_black.png", location=loc)
				elif board[i][j] == 'b':
					board_graph.DrawImage(filename="img/pieces_default/bishop_black.png", location=loc)
				elif board[i][j] == 'k':
					board_graph.DrawImage(filename="img/pieces_default/king_black.png", location=loc)
				elif board[i][j] == 'q':
					board_graph.DrawImage(filename="img/pieces_default/queen_black.png", location=loc)
				elif board[i][j] == 'P':
					board_graph.DrawImage(filename="img/pieces_default/pawn_white.png", location=loc)
				elif board[i][j] == 'R':
					board_graph.DrawImage(filename="img/pieces_default/rook_white.png", location=loc)
				elif board[i][j] == 'N':
					board_graph.DrawImage(filename="img/pieces_default/knight_white.png", location=loc)
				elif board[i][j] == 'B':
					board_graph.DrawImage(filename="img/pieces_default/bishop_white.png", location=loc)
				elif board[i][j] == 'K':
					board_graph.DrawImage(filename="img/pieces_default/king_white.png", location=loc)
				elif board[i][j] == 'Q':
					board_graph.DrawImage(filename="img/pieces_default/queen_white.png", location=loc)

def flip_board():
	global perspective
	if perspective == "white":
		perspective = "black"
	else:
		perspective = "white"

	draw_from_data(curr_data)





last_X = 0
last_Y = 0
def board_motion_event(event):
	global last_X
	global last_Y

	last_X = event.x
	last_Y = event.y

def board_mouse_one(event):
	pos = board_image_coords_to_xy(last_X, last_Y)
	moves = get_legal_moves(pos[0], pos[1])
	
	print("Moves:")
	for move in moves:
		print("   * %s" % xy_to_rank_file(move[0], move[1]))

	# print("Mouse is in %s" % coords_to_rank_file(pos[0], pos[1]+1))

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
	# 0-indexed, does NOT take input as rank/file
	global curr_data
	board = curr_data['board']

	piece = get_piece(x, y)
	print("%s on (%s, %s)" % (piece, x, y))
	moves = []

	if piece == '':
		return moves
	elif piece == 'p':
		if last_X == 0:
			# weird edge case
			return None
		if get_piece(x, y-1) == '':
			moves.append((x, y-1))
			if y == 6 and get_piece(x, y-2) == '':
				moves.append((x, y-2))
		if x > 0 and get_piece(x-1, y-1).isupper():
			moves.append((x-1, y-1))
		if x < 7 and get_piece(x+1, y-1).isupper():
			moves.append((x+1, y-1))
		if curr_data['en passant'] != '-':
			en_square = rank_file_to_xy(curr_data['en passant'])


			if abs(en_square[0] - x) == 1 and y - en_square[1] == 1:
				moves.append(en_square)
		return moves
	elif piece == 'r':
		pass
	elif piece == 'n':
		pass
	elif piece == 'b':
		pass
	elif piece == 'q':
		pass
	elif piece == 'k':
		pass

	return moves

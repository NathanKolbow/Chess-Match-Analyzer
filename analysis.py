from math import exp
import threading
import subprocess

analysis_graph = None
analysis_rect = None
rect_Y = 800

analysis_thread = None
DEFAULT_DEPTH = 18

proc = None
uci_engine_loc = "engines/stockfish11_win_64.exe"


def Init(bar):
	# Initiate bar
	global analysis_graph
	global analysis_rect

	analysis_graph = bar
	analysis_graph.DrawRectangle((0, 0), (35, 800), fill_color='white', line_color='black')
	analysis_rect = analysis_graph.DrawRectangle((0, 800), (35, 0), fill_color='gray')
	set_bar_height(400)
	analysis_graph.DrawRectangle((0, 401), (35, 400), fill_color='black', line_color='black')

	# Initiate engine
	global proc

	proc = subprocess.Popen([uci_engine_loc], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	proc.stdout.read1()

	proc.stdin.write(b'uci\n')
	proc.stdin.flush()

	proc.stdout.read1()




def set_bar_height(y):
	global analysis_graph
	global analysis_rect
	global rect_Y

	analysis_graph.Widget.coords(analysis_rect, (0, 0, 35, y))
	rect_Y = y


# Takes the number analysis (e.g. -100 to 100) and moves the bar accordingly using a sigmoid transformation
def move_bar(analysis):
	percent = 1 / (1 + exp(-analysis/2))

	set_bar_height(5 + 790 * percent)
	#analysis_graph.erase()
	#analysis_graph.DrawRectangle((0, 0), (35, 800), fill_color='white', line_color='black')
	#analysis_rect = analysis_graph.DrawRectangle((0, 800), (35, 5 + 790 * percent), fill_color='gray')
	#analysis_graph.DrawRectangle((0, 401), (35, 400), fill_color='black', line_color='black')

def init_background_analysis(depth=DEFAULT_DEPTH):
	global analysis_thread

	analysis_thread = threading.Thread(target=_progressive_analysis, args=(depth,))
	analysis_thread.start()

def close():
	global alive
	alive = False

def update_fen(FEN):
	global working_fen
	global next_item
	global turn
	global wait_condition

	working_fen = FEN
	turn = working_fen.split(' ')[1]
	next_item = True

	wait_condition.acquire()
	wait_condition.notify()
	wait_condition.release()


# Automatically moves the bar currently
# turn is 'w' if the NEXT move is white's, 'b' for black
alive = True
next_item = False
working_fen = None
turn = None

wait_condition = threading.Condition()
def _progressive_analysis(depth):
	global working_fen
	global alive
	global next_item
	global wait_condition

	print('Entering progressive analysis')
	while working_fen == None:
		wait_condition.acquire()
		wait_condition.wait()
		print('no FEN received yet')

	while alive:
		next_item = False
		print('Entering main loop')

		send = bytearray(b'position fen ')
		send.extend(working_fen.encode())
		send.extend('\n'.encode())

		proc.stdin.write(send)
		proc.stdin.flush()

		send = bytearray(b'go depth ')
		send.extend(str(depth).encode())
		send.extend('\n'.encode())

		proc.stdin.write(send)
		proc.stdin.flush()

		searching = True
		while not next_item and searching:
			ret = str(proc.stdout.read1()).split('\\n')
			for item in ret:
				if _parse_and_move(item, turn) != None:
					searching = False
		

		proc.stdin.write(b'stop\n')
		proc.stdin.flush()
		proc.stdin.write(b'isready\n')
		proc.stdin.flush()

		found_best = True
		found_readyok = False
		if searching == True:
			found_best = False

		while not found_best or not found_readyok:
			ret = proc.stdout.read1()
			if b'readyok' in ret:
				found_readyok = True
			if b'bestmove' in ret:
				found_best = True

		while alive and next_item == False:
			print('Waiting...')
			wait_condition.acquire()
			wait_condition.wait()
		print('Done waiting.')

		# After this we can wait for next_item with a condition variable


	######################################################
	##													##
	##                      TODO						##
	##													##
	##	1. get the background analyses working so that  ##
	##	   it's just constantly going and updating as	##
	##     moves are made								##
	##     a) Figure out how to kill a thread midway    ##
	##        through (probably raise_exception())      ##
	##        so that you can cancel prev operations,   ##
	##        unless SF has a built-in way to stop ops  ##
	##  2. implement shit with condition variables so   ##
	##     that everything isn't wrecking performance   ##
	##     sitting in while loops                       ##
	##													##
	######################################################



# Parses analysis and moves the analysis bar
def _parse_and_move(str, turn):
	if ' cp ' in str:
		search = 0

		while str[search:search+4] != ' cp ':
			search = search + 1

		space = search+4
		while str[space] != ' ':
			space = space + 1

		val = int(str[search+4:space])
		#print("Evaluation (%s): %s" % (turn, -val/100 if turn == 'w' else val/100))
		move_bar(-val/100 if turn == 'w' else val/100)

	if 'bestmove' in str:
		print(str)
		return str

	return None
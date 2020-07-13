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

working_fen = None


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
	proc.stdout.peek()
	proc.stdout.read1()

	proc.stdin.write(b'uci\n')
	proc.stdin.flush()

	proc.stdout.peek()
	proc.stdout.read1()




def set_bar_height(y):
	global analysis_graph
	global analysis_rect
	global rect_Y

	print("Setting height to: %s" % (y))

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

def init_background_analysis(curr_data, depth=DEFAULT_DEPTH):
	global analysis_thread

	analysis_thread = threading.Thread(target=progressive_analysis, args=(curr_data, depth,))
	analysis_thread.start()


# Automatically moves the bar currently
# turn is 'w' if the NEXT move is white's, 'b' for black
def progressive_analysis(curr_data, depth):
	global working_fen

	while curr_data == None:
		# Waiting for things to start up
		pass

	while True:
		working_fen = curr_data['fen']

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

		while True:
			ret = str(proc.stdout.read1()).split('\n')
			for item in ret:
				_parse_and_move(item, curr_data['turn'])

			if working_fen != curr_data['fen']:
				break


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
		print("Evaluation (%s): %s" % (turn, val))
		move_bar(-val/100 if turn == 'w' else val/100)

	if 'bestmove' in str:
		print(str)
		return str
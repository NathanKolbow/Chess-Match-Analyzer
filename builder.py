import PySimpleGUI as sg
from globals import *


def PostFinalization(window):
    for i in range(BEST_MOVE, BLUNDER + 1):
        ele = window.FindElement('ratings-column-%s' % (i), silent_on_error=True)
        if ele != None:
            ele.Widget.config(background='white', borderwidth=2)


def BoardElements():
	board = [
		[
			sg.Text("Hickory Neckboy", font=DEFAULT_FONT_BOLD, background_color=BG_COLOR, key='black-player'),
			sg.Text("(2800)", font=DEFAULT_FONT, background_color=BG_COLOR, key='black-rating')
		],
		[
			sg.Graph(canvas_size=(CANVAS_SIZE, CANVAS_SIZE),
					graph_bottom_left=(0,0),
					graph_top_right=(CANVAS_SIZE, CANVAS_SIZE),
					key="board-graph", 
					background_color=BG_COLOR
			)
		],
		[
			sg.Text("Nuhthan Kelbith", font=DEFAULT_FONT_BOLD, background_color=BG_COLOR, key='white-player'),
			sg.Text("(1337)", font=DEFAULT_FONT, background_color=BG_COLOR, key='white-rating')
		]
	]

	return board


def AnalysisMenuElements(ratings):
    columns = []
    for j in range(BEST_MOVE, BLUNDER + 1):
        buttons = []
        for i in range(0, len(ratings)):
            if ratings[i] < j:
                continue
            buttons.append([sg.Button('%s.\t%s' % (i+1, RatingToStr(ratings[i])), key='%s.RETRY-BUTTON.%s' % (i, j), 
                                        button_color=('white', BG_COLOR), border_width=0, font=DEFAULT_FONT)])

        columns.append(sg.Column(buttons, background_color=BG_COLOR, scrollable=True, justification='center', element_justification='left', 
                            size=(200, 200), vertical_scroll_only=True, key='ratings-column-%s' % (j), visible=False))

    analysis_menu = [
        [
            sg.Graph(
                canvas_size=(220, 100),
                graph_bottom_left=(0, 0),
                graph_top_right=(100, 100),
                key='menu-graph',
                background_color=BG_COLOR
            )
        ],
        columns,
        [
            sg.Button('First flip')
        ],
        [
            sg.Button('Second flip')
        ],
        [
            sg.Button('Third flip')
        ],
        [
            sg.Column([
                        [
                            sg.Text('Threshold: ', background_color=BG_COLOR),
                            sg.Combo(('Best move', 'Brilliant', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder'), default_value='Inaccuracy',
                                        key='threshold-dropdown', enable_events=True)
                        ],
                        [
                            sg.Button('Retry Move', disabled=True, key='RETRY-MOVE')
                        ],
                        [
                            sg.Button('Left'),
                            sg.Text('Back', background_color=BG_COLOR),
                            sg.Text('Forth', background_color=BG_COLOR),
                            sg.Button('Right')
                        ]
                    ], background_color=BG_COLOR, element_justification='center', justification='center')
        ]
    ]

    return analysis_menu, columns


def AnalysisBarElements():
	analysis_bar = [
		[
			sg.Graph(canvas_size=(50, CANVAS_SIZE),
				graph_bottom_left=(0,0),
				graph_top_right=(50,CANVAS_SIZE),
				key="analysis-graph",
				background_color=BG_COLOR
			)
		]
	]

	return analysis_bar
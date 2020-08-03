import PySimpleGUI as sg
from globals import *
from PIL import Image
import base64
from io import BytesIO
import mathemagics
import analysis
from analysis import _categorize_move


def _set_compression_images(window):
    switch_names = [ 'BUTTON-PLAYTHRU', 'BUTTON-RATE-EACH-MOVE', 'BUTTON-ANALYSIS-BAR' ]
    for name in switch_names:
        info = window[name].__dict__
        if '.disabled' in info['metadata']:
            continue
        elif window[name].Widget.config()['state'][4] == 'active' and not '.mid' in info['metadata']:
            window[name].Update(image_data=_button_mid_data(False))
            info['metadata'] += '.mid'
        #elif window[name].Widget.config()['state'][4] == 'normal' and '.mid' in info['metadata']:
        #    new = info['metadata'].split('.')[0]
        #    info['metadata'] = new
        #    window[name].Update(image_data=_button_on_data(True) if new == 'on' else _button_off_data(True))


def PostFinalization(window, overview_hover_func=None, overview_hover_text=None, overview_click=None, overview_release=None):
    callbacks = []

    for i in range(BEST_MOVE, BLUNDER + 1):
        ele = window.FindElement('ratings-column-%s' % (i), silent_on_error=True)
        if ele != None:
            ele.Widget.config(background='white', borderwidth=2)

    switch_names = [ 'BUTTON-PLAYTHRU', 'BUTTON-RATE-EACH-MOVE', 'BUTTON-ANALYSIS-BAR' ]
    if window.FindElement(switch_names[0], silent_on_error=True) != None:
        callbacks.append(_set_compression_images)

        for name in switch_names:
            window[name].Widget.config(highlightthickness=0, background=BG_COLOR, borderwidth=0, activebackground=BG_COLOR, 
                                        disabledforeground=None)

    overview_graph = window.FindElement('overview-graph', silent_on_error=True)
    if overview_graph != None:
        scores = overview_graph.__dict__['metadata']

        max_score = 2000
        OVERVIEW_SIZE[1] = OVERVIEW_PER_SCORE_MULTIPLIER * len(scores)

        y_step = OVERVIEW_PER_SCORE_MULTIPLIER
        for i in range(1, len(scores)):
            if type(scores[i]) == str:
                if '-' in scores[i]:
                    if i % 2 == 0:
                        scores[i] = -20000
                    else:
                        scores[i] = 20000
                else:
                    if scores[i] == 'MATE+0':
                        if i % 2 == 0:
                            scores[i] = -20000
                        else:
                            scores[i] = 20000
                    elif i % 2 == 0:
                        scores[i] = 20000
                    else:
                        scores[i] = -20000
            else:
                if i % 2 == 1:
                    scores[i] = -scores[i]
            
            scores[i] = min(max_score, max(-max_score, scores[i]))

        # Draw middle line
        overview_graph.DrawLine((0, 0), (0, OVERVIEW_SIZE[1]), color=OVERVIEW_CENTER_COLOR, width=OVERVIEW_CENTER_WIDTH)

        # Draw dashed lines
        vals = [2, 5, 12]
        xs = []
        for val in vals:
            xs.append(mathemagics.Transform(val) * OVERVIEW_MAX_WIDTH)

        for i in range(0, len(xs)):
            overview_graph.DrawText(str(vals[i]), (xs[i], 10), font=DEFAULT_FONT_SMALL)
            overview_graph.DrawText(str(-vals[i]), (-xs[i], 10), font=DEFAULT_FONT_SMALL)

        step = 10
        length = 5
        i = step+length
        while i < OVERVIEW_SIZE[1]:
            i += step
            for x in xs:
                overview_graph.DrawLine((x, i), (x, i+length), color=OVERVIEW_CENTER_COLOR, width=OVERVIEW_CENTER_WIDTH)
                overview_graph.DrawLine((-x, i), (-x, i+length), color=OVERVIEW_CENTER_COLOR, width=OVERVIEW_CENTER_WIDTH)

            i += length

        # Draw lines
        for i in range(1, len(scores)):
            if y_step > 2:
                point_from = (mathemagics.Transform(scores[i-1]/100) * OVERVIEW_MAX_WIDTH, (i-1)*y_step)
                point_to = (mathemagics.Transform(scores[i]/100) * OVERVIEW_MAX_WIDTH, (i)*y_step)
                points = mathemagics.ExpandCurve(point_from[1], point_to[1], point_from[0], point_to[0])
                
                if (i-1) % 2 == 0:
                    color = RatingToColor(_categorize_move(scores[i-1], scores[i]))
                else:
                    color = RatingToColor(_categorize_move(-scores[i-1], -scores[i]))
                points[0] = (points[0][1], points[0][0])
                for i in range(1, len(points)):
                    points[i] = (points[i][1], points[i][0])
                    overview_graph.DrawLine(points[i-1], points[i], color=color, width=OVERVIEW_LINE_WIDTH)
            else:
                overview_graph.DrawLine((mathemagics.Transform(scores[i-1]/100) * OVERVIEW_MAX_WIDTH, (i-1)*y_step), (mathemagics.Transform(scores[i]/100) * OVERVIEW_MAX_WIDTH, (i)*y_step), 
                                        color=OVERVIEW_COLOR, width=OVERVIEW_LINE_WIDTH)

        # Draw points
        overview_graph.DrawPoint((20/(max_score/OVERVIEW_MAX_WIDTH), 0), color=OVERVIEW_POINT_COLOR, size=OVERVIEW_POINT_SIZE)
                                # 20 comes from LiChess's starting position analysis (https://lichess.org/analysis)
        for i in range(1, len(scores)):
            overview_graph.DrawPoint((mathemagics.Transform(scores[i]/100) * OVERVIEW_MAX_WIDTH, (i)*y_step), color=OVERVIEW_POINT_COLOR, size=OVERVIEW_POINT_SIZE)

        # Bind the overview graph mouse functions
        if overview_hover_func != None:
            overview_graph.Widget.bind("<Motion>", overview_hover_func)
        if overview_click != None:
            overview_graph.Widget.bind("<Button-1>", overview_click)
        if overview_release != None:
            overview_graph.Widget.bind("<ButtonRelease-1>", overview_release)

        if overview_hover_text != None:
            overview_hover_text.append(overview_graph)
            overview_hover_text.append(overview_graph.DrawText('', (-1, -1), font=DEFAULT_FONT_SMALL))

        window.read(timeout=0)
    
    # Init analysis if we have a bar
    analysis_bar = window.FindElement('analysis-graph', silent_on_error=True)
    if analysis_bar != None:
        analysis.Init(window.TKroot)

    # Correct analysis text starting value
    text = window.FindElement('analysis-text', silent_on_error=True)
    if text != None:
        text.Update(value="depth %s/%s" % (0, DEPTH))

    return callbacks


def walrus(variable, value):
    variable = value
    return value


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


def MatchOverviewGraph(scores):
    OVERVIEW_SIZE[1] = (OVERVIEW_PER_SCORE_MULTIPLIER) * len(scores)

    graph = sg.Graph(
                        canvas_size=OVERVIEW_SIZE,
                        graph_bottom_left=(-OVERVIEW_SIZE[0]/2, OVERVIEW_SIZE[1]),
                        graph_top_right=(OVERVIEW_SIZE[0]/2, 0),
                        key='overview-graph',
                        background_color='white',
                        #pad=((5, 5), (5, 5)),
                        metadata=scores
                    )

    return graph


def AnalysisMenuElements(ratings):
    columns = []
    for j in range(BEST_MOVE, BLUNDER + 1):
        buttons = []
        for i in range(0, len(ratings)):
            if ratings[i] < j:
                continue
            buttons.append([sg.Button('%s.\t%s' % (i+1, RatingToStr(ratings[i])), key='%s.RETRY-BUTTON.%s' % (i, j), 
                                        button_color=('white', BG_COLOR), border_width=0, font=DEFAULT_FONT, metadata=ratings[i])])

        columns.append(sg.Column(buttons, background_color=BG_COLOR, scrollable=True, justification='center', element_justification='left', 
                            size=(200, 200), vertical_scroll_only=True, key='ratings-column-%s' % (j), visible=False))

    analysis_menu = [
        [
            sg.Graph(
                canvas_size=(219, 100),
                graph_bottom_left=(0, 0),
                graph_top_right=(100, 100),
                key='menu-graph',
                background_color=BG_COLOR,
                pad=((5, 0), (34, 0))
            )
        ],
        columns,
        [
            sg.Button('', image_data=_button_off_data(True), key='BUTTON-PLAYTHRU', button_color=(None, None), metadata='off'),
            sg.Text('Play-through Mode', font=DEFAULT_FONT, background_color=BG_COLOR)
        ],
        [
            sg.Button('', image_data=_button_on_data(False), key='BUTTON-RATE-EACH-MOVE', button_color=(None, None), metadata='on.disabled'),
            sg.Text('Rate Each Move', font=DEFAULT_FONT, background_color=BG_COLOR)
        ],
        [
            sg.Button('', image_data=_button_on_data(True), key='BUTTON-ANALYSIS-BAR', button_color=(None, None), metadata='on'),
            sg.Text('Analysis Bar', font=DEFAULT_FONT, background_color=BG_COLOR)
        ],
        [
            sg.Column([
                        [
                            sg.Text('Threshold: ', background_color=BG_COLOR),
                            sg.Combo(('Best move', 'Brilliant', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder'), default_value='Inaccuracy',
                                        key='threshold-dropdown', enable_events=True, font=DEFAULT_FONT)
                        ],
                        [
                            sg.Button('Retry Move', disabled=True, key='RETRY-MOVE')
                        ],
                        [
                            sg.Button('Show Solution', key='SHOW-SOLUTION')
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
    analysis_bar = sg.Graph(canvas_size=(50, CANVAS_SIZE), graph_bottom_left=(0,0), graph_top_right=(50,CANVAS_SIZE), key="analysis-graph", background_color=BG_COLOR)
    text = sg.Text('depth: 100/100', background_color=BG_COLOR, font=DEFAULT_FONT_SMALL, text_color='black', key='analysis-text')
    return analysis_bar, text


def _button_mid_data(enabled):
    button_img = Image.open('img/interface/button-mid' + ('' if enabled else '-disabled') + '.png')
    button_img = button_img.resize(SWITCH_SIZE)

    buffered = BytesIO()
    button_img.save(buffered, format="PNG")
    
    return base64.b64encode(buffered.getvalue())


def _button_on_data(enabled):
    button_img = Image.open('img/interface/button-on' + ('' if enabled else '-disabled') + '.png')
    button_img = button_img.resize(SWITCH_SIZE)

    buffered = BytesIO()
    button_img.save(buffered, format="PNG")
    
    return base64.b64encode(buffered.getvalue())


def _button_off_data(enabled):
    button_img = Image.open('img/interface/button-off' + ('' if enabled else '-disabled') + '.png')
    button_img = button_img.resize(SWITCH_SIZE)

    buffered = BytesIO()
    button_img.save(buffered, format="PNG")
    
    return base64.b64encode(buffered.getvalue())
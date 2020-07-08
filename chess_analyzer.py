import PySimpleGUI as sg
import board_utils as butil

button_right_base64 = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TtSIVh3YQcchQnSyIijpKFYtgobQVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi5Oik6CIl/i8ptIjx4Lgf7+497t4BQqPCVLNrHFA1y0jFY2I2tyoGXhFAD0KYxYzETD2RXszAc3zdw8fXuyjP8j735+hX8iYDfCLxHNMNi3iDeHrT0jnvE4dZSVKIz4nHDLog8SPXZZffOBcdFnhm2Mik5onDxGKxg+UOZiVDJZ4ijiiqRvlC1mWF8xZntVJjrXvyFwbz2kqa6zSHEccSEkhChIwayqjAQpRWjRQTKdqPefiHHH+SXDK5ymDkWEAVKiTHD/4Hv7s1C5MTblIwBnS/2PbHCBDYBZp12/4+tu3mCeB/Bq60tr/aAGY/Sa+3tcgRMLANXFy3NXkPuNwBBp90yZAcyU9TKBSA9zP6phwQugX61tzeWvs4fQAy1NXyDXBwCIwWKXvd4929nb39e6bV3w/vG3LZbIXjHQAAAAZiS0dEACcAJwAnEqqtZQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+QHBhQLA7eY8yUAAAOYSURBVFjDvZfPbxtFFMc/s463G6kHfkkcqbI78dqNQ/sPcE1bbpVorlwItAoRAVUcMBcq9UJVgiKoUorEERDi2tALKj1wQzQuYZXFXOBWaIpU1anXu4+D1+5utHZ2XcP3ODNvvvPevPm+N8pxZgBBKQOAcrlMp9P5n8ZgCgRQGIaiXC4TBAE9pMd8v2UBC8AJ4EXgOGABiMgDpdQd4GdgE/jOdfXeqP16EJTWdmoiDCMASiWDcrlMs7l9GGgAS8DT5MMu8AlwWWt7N7lfkgPA6Icki3xr65czwB/AuwXIidc2gKbvtxazyEslA9M0UbWaSxh2UxOe508Dl4E3mAw2gFWt7XbSwUePOhidTieL/JsJkgO8Dnzr+63pZDTiK5BU2GPPTzF5nADWklchEmEoZQzIb9++80pRz0XkZhiGXs7lS83m9pnHSahAa5u5uSoiclhE/pIC6Ha7J2Nbut3uuZxmuyJiVSoOtZqLkbiPBvBsAed/PXasfj0IArS2cd3ZT4E3c9g9BTQGvI4zg4hYInJPiuGuiEw7zgyOM0Ol4vQjeSGH7T0RsbS2B0m4UPCdAzwHrPl+KyUyWtvvh2F4MYdOnBokYZyh42AJuOp5fkpkjh513xORSwe/CtVTwljbx8VrwBXP81PPuVqdPR/L8bDXM2+aJlPx2z8+ZN0qsOG6uj1MrkeNaW0v+37LAM7u31gpdSQIAqbismhlkG9pba/lIRo1BrwDLALP7Nv/+ZQSZsB6UvI4uu0M8vga4iQUkQcZ87Oe57/dbG5b45LH+rI+xMF/BkooIj/Kk+GKiKT0oFJxEJH1ETY/DZQw7mTGxWfAWa3tlOee538MLI+wuxUEQa8cA9fHJL9Wr88tZZA3gJUDbL9PJuGNuI0qgr+jKFrZ22vvJ18GLuRo2W4MktB19R7wecED3K1UdHsf+Vsjki6Jda3thwMljPPgIvBngQO4nrdzMkF+HvgoT+REZC2zJ9zZ+W1RKfVlwUj8EJfY+ZzrF11Xf53ZE1ars18B1woe4KUC5Bt98lE94Ur8uZg0NoHVkT1hXM/bwGng6gTJN4DT9Xqtnf6YqN7P6NAhc9iv6FXgUsFWLZVwwLlk2JMcpdLU454wS8e1tr8AXgA+AO4XIL4PfCgiehh5f0z1fsccWFiazW0LeBlYEJF5pdSRfkntFRZ+B24BN4FNre2HBxWqKJL+AXo/ZNM0B9kpEv3nY1EU8S8aSl2yC7CMbQAAAABJRU5ErkJggg=='
button_left_base64 = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TtSIVh3YQcchQnSyIijpKFYtgobQVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi5Oik6CIl/i8ptIjx4Lgf7+497t4BQqPCVLNrHFA1y0jFY2I2tyoGXhFAD0KYxYzETD2RXszAc3zdw8fXuyjP8j735+hX8iYDfCLxHNMNi3iDeHrT0jnvE4dZSVKIz4nHDLog8SPXZZffOBcdFnhm2Mik5onDxGKxg+UOZiVDJZ4ijiiqRvlC1mWF8xZntVJjrXvyFwbz2kqa6zSHEccSEkhChIwayqjAQpRWjRQTKdqPefiHHH+SXDK5ymDkWEAVKiTHD/4Hv7s1C5MTblIwBnS/2PbHCBDYBZp12/4+tu3mCeB/Bq60tr/aAGY/Sa+3tcgRMLANXFy3NXkPuNwBBp90yZAcyU9TKBSA9zP6phwQugX61tzeWvs4fQAy1NXyDXBwCIwWKXvd4929nb39e6bV3w/vG3LZbIXjHQAAAAZiS0dEACcAJwAnEqqtZQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+QHBhQMGpyyzSIAAAPQSURBVFjDvZdPbxtlEMZ/7zrr2qgSBJA4IrL72mvHW8IHAI60HCsR+AKEEtIIChUHwoWiXkAkKKKFUqReUyFuqC0XhPgAkKSUV1lSIcEBVJoUqcKu1/Zw2LW7jTb2bhqY42h25pl5n/mzynUnACgWi4RhCIBID1D/i24MBFB0ux0OHIgMul0FcI/OmOsl4DngMDAlIg2l1EEiaQE/AKvAZeCK5+nWMH+RTlD9CgAUCha2bccGPQCCYHMcOAG8BoyTTbaBc8D7vl+/nfSXjNHrCVaxWKRQsGKEPcIwxLZtCgWLINh8EVgHFnIEJ7Z9G/htbe2n6b6/nTEAlNZOoiyDrMvAIvAK+yOfAic8TzeTlSgUxrCAnVmXga/2MTjAMeBLY4JyshLtdhtLpLezLEsx0fZbngc+Sj4HCBaoAaL19WvTwEwWb91u14jId3krsbp69YU+CKUsqNc9qlUXESmJyLZkkE6nMysiNBo1Op3OEcknf4nIwUajhtYOVqL0C8BDGbI47nmVM1o7hGHI1JR/Cfg5RxUeARYGcbV2+tlvZUB/qtGoUa26uO4ErjuBiJRF5EbOKmyJSMl1JyISxgQZH/Hmp7V23t3RMX3SPpqTC+PRVL1LwqGsF5EPJye9d5KDxJiAeNrN7LErDitlRZNQRA4NMfykVqucTLZPHPws8PJ9tOWTg0m4sfHLH8BjKUZntXZmd9sTo3TGBOV4oC2m+G5NTtbK/YmQFnwLeHO3PZFF53m6qbWzBKyl+C+1223GYhKmycNAM2rRKMMoy37bZtcBpV3YxVhMwr+BB1MslsMwPL5XEMZcKwGzQCWF2LeVshgrFosA14GnUgDMGRPgefoeEAkSHtsrA5VSV4FoEgLfD7GdMyb4OPnWWjsArwKf30cX/GjbNn0SfjvCeN6YYGEnCN9vzADn9wjg0mAdA9/EZ9QwOWVMMJcE0Wo16fV688DNnMG3o5jxJNTa+QdYzvDhsjHB60kQ1apuAjdyAvjC83RrMAkLBQsRWcqYyaIxwck+CGM2jgBejuC/A6dTb0JjgmlgJaOjNeAW8Eye1EXkpUrFXUm9CT1PXwQ+y+jrUN7gwPlarbIy6iZ8I/652G+5DMwPvQnDMMT3603gaI5KZJFzwFGtnWaSwEpZqHrdo9vt7LbNpoEz8Rm1F7kJvOX79QtpG/POnfbdm3CXbXZRRDTwQUy4rHILeA94XGvnwrAYSmsHy1Ijd30QbD4QX07PAk8DE4kF9qeI/KqUWgOuAF/7fr016nYAUI7zBJYVIbNtm3a7Hf21qv9eB4p/Ab8gLUcrjkuYAAAAAElFTkSuQmCC'

starting_pos_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
random_fen = "1n2k3/r1p1p1b1/p3q3/1P1r1np1/p5RP/R2Pp3/1Bb2P2/1N1QKBN1 w - - 3 22"

def run():
	board = [
		[
			sg.Graph(canvas_size=(800, 800),
					graph_bottom_left=(0,0),
					graph_top_right=(800,800),
					key = "board"
			)
		]
	]

	printout = [
		[sg.Output(size=(100,20))],
	]

	layout = [
		[sg.Column(board),
		sg.VSeparator(),
		sg.Column(printout)],
		[sg.Button('', key='Back', image_data=button_left_base64),
		sg.Button('', key='Next', image_data=button_right_base64)],
	]
	window = sg.Window('Match Analyzer', layout)

	board_graph = window.Element('board')
	window.Finalize()

	butil.Init(board_graph)


	#fen_data = butil.data_from_fen(starting_pos_fen)
	#butil.draw_from_data(board_graph, fen_data)
	butil.set_pos_from_fen(starting_pos_fen)



	while True:
		event, values = window.read()

		if event == 'Next':
			print("next")
		elif event == 'Back':
			print("back")
		elif event == sg.WIN_CLOSED:
			break
		elif event == "boardb1":
			print("(%s, %s)" % (butil.last_X, butil.last_Y))

	window.close()

if __name__ == '__main__':
	run()
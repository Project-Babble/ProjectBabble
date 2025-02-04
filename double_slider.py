import PySimpleGUI as sg

class RangeSlider:
    def __init__(self, canvas_size=(400, 50), slider_x_range=(0, 400), initial_values=(50, 350)):

        self.canvas_size = canvas_size
        self.slider_x_range = slider_x_range
        self.current_values = list(initial_values)


        self.graph_element = sg.Graph(
            canvas_size=self.canvas_size,
            graph_bottom_left=(0, -10),
            graph_top_right=(self.canvas_size[0], 10),
            background_color='lightgray',
            key='-GRAPH-',
            enable_events=True,
            drag_submits=True
        )

        self.moving_index = None

    def draw_slider(self, graph, value):
        graph.erase()

        graph.draw_line((self.slider_x_range[0], 0), (self.slider_x_range[1], 0), width=4, color='darkblue')

        graph.draw_rectangle(
            (self.current_values[0], -1),
            (self.current_values[1], 1),
            line_color='dodgerblue',
            fill_color='dodgerblue',
        )
        width = 1
        graph.draw_rectangle(
            (value - (width/2), -1.8),
            (value + (width/2), 1.5),
            line_color='black',
            fill_color='black',
        )
        for x in self.current_values:

            graph.draw_circle((x, 0), 8, fill_color='dodgerblue', line_color='dodgerblue')




    def handle_event(self, event, values, window):
        if event == '-GRAPH-':
            mouse_x, _ = values['-GRAPH-']
            
            if self.moving_index is None:
                for i, x in enumerate(self.current_values):
                    if abs(mouse_x - x) <= 8:
                        self.moving_index = i
                        break
            else:
                self.current_values[self.moving_index] = min(max(mouse_x, self.slider_x_range[0]), self.slider_x_range[1])
                
                if self.current_values[0] > self.current_values[1]:
                    self.current_values[0], self.current_values[1] = self.current_values[1], self.current_values[0]
                self.draw_slider(window['-GRAPH-'], 200)
                window['-RANGE-TEXT-'].update(f'{self.current_values[0]} - {self.current_values[1]}')
        else:
            self.moving_index = None

    def get_layout(self):
        return [
            [self.graph_element],
            [sg.Text("Selected Range: "), sg.Text(f"{self.current_values[0]} - {self.current_values[1]}", size=(15, 1), key='-RANGE-TEXT-')]
        ]


def main():
    range_slider = RangeSlider()
    layout = range_slider.get_layout() + [[sg.Button('Exit')]]

    window = sg.Window('Range Slider with Graph', layout, finalize=True)
    range_slider.draw_slider(window['-GRAPH-'], 200)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break

        range_slider.handle_event(event, values, window)

    window.close()

if __name__ == '__main__':
    main()
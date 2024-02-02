# https://rhodesmill.org/skyfield/
# https://stackoverflow.com/questions/2526815/moon-lunar-phase-algorithm

# ? https://stackoverflow.com/questions/76559899/calculate-the-crescent-moon-width-using-skyfield

# eclipses https://stackoverflow.com/questions/64658304/determining-lunar-eclipse-in-skyfield

# pyinstaller --clean -y -n "moon_calendar" --add-data="./hexagram_data.txt":"./hexagram_data.txt" --add-data="./de421.bsp":"./de421.bsp" --onefile --windowed main.py

import datetime

import tkinter as tk
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button, TextBox
from matplotlib.patches import Ellipse
from matplotlib.ticker import MaxNLocator

from moon_phases import get_moon_phase, get_moon_eclipses
from moon_zodiac import get_moon_at_sign

# === calendar window part ===

class MainWindow:
    def __init__(self, window):

        self.window = window
        self.window.title("Moon Calendar")

        # Create figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=window)
        #self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # moon phase timeline graphic
        self.graph_axes = self.fig.add_axes([0.075, 0.25, 0.75, 0.70])  # (x0, y0, dx, dy) start and size in % of fig
        self.current_date = self.center_date = self.cursor_date = datetime.datetime.today()
        self.date_format = "%Y-%m-%d"
        self.time_range_days = 28
        self.draw_moon_phase()

        # text box for date input
        self.date_intput_axes = self.fig.add_axes([0.865, 0.85, 0.10, 0.05])
        self.date_input_box = TextBox(self.date_intput_axes, "Enter date (YYYY-MM-DD)", initial=self.center_date.strftime(self.date_format))
        date_intput_label = self.date_intput_axes.get_children()[0]  # label is a child of the TextBox axis
        date_intput_label.set_position([0.5, 1.80])  # [x,y] - change here to set the position
        date_intput_label.set_verticalalignment('top')
        date_intput_label.set_horizontalalignment('center')
        date_intput_text = self.date_intput_axes.get_children()[1]
        date_intput_text.set_position([0.5, 0.45])  # 0.05, 0.5 -- default
        date_intput_text.set_horizontalalignment('center')
        self.date_input_box.on_submit(self.submit)

        # submit button
        self.submit_axes = self.fig.add_axes([0.865, 0.75, 0.10, 0.05])
        self.submit_button = Button(self.submit_axes, 'Show', color='lightgray', hovercolor='0.975')
        submit_button_text = self.submit_axes.get_children()[0]
        submit_button_text.set_position([0.5, 0.45])
        submit_button_text.set_horizontalalignment('center')
        self.submit_button.on_clicked(self.submit)

        # reset button
        self.reset_axes = self.fig.add_axes([0.865, 0.65, 0.10, 0.05])
        self.reset_button = Button(self.reset_axes, 'Reset', color='lightgray', hovercolor='0.975')
        reset_button_text = self.submit_axes.get_children()[0]
        reset_button_text.set_position([0.5, 0.45])
        reset_button_text.set_horizontalalignment('center')
        self.reset_button.on_clicked(self.reset)

        # Initialize cursor at current datetime
        self.cursor_info_axes = self.fig.add_axes([0.865, 0.25, 0.10, 0.32], frame_on=False)
        self.cursor_info_axes.set_xticks([])
        self.cursor_info_axes.set_yticks([])
        self.cursor_info = self.cursor_info_axes.text(
            0.5, 0.45, '', transform=self.cursor_info_axes.transAxes, va='center', ha='center')
        self.update_cursor_info_text()
        # Store the id of the vertical line (initially None)
        self.cursor_line_id = None
        # Boolean to check if the mouse button is being held down
        self.cursor_line_dragging = False
        self.info_window = None

        # To redraw circles
        self.fig.canvas.mpl_connect('resize_event', self.re_draw_all)
        # Connect to mouse events
        self.fig.canvas.mpl_connect("button_press_event", self.onclick)
        self.fig.canvas.mpl_connect("button_release_event", self.offclick)
        self.fig.canvas.mpl_connect("motion_notify_event", self.onmove)

    def submit(self, event):
        self.graph_axes.cla()
        self.center_date = datetime.datetime.strptime(self.date_input_box.text, self.date_format)
        self.draw_moon_phase()
        self.re_draw_all()

    def reset(self, event):
        self.close_info_window()
        self.graph_axes.cla()
        self.current_date = self.center_date = self.cursor_date = datetime.datetime.now()
        self.date_input_box.set_val(self.center_date.strftime(self.date_format))
        self.update_cursor_info_text()
        self.draw_moon_phase()
        self.re_draw_all()

    def re_draw_all(self, resize_event=None):

        # remove all Ellipse objects from the plot
        if resize_event is not None:
            for item in self.graph_axes.patches:
                if isinstance(item, Ellipse):
                    item.remove()

        # self.draw_moon_phase()
        self.draw_moon_phase_icons(self.moon_phases, self.moon_phase_dates)
        self.draw_moon_sign_icons(self.moon_phases, self.moon_phase_dates)

        if resize_event is not None:
            resize_event.canvas.draw()
        else:
            self.canvas.draw()

    def onclick(self, event):
        if event.inaxes == self.cursor_info_axes and event.dblclick:
            self.show_info()
        elif event.inaxes == self.graph_axes and event.dblclick:
            self.cursor_line_dragging = True
            self.update_cursor_line_and_label(event)
            self.show_info()
        else:
            self.cursor_line_dragging = True
            self.update_cursor_line_and_label(event)

    def offclick(self, event):
        self.cursor_line_dragging = False

    def onmove(self, event):
        if not self.cursor_line_dragging:
            return
        self.update_cursor_line_and_label(event)
        # update message in the info window
        if self.info_window:
            self.update_info_window()

    def update_cursor_info_text(self):
        # For minute precision, change "%Y-%m-%d" to "%Y-%m-%d %H:%M:%S" or "%Y-%m-%d %H:%M"
        date_text = self.cursor_date.strftime(self.date_format)
        time_text = self.cursor_date.strftime("%H:%M")
        moon_phase = get_moon_phase(self.cursor_date)
        moon_sign = get_moon_at_sign(self.cursor_date)[1]
        self.cursor_info.set_text(
            "Selected position:\n\n"
            "Date: {}\n"
            "Time: {}\n"
            "Phase: {:.2f}\n"
            "Sign: {}\n"
            .format(date_text, time_text, moon_phase, moon_sign))

    def update_cursor_line_and_label(self, event):
        # Check if click was in plot axis
        if event.inaxes == self.graph_axes:
            # Current values
            self.cursor_date = mdates.num2date(event.xdata)

            # Remove old line
            if self.cursor_line_id:
                self.cursor_line_id.remove()
            # Add a vertical line at cursor position
            self.cursor_line_id = self.graph_axes.axvline(event.xdata, color='r', linestyle='--')

            # Update label
            self.update_cursor_info_text()

        # Redraw canvas
        self.canvas.draw()

    def update_info_window(self):
        # check if window still exists
        if self.info_window and self.info_window.winfo_exists():
            selected_info = self.cursor_info.get_text()
            self.info_window_content.configure(text=selected_info)

    def show_info(self):
        # If the info window already exists, simply update the text
        if self.info_window and self.info_window.winfo_exists():
            self.update_info_window()
            return

        # If the window does not exist, create it
        self.info_window = tk.Toplevel(self.window)
        self.info_window.withdraw()  # hide temporarily for setup

        # The window will stay on top of all others
        self.info_window.attributes('-topmost', 1)

        self.info_window.title("Selected Point Info")

        # Apply a minimum window size
        self.info_window.minsize(250, 100)

        # Apply wrapping to the label
        self.info_window_content = tk.Message(self.info_window, width=200)
        self.info_window_content.pack()

        # Make window closeable by clicking outside of it
        #self.info_window.bind('<FocusOut>', self.close_info_window)

        self.update_info_window()  # Update info on an existing window

        self.info_window.deiconify()  # show window after setup

    def close_info_window(self, event=None):
        print(f"DEBUG close_info_window() event {event}")
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.destroy()
            self.info_window = None

    def draw_moon_phase(self):

        # Initialize base date
        base_date = self.center_date - datetime.timedelta(days=self.time_range_days//2)
        moon_phase_dates = [base_date + datetime.timedelta(hours=x) for x in range(self.time_range_days*24)]
        moon_phases = [get_moon_phase(d) for d in moon_phase_dates]
        y = [mf if mf  <= 180 else (360 - mf) for mf in moon_phases]
        #y = np.sin(np.linspace(0, 2 * np.pi, numdays))

        self.y = y
        self.moon_phases = moon_phases
        self.moon_phase_dates = moon_phase_dates

        self.graph_axes.plot(moon_phase_dates, y, color='#1f77b4')  # color default '#1f77b4' or 'k' (black)
        self.graph_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        #self.graph_axes.xaxis.set_major_locator(mdates.DayLocator())
        # Use MaxNLocator to limit the number of ticks
        self.graph_axes.xaxis.set_major_locator(MaxNLocator(nbins=self.time_range_days*24+1, integer=True))
        # # Create a function format_date that takes a tick value, x, and the position and returns the date string
        # def format_date(x, pos=None): return num2date(x).strftime('%Y-%m-%d')
        # #self.graph_axes.xaxis.set_major_formatter(FuncFormatter(format_date))
        self.graph_axes.set_xlabel('Time (days)')
        self.graph_axes.set_ylabel('Moon Phase (deg.)')
        self.graph_axes.grid(True)

        labels = self.graph_axes.get_xticklabels()
        for label in labels:
            # Fix xlabels overlap
            # self.graph_axes.setp(self.graph_axes.get_xticklabels(), rotation=30, horizontalalignment='right')
            # self.graph_axes.figure.autofmt_xdate() -- does not work at redraw
            label.set_ha("right")
            label.set_rotation(30)
            # Make cursor date label bold
            if label.get_text() == self.center_date.strftime(self.date_format):
                label.set_weight('bold')
        # Make dashed vertical line at the current datetime
        self.current_date = datetime.datetime.now()
        if moon_phase_dates[0] <= self.current_date <= moon_phase_dates[-1]:
            self.graph_axes.axvline(mdates.date2num(self.current_date), color='k', linestyle='--')

    def draw_moon_phase_icons(self, moon_phases, moon_phase_dates):

        x_y_ph_pos = []  # collect list of tuples with image coordinates and phase

        # a single date passed for drawing
        if not ((isinstance(moon_phases, list)) and (moon_phase_dates, list)):
            y_pos = moon_phases if moon_phases <= 180 else (360 - moon_phases)
            x_y_ph_pos.append((moon_phase_dates, y_pos, moon_phases))
            eclipses = get_moon_eclipses(moon_phase_dates - datetime.timedelta(days=1),
                                         moon_phase_dates + datetime.timedelta(days=1))

        else:
            target_moon_phases = [0, 90, 180, 270, 360]
            moon_phase_step = 1.5 * abs(moon_phases[1] - moon_phases[0])
            # the highest phase may be e.g. 359.45 not, 360, and diff is higher than step 0.45 vs 0.57+
            print(f"DEBUG draw_moon_phase_icons(): phase step {moon_phase_step})")
            eclipses = get_moon_eclipses(moon_phase_dates[0], moon_phase_dates[-1])

            for i, moon_phase in enumerate(moon_phases):
                if any((abs(ph - moon_phase) < moon_phase_step) for ph in target_moon_phases):
                    y_pos = moon_phase if moon_phase <= 180 else (360 - moon_phase)
                    if ((len(x_y_ph_pos) > 0 and abs(x_y_ph_pos[-1][1] - y_pos) > 2 * moon_phase_step)
                            or len(x_y_ph_pos) == 0):
                        x_y_ph_pos.append((moon_phase_dates[i], y_pos, moon_phase))

        print(f"DEBUG draw_moon_phase_icons(): total {len(x_y_ph_pos)} points at the positions x,y: {x_y_ph_pos}")

        for x_pos, y_pos, phase in x_y_ph_pos:
            date_eclipses = [eclipse_rank for eclipse_time, eclipse_rank in eclipses
                             if x_pos.strftime(self.date_format) in eclipse_time]
            has_eclipse = max(date_eclipses) if date_eclipses else False
            self.draw_moon(x_pos=x_pos, y_pos=y_pos, phase=phase, eclipse=has_eclipse)

    def draw_moon(self, x_pos=0, y_pos=0, phase=0, eclipse=False):
        # https://palettemaker.com/colors/moon
        # https://www.schemecolor.com/moon-colors.php
        # https://www.color-hex.com/color-palette/9473
        moon_color = '#F6F1D5'
        edge_shadow_color = '#94908D'
        deep_shadow_color = '#51607E'
        eclipse_color = '#731c1c'

        # window_width, window_height = self.canvas.get_width_height()  # get 800x600 values
        bbox = self.graph_axes.get_window_extent().transformed(self.canvas.figure.dpi_scale_trans.inverted())
        window_width, window_height = bbox.width, bbox.height

        # Calculate x and y data ranges
        x_range = max(xlim := self.graph_axes.get_xlim()) - min(xlim)
        y_range = max(ylim := self.graph_axes.get_ylim()) - min(ylim)

        # Diameter of circular patches as fractions of data ranges
        x_diameter = x_range / window_width / 4
        y_diameter = y_range / window_height / 4

        # Center coordinates
        center_x = mdates.date2num(x_pos)
        center_y = y_pos

        print(f"DEBUG draw_moon(): center_x {center_x:.3f}, center_y {center_y:.3f}, x_diameter {x_diameter:.3f}, y_diameter {y_diameter:.3f}")

        # Create a window (visible side of the moon)
        moon_window_circle = Ellipse((center_x, center_y), x_diameter, y_diameter,
                                color='none', zorder=1) # transform=ax.transData | ax.transAxes, the same for all

        solar_light_circle = Ellipse((center_x, center_y), x_diameter, y_diameter,
                                     fill=True, facecolor=moon_color, edgecolor=edge_shadow_color, lw=1, zorder=2)

        # moon moves from left to right, thus solar light and moon shadow side moves from right to left
        moon_shadow_edge_rounding = 0.87  # this for visual effect
        moon_shadow_shift = x_diameter * moon_shadow_edge_rounding * ((-phase) if phase < 180 else ((360-phase))) / 180
        moon_shadow_circle = Ellipse((center_x + moon_shadow_shift, center_y),
                                     x_diameter, y_diameter / moon_shadow_edge_rounding,
                               fill=True, facecolor=deep_shadow_color, edgecolor=edge_shadow_color, lw=2,  zorder=3)

        if eclipse > 1:  # rank 2 or 3
            earth_shadow_circle = Ellipse((center_x, center_y), x_diameter, y_diameter,
                                   fill=True, facecolor=eclipse_color, edgecolor=deep_shadow_color, lw=3,  zorder=4)
        elif eclipse == 1:
            earth_shadow_edge_rounding = 0.87
            earth_shadow_shift = y_diameter * earth_shadow_edge_rounding * 0.6
            earth_shadow_circle = Ellipse((center_x, center_y - earth_shadow_shift),
                                          x_diameter / earth_shadow_edge_rounding, y_diameter,
                                   fill=True, facecolor=eclipse_color, edgecolor=deep_shadow_color, lw=2,  zorder=4)
        else:
            earth_shadow_circle = Ellipse((center_x, center_y), x_diameter , y_diameter,
                                   fill=True, facecolor=eclipse_color, edgecolor=deep_shadow_color, lw=3,  zorder=4)

        # Add shapes and clippers
        # https://stackoverflow.com/questions/67075348/what-is-the-difference-between-add-artist-or-add-patch
        self.graph_axes.add_artist(moon_window_circle)  # should be first to get proper coords for clipping
        self.graph_axes.add_artist(solar_light_circle)
        solar_light_circle.set_clip_path(moon_window_circle)

        # Process full moon states  (TODO: replace the special fix with a nice automatic solution)
        if 180 - 5 < phase < 180 + 5:
            if eclipse:
                self.graph_axes.add_artist(earth_shadow_circle)
                earth_shadow_circle.set_clip_path(moon_window_circle)
        else:
            self.graph_axes.add_artist(moon_shadow_circle)
            moon_shadow_circle.set_clip_path(moon_window_circle)

        # print(f"DEBUG", moon_window_circle.get_path().contains_point((center_x, center_y))) -- always false


    def draw_moon_sign_icons(self, moon_phases, moon_phase_dates):

        moon_phases_list = moon_phases if isinstance(moon_phases, list) else [moon_phases]

        moon_phase_dates_list = moon_phase_dates if isinstance(moon_phase_dates, list) else [moon_phase_dates]
        
        moon_signs_dated_list = [(date, phase, get_moon_at_sign(date)[1])
                                 for date, phase in zip(moon_phase_dates_list, moon_phases_list)]

        for i_date, (date, phase, sign) in enumerate(moon_signs_dated_list):
            if i_date == 0:
                pass  # self.draw_moon_sign(date, phase, sign)  # drawn too close, not nice
            else:
                prev_sign = moon_signs_dated_list[i_date - 1][2]
                if sign != prev_sign:
                    self.draw_moon_sign(date, phase, sign)

    def draw_moon_sign(self, x_pos=0, y_pos=0, sign=None):
        # Coordinates are the left bottom corner of annotation, thus center letters with x-0.25 and y-16
        horizontal_position = mdates.num2date(mdates.date2num(x_pos) - 0.25).replace(tzinfo=None)
        vertical_position = (y_pos if y_pos <= 180 else (360 - y_pos)) - 16
        sign_icon = sign.split()[1]
        self.graph_axes.annotate(sign_icon, xy=(horizontal_position, vertical_position), fontsize=17)


if __name__ == "__main__":
    current_moon_phase = get_moon_phase(date=None)
    print(f'Current Moon phase is {current_moon_phase:.1f} '
          f'(Legend: New Moon 0/360, Full Moon 180)')

    window = tk.Tk()
    window.geometry('1260x500')  # '800x600'
    MainWindow(window)
    tk.mainloop()
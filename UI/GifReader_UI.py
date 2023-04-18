from UI.Reader_UI import CollapsingFrame
import tkinter
import ttkbootstrap as ttk
from ttkbootstrap import utility
utility.enable_high_dpi_awareness()


class UI:
	def __init__(self, master, sw, sh, side_color):
		self.gif_main_canvas_h = None
		self.gif_main_canvas_w = None
		self.gif_side_canvas_h = None
		self.gif_side_canvas_w = None
		self.SW = sw
		self.SH = sh
		self.side_color = side_color
		self.scaling_ratio = self.SW / 3072 if self.SW / 3072 < self.SH / 1728 else self.SH / 1728
		self.toplevel_w = 800 * self.scaling_ratio
		self.toplevel_h = 200 * self.scaling_ratio
		self.toplevel_x = self.SW / 2 - self.toplevel_w / 2
		self.toplevel_y = self.SH / 2 - self.toplevel_h / 2
		self.toplevel = tkinter.Toplevel(master=master)

		w, h, x, y = self.toplevel_w, self.toplevel_h, self.toplevel_x, self.toplevel_y
		label_ = 'Loading GIF Files...'
		self.toplevel.geometry('%dx%d+%d+%d' % (w, h, x, y))
		if self.scaling_ratio >= 0.65:
			self.bar = ttk.Progressbar(self.toplevel, orient='horizontal', length=250, mode='indeterminate')
			self.bar.step(25)
			self.label = tkinter.Label(self.toplevel, text=label_, font=('Consolas', 20, 'bold'), width=40, height=1)
		else:
			self.bar = ttk.Progressbar(self.toplevel, orient='horizontal', length=100, mode='indeterminate')
			self.bar.step(10)
			self.label = tkinter.Label(self.toplevel, text=label_, font=('Consolas', 10, 'bold'), width=40, height=1)
		self.bar.configure(bootstyle='success')
		self.label.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.bar.grid(row=1, column=0)
		self.toplevel.grid_columnconfigure(0, weight=1)
		self.toplevel.grid_rowconfigure(0, weight=1)
		self.toplevel.grid_rowconfigure(1, weight=1)
		self.bar.start()
		self.toplevel.resizable(False, False)

		self.menu = ttk.Menu(self.toplevel)
		self.toplevel.configure(menu=self.menu)
		self.jump_menu = ttk.Menu(self.menu, font=('Consolas', 15), borderwidth=0)

		self.gif_side_c_frame = CollapsingFrame(self.toplevel, size=1440 * self.scaling_ratio)
		self.gif_side_frame = ttk.Frame(self.gif_side_c_frame)
		self.gif_main_frame = ttk.Frame(self.toplevel)

		self.gif_canvas = tkinter.Canvas(self.gif_main_frame)

		self.gif_side_canvas_1 = tkinter.Canvas(self.gif_side_frame)
		self.gif_side_canvas_2 = tkinter.Canvas(self.gif_side_frame)
		self.gif_side_canvas_3 = tkinter.Canvas(self.gif_side_frame)

		self.gif_separator_h_1 = ttk.Separator(self.gif_side_frame, orient="horizontal")
		self.gif_separator_h_2 = ttk.Separator(self.gif_side_frame, orient="horizontal")

	def change_grid(self):
		self.label.destroy()
		self.bar.destroy()

		# self.menu.add_cascade(label='Jump', menu=self.jump_menu)

		self.gif_side_c_frame.grid(row=0, column=0, sticky=tkinter.NSEW)
		title = "S\nI\nD\nE\nB\nA\nR"
		if self.gif_side_c_frame.child is None:
			self.gif_side_c_frame.add(child=self.gif_side_frame, title=title, size=1440 * self.scaling_ratio)
			self.gif_side_c_frame.add_main(main=self.gif_main_frame)

		self.gif_canvas.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.gif_side_canvas_1.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.gif_separator_h_1.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.gif_side_canvas_2.grid(row=2, column=0, sticky=tkinter.NSEW)
		self.gif_separator_h_2.grid(row=3, column=0, sticky=tkinter.NSEW)
		self.gif_side_canvas_3.grid(row=4, column=0, sticky=tkinter.NSEW)

		# self.entry.grid(row=0, column=0)
		self.gif_canvas.configure(height=1440 * self.scaling_ratio, width=2000 * self.scaling_ratio)
		self.gif_side_frame.configure(height=1440 * self.scaling_ratio)
		self.gif_side_canvas_1.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)
		self.gif_side_canvas_2.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)
		self.gif_side_canvas_3.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)

		self.toplevel.grid_columnconfigure(0, weight=1)
		self.toplevel.grid_columnconfigure(1, weight=1)

		self.gif_side_frame.grid_rowconfigure(0, minsize=473 * self.scaling_ratio, weight=1)
		self.gif_side_frame.grid_rowconfigure(1, minsize=10 * self.scaling_ratio, weight=1)
		self.gif_side_frame.grid_rowconfigure(2, minsize=473 * self.scaling_ratio, weight=1)
		self.gif_side_frame.grid_rowconfigure(3, minsize=10 * self.scaling_ratio, weight=1)
		self.gif_side_frame.grid_rowconfigure(4, minsize=473 * self.scaling_ratio, weight=1)

		self.gif_main_canvas_h = 720 * self.scaling_ratio
		self.gif_main_canvas_w = 1000 * self.scaling_ratio
		self.gif_side_canvas_h = 240 * self.scaling_ratio
		self.gif_side_canvas_w = 200 * self.scaling_ratio

		x = self.SW / 2 - 2400 * self.scaling_ratio / 2
		y = self.SH / 2 - 1440 * self.scaling_ratio / 2
		self.toplevel.geometry('%dx%d+%d+%d' % (2400 * self.scaling_ratio, 1440 * self.scaling_ratio, x, y))
		self.toplevel.resizable(False, False)

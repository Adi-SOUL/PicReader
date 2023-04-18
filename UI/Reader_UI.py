import tkinter
import ttkbootstrap as ttk
from ttkbootstrap import Style, utility
utility.enable_high_dpi_awareness()
from PIL import ImageTk, Image
from tools import MEM_STATUS, SCAL_STD, THEME
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle


# noinspection PyArgumentList
def toplevel_with_bar(
		w: int,
		h: int,
		x: int,
		y: int,
		name: str,
		label_: str,
		large: bool,
		master=None
) -> tkinter.Toplevel:

	if master:
		toplevel = tkinter.Toplevel(master=master)
	else:
		toplevel = tkinter.Toplevel()
	toplevel.title(name)
	toplevel.geometry('%dx%d+%d+%d' % (w, h, x, y))
	if large:
		bar = ttk.Progressbar(toplevel, orient='horizontal', length=250, mode='indeterminate')
		bar.step(25)
		label = tkinter.Label(toplevel, text=label_, font=('Consolas', 15, 'bold'), width=40, height=1)
	else:
		bar = ttk.Progressbar(toplevel, orient='horizontal', length=100, mode='indeterminate')
		bar.step(10)
		label = tkinter.Label(toplevel, text=label_, font=('Consolas', 10, 'bold'), width=40, height=1)
	bar.configure(bootstyle='success')
	label.grid(row=0, column=0, sticky=tkinter.NSEW)
	bar.grid(row=1, column=0)
	toplevel.grid_columnconfigure(0, weight=1)
	toplevel.grid_rowconfigure(0, weight=1)
	toplevel.grid_rowconfigure(1, weight=1)
	bar.start()
	toplevel.resizable(False, False)
	return toplevel


class SideFrame(ttk.Frame):
	def __init__(self, master, **kwargs):
		super().__init__(master, **kwargs)
		self.btn = None


# noinspection PyArgumentList
class CollapsingFrame(ttk.Frame):

	def __init__(self, master, size, **kwargs):
		super().__init__(master, **kwargs)
		self.main_c: int = 0
		self.rowconfigure(0, weight=1, minsize=size)
		self.columnconfigure(1, weight=1)
		self.cumulative_column = 0
		self.child = None
		self.main = None
		self.side = None
		self.images = [ttk.PhotoImage(file=r'Pics\up.png'), ttk.PhotoImage(file=r'Pics\right.png')]

	def add_main(self, main):
		if main.winfo_class() != 'TFrame':
			return
		self.main = main
		self.main_c = self.cumulative_column
		main.grid(column=self.cumulative_column, row=0, sticky=NSEW)
		self.cumulative_column += 1

	def add(self, child, title="", bootstyle=PRIMARY, **kwargs):
		if child.winfo_class() != 'TFrame':
			return
		self.child = child
		style_color = Bootstyle.ttkstyle_widget_color(bootstyle)
		frm = ttk.Frame(self, bootstyle=style_color)
		frm.grid(column=self.cumulative_column, row=0, sticky=NSEW)

		header = ttk.Label(
			master=frm,
			text=title,
			bootstyle=(style_color, INVERSE),
			compound='center',
			font=('Consolas', 15, 'bold')
		)
		if kwargs.get('textvariable'):
			header.configure(textvariable=kwargs.get('textvariable'))
		header.grid(row=1, column=0)

		def _func(c=child): return self._toggle_open_close(c)
		btn = ttk.Button(
			master=frm,
			image=self.images[1],
			bootstyle=style_color,
			command=_func
		)
		btn.grid(row=0, column=0)

		self.rowconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)
		child.btn = btn
		child.grid(column=self.cumulative_column + 1, row=0, sticky=NSEW)

		self.cumulative_column += 2

	def _toggle_open_close(self, child):
		if child.winfo_viewable():
			child.grid_remove()
			self.main.grid(column=1, row=0, sticky=NSEW)
			child.btn.configure(image=self.images[0])
		else:
			child.grid()
			self.main.grid(column=2, row=0, sticky=NSEW)
			child.btn.configure(image=self.images[1])


# noinspection PyArgumentList
class ReaderUI:
	def __init__(self):
		self.theme_name = THEME
		if self.theme_name == 'darkly':
			self.side_color = 'azure4'
		else:
			self.side_color = 'azure3'
		self.style = Style()
		self.win = self.style.master
		self.win.title('reADpIc')
		self.win.iconbitmap('PicReader.ico')
		self.pixelVirtual = tkinter.PhotoImage(width=1, height=1)
		self.main_canvas_h = None
		self.main_canvas_w = None
		self.side_canvas_h = None
		self.side_canvas_w = None
		self.scaling_ratio = 1.
		self.SW, self.SH = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
		self.scaling_ratio = self.SW / 3072 if self.SW / 3072 < self.SH / 1728 else self.SH / 1728
		self.font_size = int(15 * self.scaling_ratio) if int(15 * self.scaling_ratio) < 15 else 15
		if self.scaling_ratio < 0.4:
			exit()

		x = self.SW / 2 - 1280 * self.scaling_ratio / 2
		y = self.SH / 2 - 900 * self.scaling_ratio / 2
		self.win.geometry('%dx%d+%d+%d' % (1280 * self.scaling_ratio, 900 * self.scaling_ratio, x, y))
		self.dark_init_img = Image.open(r'Pics\Dreadpic.png')
		self.init_img = Image.open(r'Pics\readpic.png')
		if self.theme_name == 'darkly':
			if self.scaling_ratio == 1.:
				self.init_img_tk = ImageTk.PhotoImage(self.dark_init_img)
			else:
				self.init_img_tk = ImageTk.PhotoImage(
					self.dark_init_img.resize((int(1280 * self.scaling_ratio), int(780 * self.scaling_ratio))))
		else:
			if self.scaling_ratio == 1.:
				self.init_img_tk = ImageTk.PhotoImage(self.init_img)
			else:
				self.init_img_tk = ImageTk.PhotoImage(
					self.init_img.resize((int(1280 * self.scaling_ratio), int(780 * self.scaling_ratio))))

		self.toplevel_w = 800 * self.scaling_ratio
		self.toplevel_h = 200 * self.scaling_ratio
		self.toplevel_x = self.SW / 2 - self.toplevel_w / 2
		self.toplevel_y = self.SH / 2 - self.toplevel_h / 2
		self.label = tkinter.Label(self.win, image=self.init_img_tk)
		self.label.grid(row=0, column=0, columnspan=4, sticky=tkinter.NSEW)
		self.button_1 = \
			ttk.Button(self.win, text='With File', width=30, bootstyle=('success', 'outline'))
		self.button_2 = \
			ttk.Button(self.win, text='With Dir ', width=30, bootstyle=('success', 'outline'))
		self.button_1.grid(row=1, column=0, rowspan=2, sticky=tkinter.NSEW)
		self.button_2.grid(row=1, column=1, rowspan=2, sticky=tkinter.NSEW)

		self.side_c_frame = CollapsingFrame(self.win, size=1440 * self.scaling_ratio)
		self.side_frame = SideFrame(self.side_c_frame)
		self.main_frame = ttk.Frame(self.win)

		self.canvas = tkinter.Canvas(self.main_frame)

		self.side_canvas_1 = tkinter.Canvas(self.side_frame)
		self.side_canvas_2 = tkinter.Canvas(self.side_frame)
		self.side_canvas_3 = tkinter.Canvas(self.side_frame)

		self.status = tkinter.IntVar()
		self.text = tkinter.StringVar()
		self.text_label = \
			ttk.Label(self.win, textvariable=self.text, font=('Consolas', self.font_size, 'bold'), width=20, compound='center')
		self.radiobutton_1 = \
			ttk.Radiobutton(self.win, text='On', variable=self.status, value=1, width=4, compound='center')
		self.radiobutton_1.configure(command=self.change_label)
		self.radiobutton_2 = \
			ttk.Radiobutton(self.win, text='Off', variable=self.status, value=0, width=4, compound='center')
		self.radiobutton_2.configure(command=self.change_label)

		self.separator_h_1 = ttk.Separator(self.side_frame, orient="horizontal")
		self.separator_h_2 = ttk.Separator(self.side_frame, orient="horizontal")

		self.menu_bar = ttk.Menu(self.win)
		self.win.config(menu=self.menu_bar)

		self.file_menu = ttk.Menu(self.menu_bar, font=('Consolas', 12), borderwidth=0)
		self.tool_menu = ttk.Menu(self.menu_bar, font=('Consolas', 12), borderwidth=0)
		self.convert_menu = ttk.Menu(self.file_menu, font=('Consolas', 12), borderwidth=0)
		self.themes_menu = ttk.Menu(self.file_menu, font=('Consolas', 12), borderwidth=0)

		self.menu_bar.add_cascade(label='Files', menu=self.file_menu)
		self.menu_bar.add_cascade(label='Tools', menu=self.tool_menu)
		self.file_menu.add_cascade(label='Themes', menu=self.themes_menu)
		self.file_menu.add_cascade(label='Convert Files', menu=self.convert_menu)

		if MEM_STATUS:
			self.status.set(0)
			self.text.set('Low Memory Mode: Off')
			self.radiobutton_2.state(['selected'])
			self.text_label.configure(foreground='gray')
		else:
			self.status.set(1)
			self.text.set('Low Memory Mode: On')
			self.radiobutton_1.state(['selected'])
			self.text_label.configure(foreground='green')

		if self.scaling_ratio <= SCAL_STD:
			self.button_1.configure(width=25)
			self.button_2.configure(width=25)
			self.radiobutton_1.configure(text='L On')
			self.radiobutton_2.configure(text='L Off')
			self.radiobutton_1.grid(row=1, column=2, columnspan=2)
			self.radiobutton_2.grid(row=2, column=2, columnspan=2)
		else:
			self.text_label.grid(row=1, rowspan=2, column=2)
			self.radiobutton_1.grid(row=1, column=3)
			self.radiobutton_2.grid(row=2, column=3)

		self.win.grid_columnconfigure(0, weight=1)
		self.win.grid_columnconfigure(1, weight=1)
		self.win.grid_columnconfigure(2, weight=2)
		self.win.grid_rowconfigure(0, weight=1)
		self.win.grid_rowconfigure(1, weight=1)
		self.win.grid_rowconfigure(2, weight=1)

		self.change_theme(theme_name=self.theme_name, size=self.font_size)
		self.win.resizable(False, False)

	def change_label(self) -> None:
		if self.scaling_ratio > SCAL_STD:
			if self.status.get():
				self.text.set('Low Memory Mode: On')
				self.text_label.configure(foreground='green')
			else:
				self.text.set('Low Memory Mode: Off')
				self.text_label.configure(foreground='gray')
		else:
			if self.status.get():
				self.radiobutton_1.configure(text='L On')
			else:
				self.radiobutton_2.configure(text='L Off')

	def change_theme(self, theme_name: str, size: float) -> None:
		self.style.theme_use(theme_name)
		self.style.configure('TButton', font=('Consolas', size, 'bold'))
		self.style.configure('TRadiobutton', font=('Consolas', size, 'bold'))
		if theme_name == 'darkly':
			if self.scaling_ratio == 1.:
				self.init_img_tk = ImageTk.PhotoImage(self.dark_init_img)
			else:
				self.init_img_tk = ImageTk.PhotoImage(
					self.dark_init_img.resize((int(1280 * self.scaling_ratio), int(780 * self.scaling_ratio))))
			self.side_color = 'azure4'
		else:
			if self.scaling_ratio == 1.:
				self.init_img_tk = ImageTk.PhotoImage(self.init_img)
			else:
				self.init_img_tk = ImageTk.PhotoImage(
					self.init_img.resize((int(1280 * self.scaling_ratio), int(780 * self.scaling_ratio))))
			self.side_color = 'azure3'

		self.label.configure(image=self.init_img_tk)
		self.side_canvas_1.configure(bg=self.side_color)
		self.side_canvas_2.configure(bg=self.side_color)
		self.side_canvas_3.configure(bg=self.side_color)
		self.theme_name = theme_name

	def change_grid(self) -> None:
		self.button_1.destroy()
		self.button_2.destroy()
		self.radiobutton_1.destroy()
		self.radiobutton_2.destroy()
		self.text_label.destroy()

		self.side_c_frame.grid(row=0, column=0, sticky=tkinter.NSEW)

		title = "S\nI\nD\nE\nB\nA\nR"
		if self.side_c_frame.child is None:
			self.side_c_frame.add(child=self.side_frame, title=title, size=1440 * self.scaling_ratio)
			self.side_c_frame.add_main(main=self.main_frame)

		self.canvas.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.side_canvas_1.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.separator_h_1.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.side_canvas_2.grid(row=2, column=0, sticky=tkinter.NSEW)
		self.separator_h_2.grid(row=3, column=0, sticky=tkinter.NSEW)
		self.side_canvas_3.grid(row=4, column=0, sticky=tkinter.NSEW)

		self.canvas.configure(height=1440 * self.scaling_ratio, width=2000 * self.scaling_ratio)
		self.side_frame.configure(height=1440 * self.scaling_ratio)
		self.side_canvas_1.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)
		self.side_canvas_2.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)
		self.side_canvas_3.configure(height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bg=self.side_color)

		self.win.grid_columnconfigure(0, weight=1)
		self.win.grid_columnconfigure(1, weight=1)

		self.side_frame.grid_rowconfigure(0, minsize=473 * self.scaling_ratio, weight=1)
		self.side_frame.grid_rowconfigure(1, minsize=10 * self.scaling_ratio, weight=1)
		self.side_frame.grid_rowconfigure(2, minsize=473 * self.scaling_ratio, weight=1)
		self.side_frame.grid_rowconfigure(3, minsize=10 * self.scaling_ratio, weight=1)
		self.side_frame.grid_rowconfigure(4, minsize=473 * self.scaling_ratio, weight=1)

		self.main_canvas_h = 720 * self.scaling_ratio
		self.main_canvas_w = 1000 * self.scaling_ratio
		self.side_canvas_h = 240 * self.scaling_ratio
		self.side_canvas_w = 200 * self.scaling_ratio

		x = self.SW / 2 - 2400 * self.scaling_ratio / 2
		y = self.SH / 2 - 1440 * self.scaling_ratio / 2
		self.win.geometry('%dx%d+%d+%d' % (2400 * self.scaling_ratio, 1440 * self.scaling_ratio, x, y))

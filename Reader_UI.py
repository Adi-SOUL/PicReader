import tkinter
from tkinter import ttk

from PIL import ImageTk, Image

from tools import MEM_STATUS, SCAL_STD


def toplevel_with_bar(w, h, x, y, name, label_, large):
	toplevel = tkinter.Toplevel()
	toplevel.title(name)
	toplevel.geometry('%dx%d+%d+%d' % (w, h, x, y))
	if large:
		bar = ttk.Progressbar(toplevel, orient='horizontal', length=250, mode='indeterminate')
		bar.step(25)
		label = tkinter.Label(toplevel, text=label_, font=('Consolas', 20, 'bold'), width=40, height=1)
	else:
		bar = ttk.Progressbar(toplevel, orient='horizontal', length=100, mode='indeterminate')
		bar.step(10)
		label = tkinter.Label(toplevel, text=label_, font=('Consolas', 10, 'bold'), width=40, height=1)
	label.grid(row=0, column=0, sticky=tkinter.NSEW)
	bar.grid(row=1, column=0)
	toplevel.grid_columnconfigure(0, weight=1)
	toplevel.grid_rowconfigure(0, weight=1)
	toplevel.grid_rowconfigure(1, weight=1)
	bar.start()
	return toplevel


class ReaderUI:
	def __init__(self):
		self.win = tkinter.Tk()
		self.win.title('reADpIc')
		self.pixelVirtual = tkinter.PhotoImage(width=1, height=1)

		self.scaling_ratio = 1.
		self.SW, self.SH = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
		self.scaling_ratio = self.SW / 3072 if self.SW / 3072 < self.SH / 1728 else self.SH / 1728
		size = int(20 * self.scaling_ratio) if int(20 * self.scaling_ratio) < 20 else 20
		if self.scaling_ratio < 0.4:
			exit()

		x = self.SW / 2 - 1280 * self.scaling_ratio / 2
		y = self.SH / 2 - 900 * self.scaling_ratio / 2
		self.win.geometry('%dx%d+%d+%d' % (1280 * self.scaling_ratio, 900 * self.scaling_ratio, x, y))
		init_img = Image.open(r'readpic.png')
		if self.scaling_ratio == 1.:
			self.img = ImageTk.PhotoImage(init_img)
		else:
			self.img = ImageTk.PhotoImage(
				init_img.resize((int(1280 * self.scaling_ratio), int(780 * self.scaling_ratio))))

		self.toplevel_w = 800 * self.scaling_ratio
		self.toplevel_h = 200 * self.scaling_ratio
		self.toplevel_x = self.SW / 2 - self.toplevel_w / 2
		self.toplevel_y = self.SH / 2 - self.toplevel_h / 2
		self.label = tkinter.Label(self.win, image=self.img)
		self.label.grid(row=0, column=0, columnspan=4, sticky=tkinter.NSEW)
		self.button_1 = \
			tkinter.Button(self.win, text='use file', font=('Consolas', size, 'bold'), width=30, height=3, bd=5)
		self.button_2 = \
			tkinter.Button(self.win, text='use dir ', font=('Consolas', size, 'bold'), width=30, bd=5)
		self.button_1.grid(row=1, column=0, rowspan=2, sticky=tkinter.NSEW)
		self.button_2.grid(row=1, column=1, rowspan=2, sticky=tkinter.NSEW)

		self.side_button_1 = \
			tkinter.Button(self.win, image=self.pixelVirtual, height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bd=1)
		self.side_button_2 = \
			tkinter.Button(self.win, image=self.pixelVirtual, height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bd=1)
		self.side_button_3 = \
			tkinter.Button(self.win, image=self.pixelVirtual, height=480 * self.scaling_ratio, width=400 * self.scaling_ratio, bd=1)

		self.status = tkinter.IntVar()
		self.text = tkinter.StringVar()
		self.text_label = tkinter.Label(self.win, textvariable=self.text, font=('Consolas', size, 'bold'), width=35, height=3)
		self.radiobutton_1 = \
			tkinter.Radiobutton(self.win, text='On', variable=self.status, value=1, font=('Consolas', size, 'bold'), width=5)
		self.radiobutton_1.configure(command=self.change_label)
		self.radiobutton_2 = \
			tkinter.Radiobutton(self.win, text='Off', variable=self.status, value=0, font=('Consolas', size, 'bold'))
		self.radiobutton_1.configure(command=self.change_label)

		if MEM_STATUS:
			self.status.set(0)
			self.text.set('Low Memory Mode: Off')
			self.radiobutton_2.select()
			self.radiobutton_1.deselect()
			self.text_label.configure(bg='gray')
		else:
			self.status.set(1)
			self.text.set('Low Memory Mode: On')
			self.radiobutton_2.deselect()
			self.radiobutton_1.select()
			self.text_label.configure(bg='green')

		if self.scaling_ratio <= SCAL_STD:
			self.radiobutton_1.configure(text='LMM On', font=('Consolas', size, 'bold'))
			self.button_1.configure(font=('Consolas', size, 'bold'))
			self.button_2.configure(font=('Consolas', size, 'bold'))
			self.radiobutton_2.configure(text='LMM Off', font=('Consolas', size, 'bold'))
			if MEM_STATUS:
				self.radiobutton_1.configure(bg='gray')
				self.radiobutton_2.configure(bg='green')
			else:
				self.radiobutton_1.configure(bg='green')
				self.radiobutton_2.configure(bg='gray')
			self.radiobutton_1.grid(row=1, column=2, columnspan=2, sticky=tkinter.NSEW)
			self.radiobutton_2.grid(row=2, column=2, columnspan=2, sticky=tkinter.NSEW)
		else:
			self.text_label.grid(row=1, rowspan=2, column=2, sticky=tkinter.NSEW)
			self.radiobutton_1.grid(row=1, column=3, sticky=tkinter.NSEW)
			self.radiobutton_2.grid(row=2, column=3, sticky=tkinter.NSEW)

		self.win.grid_columnconfigure(0, weight=1)
		self.win.grid_columnconfigure(1, weight=1)
		self.win.grid_columnconfigure(2, weight=2)
		self.win.grid_rowconfigure(0, weight=1)
		self.win.grid_rowconfigure(1, weight=1)
		self.win.grid_rowconfigure(2, weight=1)

		self.win.resizable(False, False)

	def change_label(self) -> None:
		if self.status.get():
			if self.scaling_ratio > SCAL_STD:
				self.text.set('Low Memory Mode: On')
				self.text_label.configure(bg='green')
			else:
				self.radiobutton_1.configure(bg='green')
				self.radiobutton_2.configure(bg='gray')
		else:
			if self.scaling_ratio > SCAL_STD:
				self.text.set('Low Memory Mode: Off')
				self.text_label.configure(bg='gray')
			else:
				self.radiobutton_1.configure(bg='gray')
				self.radiobutton_2.configure(bg='green')

	def change_grid(self) -> None:
		self.button_1.destroy()
		self.button_2.destroy()
		self.radiobutton_1.destroy()
		self.radiobutton_2.destroy()
		self.text_label.destroy()

		self.label.grid(row=0, column=1, rowspan=3, sticky=tkinter.NSEW)
		self.side_button_1.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.side_button_2.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.side_button_3.grid(row=2, column=0, sticky=tkinter.NSEW)
		self.label.configure(height=9, width=2000*self.scaling_ratio)
		x = self.SW / 2 - 2400 * self.scaling_ratio / 2
		y = self.SH / 2 - 1440 * self.scaling_ratio / 2
		self.win.geometry('%dx%d+%d+%d' % (2400 * self.scaling_ratio, 1440 * self.scaling_ratio, x, y))

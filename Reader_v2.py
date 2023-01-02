# encoding: utf-8
import os
import re
import dill
import psutil
import tkinter
import threading
from sys import exit
from queue import Queue
from _tkinter import TclError
from PIL import Image, ImageTk
from tkinter.simpledialog import askstring
from tkinter.filedialog import askdirectory, askopenfilename
from tools import flatten, sub_loader, encode, thread_func, get_img, toplevel_with_bar


class Reader:
	def __init__(self):
		self.thread_num = 5
		self.q = Queue()
		self.flag = False
		self.content = ''
		self.dir_path = ''
		self.file_list = []
		self.img_dict = {}
		self.key_list = []
		self.length = 0
		self.id_ = 0
		self.button_id_ = 0
		self.button_id_2 = 0
		self.button_id_3 = 0
		self.finished = False
		self.fastSaving = False
		self.img_1 = None
		self.img_2 = None
		self.img_3 = None

		self.win = tkinter.Tk()
		self.win.title('reADpIc')
		self.pixelVirtual = tkinter.PhotoImage(width=1, height=1)
		self.SW, self.SH = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
		x = self.SW / 2 - 1280 / 2
		y = self.SH / 2 - 900 / 2
		self.win.geometry('%dx%d+%d+%d' % (1280, 900, x, y))

		init_img = Image.open(r'readpic.png')
		self.img = ImageTk.PhotoImage(init_img)

		self.label = tkinter.Label(self.win, image=self.img)
		self.label.grid(row=0, column=0, columnspan=4, sticky=tkinter.NSEW)
		self.button_1 = \
			tkinter.Button(self.win, text='use file', command=lambda: thread_func(self.use_file), font=('Consolas', 20, 'bold'), width=30, height=3, bd=5)
		self.button_2 = \
			tkinter.Button(self.win, text='use dir ', command=lambda: thread_func(self.use_dir), font=('Consolas', 20, 'bold'), width=30, bd=5)
		self.button_1.grid(row=1, column=0, rowspan=2, sticky=tkinter.NSEW)
		self.button_2.grid(row=1, column=1, rowspan=2, sticky=tkinter.NSEW)

		self.button_3 = \
			tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_1, height=480, width=400, bd=1)
		self.button_4 = \
			tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_2, height=480, width=400, bd=1)
		self.button_5 = \
			tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_3, height=480, width=400, bd=1)

		self.status = tkinter.IntVar()
		self.text = tkinter.StringVar()
		self.text_label = tkinter.Label(self.win, textvariable=self.text, font=('Consolas', 20, 'bold'), width=35, height=3)
		self.radiobutton_1 = \
			tkinter.Radiobutton(self.win, text='On', variable=self.status, value=1, font=('Consolas', 20, 'bold'), width=5, command=self.change_label)
		self.radiobutton_2 = \
			tkinter.Radiobutton(self.win, text='Off', variable=self.status, value=0, font=('Consolas', 20, 'bold'), command=self.change_label)

		Mem = float(psutil.virtual_memory().total)/1024/1024/1024
		if Mem > 16:
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
		self.run()

	def run(self):
		self.win.bind('<Up>', self.show_last_img)
		self.win.bind('<Right>', self.show_next_img)
		self.win.bind('<Down>', self.show_next_img)
		self.win.bind('<Left>', self.show_last_img)

		self.win.bind('<Tab>', self.jump)
		self.win.bind('<Escape>', self.reload)
		self.win.protocol("WM_DELETE_WINDOW", self.close_)

		self.button_3.bind('<MouseWheel>', self.mouse_img)
		self.button_4.bind('<MouseWheel>', self.mouse_img)
		self.button_5.bind('<MouseWheel>', self.mouse_img)
		# print(self.SW)
		# print(self.SH)

		self.win.mainloop()

	def change_label(self):
		if self.status.get():
			self.text.set('Low Memory Mode: On')
			self.text_label.configure(bg='green')
		else:
			self.text.set('Low Memory Mode: Off')
			self.text_label.configure(bg='gray')

	def change_grid(self):
		self.button_1.destroy()
		self.button_2.destroy()
		self.radiobutton_1.destroy()
		self.radiobutton_2.destroy()
		self.text_label.destroy()

		self.label.grid(row=0, column=1, rowspan=3, sticky=tkinter.NSEW)
		self.button_3.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.button_4.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.button_5.grid(row=2, column=0, sticky=tkinter.NSEW)
		self.label.configure(height=9, width=2000)
		x = self.SW / 2 - 2400 / 2
		y = self.SH / 2 - 1440 / 2
		self.win.geometry('%dx%d+%d+%d' % (2400, 1440, x, y))

	def show_img(self):
		img_key = self.key_list[self.id_]
		button_id_1 = self.button_id_
		if button_id_1 == self.length - 1:
			self.button_id_2 = 0
			self.button_id_3 = 1
		elif button_id_1 == self.length - 2:
			self.button_id_2 = button_id_1 + 1
			self.button_id_3 = 0
		else:
			self.button_id_2 = button_id_1 + 1
			self.button_id_3 = button_id_1 + 2

		if self.status.get():
			self.show_img_low()
			return

		img_k_1, img_k_2, img_k_3 = self.key_list[button_id_1], self.key_list[self.button_id_2], self.key_list[
			self.button_id_3]
		self.img = ImageTk.PhotoImage(self.img_dict[img_key][0])
		self.img_1, self.img_2, self.img_3 = ImageTk.PhotoImage(self.img_dict[img_k_1][1]), ImageTk.PhotoImage(self.img_dict[img_k_2][1]), ImageTk.PhotoImage(self.img_dict[img_k_3][1])
		title_ = '{name}--{i}/{l}'.format(name=self.key_list[self.id_].split('\\')[-2], i=self.id_, l=self.length)
		self.win.title(title_)
		self.label.configure(image=self.img)
		self.button_3.configure(image=self.img_1)
		self.button_4.configure(image=self.img_2)
		self.button_5.configure(image=self.img_3)

	def show_img_low(self):
		img_key = self.key_list[self.id_]
		img_k_1, img_k_2, img_k_3 = self.key_list[self.button_id_], self.key_list[self.button_id_2], self.key_list[
			self.button_id_3]
		self.img = ImageTk.PhotoImage(get_img(img_key)[0])
		self.img_1, self.img_2, self.img_3 = ImageTk.PhotoImage(get_img(img_k_1)[1]), ImageTk.PhotoImage(get_img(img_k_2)[1]), ImageTk.PhotoImage(get_img(img_k_3)[1])
		title_ = '{name}--{i}/{l}'.format(name=self.key_list[self.id_].split('\\')[-2], i=self.id_, l=self.length)
		self.win.title(title_)
		self.label.configure(image=self.img)
		self.button_3.configure(image=self.img_1)
		self.button_4.configure(image=self.img_2)
		self.button_5.configure(image=self.img_3)

	def load_img(self):
		if self.status.get():
			self.length = len(self.file_list)
			return

		threads = [threading.Thread(target=lambda q, file_name, i, total: q.put(sub_loader(file_name, i, total)), args=(self.q, self.file_list, i, self.thread_num)) for i in range(self.thread_num + 1)]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		while not self.q.empty():
			for item in self.q.get():
				self.img_dict[item[-1]] = (item[0], item[1])
		self.length = len(self.img_dict.keys())

	def sort_img(self):
		level = max([len(x.split('\\')) for x in self.file_list])
		new_file_list = []
		for file in self.file_list:
			file_split = file.split('\\')
			if len(file_split) == level:
				new_file_list.append(file)
			else:
				ext = ['OutOfRange'] * (level - len(file_split))
				new_file_list.append('\\'.join(file_split[:-1] + ext + [file_split[-1]]))

		convert = [new_file_list]
		lvl = 1
		while lvl < level:
			sub = []
			for to_be_sort in convert:
				to_be_sort.sort(key=lambda x: encode(x.split('\\')[lvl]))
				search_length = len(to_be_sort)

				while search_length >= 1:
					sub_list = []
					__path = to_be_sort[0].split('\\')[:lvl]
					for i in range(search_length - 1, -1, -1):
						if to_be_sort[i].split('\\')[:lvl] == __path:
							sub_list.append(to_be_sort.pop(i))
					sub.append(sub_list)

					search_length = len(to_be_sort)

			convert = sub
			lvl = lvl + 1
		raw_key_list = flatten(convert)
		self.key_list = [i.replace('\\OutOfRange', '') for i in raw_key_list]
		self.key_list.reverse()

	def use_file(self):
		if not self.flag:
			if self.status.get():
				self.content = askopenfilename(filetypes=[('content text', '*.txt')])
			else:
				self.content = askopenfilename(filetypes=[('DataBase file', '*.db'), ('content text', '*.txt')])
			if self.content:
				self.flag = True
			else:
				return
		else:
			return
		try:
			self.radiobutton_1.configure(state=tkinter.DISABLED)
			self.radiobutton_2.configure(state=tkinter.DISABLED)
		except TclError:
			pass

		# for fast load here:
		if self.content.split('.')[-1] == 'db':
			x = self.SW / 2 - 600 / 2
			y = self.SH / 2 - 200 / 2
			toplevel = toplevel_with_bar(600, 200, x, y, 'Loading...', 'Now loading db file...')
			with open(self.content, 'rb') as loader:
				self.key_list, self.img_dict, self.id_ = dill.load(loader)
			self.button_id_ = self.id_
			self.length = len(self.key_list)
			try:
				toplevel.destroy()
			except RuntimeError:
				exit()
		else:
			self.dir_path = '\\'.join(self.content.split('/')[:-1])
			with open(self.content, 'r', encoding='utf-8') as file:
				while True:
					this_line = file.readline()

					if not this_line:
						break

					if this_line[-1] == '\n':
						this_line = this_line[:-1]

					self.file_list.append(this_line)
			try:
				self.button_id_ = self.id_ = int(self.file_list[-1])
				self.file_list = self.file_list[:-1]
			except ValueError:
				pass

			x = self.SW / 2 - 600 / 2
			y = self.SH / 2 - 200 / 2
			toplevel = toplevel_with_bar(600, 200, x, y, 'Loading...', 'Now loading images...')
			self.load_img()
			self.sort_img()
			try:
				toplevel.destroy()
			except RuntimeError:
				exit()

		self.change_grid()

		try:
			self.show_img()
		except IndexError:
			self.button_id_ = self.id_ = 0
			self.show_img()
		self.finished = True

	def use_dir(self):
		if not self.flag:
			self.dir_path = askdirectory()
			if self.dir_path:
				self.flag = True
			else:
				return
		else:
			return
		try:
			self.radiobutton_1.configure(state=tkinter.DISABLED)
			self.radiobutton_2.configure(state=tkinter.DISABLED)
		except TclError:
			pass

		for __dir_path, __dir_name, __file_names in os.walk(self.dir_path):
			__dir_path = '\\'.join(__dir_path.split('/'))
			for __file_name in __file_names:
				img_file = '\\'.join([__dir_path, __file_name])
				extent = __file_name.split('.')[-1].lower()
				if extent in ['png', 'jpg', 'jpeg'] and os.path.getsize(img_file) > 2e5:
					self.file_list.append(img_file)

		self.length = len(self.file_list)
		self.content = '\\'.join([self.dir_path, 'content.txt'])

		x = self.SW / 2 - 600 / 2
		y = self.SH / 2 - 200 / 2
		toplevel = toplevel_with_bar(600, 200, x, y, 'Loading...', 'Now loading images...')
		self.load_img()
		self.sort_img()

		with open(self.content, 'w', encoding='utf-8') as file:
			for i in self.key_list:
				to_file = i + '\n'
				file.write(to_file)
			file.write('0\n')
		try:
			toplevel.destroy()
		except RuntimeError:
			exit()

		self.change_grid()

		try:
			self.show_img()
		except IndexError:
			self.button_id_ = self.id_ = 0
			self.show_img()
		self.finished = True

	def mouse_img(self, event):
		if not self.finished:
			return
		if event.delta > 0:
			self.button_id_ -= 1
			if self.button_id_ < 0:
				self.button_id_ = self.length - 1
		else:
			self.button_id_ += 1
			if self.button_id_ > self.length - 1:
				self.button_id_ = 0
		self.show_img()

	def show_next_img(self, event):
		if not self.finished:
			return
		self.id_ += 1
		if self.id_ > self.length - 1:
			self.id_ = 0

		self.button_id_ = self.id_
		self.show_img()

	def show_last_img(self, event):
		if not self.finished:
			return
		self.id_ -= 1
		if self.id_ < 0:
			self.id_ = self.length - 1

		self.button_id_ = self.id_
		self.show_img()

	def jump(self, event):
		if not self.finished:
			return

		go_to = askstring(title='pages', prompt='pages')

		if go_to == 'Fast Save':
			if self.content.split('.')[-1] == 'db' or self.status.get():
				return

			self.fastSaving = True
			save_path = '\\'.join(self.dir_path.split('/') + ['fastSave.db'])
			x = self.SW / 2 - 800 / 2
			y = self.SH / 2 - 200 / 2
			toplevel = toplevel_with_bar(600, 200, x, y, 'Saving...', 'Now saving db file in \n ..\\fastSave.db')
			__save_data = (self.key_list, self.img_dict, self.id_)

			def fast_save():
				with open(save_path, 'wb') as save:
					dill.dump(__save_data, save)
				try:
					toplevel.destroy()
					self.fastSaving = False
				except RuntimeError:
					exit()

			thread_func(fast_save)
			return

		try:
			ret = re.match('[+-]*[0-9]*', go_to)
		except TypeError:
			return

		try:
			want = ret.group()
			if '+' in want:
				self.id_ += int(want.strip('+'))
			elif '-' in want:
				self.id_ -= int(want.strip('-'))
				if self.id_ < 0:
					self.id_ += self.length
			else:
				self.id_ = int(want)
		except AttributeError:
			return

		try:
			self.id_ = self.id_ % self.length

			self.button_id_ = self.id_
			self.show_img()
		except TypeError:
			pass

	def change_img_1(self):
		self.id_ = self.button_id_
		self.show_img()

	def change_img_2(self):
		self.id_ = self.button_id_2
		self.show_img()

	def change_img_3(self):
		self.id_ = self.button_id_3
		self.show_img()

	def reload(self, event):
		if not self.finished:
			return
		x = self.SW / 2 - 400 / 2
		y = self.SH / 2 - 200 / 2
		toplevel = tkinter.Toplevel()
		toplevel.title('Reload')
		toplevel.geometry('%dx%d+%d+%d' % (400, 200, x, y))

		def re_f():
			self.finished = False
			self.flag = False
			self.file_list = []
			self.key_list = []
			self.img_dict = {}
			while not self.flag:
				self.use_file()
			toplevel.destroy()

		def re_d():
			self.finished = False
			self.flag = False
			self.file_list = []
			self.key_list = []
			self.img_dict = {}
			while not self.flag:
				self.use_dir()
			toplevel.destroy()

		button_f = tkinter.Button(toplevel, text='Use file', command=lambda: thread_func(re_f), font=('Consolas', 20, 'bold'), height=3)
		button_d = tkinter.Button(toplevel, text='Use dir ', command=lambda: thread_func(re_d), font=('Consolas', 20, 'bold'), height=3)

		button_f.grid(row=0, column=0)
		button_d.grid(row=0, column=1)

		toplevel.grid_rowconfigure(0, weight=1)
		toplevel.grid_columnconfigure(0, weight=1)
		toplevel.grid_columnconfigure(1, weight=1)

	def close_(self):
		if self.flag and not self.finished:
			return
		if self.fastSaving:
			return
		if self.content.split('.')[-1] == 'db':
			pass
		else:
			try:
				with open(self.content, 'w+', encoding='utf-8') as file:
					self.key_list.append(str(self.id_))
					for i in self.key_list:
						to_file = i + '\n'
						file.write(to_file)
			except FileNotFoundError:
				pass
		self.win.destroy()
		exit()


if __name__ == '__main__':
	reader = Reader()

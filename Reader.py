import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import freeze_support
from queue import Queue
from sys import exit
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import showerror, askokcancel
from tkinter.simpledialog import askstring

import dill
import psutil
from _tkinter import TclError
from ttkbootstrap import Meter

from GifReader import Reader as GifReader
from UI.Reader_UI import *
from tools import json_path, path_str, CPU_NUM, tools, psd, HandleFileError


# noinspection PyArgumentList
class Reader(ReaderUI):
	def __init__(self):
		super().__init__()
		self.psd_toplevel = None
		self.record_for_scaling = 1
		self.NUM = CPU_NUM
		self.SHUT_DOWN = False
		self.stop_inf = None
		self.communication = Queue()

		self.content = ''
		self.dir_path = ''

		self.file_list = []
		self.img_dict = {}

		self.percent = 0
		self.length = 0
		self.img_index = 0
		self.img_key = None
		self.side_img_1_index = 0
		self.side_img_2_index = 0
		self.side_img_3_index = 0
		self.raw_img = None
		self.img = None
		self.side_img_1 = None
		self.side_img_2 = None
		self.side_img_3 = None
		self.main_c = None
		self.c_list = []
		self.ex_h = (1440, 480)
		self.ex_w = (1900, 400)

		with open(json_path, 'r', encoding='utf-8') as json_f:
			self.history = json.load(json_f)

		self.reader_status = {
			'FILE_NAME_LOAD': False,
			'LOAD_FINISH': False,
			'OLD_STYLE': False,
			'FAST_SAVE': False,
			'DRAG': False,
			'SCAL': False,
			'MEM_M': False,
			'SORTING': False,
			'FULL_FAST': False
		}

		self.run()

	def bind_command(self) -> None:
		self.tool_menu.add_command(label='Jump to', command=self.jump)
		self.tool_menu.add_command(label='Mem Monitor', command=self.mem)
		self.tool_menu.add_command(label='GIF Reader', command=self.gif_reader)
		self.tool_menu.add_command(label='Sorter', command=self.sorter)
		self.tool_menu.add_command(label='Touch', command=self.for_touch_reader)

		self.file_menu.add_command(label='Fast Save', command=self.main_fast_save)
		self.file_menu.add_command(label='Fast Save(Full size)', command=self.full_fast_save)
		self.file_menu.add_command(label='Reload', command=lambda: self.reload(None))
		self.file_menu.add_command(label='Get Back Pictures', command=self.withdraw)
		self.file_menu.add_command(label='Exit', command=self._close)

		self.themes_menu.add_command(
			label='Dark',
			command=lambda: self.change_theme(
				theme_name='darkly',
				size=self.font_size
			)
		)
		self.themes_menu.add_command(
			label='Light',
			command=lambda: self.change_theme(
				theme_name='litera',
				size=self.font_size
			)
		)

		self.convert_menu.add_command(label='PSD/Dir to PNG', command=self.psd)

		self.button_1.configure(command=lambda: tools.thread_func(self.use_file))
		self.button_2.configure(command=lambda: tools.thread_func(self.use_dir))

	def run(self) -> None:
		self.bind_command()
		self.win.bind('<Up>', self.show_last_img)
		self.win.bind('<Right>', self.show_next_img)
		self.win.bind('<Down>', self.show_next_img)
		self.win.bind('<Left>', self.show_last_img)

		self.win.bind('<Escape>', self.reload)
		self.win.protocol("WM_DELETE_WINDOW", self._close)

		self.side_canvas_1.bind('<MouseWheel>', self.img_by_mouse)
		self.side_canvas_1.bind('<Button-1>', lambda event: self.change_img(1, event))
		self.separator_h_1.bind('<MouseWheel>', self.img_by_mouse)
		self.side_canvas_2.bind('<MouseWheel>', self.img_by_mouse)
		self.side_canvas_2.bind('<Button-1>', lambda event: self.change_img(2, event))
		self.separator_h_2.bind('<MouseWheel>', self.img_by_mouse)
		self.side_canvas_3.bind('<MouseWheel>', self.img_by_mouse)
		self.side_canvas_3.bind('<Button-1>', lambda event: self.change_img(3, event))

		self.canvas.bind('<Button-1>', self.get_click)
		self.canvas.bind('<B1-Motion>', self.drag)
		self.canvas.bind('<Control-MouseWheel>', self.scaling)

		self.win.mainloop()

	def load_img(self, full_size=False) -> None:
		self.length = len(self.file_list)
		if self.status.get():
			return

		ratio = [self.scaling_ratio] * self.length
		full_size_list = [full_size] * self.length
		with ProcessPoolExecutor(self.NUM) as executor:
			load_result = executor.map(tools.get_img, self.file_list, ratio, full_size_list)

		for item in load_result:
			if item[-1] is None:
				continue
			self.img_dict[item[-1]] = [item[0], item[1]]

		self.file_list = list(self.img_dict.keys())

	def sort_img(self) -> None:
		try:
			max_depth = max([len(x.split(path_str)) for x in self.file_list])
		except ValueError:
			self.reload(None)
			return
		new_file_list = []
		for file in self.file_list:
			split_file = file.split(path_str)
			_len_file_name = len(split_file)
			if _len_file_name == max_depth:
				new_file_list.append(file)
			else:
				ext = ['OutOfRange'] * (max_depth - _len_file_name)
				new_file_list.append(path_str.join(split_file[:-1] + ext + [split_file[-1]]))

		convert = [new_file_list]
		depth = 1
		while depth < max_depth:
			sub = []
			for to_be_sort in convert:
				to_be_sort.sort(key=lambda x: tools.encode(x.split(path_str)[depth]))
				search_length = len(to_be_sort)
				while search_length >= 1:
					sub_list = []
					_path = to_be_sort[0].split(path_str)[:depth]
					for i in range(search_length - 1, -1, -1):
						if to_be_sort[i].split(path_str)[:depth] == _path:
							sub_list.append(to_be_sort.pop(i))
					sub.append(sub_list)

					search_length = len(to_be_sort)
			convert = sub
			depth = depth + 1

		raw_sorted_list = tools.flatten(convert)
		self.file_list = [i.replace(path_str + 'OutOfRange', '') for i in raw_sorted_list]
		self.file_list.reverse()

	def sorter(self) -> None:
		if not self.reader_status['LOAD_FINISH'] \
				or self.reader_status['FAST_SAVE'] \
				or self.reader_status['FULL_FAST']:
			return
		self.reader_status['SORTING'] = True
		__command_str__ = askstring(title='Sort', prompt='Keyword')
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Loading...',
			f"Now sorting for {__command_str__}",
			self.scaling_ratio > 0.625
		)

		def func():
			try:
				self.file_list = tools.clip_sort(files=self.file_list, text=__command_str__)
				toplevel.destroy()
			except MemoryError:
				showerror(title='MemoryError!', message='Can not load CLIP Model.')
			except RuntimeError:
				exit()

			self.img_index = 1
			self.side_img_1_index = 1
			self.show_img(first=False)

		tools.thread_func(func)
		self.reader_status['SORTING'] = False

	def get_read_history(self) -> None:
		self.img_index = self.history.get(self.content, 0)
		self.side_img_1_index = self.img_index

	def show_img(self, first=False) -> None:
		self.img_index = self.img_index % self.length
		self.record_for_scaling = 1

		self.side_img_2_index = self.side_img_1_index + 1
		self.side_img_3_index = self.side_img_1_index + 2

		self.side_img_1_index = self.side_img_1_index % self.length
		self.side_img_2_index = self.side_img_2_index % self.length
		self.side_img_3_index = self.side_img_3_index % self.length

		refresh_main = first
		if self.img_key != self.file_list[self.img_index]:
			refresh_main = True
			self.img_key = self.file_list[self.img_index]

		img_k_1, img_k_2, img_k_3 = \
			self.file_list[self.side_img_1_index], self.file_list[self.side_img_2_index], self.file_list[
				self.side_img_3_index]

		if self.status.get() and self.content.split('.')[-1] != 'db':
			self.raw_img = tools.get_img(self.img_key, self.scaling_ratio)[0]
			img_2 = tools.get_img(img_k_1, self.scaling_ratio)[1]
			img_3 = tools.get_img(img_k_2, self.scaling_ratio)[1]
			img_4 = tools.get_img(img_k_3, self.scaling_ratio)[1]
		else:
			self.raw_img = self.img_dict[self.img_key][0]
			img_2 = self.img_dict[img_k_1][1]
			img_3 = self.img_dict[img_k_2][1]
			img_4 = self.img_dict[img_k_3][1]

		self.side_img_1, self.side_img_2, self.side_img_3 = \
			ImageTk.PhotoImage(img_2), ImageTk.PhotoImage(img_3), ImageTk.PhotoImage(img_4)
		title_ = '{name}--{i}/{l}'.format(
			name=self.file_list[self.img_index].split(path_str)[-2],
			i=self.img_index,
			l=self.length
		)
		self.win.title(title_)

		canvases_t = [
			(self.side_canvas_1, self.side_img_1),
			(self.side_canvas_2, self.side_img_2),
			(self.side_canvas_3, self.side_img_3)
		]
		for i in range(min(self.length, 3)):
			c, img = canvases_t[i]
			c.itemconfig(self.c_list[i], image=img)

		if refresh_main:
			self.img = ImageTk.PhotoImage(self.raw_img)
			self.canvas.itemconfig(self.main_c, image=self.img)
			self.canvas.config(scrollregion=self.canvas.bbox("all"))

	def get_file_name(self, mode: str) -> None:
		if self.reader_status.get('FILE_NAME_LOAD'):
			raise HandleFileError

		if mode == 'file':
			self.content = askopenfilename(
				filetypes=[
					('DataBase file', '*.db'),
					('DataBase file (in full size)', '*.dbx'),
					('PNG, JPG, JPEG files', '*.png'),
					('PNG, JPG, JPEG files', '*.jpg'),
					('PNG, JPG, JPEG files', '*.jpeg')
				]
			)
			if not self.content:
				raise HandleFileError
			self.dir_path = path_str.join(self.content.split('/')[:-1])
			self.content = path_str.join(self.content.split('/'))
		else:
			self.dir_path = askdirectory()
			self.dir_path = path_str.join(self.dir_path.split('/'))
			if not self.dir_path:
				raise HandleFileError
			self.content = path_str.join([self.dir_path, 'content.txt'])
		self.reader_status['FILE_NAME_LOAD'] = True

		try:
			self.radiobutton_1.configure(state=tkinter.DISABLED)
			self.radiobutton_2.configure(state=tkinter.DISABLED)
		except TclError:
			pass

	def push_img(self, toplevel: tkinter.Toplevel) -> None:
		try:
			toplevel.destroy()
		except RuntimeError:
			exit()
		self.get_read_history()
		self.change_grid()

		self.canvas.delete('all')
		self.side_canvas_1.delete('all')
		self.side_canvas_2.delete('all')
		self.side_canvas_3.delete('all')

		self.main_c = self.canvas.create_image(
			self.main_canvas_w,
			self.main_canvas_h,
			image=self.init_img_tk,
			anchor="center"
		)
		self.c_list = [
			self.side_canvas_1.create_image(
				self.side_canvas_w,
				self.side_canvas_h,
				image=self.init_img_tk,
				anchor="center"
			),
			self.side_canvas_2.create_image(
				self.side_canvas_w,
				self.side_canvas_h,
				image=self.init_img_tk,
				anchor="center"
			),
			self.side_canvas_3.create_image(
				self.side_canvas_w,
				self.side_canvas_h,
				image=self.init_img_tk,
				anchor="center")
		]
		if self.length == 2:
			self.side_canvas_3.delete('all')
		elif self.length == 1:
			self.side_canvas_2.delete('all')
			self.side_canvas_3.delete('all')

		self.show_img(first=True)
		self.reader_status['LOAD_FINISH'] = True

	def _reshape_db(self) -> bool:
		s_w, b_w = self.ex_w
		ex_ratio = b_w / 400

		if self.reader_status['OLD_STYLE']:
			if str(self.scaling_ratio)[:2] == str(ex_ratio)[:2]:
				return False
			ratio = self.scaling_ratio / ex_ratio
			for key, value in self.img_dict.items():
				self.img_dict[key] = list(self.img_dict[key])
				img, button = self.img_dict[key]
				b_w, b_h = button.size
				i_w, i_h = img.size
				self.img_dict[key][1] = self.img_dict[key][1].resize((int(b_w * ratio), int(b_h * ratio)))
				self.img_dict[key][0] = self.img_dict[key][0].resize((int(i_w * ratio), int(i_h * ratio)))
		elif self.content.split(".")[-1] == 'db':
			if str(self.scaling_ratio)[:2] == str(ex_ratio)[:2]:
				return False
			ratio = self.scaling_ratio / ex_ratio
			for key, value in self.img_dict.items():
				img, button = self.img_dict[key]
				b_w, b_h = button.size
				i_w, i_h = img.size
				self.img_dict[key][1] = self.img_dict[key][1].resize((int(b_w * ratio), int(b_h * ratio)))
				self.img_dict[key][0] = self.img_dict[key][0].resize((int(i_w * ratio), int(i_h * ratio)))
		else:
			ratio_b = self.scaling_ratio / ex_ratio
			for key, value in self.img_dict.items():
				img, button = self.img_dict[key]
				b_w, b_h = button.size
				i_w, i_h = img.size
				ratio = 1440 * self.scaling_ratio / i_h if i_h >= i_w else 1900 * self.scaling_ratio / i_w
				self.img_dict[key][1] = self.img_dict[key][1].resize((int(b_w * ratio_b), int(b_h * ratio_b)))
				self.img_dict[key][0] = self.img_dict[key][0].resize((int(i_w * ratio), int(i_h * ratio)))

		return True

	def use_file(self) -> None:
		try:
			self.get_file_name(mode='file')
		except HandleFileError:
			return
		if self.content.split('.')[-1] not in ['db', 'dbx']:
			toplevel = toplevel_with_bar(
				self.toplevel_w,
				self.toplevel_h,
				self.toplevel_x,
				self.toplevel_y,
				'Loading...',
				f"Now loading {self.content.split('.')[-1]} file...",
				self.scaling_ratio > 0.625
			)
			self.file_list = [self.content]
			self.load_img()
			self.push_img(toplevel=toplevel)

			return
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Loading...',
			f'Now loading {self.content.split(".")[-1]} file...',
			self.scaling_ratio > 0.625
		)
		try:
			with open(self.content, 'rb') as loader:
				self.file_list, self.img_dict, temp, self.ex_h, self.ex_w = dill.load(loader)
			self._reshape_db()
		except ValueError:
			self.reader_status['OLD_STYLE'] = True
			with open(self.content, 'rb') as loader:
				self.file_list, self.img_dict, temp = dill.load(loader)
				self._reshape_db()
		except MemoryError:
			self.reload(None)
			return

		self.length = len(self.file_list)

		self.push_img(toplevel=toplevel)

	def use_dir(self) -> None:
		try:
			self.get_file_name(mode='dir')
		except HandleFileError:
			return

		for __dir_path, __dir_name, __file_names in os.walk(self.dir_path):
			__dir_path = path_str.join(__dir_path.split('/'))
			for __file_name in __file_names:
				img_file = path_str.join([__dir_path, __file_name])
				extent = __file_name.split('.')[-1].lower()
				if extent in ['png', 'jpg', 'jpeg'] and os.path.getsize(img_file) > 2e5:
					self.file_list.append(img_file)

		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Loading...',
			'Now loading images...',
			self.scaling_ratio > 0.625
		)

		self.load_img()
		self.sort_img()

		self.push_img(toplevel=toplevel)

	def reload(self, event) -> None:
		if not self.reader_status.get('FILE_NAME_LOAD'):
			return
		if self.reader_status['FAST_SAVE'] or self.reader_status['FULL_FAST']:
			return

		def sub_reload_func(mode: str, _toplevel: tkinter.Toplevel) -> None:
			self.file_list = []
			self.img_dict = {}
			self.ex_h = (1440, 480)
			self.ex_w = (1900, 400)
			self.reader_status['LOAD_FINISH'] = False
			self.reader_status['OLD_STYLE'] = False
			self.reader_status['FILE_NAME_LOAD'] = False
			if mode == 'file':
				func = self.use_file
			else:
				func = self.use_dir
			while not self.reader_status.get('FILE_NAME_LOAD'):
				func()
			_toplevel.destroy()

		x = self.SW / 2 - 400 * self.scaling_ratio / 2
		y = self.SH / 2 - 200 * self.scaling_ratio / 2
		toplevel = tkinter.Toplevel()
		toplevel.title('Reload')
		toplevel.geometry('%dx%d+%d+%d' % (400 * self.scaling_ratio, 200 * self.scaling_ratio, x, y))

		button_f = ttk.Button(
			toplevel,
			text='With File',
			command=lambda: tools.thread_func(sub_reload_func, {'mode': 'file', '_toplevel': toplevel}),
			bootstyle=('success', 'outline')
		)
		button_d = ttk.Button(
			toplevel,
			text='With Dir ',
			command=lambda: tools.thread_func(sub_reload_func, {'mode': 'dir', '_toplevel': toplevel}),
			bootstyle=('success', 'outline')
		)

		button_f.grid(row=0, column=0)
		button_d.grid(row=0, column=1)

		toplevel.grid_rowconfigure(0, weight=1)
		toplevel.grid_columnconfigure(0, weight=1)
		toplevel.grid_columnconfigure(1, weight=1)
		toplevel.resizable(False, False)

	def img_by_mouse(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.length <= 3 or self.reader_status['FULL_FAST']:
			return
		self.side_img_1_index = self.side_img_1_index - 1 if event.delta > 0 else self.side_img_1_index + 1

		self.show_img()

	def show_next_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['FULL_FAST']:
			return
		self.img_index += 1
		if self.length > 3:
			self.side_img_1_index = self.img_index
		self.show_img()

	def show_last_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['FULL_FAST']:
			return
		self.img_index -= 1
		if self.length > 3:
			self.side_img_1_index = self.img_index
		self.side_img_1_index = self.img_index
		self.show_img()

	def main_fast_save(self) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.status.get():
			return

		if self.reader_status['FAST_SAVE'] or self.reader_status['FULL_FAST']:
			return

		if self.content.split('.')[-1] == 'db':
			fast_save = '.'.join(self.content.split(path_str)[-1].split('.')[:-1])
		else:
			fast_save = self.content.split(path_str)[-2]
		self.reader_status['FAST_SAVE'] = True

		save_dir = askdirectory()
		if not save_dir:
			self.reader_status['FAST_SAVE'] = False
			return
		save_dir = path_str.join(save_dir.split('/'))

		save_path = path_str.join([save_dir, f'{fast_save}.db'])
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Saving...',
			f'Now saving db file in \n ..{save_path}',
			self.scaling_ratio > 0.625
		)
		__save_data = (
			self.file_list,
			self.img_dict,
			self.img_index,
			(int(1900 * self.scaling_ratio), int(480 * self.scaling_ratio)),
			(int(1440 * self.scaling_ratio), int(400 * self.scaling_ratio))
		)

		def fast_save():
			with open(save_path, 'wb') as save:
				dill.dump(__save_data, save)
			try:
				toplevel.destroy()
				self.reader_status['FAST_SAVE'] = False
			except RuntimeError:
				exit()

		tools.thread_func(fast_save)
		return

	def full_fast_save(self) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.status.get():
			return
		if self.reader_status['FAST_SAVE'] or self.reader_status['FULL_FAST']:
			return

		if self.content.split('.')[-1] == 'db':
			fast_save = '.'.join(self.content.split(path_str)[-1].split('.')[:-1])
		elif self.content.split('.')[-1] == 'dbx':
			showerror(message='dbx file has been loaded!')
			self.reader_status['FULL_FAST'] = False
			return
		else:
			fast_save = self.content.split(path_str)[-2]

		message = '''Continuing the operation will block the program until the conversion is complete.You will need to reload the folder when the conversion is complete.sure?'''
		answer = askokcancel('Warning!', message=message)
		if not answer:
			self.reader_status['FULL_FAST'] = False
			return

		self.reader_status['FULL_FAST'] = True
		save_dir = askdirectory()
		if not save_dir:
			self.reader_status['FULL_FAST'] = False
			return
		save_dir = path_str.join(save_dir.split('/'))

		save_path = path_str.join([save_dir, f'{fast_save}.dbx'])
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Saving...', f'Now saving dbx file in \n ..{save_path}',
			self.scaling_ratio > 0.625
		)

		def fast_save():
			self.img_dict = {}

			self.load_img(full_size=True)
			__save_data = (
				self.file_list,
				self.img_dict,
				self.img_index,
				(int(1900 * self.scaling_ratio), int(480 * self.scaling_ratio)),
				(int(1440 * self.scaling_ratio), int(400 * self.scaling_ratio))
			)

			with open(save_path, 'wb') as save:
				dill.dump(__save_data, save)
			try:
				toplevel.destroy()
				self.reader_status['FULL_FAST'] = False
				self.reload(None)
			except RuntimeError:
				exit()

		tools.thread_func(fast_save)

	def psd(self) -> None:

		def sub_load_func(mode):
			psd_content = None
			if mode == 'file':
				psd_content = askopenfilename()
			elif mode == 'dir':
				psd_content = askdirectory()

			if not psd_content:
				return
			try:
				psd_helper = psd.PSDHelper(psd_content)
			except HandleFileError:
				return
			toplevel.destroy()
			top = toplevel_with_bar(
				self.toplevel_w,
				self.toplevel_h,
				self.toplevel_x,
				self.toplevel_y,
				'Converting',
				'Now converting PSD Files...',
				self.scaling_ratio > 0.625
			)

			def sub_run():
				psd_helper.run()
				top.destroy()

			tools.thread_func(sub_run)

		toplevel = tkinter.Toplevel()
		toplevel.title('Converting PSD Files')
		x = self.SW / 2 - 400 * self.scaling_ratio / 2
		y = self.SH / 2 - 200 * self.scaling_ratio / 2
		toplevel.geometry('%dx%d+%d+%d' % (400 * self.scaling_ratio, 200 * self.scaling_ratio, x, y))

		button_f = ttk.Button(
			toplevel,
			text='With File',
			command=lambda: tools.thread_func(sub_load_func, {'mode': 'file'}),
			bootstyle=('success', 'outline'))
		button_d = ttk.Button(
			toplevel, text='With Dir ',
			command=lambda: tools.thread_func(sub_load_func, {'mode': 'dir'}),
			bootstyle=('success', 'outline'))

		button_f.grid(row=0, column=0)
		button_d.grid(row=0, column=1)
		toplevel.grid_rowconfigure(0, weight=1)
		toplevel.grid_columnconfigure(0, weight=1)
		toplevel.grid_columnconfigure(1, weight=1)

		toplevel.resizable(False, False)

	def mem(self) -> None:
		if self.reader_status['MEM_M']:
			return
		else:
			self.reader_status['MEM_M'] = True
			self.SHUT_DOWN = False

		top = tkinter.Toplevel(self.win)
		top.title('Memory Monitor')
		top.geometry('%dx%d+%d+%d' % (
			self.toplevel_w-400,
			self.toplevel_h,
			self.toplevel_x+200,
			self.toplevel_y))

		top.resizable(False, False)
		meter = Meter(
			top,
			metersize=180,
			padding=10,
			metertype='semi',
			subtext='Memory Usage',
			interactive=False,
			textright='%',
			meterthickness=20
		)

		def _get_mem(m):
			while True:
				if self.SHUT_DOWN:
					break
				mem = psutil.virtual_memory()
				per = mem.percent
				try:
					m.configure(amountused=per)
				except TclError:
					pass

		tools.thread_func(_get_mem, {'m': meter})
		meter.pack()

		def _stop_inf():
			self.SHUT_DOWN = True
			self.reader_status['MEM_M'] = False
			top.destroy()

		self.stop_inf = _stop_inf
		top.protocol("WM_DELETE_WINDOW", _stop_inf)

	def jump(self) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		if self.reader_status['FULL_FAST']:
			return
		__command_str__ = askstring(title='Jump to', prompt='Page:')

		try:
			__lower_command_str__ = __command_str__.lower()
		except AttributeError:
			return

		if not self.reader_status['LOAD_FINISH']:
			return
		try:
			ret = re.match('[+-]*[0-9]*', __command_str__)
		except TypeError:
			return

		try:
			want = ret.group()
			if '+' in want:
				self.img_index += int(want.strip('+'))
			elif '-' in want:
				self.img_index -= int(want.strip('-'))
			else:
				self.img_index = int(want) - 1
		except AttributeError:
			return
		except ValueError:
			return

		self.side_img_1_index = self.img_index
		self.show_img()

	def withdraw(self) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.content.split('.')[-1] not in ['db', 'dbx']:
			return
		if self.reader_status['FAST_SAVE'] or self.reader_status['FULL_FAST']:
			return

		save_dir = askdirectory()
		if not save_dir:
			self.reader_status['FAST_SAVE'] = False
			return
		save_dir = path_str.join(save_dir.split('/'))

		back_toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Converting...',
			'Now converting db-files to pictures',
			self.scaling_ratio > 0.625
		)
		path_list = [file_name.split(path_str) for file_name in self.file_list]
		common_prefix = tools.find_longest_common_prefix(path_list)[:-1]
		to_replace = path_str.join(common_prefix)

		def back_run():
			for filename in self.file_list:
				save_filename = filename.replace(to_replace, save_dir)
				try:
					self.img_dict[filename][0].save(save_filename)
				except FileNotFoundError:
					os.makedirs(path_str.join(save_filename.split(path_str)[:-1]))
					self.img_dict[filename][0].save(save_filename)
				except FileExistsError:
					pass
			back_toplevel.destroy()

		tools.thread_func(back_run)

	def change_img(self, _id: int, event) -> None:
		if self.reader_status['FULL_FAST']:
			return

		if _id == 1:
			self.img_index = self.side_img_1_index
		elif _id == 2:
			self.img_index = self.side_img_2_index
		elif _id == 3:
			self.img_index = self.side_img_3_index
		self.show_img()

	def get_click(self, event) -> None:
		self.canvas.scan_mark(event.x, event.y)

	def drag(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['SCAL']:
			return
		if self.reader_status['FULL_FAST']:
			return

		self.reader_status['DRAG'] = True
		self.canvas.scan_dragto(event.x, event.y, gain=1)
		self.reader_status['DRAG'] = False

	def scaling(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['DRAG']:
			return
		if self.reader_status['FULL_FAST']:
			return

		self.reader_status['SCAL'] = True

		if event.delta > 0:
			self.record_for_scaling *= 1.1
		else:
			self.record_for_scaling /= 1.1

		if self.record_for_scaling > 2:
			self.record_for_scaling = 2
		elif self.record_for_scaling < 0.2:
			self.record_for_scaling = 0.2

		w, h = self.raw_img.size
		img = self.raw_img.resize((int(w * self.record_for_scaling), int(h * self.record_for_scaling)))
		self.img = ImageTk.PhotoImage(img)

		self.canvas.itemconfig(self.main_c, image=self.img)
		self.canvas.config(scrollregion=self.canvas.bbox("all"))

		self.reader_status['SCAL'] = False

	def gif_reader(self) -> None:
		directory = askdirectory()
		if not directory:
			return
		directory = path_str.join(directory.split('/'))
		sub_reader = GifReader(
			self.win,
			self.SW,
			self.SH,
			self.side_color,
			self.init_img_tk,
			directory,
			self.history)
		sub_reader.run()

	def for_touch_reader(self) -> None:
		toplevel = tkinter.Toplevel()
		x = self.SW / 2 + 2400 * self.scaling_ratio / 2 - 400
		y = self.SH / 2 + 1440 * self.scaling_ratio / 2 - 200
		toplevel.geometry('%dx%d+%d+%d' % (400, 250, x, y))
		toplevel.resizable(False, False)
		frame = ttk.Frame(toplevel)
		frame.pack(fill='y')
		label__ = ttk.Label(frame)
		button_up = ttk.Button(
			frame,
			text='UP',
			width=20,
			bootstyle=('success', 'outline'),
			command=lambda: self.show_last_img(None)
		)
		label_ = ttk.Label(frame)
		button_down = ttk.Button(
			frame,
			text='DOWN',
			bootstyle=('success', 'outline'),
			command=lambda: self.show_next_img(None)
		)
		label__.grid(row=0)
		button_up.grid(row=1, sticky=tkinter.NSEW)
		label_.grid(row=2)
		button_down.grid(row=3, sticky=tkinter.NSEW)

		frame.grid_rowconfigure(1, minsize=90, weight=1)
		frame.grid_rowconfigure(3, minsize=90, weight=1)

	def _close(self) -> None:
		if (self.reader_status['FILE_NAME_LOAD'] and not self.reader_status['LOAD_FINISH'])\
				or self.reader_status['FAST_SAVE']:
			return
		if self.reader_status['FULL_FAST']:
			return

		if not self.stop_inf:
			pass
		else:
			self.stop_inf()
		self.history[self.content] = self.img_index
		self.history['theme_name'] = self.theme_name
		with open(json_path, 'w', encoding='utf-8') as file:
			json.dump(self.history, file)

		self.win.destroy()
		exit()


if __name__ == '__main__':
	freeze_support()
	reader = Reader()

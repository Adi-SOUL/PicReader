import io
import json
import os
import re
from hashlib import md5
from time import strftime, localtime

import ttkbootstrap
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import freeze_support
from sys import exit
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import showerror
from tkinter.simpledialog import askstring
from ttkbootstrap.scrolled import ScrolledFrame

import psutil
from _tkinter import TclError
from ttkbootstrap import Meter

from GifReader import Reader as GifReader
from UI.Reader_UI import *
from tools import json_path, path_str, CPU_NUM, MAGIC_NUM, tools, psd, HandleFileError

from sys import argv


# noinspection PyArgumentList
class Reader(ReaderUI):
	def __init__(self, double_click: str | None):
		super().__init__()
		self.argv_1 = double_click
		self.mode = ''
		self.record_for_scaling = 1
		self.NUM = CPU_NUM
		self.SHUT_DOWN = False
		self.stop_inf = None

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
		self.able_to_sort_by_time = True
		self.time_bytes_dict = {}

		with open(json_path, 'r', encoding='utf-8') as json_f:
			self.history = json.load(json_f)

		self.reader_status = {
			'FILE_NAME_LOAD': False,
			'LOAD_FINISH': False,
			'OLD_STYLE': False,
			'DRAG': False,
			'SCAL': False,
			'MEM_M': False,
			'SORTING': False,
			'FULL_FAST': False
		}

		self.run()

	def bind_command(self) -> None:
		self.tool_menu.add_command(label='Tree', command=self.tree)
		self.tool_menu.add_command(label='Jump to', command=self.jump)
		self.tool_menu.add_command(label='Mem Monitor', command=self.mem)
		self.tool_menu.add_command(label='GIF Reader', command=self.gif_reader)
		self.tool_menu.add_command(label='Sort by Keywords', command=self.sorter)
		self.tool_menu.add_command(label='Touch', command=self.for_touch_reader)

		self.file_menu.add_command(label='Pic to DBX', command=self.fast_save)
		self.file_menu.add_command(label='Reload', command=lambda: self.reload(None))
		self.file_menu.add_command(label='DBX to Pic', command=self.withdraw)
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

		self.sort_by_time_menu.add_command(label='Ascending', command=lambda: self.sort_by_time(order='ascending'))
		self.sort_by_time_menu.add_command(label='Descending', command=lambda: self.sort_by_time(order='descending'))

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

		tools.thread_func(self.check_arg)
		self.win.mainloop()

	def check_arg(self):
		if self.argv_1 is None:
			return

		if os.path.isfile(self.argv_1):
			extent = self.argv_1.split('.')[-1]
			if extent.lower() not in ['dbx', 'jpg', 'png', 'jpeg']:
				exit()
			else:
				self.use_file()
		else:
			self.use_dir()

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

	def sort_by_time(self, order: str) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['FULL_FAST']:
			return
		if order not in ['ascending', 'descending']:
			return
		if order == 'descending':
			reverse = True
		else:
			reverse = False

		self.reader_status['SORTING'] = True
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Loading...',
			f"Now sorting by time {order}",
			self.scaling_ratio > 0.625
		)

		def func():
			if self.mode == 'dir':
				self.file_list.sort(key=lambda x: tools.encode_with_time(x, None), reverse=reverse)
			elif self.mode == 'file':
				if self.able_to_sort_by_time:
					self.file_list.sort(key=lambda x: tools.encode_with_time(x, self.time_bytes_dict), reverse=reverse)
				else:
					toplevel.destroy()
					showerror(title='FileError!', message='Can not get time information from this DBX file.')
					return

			self.side_img_1_index = self.img_index = 0
			self.show_img(first=False)
			toplevel.destroy()

		tools.thread_func(func)
		self.reader_status['SORTING'] = False

	def sorter(self) -> None:
		if not self.reader_status['LOAD_FINISH'] \
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

			self.img_index = 0
			self.side_img_1_index = 0
			self.show_img(first=False)

		tools.thread_func(func)
		self.reader_status['SORTING'] = False

	def get_read_history(self) -> None:
		self.img_index = self.history.get(self.content, 0)
		self.side_img_1_index = self.img_index

	def show_img(self, first=False) -> None:
		self.img_index = self.img_index % self.length
		self.record_for_scaling = 1

		if self.length <= 3:
			self.side_img_1_index = 0

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

	def get_file_name(self) -> None:
		if self.reader_status.get('FILE_NAME_LOAD'):
			raise HandleFileError

		if self.mode == 'file':
			if self.argv_1 is not None:
				self.content = self.argv_1
				self.argv_1 = None
			else:
				self.content = askopenfilename(
					filetypes=[
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
		elif self.mode == 'dir':
			if self.argv_1 is not None:
				self.dir_path = self.argv_1
				self.argv_1 = None
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

		# reload tree view
		if self.tree_toplevel is not None:
			self.tree_toplevel.destroy()
			self.tree()

	def use_file(self) -> None:
		try:
			self.mode = 'file'
			self.get_file_name()
		except HandleFileError:
			return
		if self.content.split('.')[-1] != 'dbx':
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
			temp = []
			with open(self.content, 'rb') as f:
				f.seek(0, 0)
				file_md5 = md5()
				b_magic_num, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, 9))
				magic_num = b_magic_num.decode('utf-8')
				if magic_num != MAGIC_NUM:
					exit()

				test_bytes = f.read(8).lstrip(b'0')
				f.seek(9, 0)
				if test_bytes:
					test_bytes = f.read(16).lstrip(b'0').decode('utf-8')
					try:
						_ = int(test_bytes)
					except ValueError:
						INDEX_LENGTH = 4
						TOTAL_SIZE_LENGTH = 4
					else:
						INDEX_LENGTH = 8
						TOTAL_SIZE_LENGTH = 8
					f.seek(9, 0)
					IMG_SIZE_LENGTH = 16
				else:
					INDEX_LENGTH = 32
					TOTAL_SIZE_LENGTH = 128
					IMG_SIZE_LENGTH = 128

				n, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, INDEX_LENGTH))
				try:
					self.img_index = int(n.lstrip(b'0').decode('utf-8'))
				except ValueError:
					self.img_index = 0
				b_total_size, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, TOTAL_SIZE_LENGTH))
				total_size = int(b_total_size.lstrip(b'0').decode('utf-8'))
				self.length = total_size
				names = []
				sizes = []
				start = INDEX_LENGTH + TOTAL_SIZE_LENGTH + 9
				for i in range(total_size):
					b_file_name, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, 256))
					start += 256
					file_name = b_file_name.lstrip(b'0').decode('utf-8')
					b_size, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, IMG_SIZE_LENGTH))
					start += IMG_SIZE_LENGTH
					size = int(b_size.lstrip(b'0').decode('utf-8'))
					names.append(file_name)
					sizes.append(size)

				for size, name in zip(sizes, names):
					_, md5_value = next(tools.get_data_and_update_its_md5(file_md5, f, size))
					end = start + size
					temp.append([name, self.scaling_ratio, False, self.content, start, end])
					start += size

				read_md5_value = f.read(32).decode('utf-8')
				if read_md5_value != md5_value:
					exit()

				for file in names:
					time_bytes = f.read(14)
					if len(time_bytes) != 14:
						self.able_to_sort_by_time = False
						self.time_bytes_dict = {}
						break
					else:
						time_int = int(time_bytes.decode('utf-8'))
						self.time_bytes_dict[file] = time_int

			self.file_list = names
			with ProcessPoolExecutor(self.NUM) as executor:
				load_result = executor.map(tools.get_img_dbx, temp)

			for item in load_result:
				if item[-1] is None:
					continue
				self.img_dict[item[-1]] = [item[0], item[1]]
		except (MemoryError, OSError):
			self.reload(None)
			return

		self.length = len(self.file_list)
		self.sort_img()

		self.push_img(toplevel=toplevel)

	def use_dir(self) -> None:
		try:
			self.mode = 'dir'
			self.get_file_name()
		except HandleFileError:
			return

		for __dir_path, __dir_name, __file_names in os.walk(self.dir_path):
			__dir_path = path_str.join(__dir_path.split('/'))
			for __file_name in __file_names:
				img_file = path_str.join([__dir_path, __file_name])
				extent = __file_name.split('.')[-1].lower()
				if extent in ['png', 'jpg', 'jpeg'] and os.path.getsize(img_file) > 2e4:
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
		if self.reader_status['FULL_FAST']:
			return

		def sub_reload_func(mode: str, _toplevel: tkinter.Toplevel) -> None:
			self.file_list = []
			self.img_dict = {}
			self.able_to_sort_by_time = True
			self.time_bytes_dict = {}
			self.reader_status['LOAD_FINISH'] = False
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
		if not self.reader_status['LOAD_FINISH'] or self.length <= 3:
			return
		self.side_img_1_index = self.side_img_1_index - 1 if event.delta > 0 else self.side_img_1_index + 1

		self.show_img()

	def show_next_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.img_index += 1
		if self.length > 3:
			self.side_img_1_index = self.img_index
		self.show_img()

	def show_last_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.img_index -= 1
		if self.length > 3:
			self.side_img_1_index = self.img_index
		self.side_img_1_index = self.img_index
		self.show_img()

	def fast_save(self) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.status.get():
			return
		if self.reader_status['FULL_FAST']:
			return

		if self.content.split('.')[-1] == 'db':
			fast_save = '.'.join(self.content.split(path_str)[-1].split('.')[:-1])
		elif self.content.split('.')[-1] == 'dbx':
			showerror(message='dbx file has been loaded!')
			self.reader_status['FULL_FAST'] = False
			return
		else:
			fast_save = self.content.split(path_str)[-2]

		self.reader_status['FULL_FAST'] = True
		save_dir = askdirectory()
		if not save_dir:
			self.reader_status['FULL_FAST'] = False
			return
		save_dir = path_str.join(save_dir.split('/'))

		save_path = path_str.join([save_dir, f'{fast_save}.dbx'])
		percent = 0
		temp_v = ttkbootstrap.StringVar()
		temp_v.set(f'Now saving .dbx file in \n {save_path}\n {percent}%')
		toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Saving...',
			temp_v,
			self.scaling_ratio > 0.625
		)

		def _fast_save():
			i = 0
			with open(save_path, 'wb') as save:
				x = bytearray(MAGIC_NUM, encoding='utf-8')
				x += bytearray(str(self.img_index), encoding='utf-8').zfill(8)
				x += bytearray(str(len(self.file_list)), encoding='utf-8').zfill(8)
				for file in self.file_list:
					_percent = i / (2 * len(self.file_list))
					temp_v.set(f'Now saving .dbx file in \n {save_path}\n {_percent:.2f}%')
					i += 1
					x += bytearray(file, encoding='utf-8').zfill(256)
					x += bytearray(str(os.path.getsize(file)), encoding='utf-8').zfill(16)
				save_md5 = md5()
				save_md5.update(x)
				save.write(x)

				time_array = []
				for file in self.file_list:
					_percent = i / (2 * len(self.file_list))
					temp_v.set(f'Now saving .dbx file in \n {save_path}\n {_percent:.2f}%')
					i += 1
					with open(file, 'rb') as f1:
						n = f1.read()
						try:
							time_array.append(strftime('%Y%m%d%H%M%S', localtime(os.stat(file).st_mtime)))
						except Exception as e:
							temp_v.set(f'Now saving .dbx file in \n {save_path}\n {_percent:.2f}% \n Catch {e} for {file}')
							time_array.append(0)
						save_md5.update(n)
						save.write(n)
				md5_value = str(save_md5.hexdigest())
				save.write(bytearray(md5_value, encoding='utf-8'))

				for time_str in time_array:
					save.write(bytearray(time_str, encoding='utf-8'))

			try:
				toplevel.destroy()
				self.reader_status['FULL_FAST'] = False
			except RuntimeError:
				exit()

		tools.thread_func(_fast_save)

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
			self.toplevel_h+100,
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

	def jump(self, to=None) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		if to is None:
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
		else:
			self.img_index = to

		self.side_img_1_index = self.img_index
		self.show_img()

	def withdraw(self) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.content.split('.')[-1] != 'dbx':
			return
		if self.reader_status['FULL_FAST']:
			return

		save_dir = askdirectory()
		if not save_dir:
			self.reader_status['FAST_SAVE'] = False
			return
		save_dir = path_str.join(save_dir.split('/'))

		temp_ = tkinter.StringVar()
		temp_.set(f'Now converting dbx-files to pictures:\n {0}')
		back_toplevel = toplevel_with_bar(
			self.toplevel_w,
			self.toplevel_h,
			self.toplevel_x,
			self.toplevel_y,
			'Converting...',
			temp_,
			self.scaling_ratio > 0.625
		)

		def back_run():
			i = 0
			with open(self.content, 'rb') as dbx_file:
				dbx_file.seek(0, 0)
				_ = dbx_file.read(9)
				_ = dbx_file.read(32)
				total_size = int(dbx_file.read(128).lstrip(b'0').decode('utf-8'))

				names = []
				sizes = []
				for i in range(total_size):
					file_name = dbx_file.read(256).lstrip(b'0').decode('utf-8')
					size = int(dbx_file.read(128).lstrip(b'0').decode('utf-8'))
					names.append(file_name)
					sizes.append(size)

				path_list = [file_name.split(path_str) for file_name in names]
				common_prefix = tools.find_longest_common_prefix(path_list)[:-1]
				to_replace = path_str.join(common_prefix)

				for name, size in zip(names, sizes):
					_percent = i / total_size
					temp_.set(f'Now converting dbx-files to pictures:\n {_percent:.2f}%')
					i += 1
					save_filename = name.replace(to_replace, save_dir)
					img_bin = dbx_file.read(size)
					img_bin_io = io.BytesIO(img_bin)
					img = Image.open(img_bin_io)
					try:
						img.save(save_filename)
					except FileNotFoundError:
						os.makedirs(path_str.join(save_filename.split(path_str)[:-1]))
						img.save(save_filename)
					except FileExistsError:
						pass

			back_toplevel.destroy()

		tools.thread_func(back_run)

	def change_img(self, _id: int, event) -> None:
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

		self.reader_status['DRAG'] = True
		self.canvas.scan_dragto(event.x, event.y, gain=1)
		self.reader_status['DRAG'] = False

	def scaling(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['DRAG']:
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
		y = self.SH / 2 + 1440 * self.scaling_ratio / 2 - 300
		toplevel.geometry('%dx%d+%d+%d' % (400, 250, x, y))
		toplevel.resizable(False, False)
		toplevel.title('触摸按钮')
		toplevel.attributes('-topmost', 'True')
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

	def tree(self) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return

		def get_sub_file(fake_file: str, fake_file_list: list[str]) -> list:
			result = []
			for f in fake_file_list:
				if f.startswith(fake_file) and f != fake_file:
					temp = f.replace(fake_file, '')
					if temp.split(path_str)[0] not in result:
						result.append(temp.split(path_str)[0])
			return result

		def fake_is_dir(fake_file: str, fake_file_list: list[str]) -> bool:
			result = []
			for f in fake_file_list:
				if f.startswith(fake_file) and f != fake_file:
					result.append(f)
			return bool(len(result))

		def has_dir(fake_file: str, fake_file_list: list[str]) -> bool:
			for item in get_sub_file(fake_file, fake_file_list):
				if fake_is_dir(''.join([fake_file, item]), fake_file_list):
					return True
			return False

		path_list = [__file_name.split(path_str) for __file_name in self.file_list]
		common_prefix = tools.find_longest_common_prefix(path_list)
		root = path_str.join(common_prefix)

		self.tree_toplevel = tkinter.Toplevel()
		x = self.SW / 2 - 2400 * self.scaling_ratio / 2 - 50
		y = self.SH / 2 - 1440 * self.scaling_ratio / 2 + 150
		self.tree_toplevel.geometry('%dx%d+%d+%d' % (600, 1000, x, y))
		self.tree_toplevel.title('TreeView')
		self.tree_toplevel.grid_columnconfigure(0, minsize=600)
		# toplevel.resizable(False, False)

		scroll_frame = ScrolledFrame(self.tree_toplevel)
		root_collapsing_v_frame = CollapsingVFrame(scroll_frame)
		scroll_frame.pack(fill=BOTH, expand=YES)
		# scroll_frame.grid_columnconfigure(0, minsize=600)
		root_collapsing_v_frame.pack(fill=BOTH, expand=YES)

		def _tree(path, frame, depth):
			name = path.split(path_str)[-2]

			if has_dir(path, self.file_list) or path == root:
				sub_frame = CollapsingVFrame(frame)
				temp_text = '|    ' * (depth+1) + f'+----[其他]'
				# temp_frame = CollapsingVFrame(sub_frame)
				temp_group = ttk.Frame(sub_frame, padding=(0, 5))
				flag = False

				for item in get_sub_file(path, self.file_list):
					if fake_is_dir(''.join([path, item]) + path_str, self.file_list) or path == root:
						_tree(''.join([path, item]) + path_str, sub_frame, depth=depth+1)
					else:
						_to = self.file_list.index(''.join([path, item]))
						temp_name = ''.join([path, item]).split(path_str)[-1]
						ttk.Button(temp_group, text=temp_name, command=lambda: self.jump(_to)).pack(fill=X, expand=YES)
						flag = True

				text = '|    ' * depth + f'+----[{name}]'
				if flag:
					# temp_frame.add(child=temp_group, title=temp_text)
					sub_frame.add(child=temp_group, title=temp_text)
				frame.add(child=sub_frame, title=text)

			elif fake_is_dir(path, self.file_list):
				# print(path)
				group = ttk.Frame(frame, padding=(0, 5))
				for item in get_sub_file(path, self.file_list):
					_tree(''.join([path, item]) + path_str, group, depth=depth+1)
				text = '|    ' * depth + f'+----[{name}]'
				frame.add(child=group, title=text)
			else:
				_to = self.file_list.index(path[:-1])
				ttk.Button(frame, text=name, command=lambda: self.jump(_to)).pack(fill=X, expand=YES)

		tools.thread_func(_tree, {'path': root, 'frame': root_collapsing_v_frame, 'depth': 0})

		def _close_():
			self.tree_toplevel.destroy()
			self.tree_toplevel = None

		self.tree_toplevel.protocol("WM_DELETE_WINDOW", _close_)

	def _close(self) -> None:
		if (self.reader_status['FILE_NAME_LOAD'] and not self.reader_status['LOAD_FINISH'])\
				or self.reader_status['FULL_FAST']:
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
	if len(argv) == 2:
		_input_ = argv[1]
	else:
		_input_ = None
	reader = Reader(_input_)

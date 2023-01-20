import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from sys import exit
from tkinter import messagebox
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.simpledialog import askstring

import dill
import numpy as np
from _tkinter import TclError

from Reader_UI import *
from tools import json_path, path_str, CPU_NUM, tools, psd, HandleFileError


class Reader(ReaderUI):
	def __init__(self):
		super().__init__()
		self.NUM = CPU_NUM

		self.content = ''
		self.dir_path = ''

		self.file_list = []
		self.img_dict = {}

		self.length = 0
		self.img_index = 0
		self.side_img_1_index = 0
		self.side_img_2_index = 0
		self.side_img_3_index = 0
		self.side_img_1 = None
		self.side_img_2 = None
		self.side_img_3 = None
		self.img_label = None
		self.img_tk = None
		self.ex_h = (1440, 480)
		self.ex_w = (1900, 400)
		self.click_position = [0, 0, False]
		self.delta = [0, 0]
		self.record_for_scaling = 0
		self.history = {}

		self.reader_status = {
			'FILE_NAME_LOAD': False,
			'LOAD_FINISH': False,
			'OLD_STYLE': False,
			'FAST_SAVE': False,
			'DRAG': False,
			'SCAL': False
		}

		self.run()

	def load_img(self) -> None:
		self.length = len(self.file_list)
		if self.status.get():
			return

		ratio = [self.scaling_ratio] * self.length
		with ProcessPoolExecutor(self.NUM) as executor:
			load_result = executor.map(tools.get_img, self.file_list, ratio)

		for item in load_result:
			self.img_dict[item[-1]] = [item[0], item[1]]

	def sort_img(self) -> None:
		max_depth = max([len(x.split(path_str)) for x in self.file_list])
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

	def get_read_history(self) -> bool:
		with open(json_path, 'r', encoding='utf-8') as json_f:
			self.history = json.load(json_f)
		self.img_index = self.history.get(self.content, None)
		if self.img_index is not None:
			self.side_img_1_index = self.img_index
			return True
		else:
			return False

	def show_img(self) -> None:
		self.img_index = self.img_index % self.length
		img_key = self.file_list[self.img_index]
		self.delta = [0, 0]
		self.record_for_scaling = 0
		self.img_label = None

		self.side_img_2_index = self.side_img_1_index + 1
		self.side_img_3_index = self.side_img_1_index + 2

		self.side_img_1_index = self.side_img_1_index % self.length
		self.side_img_2_index = self.side_img_2_index % self.length
		self.side_img_3_index = self.side_img_3_index % self.length
		img_key = self.file_list[self.img_index]
		img_k_1, img_k_2, img_k_3 = \
			self.file_list[self.side_img_1_index], self.file_list[self.side_img_2_index], self.file_list[self.side_img_3_index]

		if self.status.get() and self.content.split('.')[-1] != 'db':
			img_1 = tools.get_img(img_key, self.scaling_ratio)[0]
			img_2 = tools.get_img(img_k_1, self.scaling_ratio)[1]
			img_3 = tools.get_img(img_k_2, self.scaling_ratio)[1]
			img_4 = tools.get_img(img_k_3, self.scaling_ratio)[1]
		else:
			img_1 = self.img_dict[img_key][0]
			img_2 = self.img_dict[img_k_1][1]
			img_3 = self.img_dict[img_k_2][1]
			img_4 = self.img_dict[img_k_3][1]

		self.img = ImageTk.PhotoImage(img_1)
		self.side_img_1, self.side_img_2, self.side_img_3 = \
			ImageTk.PhotoImage(img_2), ImageTk.PhotoImage(img_3), ImageTk.PhotoImage(img_4)

		title_ = '{name}--{i}/{l}'.format(name=self.file_list[self.img_index].split(path_str)[-2], i=self.img_index, l=self.length)
		self.win.title(title_)
		self.label.configure(image=self.img)
		self.side_button_1.configure(image=self.side_img_1)
		self.side_button_2.configure(image=self.side_img_2)
		self.side_button_3.configure(image=self.side_img_3)

	def get_file_name(self, mode: str) -> None:
		if self.reader_status.get('FILE_NAME_LOAD'):
			raise HandleFileError

		if mode == 'file':
			self.content = askopenfilename(filetypes=[('DataBase file', '*.db')])
			if not self.content:
				raise HandleFileError
			self.dir_path = path_str.join(self.content.split('/')[:-1])
		else:
			self.dir_path = askdirectory()
			if not self.dir_path:
				raise HandleFileError
			self.content = path_str.join([self.dir_path, 'content.txt'])
		self.reader_status['FILE_NAME_LOAD'] = True

		try:
			self.radiobutton_1.configure(state=tkinter.DISABLED)
			self.radiobutton_2.configure(state=tkinter.DISABLED)
		except TclError:
			pass

	def push_img(self, toplevel: tkinter.Toplevel, reshaped: bool = False,) -> None:
		try:
			toplevel.destroy()
		except RuntimeError:
			exit()
		if not self.get_read_history():
			self.img_index = self.side_img_1_index = 0
		self.change_grid()
		try:
			self.show_img()
		except IndexError:
			self.img_index = self.side_img_1_index = 0
			self.show_img()
		if reshaped:
			messagebox.showinfo(title='Warning', message='Resaving the .db file is highly recommended\n since you have changed your screen resolution.')
		self.reader_status['LOAD_FINISH'] = True

	def _reshape_db(self) -> bool:
		s_w, b_w = self.ex_w
		s_h, b_h = self.ex_h
		ex_ratio = s_w / 1900

		if str(self.scaling_ratio)[:4] == str(ex_ratio)[:4]:
			return False

		ratio = self.scaling_ratio / ex_ratio
		if not self.reader_status.get('OLD_STYLE'):
			for key, value in self.img_dict.items():
				img, button = self.img_dict[key]
				s_w, s_h = img.size
				b_w, b_h = button.size
				self.img_dict[key][0] = self.img_dict[key][0].resize((int(s_w * ratio), int(s_h * ratio)))
				self.img_dict[key][1] = self.img_dict[key][1].resize((int(b_w * ratio), int(b_h * ratio)))
		else:
			for key, value in self.img_dict.items():
				self.img_dict[key] = list(self.img_dict[key])
				img, button = self.img_dict[key]
				s_w, s_h = img.size
				b_w, b_h = button.size
				self.img_dict[key][0] = self.img_dict[key][0].resize((int(s_w * ratio), int(s_h * ratio)))
				self.img_dict[key][1] = self.img_dict[key][1].resize((int(b_w * ratio), int(b_h * ratio)))

		return True

	def use_file(self) -> None:
		try:
			self.get_file_name(mode='file')
		except HandleFileError:
			return

		x = self.SW / 2 - 600 * self.scaling_ratio / 2
		y = self.SH / 2 - 200 * self.scaling_ratio / 2
		toplevel = toplevel_with_bar(600 * self.scaling_ratio, 200 * self.scaling_ratio, x, y, 'Loading...', 'Now loading db file...', self.scaling_ratio > 0.625)
		try:
			with open(self.content, 'rb') as loader:
				self.file_list, self.img_dict, temp, self.ex_h, self.ex_w = dill.load(loader)
			reshape = self._reshape_db()
		except ValueError:
			self.reader_status['OLD_STYLE'] = True
			with open(self.content, 'rb') as loader:
				self.file_list, self.img_dict, temp = dill.load(loader)
				reshape = self._reshape_db()

		self.length = len(self.file_list)

		self.push_img(toplevel=toplevel, reshaped=reshape)

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

		x = self.SW / 2 - 600 * self.scaling_ratio / 2
		y = self.SH / 2 - 200 * self.scaling_ratio / 2
		toplevel = toplevel_with_bar(600*self.scaling_ratio, 200*self.scaling_ratio, x, y, 'Loading...', 'Now loading images...', self.scaling_ratio > 0.625)

		self.load_img()
		self.sort_img()

		self.push_img(toplevel=toplevel)

	def reload(self) -> None:
		if not self.reader_status.get('FILE_NAME_LOAD'):
			return

		def sub_reload_func(mode: str, _toplevel: tkinter.Toplevel) -> None:
			self.file_list = []
			self.key_list = []
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

		size = int(20 * self.scaling_ratio) if int(20 * self.scaling_ratio) < 20 else 20
		x = self.SW / 2 - 400*self.scaling_ratio / 2
		y = self.SH / 2 - 200*self.scaling_ratio / 2
		toplevel = tkinter.Toplevel()
		toplevel.title('Reload')
		toplevel.geometry('%dx%d+%d+%d' % (400 * self.scaling_ratio, 200 * self.scaling_ratio, x, y))

		button_f = tkinter.Button(toplevel, text='Use file', command=lambda: tools.thread_func(sub_reload_func, {'mode': 'file', '_toplevel': toplevel}), font=('Consolas', size, 'bold'), height=3)
		button_d = tkinter.Button(toplevel, text='Use dir ', command=lambda: tools.thread_func(sub_reload_func, {'mode': 'dir', '_toplevel': toplevel}), font=('Consolas', size, 'bold'), height=3)

		button_f.grid(row=0, column=0)
		button_d.grid(row=0, column=1)

		toplevel.grid_rowconfigure(0, weight=1)
		toplevel.grid_columnconfigure(0, weight=1)
		toplevel.grid_columnconfigure(1, weight=1)

	def img_by_mouse(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.side_img_1_index = self.side_img_1_index - 1 if event.delta > 0 else self.side_img_1_index + 1

		self.show_img()

	def show_next_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.img_index += 1
		self.side_img_1_index = self.img_index
		self.show_img()

	def show_last_img(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.img_index -= 1
		self.side_img_1_index = self.img_index
		self.show_img()

	def command(self, event) -> None:
		__command_str__ = askstring(title='COMMAND', prompt='command:')

		if __command_str__.lower() == 'fast save':
			if not self.reader_status['LOAD_FINISH'] or self.status.get():
				return

			if self.content.split('.')[-1] == 'db':
				re_str = ' at [0-9]{0,5}x[0-9]{0,5}'
				try:
					s = re.findall(re_str, self.content.split('/')[-1])[0]
					fast_save = self.content.split('/')[-1].replace(s, '')
				except IndexError:
					fast_save = self.content.split('/')[-1]
			else:
				fast_save = 'fastSave'
			self.reader_status['FAST_SAVE'] = True
			resolution = (str(int(3072 * self.scaling_ratio)), str(int(1728 * self.scaling_ratio)))
			save_path = path_str.join(self.dir_path.split('/') + [f'{fast_save} at {resolution[0]}x{resolution[1]}.db'])
			x = self.SW / 2 - 800 * self.scaling_ratio / 2
			y = self.SH / 2 - 200 * self.scaling_ratio / 2
			toplevel = toplevel_with_bar(800 * self.scaling_ratio, 200 * self.scaling_ratio, x, y, 'Saving...',  f'Now saving db file in \n ..{path_str}{fast_save} at {resolution[0]}x{resolution[1]}.db',  self.scaling_ratio > 0.625)
			__save_data = (self.file_list, self.img_dict, self.img_index, (int(1440 * self.scaling_ratio), int(400 * self.scaling_ratio)), (int(1900 * self.scaling_ratio), int(480 * self.scaling_ratio)))

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

		elif __command_str__.lower() == 'psd':
			psd_content = askdirectory()
			try:
				psd_helper = psd.PSDHelper(psd_content)
			except HandleFileError:
				return

			def psd_run():
				psd_helper.run()
			tools.thread_func(psd_run)
		else:  # jump id
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
					self.img_index = int(want)
			except AttributeError:
				return
			except ValueError:
				return

			self.side_img_1_index = self.img_index
			self.show_img()

	def change_img(self, _id: int) -> None:
		if _id == 1:
			self.img_index = self.side_img_1_index
		elif _id == 2:
			self.img_index = self.side_img_2_index
		elif _id == 3:
			self.img_index = self.side_img_3_index
		self.show_img()

	def get_click(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.click_position = [event.x, event.y, True]

	def scaling(self, event) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return
		self.reader_status['SCAL'] = True
		max_num, factor = 480, 1.2

		self.record_for_scaling += event.delta
		if self.record_for_scaling > 480:
			self.record_for_scaling = 480
			self.reader_status['SCAL'] = False
			return
		elif self.record_for_scaling < -480:
			self.record_for_scaling = -480
			self.reader_status['SCAL'] = False
			return

		scaling_ratio = factor**(self.record_for_scaling/120)
		key = self.file_list[self.img_index]
		raw_img_w, raw_img_h = self.img_dict[key][0].size
		self.img_label = deepcopy(self.img_dict[key][0]).resize((int(raw_img_w*scaling_ratio), int(raw_img_h*scaling_ratio)))
		self.img_label = np.asarray(self.img_label)
		if scaling_ratio >= 1:
			w_start = int((self.img_label.shape[1] - raw_img_w)/2)
			h_start = int((self.img_label.shape[0] - raw_img_h)/2)
			img = self.img_label
		else:
			img = np.zeros(shape=(raw_img_h, raw_img_w, 3))
			img.fill(255)
			w_start = int((-self.img_label.shape[1] + raw_img_w) / 2)
			h_start = int((-self.img_label.shape[0] + raw_img_h) / 2)
			img[h_start:h_start + self.img_label.shape[0], w_start:w_start + self.img_label.shape[1], :] = self.img_label[:, :, :]
		img_from_array = Image.fromarray(np.uint8(img))
		self.img_tk = ImageTk.PhotoImage(img_from_array)
		self.label.configure(image=self.img_tk)
		self.reader_status['SCAL'] = False

	def drag(self, event) -> None:
		if not self.reader_status['LOAD_FINISH'] or self.reader_status['SCAL']:
			return

		self.reader_status['DRAG'] = True
		key = self.file_list[self.img_index]
		if self.img_label is None:
			self.img_label = np.asarray(self.img_dict[key][0])
		raw_img_w, raw_img_h = self.img_dict[key][0].size

		delta_x, delta_y = event.x - self.click_position[0], event.y - self.click_position[1]
		if self.click_position[-1]:
			delta_x, delta_y = 0, 0
		self.click_position = [event.x, event.y, False]
		try:
			if self.img_label.shape[0] > raw_img_h:
				raw_img_w = int(raw_img_w * 2.3)
				img = np.zeros(shape=(raw_img_h, raw_img_w, 3))
				img.fill(255)
				d_x, d_y = self.delta[0] + delta_x, self.delta[1] - delta_y
				offset_w = int((-self.img_label.shape[1] + raw_img_w) / 2)
				offset_h = int((self.img_label.shape[0] - raw_img_h) / 2)
				d_x = -offset_w if d_x < -offset_w else d_x
				d_x = offset_w if d_x > offset_w else d_x
				d_y = -offset_h if d_y < -offset_h else d_y
				d_y = offset_h if d_y > offset_h else d_y

				self.delta = [d_x, d_y]

				img[:, offset_w + d_x:offset_w + d_x + self.img_label.shape[1], :] = self.img_label[offset_h+d_y:offset_h + d_y + raw_img_h, :, :]
			else:
				img = np.zeros(shape=(raw_img_h, raw_img_w, 3))
				img.fill(255)
				d_x, d_y = self.delta[0] + delta_x, self.delta[1] + delta_y
				offset_w = int((-self.img_label.shape[1] + raw_img_w) / 2)
				offset_h = int((-self.img_label.shape[0] + raw_img_h) / 2)
				d_x = -offset_w if d_x < -offset_w else d_x
				d_x = offset_w if d_x > offset_w else d_x
				d_y = -offset_h if d_y < -offset_h else d_y
				d_y = offset_h if d_y > offset_h else d_y

				self.delta = [d_x, d_y]

				img[offset_h+d_y:offset_h+d_y+self.img_label.shape[0], offset_w+d_x:offset_w+d_x+self.img_label.shape[1], :] = self.img_label
		except ValueError:
			self.reader_status['DRAG'] = False
			return
		img_from_array = Image.fromarray(np.uint8(img))
		self.img_tk = ImageTk.PhotoImage(img_from_array)
		self.label.configure(image=self.img_tk)
		self.reader_status['DRAG'] = False

	def bind_command(self) -> None:
		self.button_1.configure(command=lambda: tools.thread_func(self.use_file))
		self.button_2.configure(command=lambda: tools.thread_func(self.use_dir))

		self.side_button_1.configure(command=lambda: self.change_img(1))
		self.side_button_2.configure(command=lambda: self.change_img(2))
		self.side_button_3.configure(command=lambda: self.change_img(3))

	def run(self) -> None:
		self.bind_command()
		self.win.bind('<Up>', self.show_last_img)
		self.win.bind('<Right>', self.show_next_img)
		self.win.bind('<Down>', self.show_next_img)
		self.win.bind('<Left>', self.show_last_img)

		self.win.bind('<Tab>', self.command)
		self.win.bind('<Escape>', self.reload)
		self.win.protocol("WM_DELETE_WINDOW", self._close)

		self.side_button_1.bind('<MouseWheel>', self.img_by_mouse)
		self.side_button_2.bind('<MouseWheel>', self.img_by_mouse)
		self.side_button_3.bind('<MouseWheel>', self.img_by_mouse)

		self.label.bind('<Button-1>', self.get_click)
		self.label.bind('<B1-Motion>', self.drag)
		self.label.bind('<Control-MouseWheel>', self.scaling)
		self.win.mainloop()

	def _close(self) -> None:
		if (self.reader_status['FILE_NAME_LOAD'] and not self.reader_status['LOAD_FINISH']) or self.reader_status['FAST_SAVE']:
			return

		self.history[self.content] = self.img_index
		with open(json_path, 'w', encoding='utf-8') as file:
			json.dump(self.history, file)

		self.win.destroy()
		exit()


if __name__ == '__main__':
	reader = Reader()

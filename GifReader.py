import os
import re
from tkinter.simpledialog import askstring

from PIL import Image, ImageTk, ImageSequence
from tkinter import PhotoImage
from _tkinter import TclError
from UI.GifReader_UI import *
from tools import path_str, tools, HandleFileError


class Reader(UI):
	def __init__(self, master, sw, sh, side_color, init_img, directory, history):
		super().__init__(master, sw, sh, side_color)
		self.history = history
		self._seq = None
		self.shut = False
		self.directory = directory
		self.side_key_2 = None
		self.side_key_3 = None
		self.side_key_1 = None
		self.elder: int = 0
		self.side_img_3_index: int = 2
		self.side_img_2_index: int = 1
		self.side_img_1_index: int = 0
		self.img_index: int = 0
		self.c_list = []
		self.index: int = 0
		self.main_c = None
		self.init_img = init_img
		self.length = 0
		self.file_list = []
		self.thumb_dict = {}
		self.index = 0
		self.side_index = [0, 1, 2]

		self.reader_status = {
			'FILE_NAME_LOAD': False,
			'LOAD_FINISH': False
		}

	def run(self) -> None:
		self.menu.add_command(label='Jump to', command=self.jump)

		self.toplevel.bind('<Up>', self.show_last_img)
		self.toplevel.bind('<Right>', self.show_next_img)
		self.toplevel.bind('<Down>', self.show_next_img)
		self.toplevel.bind('<Left>', self.show_last_img)

		self.gif_side_canvas_1.bind('<MouseWheel>', self.img_by_mouse)
		self.gif_side_canvas_1.bind('<Button-1>', lambda event: self.change_img(1, event))
		self.gif_separator_h_1.bind('<MouseWheel>', self.img_by_mouse)
		self.gif_side_canvas_2.bind('<MouseWheel>', self.img_by_mouse)
		self.gif_side_canvas_2.bind('<Button-1>', lambda event: self.change_img(2, event))
		self.gif_separator_h_2.bind('<MouseWheel>', self.img_by_mouse)
		self.gif_side_canvas_3.bind('<MouseWheel>', self.img_by_mouse)
		self.gif_side_canvas_3.bind('<Button-1>', lambda event: self.change_img(3, event))

		def sub_run():
			self.load_img()
			self.push_img()
			# self.show_img(True)

		tools.thread_func(sub_run)

	def show_img(self, first=False) -> None:
		self.img_index = self.img_index % self.length

		# self.side_img_1_index = self.img_index
		self.side_img_2_index = self.side_img_1_index + 1
		self.side_img_3_index = self.side_img_1_index + 2

		self.side_img_1_index = self.side_img_1_index % self.length
		self.side_img_2_index = self.side_img_2_index % self.length
		self.side_img_3_index = self.side_img_3_index % self.length

		self.side_key_1 = self.file_list[self.side_img_1_index]
		self.side_key_2 = self.file_list[self.side_img_2_index]
		self.side_key_3 = self.file_list[self.side_img_3_index]

		refresh_main = first
		if self.img_index != self.elder:
			refresh_main = True

		def anime(seq: list, time: int) -> None:
			if seq != self._seq:
				return
			self.index = self.index + 1
			self.index = self.index % len(seq)
			_img = seq[self.index]
			self.gif_canvas.itemconfig(self.main_c, image=_img, anchor="center")
			self.toplevel.after(time, lambda: anime(seq, time))

		if refresh_main:
			self.history[self.directory+'_gif'] = self.img_index
			self._seq = self.thumb_dict[self.file_list[self.img_index]][1][0]
			duration = self.thumb_dict[self.file_list[self.img_index]][1][1]
			self.index = 0

			title_ = '{name}--{i}/{l}'.format(name=self.file_list[self.img_index].split(path_str)[-2], i=self.img_index, l=self.length)
			self.toplevel.title(title_)
			tools.thread_func(func=anime, kwargs={'seq': self._seq, 'time': duration})
			self.elder = self.img_index

		# self.toplevel.after(100, lambda: print('hello'))
		canvases_t = [(self.gif_side_canvas_1, self.side_key_1), (self.gif_side_canvas_2, self.side_key_2), (self.gif_side_canvas_3, self.side_key_3)]
		for i in range(min(self.length, 3)):
			c, img = canvases_t[i]
			c.itemconfig(self.c_list[i], image=self.thumb_dict[img][0])

	def load_img(self) -> None:
		if self.reader_status.get('FILE_NAME_LOAD'):
			raise HandleFileError
		self.reader_status['FILE_NAME_LOAD'] = True

		# top here
		# toplevel = gif_toplevel_with_bar(w=self.toplevel_w, h=self.toplevel_h, x=self.toplevel_x, y=self.toplevel_y, name='Loading...', label_='Loading GIF files...', large=self.scaling_ratio > 0.65)

		for __dir_path, __dir_name, __file_names in os.walk(self.directory):
			__dir_path = path_str.join(__dir_path.split('/'))
			for __file_name in __file_names:
				img_file = path_str.join([__dir_path, __file_name])
				extent = __file_name.split('.')[-1].lower()
				# if extent in ['gif'] and os.path.getsize(img_file) > 2e5:
				if extent in ['gif']:
					self.file_list.append(img_file)

		self.length = len(self.file_list)

		# we should have to sort it...

		for file in self.file_list:
			frames = []
			frame_index = 0
			while True:
				part = 'gif -index {}'.format(frame_index)
				try:
					frame = PhotoImage(file=file, format=part)
					w, h = frame.width(), frame.height()
					frame_index = frame_index + 1
					x = int(1800 * self.scaling_ratio / w)
					y = int(1440 * self.scaling_ratio / h)
					frame = frame.zoom(x=min(x, y))
					frames.append(frame)
				except TclError as e:
					break
			with Image.open(file) as im:
				duration = im.info.get('duration', 60)
				thumb = ImageSequence.Iterator(im)[0]
				w, h = thumb.size
				ratio = self.scaling_ratio
				side_size = (int(480 * ratio * w / h), int(480 * ratio)) if h >= w else (int(400 * ratio), int(400 * ratio * h / w))
				thumb.resize(side_size)
				thumb = ImageTk.PhotoImage(thumb)
			self.thumb_dict[file] = (thumb, (frames, duration))

		# return toplevel
	def get_history(self) -> None:
		self.img_index = self.history.get(self.directory+'_gif', 0)
		self.side_img_1_index = self.img_index

	def push_img(self, reshaped: bool = False) -> None:
		self.get_history()
		self.change_grid()

		self.main_c = self.gif_canvas.create_image(self.gif_main_canvas_w, self.gif_main_canvas_h, image=self.init_img, anchor="center")
		self.c_list = [
			self.gif_side_canvas_1.create_image(self.gif_side_canvas_w, self.gif_side_canvas_h, image=self.init_img, anchor="center"),
			self.gif_side_canvas_2.create_image(self.gif_side_canvas_w, self.gif_side_canvas_h, image=self.init_img, anchor="center"),
			self.gif_side_canvas_3.create_image(self.gif_side_canvas_w, self.gif_side_canvas_h, image=self.init_img, anchor="center")
		]
		if self.length == 2:
			self.gif_side_canvas_3.delete("all")
		elif self.length == 1:
			self.gif_side_canvas_2.delete("all")
			self.gif_side_canvas_3.delete("all")

		self.show_img(first=True)
		self.reader_status['LOAD_FINISH'] = True

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

	def jump(self) -> None:
		if not self.reader_status['LOAD_FINISH']:
			return

		__command_str__ = askstring(parent=self.toplevel, title='Jump to', prompt='Page:')

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

	def change_img(self, _id: int, event) -> None:
		if _id == 1:
			self.img_index = self.side_img_1_index
		elif _id == 2:
			self.img_index = self.side_img_2_index
		elif _id == 3:
			self.img_index = self.side_img_3_index
		self.show_img()

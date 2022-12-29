#encoding: utf-8
import os
import re
import tkinter
import threading
from tqdm import tqdm
from queue import Queue
from PIL import Image, ImageTk
from tkinter.simpledialog import askinteger, askstring
from tkinter.filedialog import askdirectory, askopenfilename


def encode(_str):
	num = re.findall('\d+', _str)
	try:
		_num = int(num[-1])
	except IndexError:
		_num = 0
	return _num

def get_img(img_file):
	img = Image.open(img_file)
	w, h = img.size
	if h >= w:
		factor = 1080/h
	else:
		factor = 1920/w
	new_w, new_h = int(factor*w), int(factor*h)
	# MEM_size = new_w*new_h*4
	img_resized = img.resize((new_w, new_h))
	img_tk = ImageTk.PhotoImage(img_resized)

	# return img_tk, MEM_size
	return img_tk, (new_w, new_h), img_file

def thread_func(func):
	t = threading.Thread(target=func)
	t.setDaemon(True)
	t.start()

def sub_loader(file_list, i, total):
	res = []
	block = len(file_list)//total
	if i > total:
		List = file_list[i*block:]
	else:
		List = file_list[i*block:(i+1)*block]
	for j in tqdm(range(len(List)), ascii=True, desc=f'thread_{i}'):
		try:
			name = List[j]
			res.append(get_img(name))
		except MemoryError:
			print('Memory ran out!')
			break
	return res


class Reader:
	def __init__(self):
		self.thread_num = 4
		self.q = Queue()
		self.finished = False

		self.win = tkinter.Tk()
		self.win.title('reADpIc')
		self.SW, self.SH = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
		x = self.SW/2 - 1280/2
		y = self.SH/2 - 900/2
		self.win.geometry('%dx%d+%d+%d' % (1280, 900, x, y))

		self.flag = False
		self.content = ''
		self.dir_path = ''
		self.file_list = []
		self.key_list = []
		self.img_dict = {}
		self.length = 0
		self.id_ = 0

		init_img = Image.open(r'readpic.png')
		self.img = ImageTk.PhotoImage(init_img)

		self.label = tkinter.Label(self.win, image=self.img)
		self.label.grid(row=0, column=0, columnspan=2, sticky=tkinter.NSEW)
		self.button_1 = tkinter.Button(self.win, text='use file', command=lambda :thread_func(self.use_file), font=40, height=5)
		self.button_2 = tkinter.Button(self.win, text='use dir', command=lambda :thread_func(self.use_dir), font=40)
		self.button_1.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.button_2.grid(row=1, column=1, sticky=tkinter.NSEW)
		self.win.grid_columnconfigure(0, weight=1)
		self.win.grid_columnconfigure(1, weight=1)
		self.win.grid_rowconfigure(0, weight=1)
		self.win.grid_rowconfigure(1, weight=1)
		self.run()

	def run(self):
		os.system('cls')

		self.win.bind('<Up>', self.show_last_img)
		self.win.bind('<Right>', self.show_next_img)
		self.win.bind('<Down>', self.show_next_img)
		self.win.bind('<Left>', self.show_last_img)
		self.win.bind('<MouseWheel>', self.mouse_img)
		self.win.bind('<Tab>', self.jump)
		self.win.protocol("WM_DELETE_WINDOW", self.close_)
		self.win.mainloop()

	def show_img(self):
		img_key = self.key_list[self.id_]
		self.img = self.img_dict[img_key][0]
		w, h = self.img_dict[img_key][1]
		title_ = '{name}--{i}/{l}'.format(name=self.key_list[self.id_].split('\\')[-2], i=self.id_, l=self.length)
		self.win.title(title_)
		x = int(self.SW/2 - w/2)
		y = int(self.SH/2 - h/2)
		self.win.geometry('%dx%d+%d+%d' % (w, h, x, y))
		self.label.configure(image=self.img)
		self.label.image = self.img

	def load_img(self):
		threads = [threading.Thread(target=lambda q, file_name, i, total: q.put(sub_loader(file_name, i, total)), args=(self.q, self.file_list, i, self.thread_num)) for i in range(self.thread_num+1)]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		while not self.q.empty():
			for item in self.q.get():
				self.img_dict[item[-1]] = (item[0], item[1])
		self.length = len(self.img_dict.keys())

	def sort_img(self):
		search_length = self.length
		while search_length > 1:
			sub_list = []
			__path = self.file_list[0].split('\\')[:-1]
			for i in range(search_length-1, -1, -1):
				if self.file_list[i].split('\\')[:-1] == __path:
					sub_list.append(self.file_list.pop(i))
			__len = len(sub_list)
			#sort
			sub_list.sort(key=lambda x: encode(x.split('\\')[-1]))

			for name in sub_list:
				self.key_list.append(name)

			search_length = search_length - __len

	def use_file(self):
		if not self.flag:
			self.dir_path = askopenfilename()
			if self.dir_path:
				self.flag = True
				self.button_1.destroy()
				self.button_2.destroy()
			else:
				return

		self.content = self.dir_path
		with open(self.dir_path, 'r') as file:
			while True:
				this_line = file.readline()

				if not this_line:
					break

				if this_line[-1] == '\n':
					this_line = this_line[:-1]

				self.file_list.append(this_line)
		try:
			self.id_ = int(self.file_list[-1])
			self.file_list = self.file_list[:-1]
		except ValueError:
			pass

		print('Loading...')
		self.load_img()
		print('sorting...')
		self.sort_img()
		try:
			self.show_img()
		except IndexError:
			self.id_ = 0
			self.show_img()
		self.finished = True

	def use_dir(self):
		if not self.flag:
			self.dir_path = askdirectory()
			if self.dir_path:
				self.flag = True
				self.button_1.destroy()
				self.button_2.destroy()
			else:
				return

		for __dir_path, __dir_name, __file_names in os.walk(self.dir_path):
			for __file_name in __file_names:
				img_file = '\\'.join([__dir_path, __file_name])
				if __file_name.split('.')[-1].lower() in ['png', 'jpg', 'jpeg'] and os.path.getsize(img_file) > 2e5:
					self.file_list.append(img_file)

		self.length = len(self.file_list)
		self.content = '\\'.join([self.dir_path, 'content.txt'])

		print('Loading...')
		self.load_img()
		print('Sorting...')
		self.sort_img()
		with open(self.content, 'w', encoding='utf-8') as file:
			for i in self.key_list:
				to_file = i + '\n'
				file.write(to_file)
			file.write('0\n')
		try:
			self.show_img()
		except IndexError:
			self.id_ = 0
			self.show_img()
		self.finished = True

	def show_next_img(self, event):
		if not self.finished:
			return 
		self.id_ += 1
		if self.id_ > self.length - 1:
			self.id_ = 0
		self.show_img()

	def show_last_img(self, event):
		if not self.finished:
			return 
		self.id_ -= 1
		if self.id_ > self.length - 1:
			self.id_ = 0
		self.show_img()
		
	def mouse_img(self, event):
		if not self.finished:
			return
		if event.delta > 0:
			self.show_last_img(event)
		else:
			self.show_next_img(event)
			
	def jump(self, event):
		if not self.finished:
			return 
		go_to = askstring(title='pages', prompt='pages')
		try:
			ret = re.match('[+-]*[0-9]{,}', go_to)
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
			self.id_ = self.id_%self.length
			self.show_img()
		except TypeError:
			pass

	def close_(self):
		try:
			with open(self.content, 'w+', encoding='utf-8') as file:
				self.key_list.append(str(self.id_))
				for i in self.key_list:
					to_file = i + '\n'
					file.write(to_file)
		except FileNotFoundError:
			pass
		self.win.destroy()

if __name__ == '__main__':
	reader = Reader()

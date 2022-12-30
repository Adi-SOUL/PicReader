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
		_num = _str
	return _num

def get_img(img_file):
	img = Image.open(img_file).convert('RGB')
	w, h = img.size
	if h >= w:
		factor = 1440/h
		factor_2 = 480/h
	else:
		factor = 1900/w
		factor_2 = 400/w
	new_w, new_h = int(factor*w), int(factor*h)
	img_resized = img.resize((new_w, new_h))
	img_tk = ImageTk.PhotoImage(img_resized)

	img_resized = img.resize((int(factor_2*w), int(factor_2*h)))
	img_tk_button = ImageTk.PhotoImage(img_resized)
	return img_tk, img_tk_button, img_file

def thread_func(func):
	t = threading.Thread(target=func)
	t.Daemon = True
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

		self.win = tkinter.Tk()
		self.win.title('reADpIc')
		self.pixelVirtual = tkinter.PhotoImage(width=1, height=1)
		self.SW, self.SH = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
		x = self.SW/2 - 1280/2
		y = self.SH/2 - 900/2
		self.win.geometry('%dx%d+%d+%d' % (1280, 900, x, y))

		init_img = Image.open(r'readpic.png')
		self.img = ImageTk.PhotoImage(init_img)

		self.label = tkinter.Label(self.win, image=self.img)
		self.label.grid(row=0, column=0, columnspan=2, sticky=tkinter.NSEW)
		self.button_1 = tkinter.Button(self.win, text='use file', command=lambda :thread_func(self.use_file), font=40, height=5)
		self.button_2 = tkinter.Button(self.win, text='use dir', command=lambda :thread_func(self.use_dir), font=40)
		self.button_1.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.button_2.grid(row=1, column=1, sticky=tkinter.NSEW)
		
		self.button_3 = tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_1, height=480, width=400) 
		self.button_4 = tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_2, height=480, width=400)
		self.button_5 = tkinter.Button(self.win, image=self.pixelVirtual, command=self.change_img_3, height=480, width=400)
		
		self.win.grid_columnconfigure(0, weight=1)
		self.win.grid_columnconfigure(1, weight=1)
		self.win.grid_rowconfigure(0, weight=1)
		self.win.grid_rowconfigure(1, weight=1)
		self.win.grid_rowconfigure(2, weight=1)
		self.run()

	def run(self):
		os.system('cls')

		self.win.bind('<Up>', self.show_last_img)
		self.win.bind('<Right>', self.show_next_img)
		self.win.bind('<Down>', self.show_next_img)
		self.win.bind('<Left>', self.show_last_img)
		self.win.bind('<Tab>', self.jump)
		self.win.protocol("WM_DELETE_WINDOW", self.close_)

		self.button_3.bind('<MouseWheel>', self.mouse_img)
		self.button_4.bind('<MouseWheel>', self.mouse_img)
		self.button_5.bind('<MouseWheel>', self.mouse_img)
		self.win.mainloop()

	def change_grid(self):
		self.button_1.destroy()
		self.button_2.destroy()
		self.label.grid(row=0, column=1, rowspan=3, sticky=tkinter.NSEW)
		self.button_3.grid(row=0, column=0, sticky=tkinter.NSEW)
		self.button_4.grid(row=1, column=0, sticky=tkinter.NSEW)
		self.button_5.grid(row=2, column=0, sticky=tkinter.NSEW)
		self.label.configure(height=9, width=2000)
		x = self.SW/2 - 2400/2
		y = self.SH/2 - 1440/2
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

		img_k_1, img_k_2, img_k_3 = self.key_list[button_id_1], self.key_list[self.button_id_2], self.key_list[self.button_id_3]  
		self.img = self.img_dict[img_key][0]
		self.img_1, self.img_2, self.img_3 = self.img_dict[img_k_1][1], self.img_dict[img_k_2][1], self.img_dict[img_k_3][1]
		title_ = '{name}--{i}/{l}'.format(name=self.key_list[self.id_].split('\\')[-2], i=self.id_, l=self.length)
		self.win.title(title_)
		self.label.configure(image=self.img)
		self.button_3.configure(image=self.img_1)
		self.button_4.configure(image=self.img_2)
		self.button_5.configure(image=self.img_3)

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
		level = len(self.file_list[0].split('\\'))
		convert = [self.file_list]
		l = 1 
		while l < level:
			for to_be_sort in convert:
				sub = []
				search_length = len(to_be_sort)
				while search_length > 1:
					sub_list = []
					__path = to_be_sort[0].split('\\')[:l]
					for i in range(search_length-1, -1, -1):
						if to_be_sort[i].split('\\')[:l] == __path:
							sub_list.append(to_be_sort.pop(i))

					sub_list.sort(key=lambda x: encode(x.split('\\')[l]))

					sub.append(sub_list)
					
					search_length = len(to_be_sort)
			convert = sub 
			l = l + 1
		def flatten(List):
			return sum(([x] if not isinstance(x, list) else flatten(x) for x in List), [])
		self.key_list = flatten(convert)

	def use_file(self):
		if not self.flag:
			self.dir_path = askopenfilename()
			if self.dir_path:
				self.flag = True
			else:
				return
		else:
			return 

		self.content = self.dir_path
		with open(self.dir_path, 'r', encoding='utf-8') as file:
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

		print('Loading...')
		self.load_img()
		print('Sorting...')
		self.sort_img()

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

		for __dir_path, __dir_name, __file_names in os.walk(self.dir_path):
			__dir_path = '\\'.join(__dir_path.split('/'))
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

	def close_(self):
		try:
			with open(self.content, 'w+', encoding='utf-8') as file:
				self.key_list.append(str(self.id_))
				for i in self.key_list:
					to_file = i + '\n'
					file.write(to_file)
		except FileNotFoundError:
			pass
		os.system('cls')
		self.win.destroy()

if __name__ == '__main__':
	reader = Reader()

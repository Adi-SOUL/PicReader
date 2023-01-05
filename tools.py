import re
import threading
from PIL import Image
import tkinter
from tkinter import ttk


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


def get_img(img_file, ratio):
	img = Image.open(img_file).convert('RGB')
	w, h = img.size
	if h >= w:
		factor = 1440*ratio / h
		factor_2 = 480*ratio / h
	else:
		factor = 1900*ratio / w
		factor_2 = 400*ratio / w
	new_w, new_h = int(factor * w), int(factor * h)
	img_resized = img.resize((new_w, new_h))
	# img_tk = ImageTk.PhotoImage(img_resized)

	img_resized_bu = img.resize((int(factor_2 * w), int(factor_2 * h)))
	# img_tk_button = ImageTk.PhotoImage(img_resized_bu)
	# return img_tk, img_tk_button, img_file
	return img_resized, img_resized_bu, img_file


def flatten(_list):
	return sum(([x] if not isinstance(x, list) else flatten(x) for x in _list), [])


def sub_loader(file_list, i, total, ratio):
	res = []
	block = len(file_list) // total
	if i > total:
		List = file_list[i * block:]
		if not len(List):
			return []
	else:
		List = file_list[i * block:(i + 1) * block]
	for j in range(len(List)):
		try:
			name = List[j]
			res.append(get_img(name, ratio))
		except MemoryError:
			print('Memory ran out!')
			break
	return res


def encode(_str):
	num = re.findall('\d+', _str)
	try:
		_num = int(num[-1])
	except IndexError:
		_num = 0
	return _num


def thread_func(func):
	t = threading.Thread(target=func)
	t.Daemon = True
	t.start()
	return t

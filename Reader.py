import tkinter
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.simpledialog import askinteger, askstring
from PIL import Image, ImageTk
from tqdm import tqdm
import os
import re


file_list = []
length = 0
id_ = 0
path_ = ''
content_path = ''
win = tkinter.Tk()
sub = tkinter.Toplevel()
sub.geometry('200x100+800+400')
img_ = Image.open('/Users/adijnnuuy/Desktop/init.png')
w,h = img_.size 
img_ = img_.resize((int(w/2),int(h/2)))
img_ = ImageTk.PhotoImage(img_)
os.system('clear')


def encode(_str):
	num = re.findall('\d+', _str)
	try:
		_num = int(num[0])
	except IndexError:
		_num = 0
	return _num

def get_img(img_file):
	img = Image.open(img_file)
	w, h = img.size
	if h >= 0.687*w:
		factor = 1030/h
	else:
		factor = 1500/w
	new_size = (int(factor*w), int(factor*h))
	img_resized = img.resize(new_size)
	img_tk = ImageTk.PhotoImage(img_resized)
	return img_tk

def use_file():
	global file_list, length, id_, path_, content_path
	flag = False
	while not flag:
		path_ = askopenfilename()
		if path_ != '':
			flag = True

	content_path = path_
	with open(path_, 'r') as file:
		while True:
			this_line = file.readline()

			if not this_line:
				break

			if this_line[-1] == '\n':
				this_line = this_line[:-1]

			file_list.append(this_line)	
	try:
		id_ = int(file_list[-1])
		file_list = file_list[:-1]
	except:
		id_ = 0 

	length = len(file_list)
	title_ = '{name}--{i}/{l}'.format(name=file_list[id_].split('/')[-2], i=id_, l=length)
	win.title(title_)
	img_ = get_img(file_list[id_])
	label.configure(image = img_)
	label.image = img_
	sub.destroy()

def use_dir():
	global file_list, length, id_, path_
	flag = False
	while not flag:
		path_ = askdirectory()
		if path_ != '':
			flag = True
	for dir_path, dir_name, file_names in os.walk(path_):
		for file_name in file_names:
			if file_name.split('.')[-1] in ['png', 'jpg']:
				img_file = os.path.join(dir_path, file_name)
				file_list.append(img_file)

	length = len(file_list)
	for j in tqdm(range(length-1)):
		for i in range(length-j-1):
			_a = file_list[i].split('/')[:-1]
			_b = file_list[i+1].split('/')[:-1]
			a = encode(file_list[i].split('/')[-1].split('.')[-2])
			b = encode(file_list[i+1].split('/')[-1].split('.')[-2])

			if _a != _b:
		 		continue 

			if a > b:
				temp = file_list[i+1]
				file_list[i+1] = file_list[i]
				file_list[i] = temp

	content_path = os.path.join(path_, 'content.txt')
	with open(content_path, 'w') as file:
		for i in file_list:
			to_file = i + '\n'
			file.write(to_file)

		file.write('0\n')

	img_ = get_img(file_list[0])
	title_ = '{name}--{i}/{l}'.format(name=file_list[id_].split('/')[-2], i=id_, l=length)
	win.title(title_)
	label.configure(image = img_)
	label.image = img_
	sub.destroy()

def show_next_img(event):
	global img_, id_, length
	del img_
	id_ = id_ + 1
	if id_ > length-1:
		id_ = 0
	title_ = '{name}--{i}/{l}'.format(name=file_list[id_].split('/')[-2], i=id_, l=length)
	win.title(title_)
	img_ = get_img(file_list[id_])
	label.configure(image = img_)
	label.image = img_

def show_last_img(event):
	global img_, id_, length
	del img_
	id_ = id_ - 1
	if id_ < 0:
		id_ = length-1
	title_ = '{name}--{i}/{l}'.format(name=file_list[id_].split('/')[-2], i=id_, l=length)
	win.title(title_)
	img_ = get_img(file_list[id_])
	label.configure(image = img_)
	label.image = img_

def jump(event):
	global img_, id_, length
	go_to = askstring(title='pages', prompt='pages')
	ret = re.match('[+-]*[0-9]{,}', go_to)
	try:
		want = ret.group()
		if '+' in want:
			id_ += int(want.strip("+"))
		elif '-' in want:
			id_ -= int(want.strip("-"))
			if id_ < 0:
				id_ = length + id_
		else:
			id_ = int(want)
	except AttributeError:
		return

	try:
		id_ = id_%length
		title_ = '{name}--{i}/{l}'.format(name=file_list[id_].split('/')[-2], i=id_, l=length)
		win.title(title_)
		del img_
		img_ = get_img(file_list[id_])
		label.configure(image = img_)
		label.image = img_
	except TypeError:
		pass

def close_():
	global file_list, content_path, id_
	with open(content_path, 'w+') as file:
		file_list.append(str(id_))
		for i in file_list:
			to_file = i + '\n'
			file.write(to_file)
	win.destroy()

label = tkinter.Label(win, image=img_)
label.pack()
button_1 = tkinter.Button(sub, text='use file', width=20, height=2, command=use_file)
button_2 = tkinter.Button(sub, text='use dir', width=20, height=2, command=use_dir)
button_1.pack()
button_2.pack()

win.bind('<Up>', show_last_img)
win.bind('<Right>', show_next_img)
win.bind('<Down>', show_next_img)
win.bind('<Left>', show_last_img)
win.bind('<Tab>', jump)
win.protocol("WM_DELETE_WINDOW", close_)
win.mainloop()
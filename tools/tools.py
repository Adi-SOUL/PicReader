import re
import threading
from typing import Tuple

from PIL import Image


def get_img(img_file: str, ratio: float, img_pil: Image = None) -> Tuple[Image.Image, Image.Image, str]:
	if img_pil is None:
		img = Image.open(img_file).convert('RGB')
	else:
		img = img_pil
	w, h = img.size
	factor_for_label = 1440 * ratio / h if h >= w else 1900 * ratio / w
	factor_for_button = 480 * ratio / h if h >= w else 400 * ratio / w
	img_for_label = img.resize(
		(int(factor_for_label * w), int(factor_for_label * h))
	)
	img_for_button = img.resize(
		(int(factor_for_button * w), int(factor_for_button * h))
	)
	return img_for_label, img_for_button, img_file


def encode(_str: str) -> int:
	num = re.findall('\d+', _str)
	try:
		_num_list = [str(int(i)) for i in num]
		_num_str = ''.join(_num_list)
		_num = int(_num_str)
	except IndexError:
		_num = 0
	except ValueError:
		_num = 0
	return _num


def thread_func(func, kwargs=None) -> threading.Thread:
	thread = threading.Thread(target=func, kwargs=kwargs)
	thread.Daemon = True
	thread.start()
	return thread


def flatten(_list: list) -> list:
	res = sum(([x] if not isinstance(x, list) else flatten(x) for x in _list), [])
	return res

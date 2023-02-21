import re
import threading
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
from typing import Tuple


def get_img(img_file: str, ratio: float, img_pil: Image = None) -> Tuple[Image.Image, Image.Image, str]:
	if img_pil is None:
		img = Image.open(img_file)
	else:
		img = img_pil
	w, h = img.size
	# label_size = (int(1440 * ratio * w / h), int(1440 * ratio)) if h >= w else (int(1900 * ratio), int(1900 * ratio * h / w))
	button_size = (int(480 * ratio * w / h), int(480 * ratio)) if h >= w else (int(400 * ratio), int(400 * ratio * h / w))
	img_for_label = img
	# img_for_label = img.resize(label_size)
	img_for_button = img.resize(button_size)
	return img_for_label, img_for_button, img_file


def encode(_str: str) -> int:
	num = re.findall('\d+', _str)
	if num:
		return max(0, min(int(''.join(num)), 2147483647))
	else:
		return 0


def thread_func(func, kwargs=None) -> threading.Thread:
	thread = threading.Thread(target=func, kwargs=kwargs)
	thread.Daemon = True
	thread.start()
	return thread


def flatten(_list: list) -> list:
	res = sum(([x] if not isinstance(x, list) else flatten(x) for x in _list), [])
	return res


# From ChatGPT
def find_longest_common_prefix(lists):
	if not lists:
		return []

	it = zip(*lists)
	res = []
	for group in it:
		if all(x == group[0] for x in group):
			res.append(group[0])
		else:
			break
	return res

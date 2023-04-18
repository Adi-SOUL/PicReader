import re
import threading
from PIL import Image
from cn_clip.clip import load_from_name
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
from typing import Tuple, List
from torch.cuda import is_available
from torch import no_grad
from PIL import Image

from cn_clip import clip


def get_img(
		img_file: str,
		ratio: float,
		full_size=False,
		img_pil: Image = None
) -> Tuple[None, None, None] | Tuple[Image.Image, Image.Image, str]:
	if img_pil is None:
		try:
			img = Image.open(img_file)
		except FileNotFoundError:
			return None, None, None
	else:
		img = img_pil
	w, h = img.size
	button_size = (
		int(480 * ratio * w / h),
		int(480 * ratio)
	) if h >= w else (
		int(400 * ratio),
		int(400 * ratio * h / w)
	)
	factor_for_label = 1440 * ratio / h if h >= w else 1900 * ratio / w
	img_for_button = img.resize(button_size)
	img_for_label = img.resize(
		(int(factor_for_label * w), int(factor_for_label * h))
	) if not full_size else img
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


def clip_sort(files: List[str], text: str) -> List[str]:
	device = "cuda" if is_available() else "cpu"
	model, preprocess = load_from_name("ViT-L-14", device=device, download_root='./')
	model.eval()
	_text = clip.tokenize([text]).to(device)
	res_dict = dict()
	with no_grad():
		for img_file in files:
			image = preprocess(Image.open(img_file)).unsqueeze(0).to(device)
			image_features = model.encode_image(image)
			text_features = model.encode_text(_text)
			image_features /= image_features.norm(dim=-1, keepdim=True)
			text_features /= text_features.norm(dim=-1, keepdim=True)
			similarity = text_features.cpu().numpy() @ image_features.cpu().numpy().T
			similarity = similarity[0][0]
			res_dict[img_file] = similarity

	files.sort(key=lambda img_name: res_dict[img_name])
	files.reverse()
	return files

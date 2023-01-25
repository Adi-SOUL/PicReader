import json
import os

import psutil


class HandleFileError(Exception):
	def __init__(self):
		super().__init__()


if os.name == 'nt':
	path_str = '\\'
	save_id_path = '\\'.join([os.path.expanduser('~'), 'AppData', 'Roaming', 'PicReader'])
else:
	path_str = '/'
	save_id_path = '/'.join([os.path.expanduser('~'), 'PicReader'])
if not os.path.exists(save_id_path):
	os.mkdir(save_id_path)
json_path = path_str.join([save_id_path, 'readHistory.json'])
try:
	with open(json_path, 'r', encoding='utf-8') as json_file:
		test_open = json.load(json_file)
except (json.decoder.JSONDecodeError, FileNotFoundError):
	init_in = {}
	with open(json_path, 'w', encoding='utf-8') as json_file:
		json.dump(init_in, json_file)

CPU_NUM = psutil.cpu_count()
MEM_STATUS = float(psutil.virtual_memory().total) / 1024 / 1024 / 1024 > 16.
SCAL_STD = 0.625

discarded_layers = []

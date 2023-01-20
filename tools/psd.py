import os
from concurrent.futures import ProcessPoolExecutor

from psd_tools import PSDImage

from . import path_str, discarded_layers, HandleFileError


def convert(file: str) -> None:
	psd = PSDImage.open(file)
	img = psd.composite(layer_filter=lambda x: x.is_visible() and (False if x.name in discarded_layers else True))
	new_file_path = '.'.join(file.split('.')[:-1]+['png'])
	img.save(new_file_path)


class PSDHelper:
	def __init__(self, path):
		if path == '':
			raise HandleFileError
		if os.path.isfile(path):
			self.psd_list = [path]
		else:
			self.psd_list = []
			for __dir_path, __dir_name, __file_names in os.walk(path):
				__dir_path = path_str.join(__dir_path.split('/'))
				for __file_name in __file_names:
					psd_file = path_str.join([__dir_path, __file_name])
					extent = __file_name.split('.')[-1].lower()
					if extent == 'psd' and os.path.getsize(psd_file) > 2e5:
						self.psd_list.append(psd_file)

	def run(self):
		with ProcessPoolExecutor() as executor:
			res = executor.map(convert, self.psd_list)

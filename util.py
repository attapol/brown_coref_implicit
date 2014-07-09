
from codecs import open as copen
from multiprocessing import Process
import re
import subprocess

def convert_to_two_char_string(number):
	"""Convert two numeric characters into string with leading zero. """
	if number < 10:
		return '0%s' % number
	else:
		return '%s' % number

def make_singleton_sequence_data_file(data, naming_function, label_function, feature_function_list,
		output_file_name, incremental=False, use_gold=False):
	if incremental:
		data_file = copen(output_file_name, mode='a', encoding='latin1')
	else:
		data_file = copen(output_file_name, mode='w', encoding='latin1')

	data_file.write('\n')
	for name, feature_vector, label, _, in generate_instance(data, naming_function, label_function, feature_function_list, use_gold):
		if len(feature_vector) == 0:
			data_file.write('NO_FEATURE ')
		else:
			feature_string = '%s ' % ' '.join(feature_vector)
			feature_string = re.sub(':','COLON', feature_string)
			data_file.write(feature_string)
		data_file.write('\t%s\t%s\n' % (label, name))
	data_file.close()	

def convert_sqlite_row_to_dict(sqlite_row):
	row_dict = {}
	for key in sqlite_row.keys():
		row_dict[key] = sqlite_row[key]
	return row_dict


def _merge_data_files():
	subprocess.call('cat sec*training_set.csv',
		stdout=open('training_set.csv', 'w'), shell=True)
	subprocess.call('cat sec*test_set.csv',
		stdout=open('test_set.csv', 'w'), shell=True)
	subprocess.call('rm sec*.csv', shell=True)

def run_multiple_threads(num_threads, naming_function, label_function, feature_function_list, 
						maker_function, make_file, make_db, use_gold):
	"""Run multithreaded make data file_name
	
	According to PDTB manual, evaluation procedure should use the following partitioning scheme:
	section 2 - 21 are used for training
	section 22 for dev
	section 23 for test

	In Pitler 2009, 2-20 is training. 21-22 is testing.

	maker_function should have the following arguments:
		naming_function
		label_function
		feature_function_list
		section_numbers : a list of section numbers 
		output_file_name : a file name to write features to
		make_file : making the feature matrix file or no
		make_db : writing to the db or no. this is convenient for pipeline architecture 
		use_gold : using gold standard features or no
	"""
	make_file = True
	make_db = False
	num_threads_training = num_threads - 1
	sections_per_threads = 20 / (num_threads_training)
	procs = []
	for i in range(num_threads_training):
		start_sec = 2 + (i * sections_per_threads)
		if i == num_threads_training - 1:
			end_sec = 20 + 1
			#end_sec = 21 + 1
		else:
			end_sec = 2 + ((i + 1) * sections_per_threads)
		file_name = 'sec_%s_%s_training_set.csv' % (start_sec, end_sec - 1)
		p = Process(target=maker_function, \
				args= (naming_function, label_function, feature_function_list, range(start_sec, end_sec), file_name, make_file, make_db, use_gold))
		procs.append(p)
	p = Process(target=maker_function, \
			args= (naming_function, label_function, feature_function_list, [21, 22], 'sec_21_22_test_set.csv', make_file, make_db, use_gold))
	procs.append(p)
	for p in procs: p.start()
	for p in procs: p.join()
	_merge_data_files()


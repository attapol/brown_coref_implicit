import json
from tpl.testing import assert_le, assert_ge, assert_eq

def enum(*sequential, **named):
	"""Enum for python
	 a little hacky but works

	 >>> Numbers = enum('ZERO', 'ONE', 'TWO')
	 >>> Numbers.ZERO
	 0
	"""
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)

def cbind(filename1, filename2, output_filename):
	"""Concatenate column-wise two files of equal number of lines
	
	If I end up using this often, I should separate it and make it a unix-like util	
	"""
	file1 = open(filename1).readlines()
	file2 = open(filename2).readlines()
	output_file = open(output_filename, mode='w')
	assert_eq(len(file1), len(file2))
	for line1, line2 in zip(file1, file2):
		output_file.write('%s %s\n' % (line1.strip(), line2.strip()))

def slice_list(li, num_chunks):
	"""Slice list into chunks of equal sizes 

	"""
	assert_ge(num_chunks, 1)
	start = 0
	result = []
	for i in xrange(num_chunks):
		stop = start + len(li[i::num_chunks])
		result.append(li[start:stop])
		start = stop
	return result

def convert_to_two_char_string(number):
	"""Convert two numeric characters into string with leading zero. """
	assert_ge(number, 0)
	assert_le(number, 99)
	if number < 10:
		return '0%s' % number
	else:
		return '%s' % number

class TJsonEncoder (json.JSONEncoder):
	"""Use it with json.loads for some objects

	This is handy when to_dict has been implemented for the object. 
	"""
	def default(self, obj):
		if 'to_dict' in dir(obj):
			return obj.to_dict()
		else:
			return json.JSONEncoder.default(self, obj)

def matrix_to_string(matrix, header=None):
	"""
	Return a pretty, aligned string representation of a nxm matrix.

	This representation can be used to print any tabular data, such as
	database results. It works by scanning the lengths of each element
	in each column, and determining the format string dynamically.

	the implementation is adapted from here
	mybravenewworld.wordpress.com/2010/09/19/print-tabular-data-nicely-using-python/

	Args:
		matrix - Matrix representation (list with n rows of m elements).
		header -  Optional tuple or list with header elements to be displayed.

	Returns:
		nicely formatted matrix string
	"""

	if isinstance(header, list):
		header = tuple(header)
	lengths = []
	if header:
		lengths = [len(column) for column in header]

	#finding the max length of each column
	for row in matrix:
		for column in row:
			i = row.index(column)
			column = str(column)
			column_length = len(column)
			try:
				max_length = lengths[i]
				if column_length > max_length:
					lengths[i] = column_length
			except IndexError:
				lengths.append(column_length)

	#use the lengths to derive a formatting string
	lengths = tuple(lengths)
	format_string = ""
	for length in lengths:
		format_string += "%-" + str(length) + "s "
	format_string += "\n"

	#applying formatting string to get matrix string
	matrix_str = ""
	if header:
		matrix_str += format_string % header
	for row in matrix:
		matrix_str += format_string % tuple(row)

	return matrix_str

"""Populate relation database for experiment setup

This should be run after the parses table is in place and populated.
We need to look up the argument location (wsj_id, sentence_id) from the parse tables.

The entire table should take ~470 seconds to populate with two cores.
We use two cores because they have to query the parse tables... More cores slow down the process.
"""
import sqlite3
from multiprocessing import Process
from os.path import expanduser

from tpl.testing import assert_eq
from tpl.sqlite3_util import insert_rows
from tpl.timer import Timer
from tpl.pdtb_tools.corpus import CorpusReader
from tpl.pdtb_tools.util import locate_sentence


def make_row(relation):
	"""Make a tuple from a relation object
	
	This tuple factory assumes the schema to have specific fields.
	"""
	arg1_span = (relation.arg1.selection.span_ranges[0][0],
		relation.arg1.selection.span_ranges[-1][1])
	arg2_span = (relation.arg2.selection.span_ranges[0][0],
		relation.arg2.selection.span_ranges[-1][1])

	arg1_sentence_id, _ = locate_sentence(arg1_span, relation.wsj_section, 'db_pdtb.sqlite')
	arg2_sentence_id, _ = locate_sentence(arg2_span, relation.wsj_section, 'db_pdtb.sqlite')

	try:
		row = {
			'wsj_section': relation.wsj_section_number,
			'wsj_id': relation.wsj_section,
			'arg1_sentence_id': arg1_sentence_id,
			'arg2_sentence_id': arg2_sentence_id,
			'relation_json': str(relation),
			'sense': relation.relation_sense_tags(1)[0],
			'relation_type': relation.type
		}
	except Exception as e:
		print relation
		raise e
	return row


def populate_all_relations_from_sections(section_numbers):
	predicate = lambda x: x.wsj_section_number in section_numbers
	table_name = 'relations'
	populate_relations_from_sections(section_numbers, predicate, table_name)

def populate_relations_from_sections(section_numbers, predicate, table_name):
	"""Populate relation table

	This function makes it easy to selectively add tuples to table table_name
	that satisfies a predicate and comes from certain section numbers.
	The table has to be created before hand. 

	"""
	home = expanduser('~')
	corpus = CorpusReader('%s/nlp/wsj/python_pdtb/wsj_pdtb.jsons' % home)
	rows = []
	for relation in corpus.select(predicate):
		rows.append(make_row(relation))
	con = sqlite3.connect('db_pdtb.sqlite', check_same_thread = False, timeout=60.0 * 30, isolation_level='EXCLUSIVE')
	cur = con.cursor()
	insert_rows(cur, table_name, rows)
	con.commit()


def run_multiple_threads(num_threads):
	sections_per_threads = 24 / num_threads
	procs = []
	for i in range(num_threads):
		if i == num_threads - 1:
			p = Process(target=populate_all_relations_from_sections, 
				args=(range(i * sections_per_threads, 24 + 1),))
		else:
			p = Process(target=populate_all_relations_from_sections, 
				args=(range(i * sections_per_threads, (i + 1) * sections_per_threads),))
		procs.append(p)
	with Timer('Populate the database with relevant relations'):
		for p in procs: p.start()
		for p in procs: p.join()

def test():
	assert_eq(locate_sentence((95,110), '0001'), 1)
	populate_all_relations_from_sections([0])

if __name__ == '__main__':
	run_multiple_threads(2)

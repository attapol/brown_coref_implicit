from codecs import open as copen
import glob
import json
from multiprocessing import Process
import re
import sys
import sqlite3

from tpl.clause_splitting import split_clauses_from_sentence
from tpl.misc import TJsonEncoder, slice_list
from tpl.sqlite3_util import insert_rows
from tpl.timer import Timer

def extract_rows(auto_parsed_file_name):
	wsj_id_re = re.compile('wsj_(\d\d\d\d)')
	wsj_id = wsj_id_re.search(auto_parsed_file_name).group(1)
	corenlp_result = json.loads(copen(auto_parsed_file_name, mode='r').read())
	sentences = corenlp_result['sentences']
	rows = []
	for i, sentence in enumerate(sentences):
		split_clauses_from_sentence(sentence)
		sentence_start = sentence['words'][0][1]['CharacterOffsetBegin']
		sentence_end = sentence['words'][-1][1]['CharacterOffsetEnd']
		parse_json_string = json.dumps(sentence, cls=TJsonEncoder)
		coref_json_string = json.dumps([])
		if 'coref' in corenlp_result:
			coref_json_string = json.dumps(corenlp_result['coref'])
		row = {
			'wsj_section': int(wsj_id[0:2]),
			'wsj_id': wsj_id,
			'sentence_id': i,
			'parse_json': parse_json_string,
			'sentence_start': sentence_start,
			'sentence_end': sentence_end,
			'sentence_text': sentence['text'],
			'coreference_json': coref_json_string
		}
		rows.append(row)
	return rows


def populate_parses_from_files(file_names):
	rows = []
	for auto_parsed_file_name in file_names:
		print auto_parsed_file_name
		rows.extend(extract_rows(auto_parsed_file_name))
	con = sqlite3.connect('db_pdtb.sqlite', check_same_thread=False, 
			timeout=60.0 * 30, isolation_level="EXCLUSIVE")
	cur = con.cursor()
	print 'Writing %s rows' % len(rows)
	insert_rows(cur, 'parses', rows)
	con.commit()	
	print 'Finished writing %s rows' % len(rows)

def populate_new_parses(auto_parsed_root):
	file_names = glob.glob('%s/*' % auto_parsed_root)
	procs = [Process(target=populate_parses_from_files, args=(chunk,)) for chunk in slice_list(file_names, 8)]
	with Timer('Populate the database with parses'):
		for p in procs:
			p.start()
		for p in procs:
			p.join()


if __name__ == '__main__':
	populate_new_parses(sys.argv[1])

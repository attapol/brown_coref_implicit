import sqlite3

def get_partition_type(wsj_id):
	wsj_section = int(wsj_id[0:2])
	if wsj_section in range(2,21 + 1):
		return 'train'
	elif wsj_section == 24:
		return 'test'
	elif wsj_section == 0 or wsj_section == 1 or \
			wsj_section == 22 or wsj_section == 24:
		return 'dev'
	else:
		return 'unknown'

def get_indices_from_span_ranges(span_ranges, parse):
	"""Get the token position indices from the character offset 

	Arguments:
		span_ranges : a list of pairs each of which is (start, end) character offset
		parse : the parse of the sentence. A dictionary with parse format from my parser
	"""
	indices = []
	if span_ranges is None:
		return []
	for span_range in span_ranges:
		for i, word in enumerate(parse['words']):
			word_string = word[0]
			word_info_dict = word[1]
			start = int(word_info_dict['CharacterOffsetBegin'])
			end = int(word_info_dict['CharacterOffsetEnd'])
			if span_range[0] <= start <= end <= span_range[1]:
				indices.append(i)
	return indices

def locate_sentence(span, wsj_id, db_file_name):
	conn = sqlite3.connect(db_file_name, check_same_thread=False, isolation_level="DEFERRED")
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	sql_command = """SELECT sentence_id, parse_json FROM parses WHERE wsj_id = "%s" AND
		sentence_start < %s AND %s <= sentence_end  """ %  \
		(wsj_id, span[1], span[1]) 
	cur.execute(sql_command)
	row = cur.fetchone()
	try:
		sentence_id = int(row['sentence_id'])
		parse_json = row['parse_json']
		return sentence_id, parse_json
	except:
		print sql_command
		print span
		return -1, None
	

import glob
import re
import sys
from collections import deque, OrderedDict
from codecs import open as copen
from tpl.pdtb_tools.corpus import Corpus

		
def parse_pdtb_file(pdtb_file_name):
	relation_jsons = []
	with copen(pdtb_file_name, mode='r', encoding='latin1') as f:
		lines = deque([x for x in f.readlines()])
	while len(lines) > 0:
		relation_json = relation(lines)
		relation_jsons.append(relation_json)
	return relation_jsons

termination_line = '_____'

stack_buffer = []

def relation(lines):
	relation_dict = OrderedDict()
	first_line = lines.popleft()
	assert (termination_line in first_line)
	line = lines.popleft()
	if '_AltLex_' in line:
		relation_dict = altLexRelation(lines)
	elif '_Explicit_' in line:
		relation_dict = explicitRelation(lines)
	elif '_Implicit_' in line:
		relation_dict = implicitRelation(lines)	
	elif '_EntRel_' in line:
		relation_dict = entityRelation(lines)
	elif '_NoRel_' in line:
		relation_dict = noRelation(lines)
	#print json.dumps(relation_dict, indent=3)
	last_line = lines.popleft()
	assert (termination_line in last_line)
	return relation_dict	

def altLexRelation(lines):
	relation = OrderedDict()
	relation['type'] = 'AltLex'
	relation['selection'] = selection(lines)
	relation['altLexRelationFeatures'] = altLexRelationFeatures(lines)
	relation['sup1'] = sup(lines)
	relation['arg1'] = arg(lines)
	relation['arg2'] = arg(lines)
	relation['sup2'] = sup(lines)
	return relation

def explicitRelation(lines):
	relation = OrderedDict()
	relation['type'] = 'Explicit'
	relation['selection'] = selection(lines)
	relation['explicitRelationFeatures'] = explicitRelationFeatures(lines)
	relation['sup1'] = sup(lines)
	relation['arg1'] = arg(lines)
	relation['arg2'] = arg(lines)
	relation['sup2'] = sup(lines)
	return relation
	

def implicitRelation(lines):
	relation = OrderedDict()
	relation['type'] = 'Implicit'
	relation['inferenceSite'] = inferenceSite(lines)
	relation['implicitRelationFeatures'] = implicitRelationFeatures(lines)
	relation['sup1'] = sup(lines)
	relation['arg1'] = arg(lines)
	relation['arg2'] = arg(lines)
	relation['sup2'] = sup(lines)
	return relation

def entityRelation(lines):
	relation = OrderedDict()
	relation['type'] = 'EntRel'
	relation['inferenceSite'] = inferenceSite(lines)
	relation['arg1'] = arg_no_attribution(lines)
	relation['arg2'] = arg_no_attribution(lines)
	return relation

def noRelation(lines):
	relation = OrderedDict()
	relation['type'] = 'NoRel'
	relation['inferenceSite'] = inferenceSite(lines)
	relation['arg1'] = arg_no_attribution(lines)
	relation['arg2'] = arg_no_attribution(lines)
	return relation

def sup(lines):
	head = lines.popleft()
	if '__Sup' not in head:
		lines.appendleft(head)
		return OrderedDict()
	else:
		return {'selection': selection(lines)} 

def arg(lines):
	first_line = lines.popleft()
	if '__Arg' not in first_line:
		Exception(' ')
		return OrderedDict()
	else:
		result = OrderedDict()	
		result['selection'] = selection(lines)
		result['attributionFeatures'] = attributionFeatures(lines)
		return result

def arg_no_attribution(lines):
	if '__Arg' not in lines.popleft():
		return OrderedDict()
	else:
		return {'selection': selection(lines)}
	

span_list_pattern = re.compile('\d+\.\.\d+')
def selection(lines):
	line = lines[0]
	if not span_list_pattern.match(line):
		return OrderedDict()	
	relation = OrderedDict()
	relation['SpanList'] = terminal(lines)
	relation['GornAddressList'] = terminal(lines)
	relation['RawText'] = rawText(lines)
	return relation

def rawText(lines):
	if '#### Text' not in lines[0]:
		return OrderedDict()
	terminal(lines)
	result = ''
	while True:
		line = terminal(lines)
		if len(line) > 0 and line[0] == '#':
			return result
		result += line

def inferenceSite(lines):
	relation = OrderedDict()
	relation['StringPosition'] = terminal(lines)
	relation['SentenceNumber'] = terminal(lines)
	return relation

def explicitRelationFeatures(lines):
	relation = OrderedDict()
	relation['attributionFeatures'] = attributionFeatures(lines)
	relation['Conn1'] = connective(lines)
	return relation

def altLexRelationFeatures(lines):
	relation = OrderedDict()
	relation['attributionFeatures'] = attributionFeatures(lines)
	relation['SemanticClass'] = semanticClass(lines)
	return relation

def implicitRelationFeatures(lines):
	relation = OrderedDict()
	relation['attributionFeatures'] = attributionFeatures(lines)
	relation['Conn1'] = connective(lines)
	#check for an extra connective
	success = try_parse([connective], lines)
	if success: 
		relation['Conn2'] = connective(lines)
	return relation

semantic_class_pattern = re.compile('\w+\.\w+')
def semanticClass(lines):
	return terminal(lines)
	line = lines[0]
	if not semantic_class_pattern.match(line):
		return OrderedDict()
	else:
		return terminal(lines)

connective_pattern = re.compile("[a-zA-Z' ]+, [A-Z]")
def connective(lines):
	line = lines[0]
	if not connective_pattern.match(line):
		return OrderedDict()
	else:
		return terminal(lines)

def attributionFeatures(lines):
	result = OrderedDict()
	if '### Features' not in lines[0]:
		return OrderedDict()
	terminal(lines)
	result['Attribution'] = terminal(lines)
	if span_list_pattern.match(lines[0]):
		result['selection'] = selection(lines)
	return result
	

def terminal(lines):
	if len(lines) == 0:
		return OrderedDict()
	terminal_string = lines.popleft()
	stack_buffer.append(terminal_string)
	if termination_line in terminal_string:
		return OrderedDict()
	else:
		return terminal_string.strip()


def try_parse(option, lines):
	stack_buffer = []
	for symbol in option:
		result = symbol(lines)
		#parsing failed. rolling back from the stack buffer
		if result == OrderedDict():
			while len(stack_buffer) > 0:
				lines.appendleft(stack_buffer.pop())
			return False
	while len(stack_buffer) > 0:
		lines.appendleft(stack_buffer.pop())
	return True
	
if __name__ == '__main__':
	pdtb_files = glob.glob(sys.argv[1])

	wsj_pattern = re.compile('wsj_(\d\d\d\d)')
	corpus = Corpus()

	for file_name in pdtb_files:
		print file_name
		wsj_section = wsj_pattern.search(file_name).group(1)
		relation_jsons = parse_pdtb_file(file_name)
		print len(relation_jsons)
		corpus.add_relations(wsj_section, relation_jsons)



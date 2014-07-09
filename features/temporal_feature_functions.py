
import json
import os
from collections import Counter

from nltk.tree import Tree

from tpl.language.syntactic_structure import DependencyGraph
from tpl.pdtb_tools.relation import Relation
from tpl.pdtb_tools.util import get_indices_from_span_ranges


def temporal_label_function(instance):
	if len(instance['arg1_token_indices']) == 0 or len(instance['arg2_token_indices']) == 0 or \
		instance['relation_type'] == 'EntRel' or instance['relation_type'] == 'NoRel':
		return None

	has_temporal = 'Temporal' in instance['relation'].relation_sense_tags_at_level(0)
	if has_temporal:
		return 'Temporal'
	else:
		return 'no'

def subclass_temporal_label_function(instance):
	"""Synchrony and Asynchrony
	
	not tested yet. Will get back here when we have most features down	
	"""
	relation_sense_tags = instance['relation'].relation_sense_tags(1)
	second_conn_sense_tags = instance['relation'].relation_sense_tags(2)
	if second_conn_sense_tags is not None:
		relation_sense_tags.extend(second_conn_sense_tags)

	for sense in relation_sense_tags:
		if len(sense.split('.')) > 1:
			subclass_sense = sense.split('.')[1]
			if subclass_sense == 'Asynchronous' or subclass_sense == 'Synchrony':
				#XXX: Assume mutual exclusivity here
				return subclass_sense
	return 'Not_temporal'

def subsubclass_temporal_label_function(instance):
	"""Precedence, Succesion, and Synchrony"""
	pass

def _get_majority_head_verb_index(parse, token_indices):
	word_index_to_head_verb_index = parse['word_index_to_head_verb_index']
	head_verb_indices = [int(word_index_to_head_verb_index[str(x)]) \
			for x in token_indices if str(x) in word_index_to_head_verb_index]
	if len(head_verb_indices) == 0:
		return None
	majority_head_verb_index = Counter(head_verb_indices).most_common(1)[0][0]
	return majority_head_verb_index

def initialization_feature(instance, use_gold=False):
	instance['relation'] = Relation.from_json(instance['relation_json'])
	relation = instance['relation']
	instance['arg1_parse'] = json.loads(instance['arg1_parse_json'])
	instance['arg2_parse'] = json.loads(instance['arg2_parse_json'])
	if instance['arg1_parse']['dependency_tree'] is not None:
		instance['arg1_dependency_tree'] = DependencyGraph.from_dict(instance['arg1_parse']['dependency_tree'])
	else:
		instance['arg1_dependency_tree'] = None
	if instance['arg2_parse']['dependency_tree'] is not None:
		instance['arg2_dependency_tree'] = DependencyGraph.from_dict(instance['arg2_parse']['dependency_tree'])
	else:
		instance['arg2_dependency_tree'] = None

	instance['parse_tree1'] = Tree(instance['arg1_parse']['parsetree'])
	instance['parse_tree2'] = Tree(instance['arg2_parse']['parsetree'])
	instance['arg1_token_indices'] = \
		get_indices_from_span_ranges(relation.arg1.text_span_ranges, instance['arg1_parse'])
	instance['arg2_token_indices'] = \
		get_indices_from_span_ranges(relation.arg2.text_span_ranges, instance['arg2_parse'])

	instance['sentence1_tokens'] = [x[0] for x in instance['arg1_parse']['words']]
	instance['sentence2_tokens'] = [x[0] for x in instance['arg2_parse']['words']]
	
	instance['arg1_majority_head_verb_index'] = \
		_get_majority_head_verb_index(instance['arg1_parse'], instance['arg1_token_indices'])
	instance['arg2_majority_head_verb_index'] = \
		_get_majority_head_verb_index(instance['arg2_parse'], instance['arg2_token_indices'])

	return []

def first_last_pairs(instance, use_gold=False):
	sentence1_tokens = instance['sentence1_tokens']
	sentence2_tokens = instance['sentence2_tokens']
	arg1_token_indices = instance['arg1_token_indices']
	arg2_token_indices = instance['arg2_token_indices']
	feature_vector = [
		'F1L1=%s_%s' % (sentence1_tokens[arg1_token_indices[0]], sentence1_tokens[arg1_token_indices[-1]]),
		'F1F2=%s_%s' % (sentence1_tokens[arg1_token_indices[0]], sentence2_tokens[arg2_token_indices[0]]),
		'L1L2=%s_%s' % (sentence1_tokens[arg1_token_indices[-1]], sentence2_tokens[arg2_token_indices[-1]]),
		]
	for i, feature in enumerate(feature_vector):
		if ':' in feature:
			feature_vector[i] = feature.replace(':','COLON')
	return feature_vector

def all_words(instance, use_gold=False):
	sentence1_tokens = instance['sentence1_tokens']
	sentence2_tokens = instance['sentence2_tokens']
	arg1_token_indices = instance['arg1_token_indices']
	arg2_token_indices = instance['arg2_token_indices']
	feature_vector = []
	feature_vector.extend([sentence1_tokens[x] for x in arg1_token_indices])
	feature_vector.extend([sentence2_tokens[x] for x in arg2_token_indices])
	for i, feature in enumerate(feature_vector):
		if ':' in feature:
			feature_vector[i] = feature.replace(':','COLON')
	return feature_vector


def _get_first_three(token_indices, tokens):
	feature_vector = []
	for i in range(min(3, len(token_indices))):
		token_index = token_indices[i]
		feature_vector.append(tokens[token_index].replace(':','COLON'))
	return '_'.join(feature_vector)
	
def first_three(instance, use_gold=False):
	sentence1_tokens = instance['sentence1_tokens']
	sentence2_tokens = instance['sentence2_tokens']
	arg1_token_indices = instance['arg1_token_indices']
	arg2_token_indices = instance['arg2_token_indices']
	feature_vector = []
	feature_vector.append(_get_first_three(arg1_token_indices, sentence1_tokens))
	feature_vector.append(_get_first_three(arg2_token_indices, sentence2_tokens))
	return feature_vector

def _contains_timex(token_indices, parse):
	has_timex = False
	for i in token_indices:
		token, word_info = parse['words'][i]
		if word_info['NamedEntityTag'] == 'DATE':
			has_timex = True
			break
	return has_timex

def has_time_expressions(instance, use_gold=False):
	arg1_parse = instance['arg1_parse'] 
	arg1_token_indices = instance['arg1_token_indices']
	arg1_has_timex = _contains_timex(arg1_token_indices, arg1_parse)
	
	arg2_parse = instance['arg2_parse']
	arg2_token_indices = instance['arg2_token_indices']
	arg2_has_timex = _contains_timex(arg2_token_indices, arg2_parse)

	feature_vector = []
	if arg1_has_timex and arg2_has_timex:
		feature_vector.append('ARG1_ARG2_TIMEX')
	elif arg1_has_timex:
		feature_vector.append('ARG1_TIMEX')	
	elif arg2_has_timex:
		feature_vector.append('ARG2_TIMEX')
	return feature_vector


def _get_timex(token_indices, parse):
	timex_list = []
	current_timex = None
	for i in token_indices:
		token, word_info = parse['words'][i]
		NER_tag = word_info['NamedEntityTag']
		if NER_tag == 'DATE' or NER_tag == 'DURATION' or NER_tag == 'SET':
			current_timex = NER_tag
		else:
			if current_timex is not None:
				timex_list.append(current_timex)
				current_timex = None
	if len(timex_list) == 0:
		timex_list.append('NO_TIMEX')
	return timex_list

def time_expression_list(instance, use_gold=False):
	arg1_parse = instance['arg1_parse'] 
	arg1_token_indices = instance['arg1_token_indices']
	arg1_timex_list = _get_timex(arg1_token_indices, arg1_parse)
	
	arg2_parse = instance['arg2_parse']
	arg2_token_indices = instance['arg2_token_indices']
	arg2_timex_list = _get_timex(arg2_token_indices, arg2_parse)

	feature_vector = []
	for arg1_timex in arg1_timex_list:
		feature_vector.append('ARG1_TIMEX_TYPE=%s' % arg1_timex)
	for arg2_timex in arg2_timex_list:
		feature_vector.append('ARG2_TIMEX_TYPE=%s' % arg2_timex)
	for arg1_timex in arg1_timex_list:
		for arg2_timex in arg2_timex_list:
			feature_vector.append('ARG1_ARG2_TIMEX_TYPE=%s_%s' % (arg1_timex, arg2_timex))
	return feature_vector

def _get_production_rules(parse_tree, token_indices):
	"""Find all of the production rules from the subtree that spans over the token indices

	Args:
		parse_tree : an nltk tree object that spans over the sentence that the arg is in
		token_indices : the indices where the arg is.

	Returns:
		a set of production rules used over the argument

	"""
	if len(token_indices) == 1:
		tree_position = parse_tree.leaf_treeposition(token_indices[0])
		arg_subtree = parse_tree[tree_position[0:-1]]
	else:
		start_index = min(token_indices)
		end_index = max(token_indices) + 1
		tree_position = parse_tree.treeposition_spanning_leaves(start_index, end_index)
		arg_subtree = parse_tree[tree_position]

	rule_set = set()
	try:
		for rule in arg_subtree.productions():
			s = rule.__str__()
			#we want to skip all of the unary production rules
			if "'" not in s and 'ROOT' not in s:
			#if 'ROOT' not in s:
				s = s.replace(' -> ', '->')
				s = s.replace(' ','_')
				s = s.replace(':','COLON')
				rule_set.add(s)
	except:
		pass
	return rule_set

def production_rules(instance, use_gold=False):

	rule_set1 = _get_production_rules(instance['parse_tree1'], instance['arg1_token_indices'])
	rule_set2 = _get_production_rules(instance['parse_tree2'], instance['arg2_token_indices'])

	rule_set1_only = rule_set1 - rule_set2 
	rule_set2_only = rule_set2 - rule_set1 

	feature_vector = []
	for rule in rule_set1.intersection(rule_set2):
		feature_vector.append('BOTH_ARGS_RULE=%s' % rule)
	for rule in rule_set1_only:
		feature_vector.append('ARG1RULE=%s' % rule)
	for rule in rule_set2_only:
		feature_vector.append('ARG2RULE=%s' % rule)
	return feature_vector

def indiv_production_rules(instance, use_gold=False):
	rule_set1 = _get_production_rules(instance['parse_tree1'], instance['arg1_token_indices'])
	rule_set2 = _get_production_rules(instance['parse_tree2'], instance['arg2_token_indices'])
	feature_vector = []
	for rule in rule_set1:
		feature_vector.append('INDIV_ARG1RULE=%s' % rule)
	for rule in rule_set2:
		feature_vector.append('INDIV_ARG2RULE=%s' % rule)
	return feature_vector

def word_feature(instance, use_gold=False):
	arg1_tokens = set([instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']])
	arg2_tokens = set([instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']])

	arg1_token_only = arg1_tokens - arg2_tokens
	arg2_token_only = arg2_tokens - arg1_tokens
	feature_vector = []
	for token in arg1_tokens.intersection(arg2_tokens):
		feature_vector.append('BOTHARGTOKEN=%s' % token)
	for token in arg1_token_only:
		feature_vector.append('ARG1TOKEN=%s' % token)
	for token in arg2_token_only:
		feature_vector.append('ARG2TOKEN=%s' % token)
	return feature_vector

def attributions(instance, use_gold=False):
	relation = instance['relation']
	arg1_att_type = relation.arg_attribution_type(1)
	arg2_att_type = relation.arg_attribution_type(2)
	rel_source, arg1_source, arg2_source = relation.attribution_source_tuple
	if arg1_source == 'Inh':
		arg1_source = rel_source
	if arg2_source == 'Inh':
		arg2_source = rel_source
	return ['ARG1ATT_TYPE=%s' % arg1_att_type,
			'ARG2ATT_TYPE=%s' % arg2_att_type,
			'BOTHATT_TYPE=%s_%s' % (arg1_att_type, arg2_att_type),
			'ARG1ATT_SOURCE=%s' % arg1_source,
			'ARG2ATT_SOURCE=%s' % arg2_source,
			'BOTHATT_SOURCE=%s_%s' % (arg1_source, arg2_source),]


class TenseMapper(object):

	PATTERN_TO_TENSE = {
		'VBZ': 'present_simple',
		'VBP': 'present_simple',
		'has': 'present_simple',
		'have': 'present_simple',
		'VBZ VBN': 'present_simple_passive',
		'VBP VBN': 'present_simple_passive',
		'VBZ VBG': 'present_cont',
		'VBP VBG': 'present_cont',
		'VBZ VBG VBN': 'present_cont_passive',
		'VBP VBG VBN': 'present_cont_passive',
		'has VBN': 'present_perfect',
		'have VBN': 'present_perfect',
		'has VBN VBN': 'present_perfect_passive',
		'have VBN VBN': 'present_perfect_passive',
		'has VBN VBG': 'present_perfect_cont',
		'have VBN VBG': 'present_perfect_cont',
		'VBD': 'past_simple',
		'had': 'past_simple',
		'VBD VBN': 'past_simple_passive',
		'VBD VBG': 'past_cont',
		'VBD VBG VBN': 'past_cont_passive',
		'had VBN': 'past_perfect',
		'had VBN VBN': 'past_perfect_passive',
		'had VBN VBG': 'past_perfect_cont'
		}

	@classmethod
	def _recurse_search_tag(cls, root, tag_list, so_far):
		for child in root:
			if (child.node == 'S' or child.node == 'SBAR') and len(so_far) == 0:
				return cls._recurse_search_tag(child, tag_list, so_far)
			elif child.node == 'VP' and len(so_far) == 0:
				#starting symbols
				return cls._recurse_search_tag(child, ['MD', 'VBD', 'VBZ', 'VBP'], so_far)
			elif child.node == 'VP' and len(so_far) > 0:
				#second symbols
				return cls._recurse_search_tag(child, ['VBN', 'VBG'], so_far)
			elif child.node == 'CC' and len(so_far) > 0:
				break
			elif child.node in tag_list:
				if child.node == 'MD':
					if child[0] == 'will':
						return 'future'
					else:
						return None
				elif child[0] == 'has' or child[0] == 'have' or child[0] == 'had':
					so_far.append(child[0])
				else:
					so_far.append(child.node)

		history = ' '.join(so_far)
		return history

	@classmethod
	def _get_tense(cls, parse, token_indices, use_gold=False):
		if len(token_indices) == 1:
			return 'one_token'
		parse_tree = Tree(parse['parsetree'])
		start_index = min(token_indices)
		end_index = max(token_indices) + 1
		tree_position = parse_tree.treeposition_spanning_leaves(start_index, end_index)
		arg_subtree = parse_tree[tree_position]
		return cls._recurse_search_tag(arg_subtree, ['VP'], [])


	@classmethod
	def tense_features(cls, instance, use_gold=False):
		arg1_verb_pattern = cls._get_tense(instance['arg1_parse'], instance['arg1_token_indices'])
		arg2_verb_pattern = cls._get_tense(instance['arg2_parse'], instance['arg2_token_indices'])
		if arg1_verb_pattern in cls.PATTERN_TO_TENSE:
			arg1_tense = cls.PATTERN_TO_TENSE[arg1_verb_pattern]
		else:
			arg1_tense = 'tenseless'
		if arg2_verb_pattern in cls.PATTERN_TO_TENSE:
			arg2_tense = cls.PATTERN_TO_TENSE[arg2_verb_pattern]
		else:
			arg2_tense = 'tenseless'
		return ['ARG1TENSE=%s' % arg1_tense,
				'ARG2TENSE=%s' % arg2_tense,
				'BOTHTENSE=%s=%s' %(arg1_tense, arg2_tense)]

		


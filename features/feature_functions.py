import json
import os
from collections import defaultdict


#LABEL FUNCTIONS
def all_label_with_entrel_function(instance):
	"""Like all_label_function but EntRels are considered 'Expansion'

	We need this to follow what Pitler 2009 did. 
	"""
	if len(instance['arg1_token_indices']) == 0 or len(instance['arg2_token_indices']) == 0 or \
			instance['relation_type'] == 'NoRel':
		return None
	if instance['relation_type'] == 'EntRel':
		return 'Expansion'
	sense_tags_level0 = instance['relation'].relation_sense_tags_at_level(0)

	if len(sense_tags_level0) > 1:
		return None

	return sense_tags_level0[0]

def all_label_function(instance):
	if len(instance['arg1_token_indices']) == 0 or len(instance['arg2_token_indices']) == 0 or \
		instance['relation_type'] == 'EntRel' or instance['relation_type'] == 'NoRel':
		return None
	sense_tags_level0 = instance['relation'].relation_sense_tags_at_level(0)

	if len(sense_tags_level0) > 1:
		return None

	return sense_tags_level0[0]
	
def relation_label_function_with_entrel(instance, relation_type):
	"""Label function for one vs others labels

	"""
	if len(instance['arg1_token_indices']) == 0 or len(instance['arg2_token_indices']) == 0 or \
			instance['relation_type'] == 'NoRel':
		return None
	sense_tags_level0 = instance['relation'].relation_sense_tags_at_level(0)

	if len(sense_tags_level0) > 1:
		return None

	if sense_tags_level0[0] == relation_type:
		return relation_type
	else:
		return 'Others'


def relation_label_function(instance, relation_type):
	"""Label function for one vs others labels

	"""
	if len(instance['arg1_token_indices']) == 0 or len(instance['arg2_token_indices']) == 0 or \
		instance['relation_type'] == 'EntRel' or instance['relation_type'] == 'NoRel':
		return None
	sense_tags_level0 = instance['relation'].relation_sense_tags_at_level(0)

	if len(sense_tags_level0) > 1:
		return None

	if sense_tags_level0[0] == relation_type:
		return relation_type
	else:
		return 'Others'

def insane_feature(instance, use_gold=False):
	"""This is for entertainment and wishful thinking"""
	label = all_label_function(instance)
	if label is not None:
		return [label]
	else:
		return []

def word_pairs(instance, use_gold=False):
	arg1_tokens = set([instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']])
	arg2_tokens = set([instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']])
	feature_vector = []
	for arg1_token in arg1_tokens:
		for arg2_token in arg2_tokens:
			feature_vector.append('WORD_%s_%s' % (arg1_token, arg2_token))
	return feature_vector

def _find_money_date_percent(parse, token_indices):
	tag_set = set()
	for i in token_indices:
		NE_tag = parse['words'][i][1]['NamedEntityTag'] 
		if NE_tag == 'MONEY' or NE_tag == 'PERCENT' or NE_tag == 'DATE':
			tag_set.add(NE_tag)
	return tag_set

def money_date_percent_feature(instance, use_gold=False):
	arg1_tag_set = _find_money_date_percent(instance['arg1_parse'], instance['arg1_token_indices'])
	arg2_tag_set = _find_money_date_percent(instance['arg2_parse'], instance['arg2_token_indices'])
	feature_vector = []
	for arg1_tag in arg1_tag_set:
		for arg2_tag in arg2_tag_set:
			feature_vector.append('TAG_%s_%s' % (arg1_tag, arg2_tag))
	return feature_vector

def is_arg1_multiple_sentences(instance, use_gold=False):
	if instance['relation'].arg1.selection.num_sentences > 1:
		return ['ARG1_MULTIPLE_SENTENCES']
	else:
		return []

def _find_main_verb_index(dependency_tree, parse, token_indices):
	if dependency_tree is None or dependency_tree.root_node is None:
		return None
	agenda = []
	agenda.append(dependency_tree.root_node)
	while len(agenda) > 0:
		current = agenda.pop(0)
		token_position = current.token_position
		if parse['words'][token_position][1]['PartOfSpeech'][0] == 'V' and \
				token_position in token_indices:
			return token_position
		agenda.extend(current.children)
	return None
	
def same_pred_amount_pattern(instance, use_gold=False):
	pass

def list_punc_arg(instance, use_gold=False):
	if instance['arg2_token_indices'][0] > 0  and \
		len(instance['arg2_parse']['words']) > (instance['arg2_token_indices'][-1] + 1) and \
		instance['arg2_parse']['words'][instance['arg2_token_indices'][0] - 1][0] == ';' and \
		instance['arg2_parse']['words'][instance['arg2_token_indices'][-1] + 1][0] == ';':
			return ['SEMI_COLON_SURROUND']
	return []


class CorefFeaturizer(object):

	def __init__(self):
		"""Create a cache dictionary for coreference chain"""
		home = os.path.expanduser('~')
		self.wsj_to_mention_chain_map = {}
		self.relation_id_to_interg_coref_pairs = {}
		self.word_to_brown_mapping = {}
		self.brown_to_words_mapping = defaultdict(list)
		
		brown_cluster_file_name  = 'brown-rcv1.clean.tokenized-CoNLL03.txt-c1000-freq1.txt'
		self.load_brown_clusters('%s/nlp/lib/lexicon/brown_clusters/%s' % \
				(home, brown_cluster_file_name))
	
	def all_coref_features(self, instance, use_gold=False):
		"""All coreference features in one function
		
		Individual coreference feature is too weak and small.
		This function combines all of them for feature study + ablation study
		"""
		feature_functions = [self.coref_arg_feature, 
							self.coref_verb_pair_feature, 
							self.coref_head_verb_pair_feature, 
							self.synonym_head_verb_pair_feature, 
							self.same_main_verb_feature, ]
		feature_vector = []
		for feature_function in feature_functions:
			feature_vector.extend(feature_function(instance, use_gold))
		return feature_vector	

	def load_brown_clusters(self, path):
		self.word_to_brown_mapping = {}
		try:
			lexicon_file = open(path)
			for line in lexicon_file:
				cluster_assn, word, _ = line.split('\t')
				self.word_to_brown_mapping[word] = cluster_assn	
				self.brown_to_words_mapping[cluster_assn].append(word)
		except:
			print 'fail to load brown cluster data'

	def _get_mention_to_coref_chain_map(self, instance):
		"""Pre-map wsj_id to {mention: coref chain} dict

		A mention is represented by 
			(sentence_index, token_index) 

		The resulting map maps from a mention to coreferential mentions.
		"""
		if instance['wsj_id'] in self.wsj_to_mention_chain_map:
			return self.wsj_to_mention_chain_map[instance['wsj_id']]

		#coref is a list of anaphor-antecedent pairs
		coref = json.loads(instance['coreference_json']) 
		antecedent_to_anaphor_set = {}
		for anaphor, antecedent in coref:
			_, anaphor_sentence_index, anaphor_head_index, _, _ = anaphor
			_, antecedent_sentence_index, antecedent_head_index, _, _ = antecedent
			antecedent_index = (antecedent_sentence_index, antecedent_head_index)
			anaphor_index = (anaphor_sentence_index, anaphor_head_index)
			if antecedent_index in antecedent_to_anaphor_set:
				antecedent_to_anaphor_set[antecedent_index].add(anaphor_index)
			else:
				antecedent_to_anaphor_set[antecedent_index] = set()
				antecedent_to_anaphor_set[antecedent_index].add(anaphor_index)

		mention_to_coref_chain = {}
		for antecedent, anaphor_set in antecedent_to_anaphor_set.iteritems():
			anaphor_set.add(antecedent)
			for mention in anaphor_set:
				mention_to_coref_chain[mention] = anaphor_set
		self.wsj_to_mention_chain_map[instance['wsj_id']] = mention_to_coref_chain
		return mention_to_coref_chain

	def test_coreference_feature(self, instance, use_gold=False):
		mention_to_coref_chain	= self._get_mention_to_coref_chain_map(instance)
		feature_vector = []
		feature_vector.append('%s' % instance['relation'].arg1.text)
		for i in instance['arg1_token_indices']:
			mention_id = (instance['arg1_sentence_id'], i) 
			if mention_id in mention_to_coref_chain:
				coref_chain = mention_to_coref_chain[mention_id]
				feature_vector.append('%s -> %s' % (instance['sentence1_tokens'][i], coref_chain))
		return feature_vector

	def coref_arg_feature(self, instance, use_gold=False):
		"""Number of inter-argument coreferential pairs"""
		mention_to_coref_chain	= self._get_mention_to_coref_chain_map(instance)
		arg1_coref_chains = self._get_arg_coref_chains(mention_to_coref_chain, 
			instance['arg1_sentence_id'], instance['arg1_token_indices'])
		arg2_coref_chains = self._get_arg_coref_chains(mention_to_coref_chain, 
			instance['arg2_sentence_id'], instance['arg2_token_indices'])
		num_coreferential = 0
		for arg1_coref_chain in arg1_coref_chains:
			for arg2_coref_chain in arg2_coref_chains:
				if arg1_coref_chain[1] == arg2_coref_chain[1]:
					num_coreferential += 1
		return ['NUM_COREF=%s' % num_coreferential]

	def coref_verb_pair_feature(self, instance, use_gold=False):
		inter_arg_coref_pairs = self.find_inter_arg_coref_pairs(instance)
		feature_vector = []
		for pair in inter_arg_coref_pairs:
			arg1_mention_parent_index = instance['arg1_dependency_tree'].get_parent_index(pair[0])
			#child1 = instance['arg1_parse']['words'][pair[0]]
			parent1 = instance['arg1_parse']['words'][arg1_mention_parent_index]
			arg2_mention_parent_index = instance['arg2_dependency_tree'].get_parent_index(pair[1])
			#child2 = instance['arg2_parse']['words'][pair[1]]
			parent2 = instance['arg2_parse']['words'][arg2_mention_parent_index]

			if parent1[1]['PartOfSpeech'][0] == 'V' and \
				parent2[1]['PartOfSpeech'][0] == 'V':
				feature_vector.append('CV_%s_%s' % (parent1[1]['Lemma'], parent2[1]['Lemma']))	
				if parent1[1]['Lemma'] == parent2[1]['Lemma'] and parent1[1]['Lemma'] != 'be':
					feature_vector.append('SAME_CV')
		return feature_vector

	def coref_head_verb_pair_feature(self, instance, use_gold=False):
		"""Use head verb instead"""
		inter_arg_coref_pairs = self.find_inter_arg_coref_pairs(instance)
		feature_vector = []
		for pair in inter_arg_coref_pairs:
			arg1_mention_parent_index = instance['arg1_dependency_tree'].get_parent_index(pair[0])
			#child1 = instance['arg1_parse']['words'][pair[0]]
			parent1 = instance['arg1_parse']['words'][arg1_mention_parent_index]
			arg2_mention_parent_index = instance['arg2_dependency_tree'].get_parent_index(pair[1])
			#child2 = instance['arg2_parse']['words'][pair[1]]
			parent2 = instance['arg2_parse']['words'][arg2_mention_parent_index]

			if parent1[1]['PartOfSpeech'][0] == 'V' and \
				parent2[1]['PartOfSpeech'][0] == 'V':
				feature_vector.append('CV_%s_%s' % (parent1[1]['Lemma'], parent2[1]['Lemma']))	
				if parent1[1]['Lemma'] == parent2[1]['Lemma'] and parent1[1]['Lemma'] != 'be':
					feature_vector.append('SAME_CV')
		return feature_vector

	def synonym_head_verb_pair_feature(self, instance, use_gold=False):
		"""Head verb pairs for each synonym pair"""
		inter_arg_synonym_pairs = self.find_inter_arg_synonym_pairs(instance)
		inter_arg_synonym_pairs.extend(self.find_inter_arg_coref_pairs(instance))

		feature_vector = []
		if len(inter_arg_synonym_pairs) == 0:
			feature_vector.append('NO_SYN')
		for pair in inter_arg_synonym_pairs:
			head_verb_index1 = instance['arg1_parse']['word_index_to_head_verb_index'][str(pair[0])]
			head_verb_index2 = instance['arg2_parse']['word_index_to_head_verb_index'][str(pair[1])]
			head_verb1 = instance['arg1_parse']['words'][head_verb_index1]
			head_verb2 = instance['arg2_parse']['words'][head_verb_index2]
			if head_verb1[1]['PartOfSpeech'][0] == 'V' and head_verb2[1]['PartOfSpeech'][0] == 'V' and \
				head_verb1[0] in self.word_to_brown_mapping and  head_verb2[0] in self.word_to_brown_mapping:
				#feature_vector.append('SV_%s_%s' % 
						#(head_verb1[1]['Lemma'], head_verb2[1]['Lemma']))	
				#feature_vector.append('SV_%s_%s' % 
						#(self.word_to_brown_mapping[head_verb1[0]], self.word_to_brown_mapping[head_verb2[0]]))
				if self.word_to_brown_mapping[head_verb1[0]] == self.word_to_brown_mapping[head_verb2[0]]:
					feature_vector.append('SV_%s' % self.word_to_brown_mapping[head_verb1[0]])
					feature_vector.append('SIMILAR_SV')
				if head_verb1[1]['Lemma'] == head_verb2[1]['Lemma'] and head_verb1[1]['Lemma'] != 'be':
					feature_vector.append('SAME_SV')
		return feature_vector

	def coref_subject_feature(self, instance, use_gold=False):
		"""Is there a coreferential subject pair or not

		"""
		arg1_main_verb_index = _find_main_verb_index(instance['arg1_dependency_tree'],
				instance['arg1_parse'], instance['arg1_token_indices'])
		arg2_main_verb_index = _find_main_verb_index(instance['arg2_dependency_tree'],
				instance['arg2_parse'], instance['arg2_token_indices'])
		feature_vector = []
		has_coref_subj = False
		if arg1_main_verb_index is not None and arg2_main_verb_index is not None:
			main_verb1 = instance['arg1_parse']['words'][arg1_main_verb_index] 
			main_verb2 = instance['arg2_parse']['words'][arg2_main_verb_index] 
			main_verb_node1 = \
				instance['arg1_dependency_tree'].node_linear_position_to_node(arg1_main_verb_index)
			main_verb_node2 = \
				instance['arg2_dependency_tree'].node_linear_position_to_node(arg2_main_verb_index)

			#children nodes who are nsubj
			nsubj1 = main_verb_node1.find_children_by_dep_type('nsubj')
			nsubj2 = main_verb_node2.find_children_by_dep_type('nsubj')
			# nsubj1 and nsubj2 will actually have either one or zero element
			# coordination introduces the dependency on the subj itself
			if len(nsubj1) > 0 and len(nsubj2) > 0:
				nsubj1 = nsubj1[0]
				nsubj2 = nsubj2[0]
				inter_arg_coref_pairs = self.find_inter_arg_coref_pairs(instance)
				if (nsubj1.token_position, nsubj2.token_position) in inter_arg_coref_pairs:
					has_coref_subj = True
					#print (nsubj1.token, nsubj2.token)
					#print (nsubj1.token_position, nsubj2.token_position)
					#print inter_arg_coref_pairs
		if has_coref_subj:
			feature_vector.append('COREFERENTIAL_SUBJ')
		return feature_vector

	def same_main_verb_feature(self, instance, use_gold=False):
		arg1_main_verb_index = _find_main_verb_index(instance['arg1_dependency_tree'],
				instance['arg1_parse'], instance['arg1_token_indices'])
		arg2_main_verb_index = _find_main_verb_index(instance['arg2_dependency_tree'],
				instance['arg2_parse'], instance['arg2_token_indices'])
		feature_vector = []
		if arg1_main_verb_index is not None and arg2_main_verb_index is not None:
			main_verb1 = instance['arg1_parse']['words'][arg1_main_verb_index] 
			main_verb2 = instance['arg2_parse']['words'][arg2_main_verb_index] 
			main_verb_node1 = \
				instance['arg1_dependency_tree'].node_linear_position_to_node(arg1_main_verb_index)
			main_verb_node2 = \
				instance['arg2_dependency_tree'].node_linear_position_to_node(arg2_main_verb_index)

			nsubj1 = main_verb_node1.find_children_by_dep_type('nsubj')
			nsubj2 = main_verb_node2.find_children_by_dep_type('nsubj')
			has_same_nsubj = len(nsubj1) > 0 and len(nsubj2) > 0 and \
						nsubj1[0].no_number_token == nsubj2[0].no_number_token
			feature_vector.append('MAIN_VERB_PAIR_%s_%s' % 
					(main_verb1[1]['Lemma'], main_verb2[1]['Lemma']))
			# Verb exact match
			if main_verb1[1]['Lemma'] == main_verb2[1]['Lemma'] and \
					main_verb1[1]['Lemma'] != 'be':
				if has_same_nsubj:
					return feature_vector
					feature_vector.append('SAME_MAIN_VERB_%s_SAME_SUBJ' % main_verb1[1]['Lemma'])
				else:
					return feature_vector
					feature_vector.append('SAME_MAIN_VERB_%s_DIFF_SUBJ' % main_verb1[1]['Lemma'])
			elif main_verb1[1]['Lemma'] != 'be' and \
				main_verb2[1]['Lemma'] != 'be' and \
				main_verb1[0] in self.word_to_brown_mapping and \
				main_verb2[0] in self.word_to_brown_mapping and \
				self.word_to_brown_mapping[main_verb1[0]][0:10] == \
				self.word_to_brown_mapping[main_verb2[0]][0:10]:
					if has_same_nsubj:
						feature_vector.append('SAME_BROWN_MAIN_VERB_SAME_SUBJ')
					else:
						feature_vector.append('SAME_BROWN_MAIN_VERB_DIFF_SUBJ')
		return feature_vector

	def _get_arg_coref_chains(self, mention_to_coref_chain, sentence_id, arg_token_indices):
		"""Get mention_id and coref chain pairs

		((sentence_id, token_index), [mention_id, mention_id])
		"""
		coref_chain_pairs = []
		for i in arg_token_indices:
			mention_id = (sentence_id, i)
			if mention_id in mention_to_coref_chain:
				coref_chain = mention_to_coref_chain[mention_id]
				coref_chain_pairs.append((mention_id,coref_chain))
		return coref_chain_pairs

	
	def find_inter_arg_coref_pairs(self, instance):
		"""Inter-argument coreferential pairs

		A list of pairs of (arg1 token index, arg2 token index)
		"""
		if instance['relation_id'] in self.relation_id_to_interg_coref_pairs:
			return self.relation_id_to_interg_coref_pairs[instance['relation_id']]

		mention_to_coref_chain	= self._get_mention_to_coref_chain_map(instance)
		arg1_coref_chains = self._get_arg_coref_chains(mention_to_coref_chain, 
			instance['arg1_sentence_id'], instance['arg1_token_indices'])
		arg2_coref_chains = self._get_arg_coref_chains(mention_to_coref_chain, 
			instance['arg2_sentence_id'], instance['arg2_token_indices'])
		inter_arg_coref_pairs = []
		for arg1_coref_chain in arg1_coref_chains:
			for arg2_coref_chain in arg2_coref_chains:
				if arg1_coref_chain[1] == arg2_coref_chain[1]:
					#appending a pair of (arg1 token index, arg2 token index)
					inter_arg_coref_pairs.append((arg1_coref_chain[0][1], arg2_coref_chain[0][1]))
		self.relation_id_to_interg_coref_pairs[instance['relation_id']] = inter_arg_coref_pairs
		return inter_arg_coref_pairs

	def find_inter_arg_synonym_pairs(self, instance):
		"""Synonyms are as defined in Brown cluster"""
		arg1_brown_words = [
			(i, self.word_to_brown_mapping[instance['arg1_parse']['words'][i][0]])
			for i in instance['arg1_token_indices'] 
			if instance['arg1_parse']['words'][i][1]['PartOfSpeech'][0] == 'N' and \
				instance['arg1_parse']['words'][i][0] in self.word_to_brown_mapping
			]
		arg2_brown_words = [
			(i, self.word_to_brown_mapping[instance['arg2_parse']['words'][i][0]])
			for i in instance['arg2_token_indices']
			if instance['arg2_parse']['words'][i][1]['PartOfSpeech'][0] == 'N' and \
				instance['arg2_parse']['words'][i][0] in self.word_to_brown_mapping
			]
		pairs = []
		for arg1_brown_word in arg1_brown_words:
			for arg2_brown_word in arg2_brown_words:
				if arg1_brown_word[1] == arg2_brown_word[1]:
					pair = (arg1_brown_word[0], arg2_brown_word[0])
					if not(instance['arg1_parse']['words'][pair[0]][1]['PartOfSpeech'] == 'NNP' \
						and instance['arg2_parse']['words'][pair[1]][1]['PartOfSpeech'] == 'NNP'):
						pairs.append(pair)
		return pairs


class LexicalFeaturizer(object):

	def __init__(self):
		home = os.path.expanduser('~')
		self.load_inquirer('%s/nlp/lib/lexicon/inquirer/inquirer_merged.json' % home)
		self.load_mpqa('%s/nlp/lib/lexicon/mpqa_subj_05/mpqa_subj_05.json' % home)
		#self.load_sentiwordnet('%s/nlp/lib/lexicon/sentiwordnet3.0/SentiWordNet_3.0.0_20130122.json' % home)
		brown_cluster_file_name  = 'brown-rcv1.clean.tokenized-CoNLL03.txt-c3200-freq1.txt'
		self.load_brown_clusters('%s/nlp/lib/lexicon/brown_clusters/%s' % \
				(home, brown_cluster_file_name))

	def load_inquirer(self, path):
		"""Load Inquirer General Tag corpus

		(WORD) --> [tag1, tag2, ...]
		"""
		try:
			lexicon_file = open(path)
			self.inquirer_dict = json.loads(lexicon_file.read())
		except:
			pass

	def load_mpqa(self, path):
		"""Load MPQA dictionary
		
		(WORD) -->  [positive|negative, strong|weak]
		"""
		try:
			lexicon_file = open(path)
			self.mpqa_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to load mpqa corpus'

	def load_sentiwordnet(self, path):
		try:
			lexicon_file = open(path)
			self.sentiwordnet_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to load sentiwordnet'

	def load_brown_clusters(self, path):
		self.word_to_brown_mapping = {}
		try:
			lexicon_file = open(path)
			for line in lexicon_file:
				cluster_assn, word, _ = line.split('\t')
				self.word_to_brown_mapping[word] = cluster_assn	
		except:
			print 'fail to load brown cluster data'

	def lemma(self, instance, use_gold=False):
		"""This is not a real feature.

		Just want to compare lemmatized look up with raw look up
		"""
		parse = instance['arg1_parse']
		token_indices = instance['arg1_token_indices']
		word_index_to_head_verb_index = parse['word_index_to_head_verb_index']
		head_verb_indices = [int(word_index_to_head_verb_index[str(x)]) \
				for x in token_indices if str(x) in word_index_to_head_verb_index]
		if len(head_verb_indices) == 0:
			return []
		majority_head_verb_index = Counter(head_verb_indices).most_common(1)[0][0]
		lemmatized_head_verb = parse['words'][majority_head_verb_index][1]['Lemma'].upper()
		l_tags = []
		if lemmatized_head_verb in self.inquirer_dict:
			l_tags = self.inquirer_dict[lemmatized_head_verb]
		head_verb = parse['words'][majority_head_verb_index][0].upper()
		h_tags = []
		if head_verb in self.inquirer_dict:
			h_tags = self.inquirer_dict[head_verb]
		return [lemmatized_head_verb, l_tags.__str__(),
				head_verb, h_tags.__str__()] 


	def _get_inquirer_tags(self, parse, majority_head_verb_index):
		#lemmatized_head_verb = parse['words'][majority_head_verb_index][1]['Lemma'].upper()
		if majority_head_verb_index is None:
			return []
		head_verb = parse['words'][majority_head_verb_index][0].upper()
		if head_verb in self.inquirer_dict:
			return self.inquirer_dict[head_verb]
		#elif lemmatized_head_verb in self.inquirer_dict:
			#return self.inquirer_dict[lemmatized_head_verb]
		else:
			return []

	def inquirer_tag_feature(self, instance, use_gold=False):
		arg1_tags = self._get_inquirer_tags(instance['arg1_parse'], instance['arg1_majority_head_verb_index'])
		arg2_tags = self._get_inquirer_tags(instance['arg2_parse'], instance['arg2_majority_head_verb_index'])
		feature_vector = []
		if len(arg1_tags) > 0 and len(arg2_tags) > 0:
			for arg1_tag in arg1_tags:
				for arg2_tag in arg2_tags:
					feature_vector.append('TAGS=%s_%s' % (arg1_tag, arg2_tag))
		for arg1_tag in arg1_tags:
			feature_vector.append('ARG1_TAG=%s' % arg1_tag)
		for arg2_tag in arg1_tags:
			feature_vector.append('ARG2_TAG=%s' % arg1_tag)
		return feature_vector

	def _get_mpqa_score(self, parse, token_indices):
		positive_score = 0
		negative_score = 0
		neg_positive_score = 0
		neutral_score = 0
		for i in token_indices:
			#token = parse['words'][i][1]['Lemma'].upper()
			token = parse['words'][i][0].upper()
			if token in self.mpqa_dict:
				polarity = self.mpqa_dict[token][0]
				if i != 0 and parse['words'][i-1][0] == 'not' and polarity == 'positive':
					neg_positive_score += 1
				if polarity == 'positive':
					positive_score += 1
				elif polarity =='negative':
					negative_score += 1
				elif polarity == 'neutral':
					neutral_score += 1
		return (positive_score, negative_score, neg_positive_score, neutral_score)


	def mpqa_score_feature(self, instance, use_gold=False):
		positive_score1, negative_score1, neg_positive_score1, neutral_score1 = \
				self._get_mpqa_score(instance['arg1_parse'], instance['arg1_token_indices'])
		positive_score2, negative_score2, neg_positive_score2, neutral_score2 = \
				self._get_mpqa_score(instance['arg2_parse'], instance['arg2_token_indices'])
		feature_vector = []
		feature_vector.append('Arg1MPQAPositive:%s' % positive_score1)
		feature_vector.append('Arg2MPQAPositive:%s' % positive_score2)
		feature_vector.append('Arg1MPQANegative:%s' % negative_score1)
		feature_vector.append('Arg2MPQANegative:%s' % negative_score2)
		feature_vector.append('Arg1MPQANegPositive:%s' % neg_positive_score1)
		feature_vector.append('Arg2MPQANegPositive:%s' % neg_positive_score2)
		return feature_vector

	def _get_brown_word_feature(self, tokens, token_indices):
		"""Get a bag of brown clusters

		"""
		bag = set()
		for i in token_indices:
			token = tokens[i]
			if token in self.word_to_brown_mapping:
				bag.add(self.word_to_brown_mapping[token])
		return bag

	def all_brown(self, instance, use_gold=False):
		feature_vector = []
		feature_vector.extend(self.brown_word_feature(instance, use_gold))
		feature_vector.extend(self.brown_word_pairs(instance, use_gold))
		return feature_vector

	def brown_word_feature(self, instance, use_gold=False):
		arg1_brown_words = self._get_brown_word_feature(instance['sentence1_tokens'], instance['arg1_token_indices'])
		arg2_brown_words = self._get_brown_word_feature(instance['sentence2_tokens'], instance['arg2_token_indices'])

		arg1_only = arg1_brown_words - arg2_brown_words
		arg2_only = arg2_brown_words - arg1_brown_words
		both_args = arg1_brown_words.intersection(arg2_brown_words)

		feature_vector = []
		for brown_word in both_args:
			feature_vector.append('BOTH_ARGS_BROWN=%s' % brown_word)
		for brown_word in arg1_only:
			feature_vector.append('ARG1_BROWN=%s' % brown_word)
		for brown_word in arg2_only:
			feature_vector.append('ARG2_BROWN=%s' % brown_word)
		return feature_vector

	def brown_word_pairs(self, instance, use_gold=False):
		arg1_brown_words = self._get_brown_word_feature(instance['sentence1_tokens'], instance['arg1_token_indices'])
		arg2_brown_words = self._get_brown_word_feature(instance['sentence2_tokens'], instance['arg2_token_indices'])
		feature_vector = []
		for word1 in arg1_brown_words:
			for word2 in arg2_brown_words:
				feature_vector.append('PAIR=%s___%s' % (word1, word2))
		return feature_vector

	def indiv_brown_words(self, instance, use_gold=False):
		arg1_brown_words = self._get_brown_word_feature(instance['sentence1_tokens'], instance['arg1_token_indices'])
		arg2_brown_words = self._get_brown_word_feature(instance['sentence2_tokens'], instance['arg2_token_indices'])
		feature_vector = []
		for brown_word in arg1_brown_words:
			feature_vector.append('INDIV_ARG1_BROWN=%s' % brown_word)
		for brown_word in arg2_brown_words:
			feature_vector.append('INDIV_ARG2_BROWN=%s' % brown_word)
		return feature_vector

		


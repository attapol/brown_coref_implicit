import os
import json
from collections import Counter

def word_pairs(instance, use_gold=False):
	sentence1_tokens = instance['sentence1_tokens']
	sentence2_tokens = instance['sentence2_tokens']
	arg1_token_indices = instance['arg1_token_indices']
	arg2_token_indices = instance['arg2_token_indices']
	feature_vector = []
	for arg1_token_index in arg1_token_indices:
		for arg2_token_index in arg2_token_indices:
			feature = '%s__%s' % (sentence1_tokens[arg1_token_index], sentence2_tokens[arg2_token_index])
			feature_vector.append(feature)
	return feature_vector

def _get_first_three(token_indices, tokens):
	feature_vector = []
	for i in range(min(3, len(token_indices))):
		token_index = token_indices[i]
		feature_vector.append(tokens[token_index].replace(':','COLON'))
	return '_'.join(feature_vector)

def first_last_first_3(instance, use_gold=False):
	"""
	
	first and last of arg1
	first and last of arg2
	first of arg1 and arg2 together
	last of arg1 and arg2 together
	first three of arg1
	first three of arg2
	"""
	sentence1_tokens = instance['sentence1_tokens']
	sentence2_tokens = instance['sentence2_tokens']
	arg1_token_indices = instance['arg1_token_indices']
	arg2_token_indices = instance['arg2_token_indices']

	first_arg1 = sentence1_tokens[arg1_token_indices[0]]
	last_arg1 = sentence1_tokens[arg1_token_indices[-1]]
	first_arg2 = sentence2_tokens[arg2_token_indices[0]]
	last_arg2 = sentence2_tokens[arg2_token_indices[-1]]
	first_3_arg1 = _get_first_three(arg1_token_indices, sentence1_tokens)
	first_3_arg2 = _get_first_three(arg2_token_indices, sentence2_tokens)

	feature_vector = []
	feature_vector.append(first_arg1)
	feature_vector.append(last_arg1)
	feature_vector.append(first_arg2)
	feature_vector.append(last_arg2)
	feature_vector.append('%s__%s' % (first_arg1, first_arg2))
	feature_vector.append('%s__%s' % (last_arg1, last_arg2))
	feature_vector.append(first_3_arg1)
	feature_vector.append(first_3_arg2)
	return feature_vector


def _get_average_vp_length(parse_tree, arg_token_indices):
	start_index = min(arg_token_indices)
	end_index = max(arg_token_indices) + 1
	if end_index - start_index == 1:
		return 0

	tree_position = parse_tree.treeposition_spanning_leaves(start_index, end_index)
	subtree = parse_tree[tree_position]

	agenda = [subtree]
	while len(agenda) > 0:
		current = agenda.pop(0)
		if current.height() > 2:
			if current.node == 'VP':
				return len(current.leaves())
			for child in current:
				agenda.append(child)
	return 0	

def average_vp_length(instance, use_gold=False):
	arg1_average_vp_length = _get_average_vp_length(instance['parse_tree1'], instance['arg1_token_indices'])
	arg2_average_vp_length = _get_average_vp_length(instance['parse_tree2'], instance['arg2_token_indices'])
	return ['ARG1_VP_LENGTH=%s' % arg1_average_vp_length,
			'ARG2_VP_LENGTH=%s' % arg2_average_vp_length,
			'VP_LENGTH_%s_%s' % (arg1_average_vp_length, arg2_average_vp_length)]

def _has_modality(parse, token_indices):
	for i in token_indices:
		if parse['words'][i][1]['PartOfSpeech'] == 'MD':
			return 'HAS_MODALITY'
	return 'NO_MODALITY'

def modality(instance, use_gold=False):
	arg1_modality = _has_modality(instance['arg1_parse'], instance['arg1_token_indices'])
	arg2_modality = _has_modality(instance['arg2_parse'], instance['arg2_token_indices'])
	feature_vector = ['ARG1_%s' % arg1_modality,
			'ARG2_%s' % arg2_modality, 
			'ARG1_%s_ARG2_%s' % (arg1_modality, arg2_modality)]
	return feature_vector

	

class ParkLexicalFeaturizer(object):

	def __init__(self):
		home = os.path.expanduser('~')
		self.load_inquirer('%s/nlp/lib/lexicon/inquirer/inquirer_merged.json' % home)
		self.load_mpqa('%s/nlp/lib/lexicon/mpqa_subj_05/mpqa_subj_05.json' % home)
		self.load_levin('%s/nlp/lib/lexicon/levin/levin.json' % home)
		self.load_sentiwordnet('%s/nlp/lib/lexicon/sentiwordnet3.0/SentiWordNet_3.0.0_20130122.json' % home)
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
			print 'fail to load general inquirer corpus'

	def load_mpqa(self, path):
		"""Load MPQA dictionary
		
		(WORD) -->  [positive|negative, strong|weak]
		"""
		try:
			lexicon_file = open(path)
			self.mpqa_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to load mpqa corpus'

	def load_levin(self, path):
		"""Load Levin's verb class dictionary

		(WORD) --> [class1, class2, ...]
		"""
		try:
			lexicon_file = open(path)
			self.levin_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to laod levin verb classes'

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
			is_negated = False
			if majority_head_verb_index > 0:
				preceding_word = parse['words'][majority_head_verb_index - 1][0]
				is_negated = preceding_word == 'not' or preceding_word =="n't"
			tags = self.inquirer_dict[head_verb] 
			if is_negated:
				return map(lambda x: 'NOT_%s'%x, tags)
			else:
				return tags
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
				if i != 0 and polarity == 'positive':
					preceding_token = parse['words'][i-1][0].upper()
					if (preceding_token in self.mpqa_dict and self.mpqa_dict[preceding_token] == 'negative'):
						neg_positive_score += 1
					else:
						positive_score += 1
				elif polarity == 'positive':
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
		feature_vector1 = []
		feature_vector1.append('Arg1MPQAPositive:%s' % positive_score1)
		feature_vector1.append('Arg1MPQANegative:%s' % negative_score1)
		feature_vector1.append('Arg1MPQANegPositive:%s' % neg_positive_score1)

		feature_vector2 = []
		feature_vector2.append('Arg2MPQAPositive:%s' % positive_score2)
		feature_vector2.append('Arg2MPQANegative:%s' % negative_score2)
		feature_vector2.append('Arg2MPQANegPositive:%s' % neg_positive_score2)

		feature_vector = []
		for f1 in feature_vector1:
			for f2 in feature_vector2:
				feature = '%s__%s' % (f1, f2)
				feature_vector.append(feature.replace(':', 'COLON'))
		feature_vector.extend(feature_vector1)
		feature_vector.extend(feature_vector2)
		return feature_vector


	def _get_levin_verb_tags(self, parse, arg_token_indices):
		verbs_tags = []
		for arg_token_index in arg_token_indices:
			if parse['words'][arg_token_index][1]['PartOfSpeech'][0] == 'V':
				lemmatized_verb = parse['words'][arg_token_index][1]['Lemma']
				if lemmatized_verb in self.levin_dict:
					verbs_tags.append(set(self.levin_dict[lemmatized_verb]))
		return verbs_tags

	def levin_verbs(self, instance, use_gold=False):
		arg1_levin_verb_tags = self._get_levin_verb_tags(instance['arg1_parse'], instance['arg1_token_indices'])		
		arg2_levin_verb_tags = self._get_levin_verb_tags(instance['arg2_parse'], instance['arg2_token_indices'])		
		num_verbs_in_common = 0
		for tags1 in arg1_levin_verb_tags:
			for tags2 in arg2_levin_verb_tags:
				if not tags1.isdisjoint(tags2):
					num_verbs_in_common += 1
		return ['COMMON_LEVIN_VERBS=%s' % num_verbs_in_common]


	def _get_brown_word_feature(self, tokens, token_indices):
		"""Get a bag of brown clusters

		"""
		bag = set()
		for i in token_indices:
			token = tokens[i]
			if token in self.word_to_brown_mapping:
				bag.add(self.word_to_brown_mapping[token])
		return bag

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




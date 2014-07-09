"""Collection of feature functions related to word embeddings

These functions were used after EACL 2014 paper
"""
import numpy as np
import os

SKIPGRAM_WORD_EMBEDDING_FILE = '~/nlp/lib/lexicon/google_word_vector/GoogleNews-vectors-negative300.txt'
BROWN_CLUSTER_FILE = '~/nlp/lib/lexicon/brown_clusters/brown-rcv1.clean.tokenized-CoNLL03.txt-c3200-freq1.txt'

class WordEmbeddingDict(object):

	def __init__(self, word_embedding_file):
		lines = open(word_embedding_file).readlines()
		self.num_units = len(lines[1].strip().split(' ')) - 1
		self.vocab_size = len(lines)
		self.word_to_vector = {}
		for line in lines[1:]:
			word, vector = line.split(' ', 1)
			self.word_to_vector[word] = vector.strip()

	def __getitem__(self, key):
		vector = self.word_to_vector[key]
		if isinstance(vector, str):
			self.word_to_vector[key] = np.array([float(x) for x in vector.split(' ')])
		return self.word_to_vector[key] 	

	def __contains__(self, key):
		return key in self.word_to_vector

class WordEmbeddingBrownFeaturizer(object):

	def __init__(self):
		self.word_embedding_dict = WordEmbeddingDict(os.path.expanduser(SKIPGRAM_WORD_EMBEDDING_FILE))
		self._load_brown_clusters(os.path.expanduser(BROWN_CLUSTER_FILE))
		self.distance_threshold = 10

	def _load_brown_clusters(self, path):
		self.word_to_brown_mapping = {}
		try:
			lexicon_file = open(path)
			for line in lexicon_file:
				cluster_assn, word, _ = line.split('\t')
				self.word_to_brown_mapping[word] = cluster_assn	
		except:
			print 'fail to load brown cluster data'

	def _get_brown_word_feature(self, tokens, token_indices):
		"""Get brown clusters for the tokens

		"""
		brown_cluster_list = []
		for i in token_indices:
			token = tokens[i]
			if token in self.word_to_brown_mapping:
				brown_cluster_list.append(self.word_to_brown_mapping[token])
			else:
				brown_cluster_list.append(None)
		return brown_cluster_list

	def _compute_distance(self, word1, word2):
		word1_vector = self.word_embedding_dict[word1]
		word2_vector = self.word_embedding_dict[word2]
		distance = np.linalg.norm(word1_vector - word2_vector)
		return distance

	#feature function
	def selected_word_pairs(self, instance, use_gold=False):
		arg1_tokens = set([instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']])
		arg2_tokens = set([instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']])
		feature_vector = []
		for arg1_token in arg1_tokens:
			for arg2_token in arg2_tokens:
				if self._compute_distance(arg1_token, arg2_token) < self.distance_threshold:
					feature_vector.append('WORD_%s_%s' % (arg1_token, arg2_token))
		return feature_vector

	#feature function
	def selected_brown_pairs(self, instance, use_gold=False):
		arg1_brown_words = self._get_brown_word_feature(instance['sentence1_tokens'], instance['arg1_token_indices'])
		arg2_brown_words = self._get_brown_word_feature(instance['sentence2_tokens'], instance['arg2_token_indices'])
		arg1_tokens = [instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']]
		arg2_tokens = [instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']]
		feature_vector = []
		for word1, cluster1 in zip(arg1_tokens, arg1_brown_words):
			for word2, cluster2 in zip(arg2_tokens, arg2_brown_words):
				if self._compute_distance(word1, word2) < self.distance_threshold:
					feature_vector.append('PAIR=%s___%s' % (word1, word2))
		return feature_vector

	#feature function
	def word_pair_distance(self, instance, use_gold=False):
		arg1_tokens = set([instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']])
		arg2_tokens = set([instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']])
		feature_vector = []
		for arg1_token in arg1_tokens:
			for arg2_token in arg2_tokens:
				if arg1_token in self.word_embedding_dict and arg2_token in self.word_embedding_dict:
					distance =  self._compute_distance(arg1_token, arg2_token)
					feature_vector.append('WORD_PAIR_%s_%s=%.6f' % (arg1_token, arg2_token, distance))
		return feature_vector

	#feature function
	def brown_pair_distance(self, instance, use_gold=False):
		arg1_brown_words = self._get_brown_word_feature(instance['sentence1_tokens'], instance['arg1_token_indices'])
		arg2_brown_words = self._get_brown_word_feature(instance['sentence2_tokens'], instance['arg2_token_indices'])
		arg1_tokens = [instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']]
		arg2_tokens = [instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']]
		assert(len(arg1_brown_words) == len(arg1_tokens))
		assert(len(arg2_brown_words) == len(arg2_tokens))
		feature_vector = []
		for arg1_token, arg1_brown in zip(arg1_tokens, arg1_brown_words):
			for arg2_token, arg2_brown in zip(arg2_tokens, arg2_brown_words):
				if arg1_token in self.word_embedding_dict and arg2_token in self.word_embedding_dict and \
						arg1_brown is not None and arg2_brown is not None:
					distance =  self._compute_distance(arg1_token, arg2_token)
					feature_vector.append('BROWN_PAIR_%s_%s=%.6f' % (arg1_brown, arg2_brown, distance))
		return feature_vector

	#feature function
	def distance_only(self, instance, use_gold=False):
		arg1_tokens = set([instance['sentence1_tokens'][i] for i in instance['arg1_token_indices']])
		arg2_tokens = set([instance['sentence2_tokens'][i] for i in instance['arg2_token_indices']])
		feature_vector = []
		for arg1_token in arg1_tokens:
			for arg2_token in arg2_tokens:
				if arg1_token in self.word_embedding_dict and arg2_token in self.word_embedding_dict:
					distance =  self._compute_distance(arg1_token, arg2_token)
					feature_vector.append('%.6f' % distance)
		return feature_vector




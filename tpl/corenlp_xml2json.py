""" Convert Stanford CoreNLP xml to this json format

The format is somewhat ugly. But this is to comply with ~/nlp/tpl/language/stanford_parser.py.
If we want to change this, we need to change the format from the interactive mode as well.

'sentences' : a list of sentences

	Each sentence is a dictionary with the following fields

		'parsetree' : one line Penn style bracketed parse. use nltk.tree.Tree to parse it
			e.g. print nltk.tree.Tree(parse_tree).pprint()

		'dependencies' : a list of basic dependency relations (also a list)
			[['nn','Vinken-2','Pierre-1'], ['nsubj','join-3','Vinken-2']]
			Note that the index is off by one because of the ROOT node

		'otherDependencies' : a dictionary from dependency scheme to dependencies
			'basic-dependencies'  this is redundantly stored
			'collapsed-dependencies'
			'collapsed-ccprocessed-dependencies'

		'text' : the raw text string for this sentence

		'words' : a list of words
		Each word is a tuple of (word, dictionary)

			word is just a string

			dictionary has the following fields:

				'CharacterOffsetBegin'
				'CharacterOffsetEnd'
				'Lemma'
				'PartOfSpeech'
				'Speaker' (if available. new to the new version of CoreNLP)

		sentimentValue : sentiment value
		sentiment : overall sentence sentiment {'Positive', 'Neutral', 'Negative'}

'coref' : a list of coreference chains

	Each coreference chain is a list of mentions.
		Each mention is a tuple of (token, sentence id, head position, start position, end position)

"""

import json
import sys
from multiprocessing import Process
from xmltodict import parse

from tpl.misc import slice_list

def xml2json(xmlstring):
	"""Convert xmlstring from StanfordCoreNLP to json format"""
	temp_dict = parse(xmlstring)
	new_dict = {}
	new_dict['sentences'] = []
	for i, sentence in enumerate(temp_dict['root']['document']['sentences']['sentence']):
		if i <= 1: 
			continue
		s = {}
		s['parsetree'] = sentence['parse']
		if 'dep' in sentence['dependencies'][0]:
			s['dependencies'] = extract_dependency_triplets(sentence['dependencies'][0]['dep'])
		else:
			s['dependencies'] = []

		s['words'] = []
		#if there are no multiple entries. the xmltodict does not give out a list.
		if not isinstance(sentence['tokens']['token'], list):
			sentence['tokens']['token'] = [sentence['tokens']['token']]
		for word in sentence['tokens']['token']:
			word_info = {}
			token = word['word']	
			word_info['Lemma'] = word['lemma']
			word_info['NamedEntityTag'] = word['NER']
			word_info['PartOfSpeech'] = word['POS']
			if 'Speaker' in word:
				word_info['Speaker'] = word['Speaker']
			else:
				word_info['Speaker'] = ''
			word_info['CharacterOffsetBegin'] = int(word['CharacterOffsetBegin'])
			word_info['CharacterOffsetEnd'] = int(word['CharacterOffsetEnd'])
			s['words'].append((token, word_info))
		s['text'] = ' '.join([x[0] for x in s['words']])

		# new stuff
		s['otherDependencies'] = {}
		for dependency_scheme in sentence['dependencies']:
			if 'dep' in dependency_scheme:
				s['otherDependencies'][dependency_scheme['@type']] = extract_dependency_triplets(dependency_scheme['dep'])
			else:
				s['otherDependencies'][dependency_scheme['@type']] = []

		#sentiment
		s['sentimentValue'] =  int(sentence['@sentimentValue'])
		s['sentiment'] =  sentence['@sentiment']

		new_dict['sentences'].append(s)
	if 'coreference' in temp_dict['root']['document']:
		new_dict['coref'] = extract_coref_chains(temp_dict['root']['document']['coreference']['coreference'])
	else:
		new_dict['coref'] = []
	return new_dict

def extract_dependency_triplets(dependency_list):
	new_relations = []
	#if there are no multiple entries. the xmltodict does not give out a list.
	if not isinstance(dependency_list, list):
		dependency_list = [dependency_list]

	for relation in dependency_list:
		new_relation = (relation['@type'], 
				'%s-%s' % (relation['governor']['#text'], relation['governor']['@idx']),
				'%s-%s' % (relation['dependent']['#text'], relation['dependent']['@idx']))
		new_relations.append(new_relation)
	return new_relations

def extract_coref_chains(coref_chain_list):
	new_coref_chain_list = []
	if not isinstance(coref_chain_list, list):
		coref_chain_list = [coref_chain_list]
	for coref_chain in coref_chain_list:
		mentions = []
		for mention in coref_chain['mention']:
			mentions.append((mention['text'], int(mention['sentence']), int(mention['head']), \
					int(mention['start']), int(mention['end'])))
		new_coref_chain_list.append(mentions)
	return new_coref_chain_list

def convert_files(file_names):
	for file_name in file_names:
		print file_name
		parse_dict = xml2json(open(file_name).read())
		json_file_name = file_name.rsplit('.')[0] + '.json'
		new_file = open(json_file_name, mode='w')
		new_file.write(json.dumps(parse_dict))
		new_file.close()

if __name__ == '__main__':
	procs = [Process(target=convert_files, args=(chunk,)) for chunk in slice_list(sys.argv[1:], 12)]
	for p in procs:
		p.start()
	for p in procs:
		p.join()

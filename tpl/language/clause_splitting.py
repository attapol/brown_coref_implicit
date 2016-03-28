"""Clause splitting utility

A clause is defined as a subtree from a dependency parse tree
such that the root of the subtree is a verb and the descendants are 
non-verbs. Each node must belong to exactly one subtree

Copula verbs make things a little difficult. They need to be switched 
with their parents on the tree.
"""
from tpl.language.syntactic_structure import DependencyGraph, Edge, Node

def split_clauses_from_sentence(sentence):
	"""Split clauses from dependencies given out by the parser

	Each sentence is a dictionary with the following fields

		parsetree : one line Penn style bracketed parse. use nltk.tree.Tree to parse it
			e.g. print nltk.tree.Tree(parse_tree).pprint()

		dependencies : a list of dependency relations (also a list)
			[['nn','Vinken','Pierre'], ['nsubj','join','Vinken']]

		text : the raw text string for this sentence

		words : a list of words (also a list)
			
	Each word is a list of [word, dictionary]

		word is just a string

		dictionary has the following fields:

			CharacterOffsetBegin
			CharacterOffsetEnd
			Lemma
			PartOfSpeech

	"""
	if 'clause_list' in sentence and 'head_verbs' in sentence:
		return (sentence['clause_list'], sentence['head_verbs'])
	dependencies = sentence['dependencies']
	if len(dependencies) == 0:
		sentence['dependency_tree'] = None
		sentence['word_index_to_head_verb_index'] = {}
		return ([],[])
	pos = [word[1]['PartOfSpeech'] for word in sentence['words']]
	dependency_tree = convert_dependencies_to_tree(dependencies)
	if dependency_tree is None:
		sentence['dependency_tree'] = None
		sentence['word_index_to_head_verb_index'] = {}
		return ([],[])
	sentence['dependency_tree'] = dependency_tree
	sentence['clause_list'], sentence['head_verbs'] = \
		split_clauses_from_dependency_tree(dependency_tree.root_node, pos)
	sentence['word_index_to_head_verb_index'] = \
		_get_head_verb_mapping(sentence['clause_list'], sentence['head_verbs'], sentence['words'])
	return sentence['clause_list'], sentence['head_verbs'] 

def _get_head_verb_mapping(clause_list, head_verb_indices, words):
	"""Create a map from word index to head verb index

	The indices in clause_list and head_verb_indices are one off. 
	So we need to subtract one when we build the map

	Returns:
		a dictionary mapping word index to head verb index
		The indices are NOT one off.
	"""
	word_index_to_head_verb_index = {}
	num_words = len(words)
	for i in xrange(num_words):
		found_clause = False
		for clause, head_verb in zip(clause_list, head_verb_indices):
			#punctuation is not included in the tree so we have
			#to use a heuristic here
			if (i + 1 in clause) or \
				((not words[i][0].isalnum()) and clause[0] - 2 <= i + 1 <= clause[-1] + 2):
				found_clause = True
				word_index_to_head_verb_index[i] = head_verb - 1
				break
		if not found_clause:
			#this should not happen. duck taping
			if len(clause_list) == 1:
				word_index_to_head_verb_index[i] = 0
			else:
				word_index_to_head_verb_index[i] = -1
			#print clause_list
			#print i
			#print words[i][0]
			#temp_words = [x[0] for x in words]
			#print ' '.join(temp_words)
			#raise Exception('Clause not found')

	return word_index_to_head_verb_index

def split_clauses_from_dependency_tree(dependency_tree_node, pos):
	"""Split clauses

	Returns:
		a list of lists. Each sublist contains indices of the tokens
	in the clause. The indices are one off because the ROOT node is indexed at 0.

	"""
	if dependency_tree_node is None:
		return ([], [])
	assert(len(dependency_tree_node.edges) == 1 and \
		dependency_tree_node.token_position == -1)
	
	clauses = []
	head_verbs = []
	_recurse_split_clauses(dependency_tree_node.edges[0].to_node, pos, [], clauses, [], head_verbs)
	for clause in clauses:
		clause.sort()
	return (clauses, head_verbs)

def _recurse_split_clauses(root_node, pos, clause_so_far, clause_list, path, head_verbs):
	"""Recursively split clauses

	Args:
		root_node: the root (changing with each call)
		pos: a list of parts of speech
		clause_so_far: a list of tokens (their positions) in the clause so far
		clause_list: a list of clauses that we have collected so far
		path: an orderd list of edges the path from the current head verb to root_node. 
			[] if root_node is the head
		head_verbs: a list of head verbs (their positions) that we have collected so far
	"""
	#the exception case
	if pos[root_node.token_position][0] != 'V':
		for edge in root_node.edges:
			if edge.dep_type == 'cop' or edge.dep_type == 'aux':
				Node.swap_token(edge.from_node, edge.to_node)
				edge.dep_type = '_' + edge.dep_type
				_recurse_split_clauses(edge.from_node, pos, [], clause_list, [], head_verbs)
				return

	#new clause. add to the list
	if len(clause_so_far) == 0:
		clause_list.append(clause_so_far)
		head_verbs.append(root_node.token_position + 1)
	root_node.path_to_head_verb = [x for x in path]
	clause_so_far.append(root_node.token_position + 1)


	#base case
	if len(root_node.edges) == 0:
		return

	#recursive case
	for edge in root_node.edges:
		#new head verb
		if pos[edge.to_node.token_position][0] == 'V' and not edge.dep_type == 'rcmod':
			new_clause = []
			_recurse_split_clauses(edge.to_node, pos, new_clause, clause_list, [], head_verbs)
			#we don't allow a clause with just one token
			if len(new_clause) <= 1:
				clause_list.remove(new_clause)
				head_verbs.pop()
				clause_so_far.append(edge.to_node.token_position + 1)
		else:
			path.append(edge)
			_recurse_split_clauses(edge.to_node, pos, clause_so_far, clause_list, path, head_verbs)
			path.pop()


def convert_dependencies_to_tree(dependencies):
	"""Tree is a graph where each node has exactly one parent
	and there's no cycle 
	"""
	tree_dependencies = treeify(dependencies)
	graph = convert_dependencies_to_graph(tree_dependencies)
	return graph

def treeify(dependencies):
	"""Remove dependency that points to the node that already has a parent
	"""
	tree_dependencies = [x for x in dependencies]
	child_to_parents = {}
	for dep in dependencies:
		if dep[2] in child_to_parents:
			child_to_parents[dep[2]].append(dep)
		else:
			child_to_parents[dep[2]] = [dep]

	for child, parents in child_to_parents.items():
		parents.sort(key=lambda x: x[1].rsplit('-', 1)[1])
		if len(parents) > 1:
			for i in xrange(1, len(parents)):
				parent = parents[i]
				tree_dependencies.remove(parent)
	return tree_dependencies

def convert_dependencies_to_graph(dependencies):
	graph = DependencyGraph()
	root_node = None
	assert(len(dependencies) > 0)
	#Try to find root
	for dep in dependencies:
		if dep[0] == 'root':
			root_node = Node(dep[1])
			first_real_node = Node(dep[2])
			root_edge = Edge(root_node, first_real_node, dep[0])
			root_node.edges.append(root_edge)
			graph.root_node = root_node
			graph.add_node(root_node)
			graph.add_node(first_real_node)
			graph.add_edge(root_edge)
			break
	if root_node is not None:
		_construct_subgraph(dependencies, first_real_node, graph)
	return graph

def _construct_subgraph(dependencies, root_node, graph):
	for dep in dependencies:
		if dep[1] == root_node.token:
			new_node = Node(dep[2])
			new_edge = Edge(root_node, new_node, dep[0])
			root_node.edges.append(new_edge)
			graph.add_node(new_node)
			graph.add_edge(new_edge)
			_construct_subgraph(dependencies, new_node, graph)

import json
from tpl.misc import TJsonEncoder
if __name__ == '__main__':
	"""For testing purposes"""
	from tpl.language.stanford_parser import Parser
	parser = Parser()
	parse_result = parser.parse('Barack Obama, who you talked to yesterday, play basketball.')
	sentence = parse_result['sentences'][0]
	split_clauses_from_sentence(sentence)
	print json.dumps(sentence, indent=2, cls=TJsonEncoder)
	print json.dumps(sentence['dependency_tree'].to_dict(), indent=2)
	dgraph = DependencyGraph.from_dict(sentence['dependency_tree'].to_dict())
	print json.dumps(dgraph.to_dict(), indent=2)
	print dgraph.to_dict() == DependencyGraph.from_dict(dgraph.to_dict()).to_dict()

"""Data structures for syntactic units

This package for now only includes dependency graph.

"""

class DependencyGraph(object):
	"""Support convention of G = <V, E>

	It provides a quick access to any node in a sentence because
	we know the position in the linear order in the original sentence.

	"""
	
	def __init__(self):
		self.root_node = None
		self.nodes = []
		self.edges = []

	def add_node(self, node):
		self.nodes.append(node)


	def add_edge(self, edge):
		self.edges.append(edge)

	def node_linear_position_to_node(self, node_position):
		for node in self.nodes:
			if node.token_position == node_position:
				return node
		return None

	def get_parent_index(self, source_node_position):
		for edge in self.edges:
			if edge.to_node.token_position == source_node_position:
				return edge.from_node.token_position
		return -1
		raise Exception('the node has no parents (this should not happen)')

	def get_child_indices(self, source_node_position):
		source_node = self.node_linear_position_to_node(source_node_position)
		return [edge.to_node.token_position for edge in source_node.edges]

	def get_path_from_to(self, source_node_position, target_node_position):
		"""Get the edges that lead from one node to the other

		Args:
			source_node_position : the position of the source node on the original sentence
			target_node_position : the position of the target node on the original sentence
			NOTE: the positions are NOT one off.

		Returns:
			A list of edges that form the path
		"""
		source_node = self.node_linear_position_to_node(source_node_position)
		target_node = self.node_linear_position_to_node(target_node_position)
		path_so_far = []
		self._recurse_get_path_from_to(source_node, target_node, path_so_far)
		return path_so_far	

	def _recurse_get_path_from_to(self, source_node, target_node, path_so_far):
		if source_node == target_node:
			return True

		for edge in source_node.edges:
			child = edge.to_node
			path_so_far.append(edge.dep_type)	
			if self._recurse_get_path_from_to(child, target_node, path_so_far):
				return True
			path_so_far.pop()

		return False
	
	def get_path_to_head_verb(self, source_node_position):
		"""Get a list of edges that form a path to head verb

		Clause splitting algorithm must have been run before this
		or it will fail silently by returning None

		"""
		source_node = self.node_linear_position_to_node(source_node_position)
		if source_node is not None:
			return source_node.path_to_head_verb
		else:
			#this might be punctuation because it is not included in the dependency tree
			return None

	def to_dict(self):
		if self.root_node is None:
			return {
				'root_node_position': None,
				'nodes': [node._to_dict() for node in self.nodes],
				'edges': [edge._to_dict() for edge in self.edges]
			}
		else:
			return {
				'root_node_position': self.root_node.token_position,
				'nodes': [node._to_dict() for node in self.nodes],
				'edges': [edge._to_dict() for edge in self.edges]
			}

	@classmethod
	def from_dict(cls, json_dict):
		dgraph = DependencyGraph()

		#recreating nodes
		dgraph.nodes = [Node._from_dict(node) for node in json_dict['nodes']]
		node_position_to_node = {}
		for node in dgraph.nodes:
			node_position_to_node[node.token_position] = node

		#recreating edges
		dgraph.edges = [] 
		edge_string_to_edge = {}
		for edge in json_dict['edges']:
			from_node = node_position_to_node[edge['from_node_position']]
			to_node = node_position_to_node[edge['to_node_position']]
			edge = Edge(from_node, to_node, edge['dep_type'])
			edge_string_to_edge[edge.__str__()] = edge
			dgraph.edges.append(edge)
			from_node.edges.append(edge)

		#finding the root node
		for node in dgraph.nodes:
			if node.token_position == json_dict['root_node_position']:
				dgraph.root_node = node
			edge_list_path = \
					[edge_string_to_edge[edge_str] for edge_str in node.path_to_head_verb]
		return dgraph

class Node(object):
	"""A node for a dependency tree 
	
	Fields:
		edges: a list of edges where each edge.from_node == self
		token: a token of form word-position e.g. analysts-3
		no_num_token : the token without the position e.g. analysts
		token_position : the position of the token on the original sentence e.g. 3
	"""

	def __init__(self, token):
		self.edges = []
		self.token = token
		self.no_number_token, self.token_position = token.rsplit('-', 1)
		self.token_position = int(self.token_position) - 1
		self.path_to_head_verb = []

	@property
	def children(self):
		return [edge.to_node for edge in self.edges]

	def find_children_by_dep_type(self, dep_type):
		return [edge.to_node for edge in self.edges if edge.dep_type == dep_type]

	def _to_dict(self):
		return {
			'token': self.token,
			'path_to_head_verb': [edge.__str__() for edge in self.path_to_head_verb]
		}

	@classmethod
	def _from_dict(cls, json_dict):
		"""Json decoding support

		NOTE: path_to_head_verb wasn't filled in with the actual list. 
		DependencyGraph class has to do extra stuff to decode.
		This is why this method is marked as 'private'.
		It should only be called by DependencyGraph
		"""
		node = Node(json_dict['token'])	
		node.path_to_head_verb = json_dict['path_to_head_verb']
		return node

	def __str__(self):
		return 'root = %s, immediate children = %s' \
			% (self.token, (','.join([e.to_node.token for e in self.edges])))

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return self.token == other.token

	def num_children(self):
		return len(self.edges)

	@classmethod
	def swap_token(cls, node1, node2):
		tmp_token = node1.token
		tmp_no_number_token = node1.no_number_token
		tmp_token_position = node1.token_position

		node1.token = node2.token
		node1.no_number_token = node2.no_number_token
		node1.token_position = node2.token_position

		node2.token = tmp_token
		node2.no_number_token = tmp_no_number_token
		node2.token_position = tmp_token_position

class Edge(object):
	"""Edge for representing a dependency between two nodes and its type
	"""

	def __init__(self, from_node, to_node, dep_type):
		self.dep_type = dep_type
		self.from_node = from_node
		self.to_node = to_node

	def __str__(self):
		return '(%s, %s, %s)' % (self.dep_type, self.from_node.token, self.to_node.token)

	def __repr__(self):
		return self.__str__()

	def _to_dict(self):
		return {
			'dep_type': self.dep_type,
			'from_node_position': self.from_node.token_position,
			'to_node_position': self.to_node.token_position,
		}


def find_lowest_common_ancestor(tree, token_indices, start_index=0):
	return _recurse_find_lowest_common_ancestor(tree, token_indices, 0)



def get_coverage(tree, start_index):
	"""Find out the token coverage of the non-terminal"""
	pass

	

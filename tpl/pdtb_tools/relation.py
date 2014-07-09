"""Relation class wrapper for PDTB discourse relation tokens

The JSON structure created by Corpus class is a bit messy to access
because the optional fields might not exist.
"""
import json
from tpl.testing import assert_ge

class Relation(object):

	def __init__(self, relation_dict):
		self.data_dict = relation_dict
		self.arg1 = Arg(relation_dict['arg1'])
		self.arg2 = Arg(relation_dict['arg2'])

	@property
	def wsj_section(self):
		return self.data_dict['wsj_section']

	@property
	def wsj_section_number(self):
		return int(self.wsj_section[0:2])

	@property
	def wsj_doc_number(self):
		return int(self.wsj_section[2:4])


	@property
	def type(self):
		return self.data_dict['type']

	@property
	def attribution_source_tuple(self):
		"""Return (Rel source, Arg1 source, Arg2 source)"""
		rel_source = self.attribution_features.source
		arg1_source = self.arg1.attribution_features.source
		arg2_source = self.arg2.attribution_features.source
		return (rel_source, arg1_source, arg2_source)

	@property
	def conn_attribution_features(self):
		if self.attribution_features is not None:
			return self.attribution_features
		else:
			return None

	@property
	def conn_attribution_type(self):
		if self.attribution_features is not None:
			return self.attribution_features.type
		else:
			return None

	@property
	def conn_attribution_span(self):
		if self.attribution_features is not None:
			return self.attribution_features.span
		else:
			return None
	
	def arg_attribution_features(self, arg_index):
		assert(arg_index == 1 or arg_index == 2)
		if arg_index == 1:
			return self.arg1.attribution_features
		else:
			return self.arg2.attribution_features

	def arg_attribution_type(self, arg_index):
		assert(arg_index == 1 or arg_index == 2)
		if arg_index == 1:
			return self.arg1.attribution_features.type
		else:
			return self.arg2.attribution_features.type

	def __repr__(self):
		return json.dumps(self.data_dict, indent=4)

	def __str__(self):
		return json.dumps(self.data_dict, indent=4)

	@classmethod
	def from_json(cls, relation_dict):
		if not isinstance(relation_dict, dict):
			relation_dict = json.loads(relation_dict)
		relation_type = relation_dict['type']
		if relation_type == 'Explicit':
			return ExplicitRelation(relation_dict)	
		if relation_type == 'Implicit':
			return ImplicitRelation(relation_dict)	
		if relation_type == 'AltLex':
			return AltLexRelation(relation_dict)	
		if relation_type == 'NoRel':
			return NoRelRelation(relation_dict)	
		if relation_type == 'EntRel':
			return EntRelRelation(relation_dict)	

class RelevantRelation(Relation):

	def __init__(self, relation_dict):
		super(RelevantRelation, self).__init__(relation_dict)

	def relation_sense_tags(self, conn_index):
		assert(conn_index == 1 or conn_index == 2)
		if conn_index == 1:
			conn = self.conn1
		else:
			conn = self.conn2

		if conn is not None and not isinstance(conn, dict):
			return conn.split(', ')[1:]
		else: 
			return None

	def relation_sense_tags_at_level(self, level):
		"""Get the sense the specified level starting from 0 = top level"""
		assert_ge(level, 0)
		sense_tags1 = self.relation_sense_tags(1)
		sense_tags2 = self.relation_sense_tags(2)
		sense_tags = []
		if sense_tags1 is not None:
			for sense in sense_tags1:
				split_sense = sense.split('.')
				if len(split_sense) >= level:
					sense_tags.append(split_sense[level])
		if sense_tags2 is not None:
			for sense in sense_tags2:
				split_sense = sense.split('.')
				if len(split_sense) >= level:
					sense_tags.append(split_sense[level])
		return sense_tags
	
class ExplicitRelation(RelevantRelation):
	
	def __init__(self, relation_dict):
		super(ExplicitRelation, self).__init__(relation_dict)
		self.attribution_features = \
			AttributionFeatures(relation_dict['explicitRelationFeatures']['attributionFeatures'])
		self.selection = Selection(relation_dict['selection'])
		self.conn1 = relation_dict['explicitRelationFeatures']['Conn1']
		self.conn2 = None

	@property
	def connective(self):
		return self.selection.raw_text


class ImplicitRelation(RelevantRelation):
	
	def __init__(self, relation_dict):
		super(ImplicitRelation, self).__init__(relation_dict)
		self.attribution_features = \
			AttributionFeatures(relation_dict['implicitRelationFeatures']['attributionFeatures'])
		self.selection = None
		self.conn1 = relation_dict['implicitRelationFeatures']['Conn1']
		if 'Conn2' in relation_dict['implicitRelationFeatures']:
			self.conn2 = relation_dict['implicitRelationFeatures']['Conn2']
		else:
			self.conn2 = None

class AltLexRelation(RelevantRelation):
	
	def __init__(self, relation_dict):
		super(AltLexRelation, self).__init__(relation_dict)
		self.attribution_features = \
			AttributionFeatures(relation_dict['altLexRelationFeatures']['attributionFeatures'])
		self.selection = Selection(relation_dict['selection'])
		self.conn1 = None

	def relation_sense_tags(self, conn_index):
		"""Conn head is not included in the field"""
		assert(conn_index == 1 or conn_index == 2)
		return [self.data_dict['altLexRelationFeatures']['SemanticClass']]

class NonRelevantRelation(Relation):
	"""EntRel and NoRel have the same structure 

	"""
	@property
	def conn_attribution_features(self):
		return None

	@property
	def conn_attribution_span(self):
		return None

class NoRelRelation(NonRelevantRelation):
	def __init__(self, relation_dict):
		super(NoRelRelation, self).__init__(relation_dict)

	def relation_sense_tags(self, conn_index):
		return ['NoRelSense']

class EntRelRelation(NonRelevantRelation):
	
	def __init__(self, relation_dict):
		super(EntRelRelation, self).__init__(relation_dict)

	def relation_sense_tags(self, conn_index):
		return ['Expansion']

	def relation_sense_tags_at_level(self, level):
		"""Get the sense the specified level starting from 0 = top level"""
		return ['Expansion']

class Arg(object):
	"""
	
	Selection
	AttributionFeatures
	"""
	def __init__(self, arg_dict):
		self.data_dict = arg_dict
		self.selection = Selection(arg_dict['selection'])
		if 'attributionFeatures' in arg_dict:
			self.attribution_features = AttributionFeatures(arg_dict['attributionFeatures'])
		else:
			self.attribution_features = None

	@property
	def text(self):
		return self.selection.raw_text

	@property
	def text_span_ranges(self):
		return self.selection.span_ranges

	@property
	def attribution_span(self):
		return self.attribution_features.span

class AttributionFeatures(object):

	def __init__(self, attribution_feature_dict):
		self.data_dict = attribution_feature_dict
		if 'selection' in self.data_dict:
			self.selection = Selection(self.data_dict['selection'])
		else:
			self.selection = None
	
	@property
	def span_ranges(self):
		if self.selection is not None:
			return self.selection.span_ranges
		else:
			return None

	@property
	def span(self):
		if self.selection is None:
			return None
		else:
			return self.selection.raw_text

	@property
	def feature_tuple(self):
		"""Returns a tuple of (source, type, polarity, determinacy)"""
		return tuple(self.data_dict['Attribution'].split(', '))


	@property
	def source(self):
		return self.data_dict['Attribution'].split(',')[0].strip()

	@property
	def type(self):
		return self.data_dict['Attribution'].split(',')[1].strip()

	@property
	def polarity(self):
		return self.data_dict['Attribution'].split(',')[2].strip()

	@property
	def determinacy(self):
		return self.data_dict['Attribution'].split(',')[3].strip()

	def __str__(self):
		return self.data_dict.__str__()


class Selection(object):
	"""

	GornAddressList
	SpanList
	RawText
	"""
	def __init__(self, selection_dict):
		self.data_dict = selection_dict

	@property
	def raw_text(self):
		return self.data_dict['RawText']

	@property
	def gorn_address_list(self):
		return self.data_dict['GornAddressList'].strip().split(';')

	@property
	def num_sentences(self):
		gorn_address_list = self.gorn_address_list
		sentence_id_set = set()
		for gorn_address in gorn_address_list:
			sentence_id_set.add(gorn_address.split(',')[0])	
		return len(sentence_id_set)

	@property
	def span_ranges(self):
		span_list_text = self.data_dict['SpanList']
		if ';' in span_list_text:
			spans = []
			for span_range_text in span_list_text.split(';'):
				split_span_range_text = span_range_text.split('..')
				spans.append((int(split_span_range_text[0]), int(split_span_range_text[1])))
			return spans
		else:
			span_range_text = span_list_text.split('..')
			return [(int(span_range_text[0]), int(span_range_text[1]))]


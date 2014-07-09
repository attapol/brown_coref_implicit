"""Classes that parse json and put into an object wrapper
The jsons look like this for each type of relation

ExplicitRel
{
  "type": "Explicit", 
  "selection": {
    "SpanList": "258..262", 
    "GornAddressList": "1,0,1,2,0", 
    "RawText": "once"
  }, 
  "explicitRelationFeatures": {
    "attributionFeatures": {
      "Attribution": "Ot, Comm, Null, Null", 
      "selection": {
        "SpanList": "361..377", 
        "GornAddressList": "1,1;1,2;1,3;1,4", 
        "RawText": "researchers said"
      }
    }, 
    "Conn1": "once, Temporal.Asynchronous.Succession"
  }, 
  "sup1": {}, 
  "arg1": {
    "selection": {
      "SpanList": "202..257", 
      "GornAddressList": "1,0,0;1,0,1,0;1,0,1,1;1,0,1,3", 
      "RawText": "The asbestos fiber, crocidolite, is unusually resilient"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "arg2": {
    "selection": {
      "SpanList": "263..282", 
      "GornAddressList": "1,0,1,2,1", 
      "RawText": "it enters the lungs"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "sup2": {}, 
  "wsj_section": "0003"
}

Implicit
{
  "type": "Implicit", 
  "inferenceSite": {
    "StringPosition": "778", 
    "SentenceNumber": "5"
  }, 
  "implicitRelationFeatures": {
    "attributionFeatures": {
      "Attribution": "Ot, Comm, Null, Null", 
      "selection": {
        "SpanList": "726..753", 
        "GornAddressList": "4,0;4,1,0;4,1,1;4,1,2;4,2", 
        "RawText": "A Lorillard spokewoman said"
      }
    }, 
    "Conn1": "in fact, Expansion.Restatement.Specification"
  }, 
  "sup1": {}, 
  "arg1": {
    "selection": {
      "SpanList": "756..776", 
      "GornAddressList": "4,1,3", 
      "RawText": "This is an old story"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "arg2": {
    "selection": {
      "SpanList": "778..874", 
      "GornAddressList": "5", 
      "RawText": "We're talking about years ago before anyone heard of asbestos having any questionable properties"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "sup2": {}, 
  "wsj_section": "0003"
}

EntRel
{
  "type": "EntRel", 
  "inferenceSite": {
    "StringPosition": "94", 
    "SentenceNumber": "1"
  }, 
  "arg1": {
    "selection": {
      "SpanList": "9..92", 
      "GornAddressList": "0", 
      "RawText": "Pierre Vinken, 61 years old, will join the board as a nonexecutive director Nov. 29"
    }
  }, 
  "arg2": {
    "selection": {
      "SpanList": "94..161", 
      "GornAddressList": "1", 
      "RawText": "Mr. Vinken is chairman of Elsevier N.V., the Dutch publishing group"
    }
  }, 
  "wsj_section": "0001"
}

NoRel
{
  "type": "NoRel", 
  "inferenceSite": {
    "StringPosition": "3595", 
    "SentenceNumber": "26"
  }, 
  "arg1": {
    "selection": {
      "SpanList": "3410..3593", 
      "GornAddressList": "25", 
      "RawText": "Workers dumped large burlap sacks of the imported material into a huge bin, poured in cotton and acetate fibers and mechanically mixed the dry fibers in a process used to make filters"
    }
  }, 
  "arg2": {
    "selection": {
      "SpanList": "3595..3716", 
      "GornAddressList": "26", 
      "RawText": "Workers described \"clouds of blue dust\" that hung over parts of the factory, even though exhaust fans ventilated the area"
    }
  }, 
  "wsj_section": "0003"
}

AltLex
{
  "type": "AltLex", 
  "selection": {
    "SpanList": "404..423", 
    "GornAddressList": "4,0;4,2", 
    "RawText": "The idea, of course"
  }, 
  "altLexRelationFeatures": {
    "attributionFeatures": {
      "Attribution": "Wr, Comm, Null, Null"
    }, 
    "SemanticClass": "Contingency.Cause.Reason"
  }, 
  "sup1": {}, 
  "arg1": {
    "selection": {
      "SpanList": "310..402", 
      "GornAddressList": "3", 
      "RawText": "And the city decided to treat its guests more like royalty or rock stars than factory owners"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "arg2": {
    "selection": {
      "SpanList": "404..572", 
      "GornAddressList": "4", 
      "RawText": "The idea, of course: to prove to 125 corporate decision makers that the buckle on the Rust Belt isn't so rusty after all, that it's a good place for a company to expand"
    }, 
    "attributionFeatures": {
      "Attribution": "Inh, Null, Null, Null"
    }
  }, 
  "sup2": {}, 
  "wsj_section": "0010"
}


"""
import sqlite3
import json
from codecs import open as copen
from collections import OrderedDict
from tpl.pdtb_tools.relation import Relation

class Corpus:

	def __init__(self):
		self.json_file = copen('wsj_pdtb.jsons', mode='w', encoding='latin1')

	def close(self):
		self.json_file.close()

	def add_relations(self, wsj_section, relation_jsons):
		for relation_json in relation_jsons:
			relation_json['wsj_section'] = wsj_section
			self.json_file.write(json.dumps(relation_json))
			self.json_file.write('\n')

class CorpusReader:
	"""Tools for lazily reading in wsj_pdtb.jsons

	This class is more convenient for debugging and developing because it does not
	read every data point in at once. 
	"""

	def __init__(self, jsons_file):
		self.data_list = None	
		self.jsons_file = jsons_file

	def _init_data_list(self):
		self.data_list = []
		with copen(self.jsons_file, mode='r', encoding='latin1') as f:
			for line in f:
				new_relation = Relation.from_json(json.loads(line, object_pairs_hook=OrderedDict))
				self.data_list.append(new_relation)

	@property
	def data(self):
		if self.data_list is None:
			self.data_list = []
			with copen(self.jsons_file, mode='r', encoding='latin1') as f:
				for line in f:
					new_relation = Relation.from_json(json.loads(line, object_pairs_hook=OrderedDict))
					self.data_list.append(new_relation)
					yield new_relation	
		else:
			for i in xrange(len(self.data_list)):
				yield self.data_list[i]

	def select_wsj_section(self, section_number):
		return self.select_wsj_section([section_number])

	def select_wsj_sections(self, section_number_list):
		if self.data_list is None:
			self._init_data_list()
		for i in xrange(len(self.data_list)):
			if self.data_list[i].wsj_section_number in section_number_list:
				yield self.data_list[i]

	def select(self, predicate):
		for relation in self.data:
			if predicate(relation):
				yield relation

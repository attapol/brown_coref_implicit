import sqlite3

from features.temporal_feature_functions import *
from features.feature_functions import *
from features.park_feature_functions import *
from features.naming_functions import *

from util import convert_sqlite_row_to_dict, make_singleton_sequence_data_file, convert_to_two_char_string, run_multiple_threads

db_file = 'db_pdtb.db'
	
def make_data_file_from_sections(naming_function, label_function, 
		feature_function_list, section_numbers, output_file_name, 
		make_file=True, make_db=False, use_gold=False):
	"""A maker function to be used directly or by run_multiple_threads

	"""
	for section_number in section_numbers:
		start_section_number_str = convert_to_two_char_string(section_number)
		end_section_number_str = convert_to_two_char_string(section_number + 1)
		with sqlite3.connect(db_file, check_same_thread=False) as conn:
			conn.row_factory = sqlite3.Row
			print "Retrieving data for section %s" % section_number
			sql_command = """
				SELECT *
				FROM implicit_relations
				WHERE wsj_id > '%s' AND wsj_id < '%s' 
				""" % (start_section_number_str, end_section_number_str)
			instances = conn.execute(sql_command).fetchall()
		instances = [convert_sqlite_row_to_dict(x) for x in instances]
		if make_file:
			make_singleton_sequence_data_file(instances, naming_function, label_function, feature_function_list,
					output_file_name, incremental=True, use_gold=use_gold)


def vsall_experiment5():
	"""This is the version that yields the results in the EACL paper.

	"""
	plf = ParkLexicalFeaturizer()
	lf = LexicalFeaturizer()
	cf = CorefFeaturizer()
	feature_function_list = [initialization_feature, money_date_percent_feature,
			is_arg1_multiple_sentences, list_punc_arg, 
			cf.coref_arg_feature, cf.coref_verb_pair_feature, cf.coref_head_verb_pair_feature,
			cf.synonym_head_verb_pair_feature, cf.same_main_verb_feature,
			first_last_first_3, average_vp_length, modality, plf.inquirer_tag_feature, plf.mpqa_score_feature,
			plf.levin_verbs, production_rules, lf.brown_word_feature, lf.brown_word_pairs]
	naming_function = wsj_id_sentence_pair_naming_function
	label_function = all_label_with_entrel_function
	label_function = all_label_function
	run_multiple_threads(6, naming_function, label_function, feature_function_list, \
			make_data_file_from_sections, make_file=True, make_db=False, use_gold=False)

if __name__ == '__main__':
	vsall_experiment5()


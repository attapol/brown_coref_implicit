
def wsj_id_naming_function(instance):
	name = '%s' % (instance['wsj_id'], )
	return name

def wsj_id_sentence_pair_naming_function(instance):
	name = '%s "%s" "%s"' % (instance['wsj_id'], instance['relation'].arg1.text, instance['relation'].arg2.text)
	return name


CREATE TABLE IF NOT EXISTS implicit_relations AS
SELECT r.wsj_id as 		wsj_id,
r.id as 				relation_id,
r.relation_json as 		relation_json,
r.relation_type as		relation_type,
r.arg1_sentence_id as 	arg1_sentence_id, 
r.arg2_sentence_id as 	arg2_sentence_id, 
p1.parse_json as 		arg1_parse_json,
p2.parse_json as 		arg2_parse_json,
p1.coreference_json as	coreference_json
FROM relations as r, parses as p1, parses as p2
WHERE r.wsj_id = p1.wsj_id AND r.wsj_id = p2.wsj_id AND
r.arg1_sentence_id = p1.sentence_id AND r.arg2_sentence_id = p2.sentence_id AND
(r.relation_type = 'Implicit' or r.relation_type = 'EntRel');

CREATE INDEX IF NOT EXISTS implicit_relation_id ON implicit_relations (wsj_id);

CREATE TABLE IF NOT EXISTS source_temp AS
SELECT r.wsj_id as 		wsj_id,
r.id as 				relation_id,
r.relation_json as 		relation_json,
r.arg1_sentence_id as 	arg1_sentence_id, 
r.arg2_sentence_id as 	arg2_sentence_id, 
s1.truth_json as 		arg1_gold_attribution_span_json,
s2.truth_json as 		arg2_gold_attribution_span_json,
s1.predicted_json as 	arg1_auto_attribution_span_json,
s2.predicted_json as 	arg2_auto_attribution_span_json,
p1.parse_json as 		sentence1, 
p2.parse_json as 		sentence2
FROM relevant_relations AS r, parses AS p1, parses AS p2, 
attribution_spans as s1, attribution_spans as s2
WHERE r.wsj_id = p1.wsj_id AND r.wsj_id = p2.wsj_id AND 
r.arg1_sentence_id = p1.sentence_id AND r.arg2_sentence_id = p2.sentence_id AND
r.wsj_id = s1.wsj_id AND r.wsj_id = s2.wsj_id AND 
r.arg1_sentence_id = s1.sentence_id AND r.arg2_sentence_id = s2.sentence_id;

CREATE INDEX IF NOT EXISTS source_wsj_id ON source_temp (wsj_id);

CREATE TABLE IF NOT EXISTS parses(
	wsj_section INTEGER,
	wsj_id TEXT,
	sentence_id INTEGER,
	partition TEXT,
	parse_json TEXT,
	sentence_start INTEGER,
	sentence_end INTEGER,
	sentence_text TEXT,
	coreference_json TEXT,
	PRIMARY KEY (wsj_id, sentence_id)	
);

CREATE TABLE IF NOT EXISTS relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	wsj_section INTEGER,
	wsj_id TEXT,
	arg1_sentence_id INTEGER,
	arg2_sentence_id INTEGER,
	relation_json TEXT,
	sense TEXT,
	relation_type TEXT,
	FOREIGN KEY (wsj_id) REFERENCES parses(wsj_id),
	FOREIGN KEY (wsj_id, arg1_sentence_id) REFERENCES parses(wsj_id, sentence_id),
	FOREIGN KEY (wsj_id, arg2_sentence_id) REFERENCES parses(wsj_id, sentence_id)
);
CREATE INDEX IF NOT EXISTS relation_foreign_keys ON relations (wsj_id);

CREATE TABLE IF NOT EXISTS attribution_span_features (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	wsj_id TEXT,
	sentence_id INTEGER,
	attribution_span TEXT,
	span_text TEXT,
	token_indices_json TEXT,
	parse_json TEXT,
	feature_json TEXT,
	detected INTEGER DEFAULT -1,
	truth_source TEXT,
	predicted_source TEXT,
	truth_type TEXT,
	predicted_type TEXT,
	truth_determinacy TEXT,
	predicted_determinacy TEXT,
	truth_polarity TEXT,
	predicted_polarity TEXT,
	CHECK (detected = 0 or detected = 1 or detected = -1),
	FOREIGN KEY (wsj_id, sentence_id) REFERENCES parses(wsj_id, sentence_id)
);

CREATE INDEX IF NOT EXISTS span_feature_foreign_keys ON attribution_span_features (wsj_id, sentence_id);



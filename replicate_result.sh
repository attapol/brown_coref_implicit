python2.7 -c 'import make_data_file; make_data_file.vsall_experiment5()'
TRAINING_SET=training_set.csv
TEST_SET=test_set.csv
sed -i 's/:/COLON/g' $TRAINING_SET
sed -i 's/:/COLON/g' $TEST_SET
javac NBMalletRunner.java

python2.7 prune_features.py $TRAINING_SET 5
java NBMalletRunner -training_set $TRAINING_SET -test_set $TEST_SET -output_prefix eacl_paper_exp -label_against_all Expansion -ratio 0.8 
java NBMalletRunner -training_set $TRAINING_SET -test_set $TEST_SET -output_prefix eacl_paper_temp -label_against_all Temporal -ratio 1.1 

python2.7 prune_features.py $TRAINING_SET 10
java NBMalletRunner -training_set $TRAINING_SET -test_set $TEST_SET -output_prefix eacl_paper_cont -label_against_all Contingency -ratio 0.9 

python2.7 prune_features.py $TRAINING_SET 15
java NBMalletRunner -training_set $TRAINING_SET -test_set $TEST_SET -output_prefix eacl_paper_comp -label_against_all Comparison -ratio 1.1


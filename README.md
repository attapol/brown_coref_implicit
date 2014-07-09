#Experimental code for Implicit Discourse Relation Classifier
The code that replicates results from 

Attapol T. Rutherford, Nianwen Xue (2014). Discovering Implicit Discourse Relations Through Brown Cluster Pair Representation and Coreference Patterns. Proceedings of the 14th Conference of the European Chapter of the Association for Computational Linguistics (EACL 2014)

## Prerequisites
1. Stanford CoreNLP suite
2. Python2.7 
3. sqlite3

## Recipe for replicating the results

1. Parse PDTB data into jsons
```python2.7 tpl/pdtb_tools/parse_pdtb.py path/to/pdtb/*```
You will then get ```wsj_pdtb.jsons``` file, which contain each relation in a json string on each line.

2. Parse WSJ text data with StanfordCoreNLP into XML format. This process takes quite a bit of time because we are parsing a large number of sentences.

3. Convert the parses into json format ```python2.7 corenlp_xml2json.py path/to/xml_parses/*``` Then you will have json file for each wsj file, which gets put into the same folder as the xml parse folder.

4. Adding the data to the database and converting them ```db/init_db path/to/parse_folder```. This will take quite a bit of time. 

5. Make a data file ```python2.7 make_data_file.py```
Then you have ```training_set.csv``` and ```test_set.csv```. The data are in tab-separated format. ```feature1 feature2\tlabel\twsj_section``` 

6. Use machine learning package of your choice to run classifier. To follow the process described in the paper, we also need to exclude the features that appear less than 5 times and reweight the instances such that the positive and negative classes receive the same total weights. 




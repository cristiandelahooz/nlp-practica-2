import pandas as pd
import numpy as np
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
import re
import os
import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import xml.etree.ElementTree as ElementTree

nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def wrap_trec_file(file_path):
    with open(file_path, 'r') as f:
        xml_content = f.read()
    return '<root>' + xml_content + '</root>'

def load_documents():
    xml = wrap_trec_file('cranfield-trec-dataset/cran.all.1400.xml')
    root = ElementTree.fromstring(xml)
    df = pd.DataFrame(columns=['docno', 'title', 'author', 'bib', 'text'])
    for doc in root:
        docno = doc.find('docno').text.strip() if doc.find('docno').text is not None else ''
        title = doc.find('title').text.strip() if doc.find('title').text is not None else ''
        author = doc.find('author').text.strip() if doc.find('author').text is not None else ''
        bib = doc.find('bib').text.strip() if doc.find('bib').text is not None else ''
        text = doc.find('text').text.strip() if doc.find('text').text is not None else ''
        new_row = pd.DataFrame({'docno': [docno], 'title': [title], 'author': [author], 'bib': [bib], 'text': [text]})
        df = pd.concat([df, new_row], ignore_index=True)
    return df

def load_queries(query_file):
    tree = ElementTree.parse(query_file)
    root = tree.getroot()
    queries = []
    query_ids = []
    for topic in root.findall('top'):
        qid = topic.find('num').text.strip()
        title = topic.find('title').text
        queries.append(title)
        query_ids.append(qid)
    return query_ids, queries

nlp = spacy.load("en_core_web_sm")

def data_cleaning(dataframe):
    dataframe['title'] = dataframe['title'].str.lower()
    dataframe['text'] = dataframe['text'].str.lower()
    dataframe['title'] = dataframe['title'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
    dataframe['text'] = dataframe['text'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
    dataframe['title'] = dataframe['title'].apply(word_tokenize)
    dataframe['text'] = dataframe['text'].apply(word_tokenize)
    stop_words = set(stopwords.words('english'))
    dataframe['title'] = dataframe['title'].apply(lambda x: [word for word in x if word not in stop_words])
    dataframe['text'] = dataframe['text'].apply(lambda x: [word for word in x if word not in stop_words])
    dataframe['title'] = dataframe['title'].apply(lambda x: [token.lemma_ for token in nlp(' '.join(x))])
    dataframe['text'] = dataframe['text'].apply(lambda x: [token.lemma_ for token in nlp(' '.join(x))])
    return dataframe

def vectorize(docs, queries):
    vectorizer = TfidfVectorizer(stop_words='english', max_df=0.85)
    doc_vectors = vectorizer.fit_transform(docs)
    query_vectors = vectorizer.transform(queries)
    return doc_vectors, query_vectors, vectorizer

def rank_documents(doc_vectors, query_vector, doc_ids):
    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    ranked_indices = np.argsort(similarities)[::-1]
    return [(doc_ids[i], similarities[i]) for i in ranked_indices]

def save_trec_results(query_id, ranked_docs, run_name, output_file):
    with open(output_file, 'a') as f:
        for rank, (doc_id, score) in enumerate(ranked_docs[:100], 1):
            f.write(f"{query_id} Q0 {doc_id} {rank} {score:.4f} {run_name}\n")

def expand_query_with_synsets(query):
    expanded_query_words = []
    for word in query.split():
        expanded_query_words.append(word)
        synsets = wordnet.synsets(word)
        if synsets:
            for lemma in synsets[0].lemmas():
                lemma_name = lemma.name().replace('_', ' ')
                if lemma_name not in expanded_query_words:
                    expanded_query_words.append(lemma_name)
    return ' '.join(expanded_query_words)

def clean_and_expand_queries(queries):
    cleaned_queries = []
    stop_words = set(stopwords.words('english'))
    for q in queries:
        q = q.lower()
        q = re.sub(r'[^\w\s]', '', q)
        tokens = word_tokenize(q)
        q_words = [word for word in tokens if word not in stop_words]
        lemmatized = [token.lemma_ for token in nlp(' '.join(q_words))]
        final_query = ' '.join(lemmatized)
        expanded_query = expand_query_with_synsets(final_query)
        cleaned_queries.append(expanded_query)
    return cleaned_queries

# --- Main Execution ---
docs = load_documents()
docs = data_cleaning(docs)
query_ids, queries = load_queries('cranfield-trec-dataset/cran.qry.xml')
expanded_queries = clean_and_expand_queries(queries)

# Modelo 1: Title-Only (con Expansión de Consulta)
docs_title = docs['title'].apply(lambda x: ' '.join(x) if isinstance(x, list) else x)
doc_vectors_title, query_vectors_title, _ = vectorize(docs_title, expanded_queries)
output_file_title = "trec_results_title.txt"
if os.path.exists(output_file_title): os.remove(output_file_title)
for i, (qid, query_vector) in enumerate(zip(query_ids, query_vectors_title)):
    ranked_docs = rank_documents(doc_vectors_title, query_vector, docs['docno'])
    save_trec_results(qid, ranked_docs, "title_expanded", output_file_title)

# Modelo 2: Title + Text (con Expansión de Consulta)
docs['title_text'] = docs.apply(lambda row: ' '.join(row['title']) + ' ' + ' '.join(row['text']), axis=1)
docs_title_text = docs['title_text']
doc_vectors_tt, query_vectors_tt, _ = vectorize(docs_title_text, expanded_queries)
output_file_tt = "trec_results_title_text.txt"
if os.path.exists(output_file_tt): os.remove(output_file_tt)
for i, (qid, query_vector) in enumerate(zip(query_ids, query_vectors_tt)):
    ranked_docs = rank_documents(doc_vectors_tt, query_vector, docs['docno'])
    save_trec_results(qid, ranked_docs, "title_text_expanded", output_file_tt)

print("Processing complete. Results files generated.")

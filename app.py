# -*- coding: utf-8 -*-
"""Phase 5 main_code without elastic search.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FrIu_N-PRgcQIw5jom1cIFbFtj75AFVn

# Set up
"""
!pip install scikit-learn==1.0.2
import streamlit as st
import pandas as pd
import numpy as np
import sklearn
import pickle
import pprint
import json
import requests
import sklearn.externals
import joblib
import gdown

import re
import string
#from nltk.corpus import stopwords
#from nltk.stem import PorterStemmer
#from bs4 import BeautifulSoup
#from tqdm import tqdm 

import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from pprint import pprint


# Install the latest main of Haystack
#!pip install --upgrade pip
#!pip install git+https://github.com/deepset-ai/haystack.git

import logging

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.INFO)


import os
from subprocess import Popen, PIPE, STDOUT



#############################################################################################################################################




#"""# External Knowledge :

#"""To obtain relevant web pages and videos for query /questions asked by a user by "Bing Search Api". """

@st.cache(suppress_st_warning=True)
def obtain_doc_using_api(query):

    
    #''' Defining the variables '''

    subscription_key = "056fbf0db0944abe8ebb9b8cca433712"
    assert subscription_key
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    search_term = query
    
    ''' Making Request '''

    headers = {"Ocp-Apim-Subscription-Key": subscription_key }
    params = {"q": search_term, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    #''' Converting obtained data into dataframe '''
    x = search_results["webPages"]["value"]
    doc = pd.DataFrame(x)
    
    return doc

#######################################################################################################################################


from haystack.document_stores import InMemoryDocumentStore
document_store = InMemoryDocumentStore()


#''' Use TfidfRetriever to find candidate documents based on the similarity of embeddings '''

from haystack.nodes import FARMReader ,TfidfRetriever
from haystack.utils import  print_answers

#''' Intialize Retriever '''

retriever = TfidfRetriever(document_store=document_store)


#"""# Retrieve document from document store :"""

#''' Store the obtained data in a document store.'''

#''' Retrieve the related documents by "Tfidf Retriever. ''' 



@st.cache(allow_output_mutation=True)
def Retrieve_doc(output_1):

    #'''Converting the obtained data into list-of-dictionaries form to store in a document store '''
    list_of_dict = []
    for index, row in output_1.iterrows():
        dictss =  {
            'content': output_1["snippet"][index],
            'meta': {'name': output_1["name"][index],'id': output_1["id"][index], 'url':output_1["url"][index], "display_url": output_1["displayUrl"][index],'language':output_1["language"][index]}
        }
        list_of_dict.append(dictss)
    
    #document_store.delete_documents
    document_store.write_documents(list_of_dict)

    return retriever


##################################################################################################################################


#"""# Finetuning a pretrained model in our data:"""

#''' loading the dataset '''

#df= pd.read_csv("/content/drive/MyDrive/AI AND ML/PROJECT/Phase 2 data/Dataset for Bert without preprocess.csv")
#df.head()

#df1 = df.drop(["questions_date_added", "comments_body"], axis =1)
#doc = df1.sample(100, random_state = 42)
#doc.rename(columns = {'answers_body':'document_text'}, inplace = True )
#document_100 = doc["document_text"].to_csv("train_100.csv", index= False)

#''' Creating Training data '''
#document_100 =  pd.read_csv("/content/train_100.csv")
#document_100.iloc[40]

#doc.iloc[99][3]

#doc.iloc[72]["questions_body"]

#doc.iloc[72]["questions_title"]

#''' Using this training data , we finetune "reader" model '''


#reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)
#data_dir = "/content/drive/MyDrive/AI AND ML/PROJECT/Phase 5 data"
#reader.train(data_dir = data_dir , train_filename="answers100.json", use_gpu=True, n_epochs=10, save_dir="my_model",)
#reader.save(directory="my_model")

#new_reader = FARMReader(model_name_or_path = "my_model")
#joblib.dump(new_reader, 'model.pickle')



############################################################################################################################################


#"""# Answer Extraction :"""

from haystack.pipelines import Pipeline

#''' Custom built extractive QA pipeline '''

@st.cache
def answer_extract_custom(output_2,query):
   
    url = "https://drive.google.com/uc?id=1yhMfyZBnwXWP-AOy6zO-Ly3VbYXvcZ-i"
    output = "model.pickle"
    gdown.download(url, output, quiet=False)

    p_extractive = Pipeline()
    new_reader = joblib.load('model.pickle')
    p_extractive.add_node(component=output_2, name="Retriever",inputs=["Query"] )
    p_extractive.add_node(component=new_reader , name="Reader", inputs=["Retriever"])
    prediction = p_extractive.run(query = query, params = {"Retriever": {"top_k": 10}, "Reader": {"top_k": 1}})
    
    #result= print_answers(prediction, details="minimum")
    result = prediction
    data = result['answers']
    pp = pd.DataFrame(data)
    answer=[]
    for index, item in pp.iterrows():
        answer.append(item["answer"])

    return answer


##########################################################################################################################

# Postprocessing function
@st.cache
def preprocess(x):

    #converting to lower case 
    #x=str(x).lower()

    #Decontraction
    #specific
    x= re.sub(r"won't","will  not",str(x))
    x= re.sub(r"can't", "can  not",str(x))

    # general
    x= re.sub(r"n't"," not",str(x))
    x=re.sub(r"'re"," are",str(x))
    x=re.sub(r"\'s"," is",str(x))
    x=re.sub(r"'d"," would",str(x))
    x= re.sub(r"'ll"," will",str(x))
    x=re.sub(r"'ve"," have",str(x))
    x=re.sub(r"'m"," am",str(x))
  
    x=re.sub(r"she's", "she is",str(x))
    x=re.sub(r"'s", " own",str(x))
    #x=re.sub(r"%", "  percent ",x)
    #x=re.sub(r"â‚¹", "  rupee ",x)
    #x=re.sub(r"<", "  ",str(x))
    #x=re.sub(r"â‚¬", "  euro ",x)

    #remove special characters
    x=re.sub(r"[^A-Za-z0-9\s]"," ",str(x))

    return x
  

def main():
   
    st.title(" Welcome to Q&A system :")
    st.subheader("Write your Question :")
    query = st.text_area(' Query')

    if st.button('Submit'):
    
        st.text('Loading data...')
    # ''' Obtain the documents using Bing Search API '''
        output1 = obtain_doc_using_api(query)

    #'''Store the document in document_store and get the Retriever '''
        output2 = Retrieve_doc(output1)

    #''' Give Retriever and question as input and get the  top 1 extracted answers '''
        
        final_result = answer_extract_custom(output2, query)
        result = preprocess(final_result)

    st.write("Answer : {}".format(result))
    

if __name__=='__main__':
    main()

 

################################################################################################################################################

#'''Enter Question: '''
#question = "What classes will better prepare me for the emerging market of IT Security?"
#result = predict_answer(question)
#result




##########################################################################<END>################################################################

from flask import Flask, request
#import sparknlp
#from sparknlp.pretrained import PretrainedPipeline

import spacy

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("es_core_news_sm")

from question_generation import get_question 

# Cargas cosas de path 
#import pathlib
#import os
#path = pathlib.Path().resolve()
#path_to_model = os.path.join(str(path), 'explain_document_lg_es')

# Inicializar pipeline a partir de modelo en disco
# sparknlp.start()
# explain_pipeline = PretrainedPipeline.from_disk(path_to_model)

# App de flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    print(request.json)
    text = str(request.json['text'])
    if isinstance(text, str):
        #annotated_text = explain_pipeline.annotate(text)
        annotated_text = nlp(text)
        print(annotated_text.to_json())
        return annotated_text.to_json()
    else:
        return 'No envio un texto'

@app.route('/question')
def get_question_controller():
    answer = str(request.json['answer'])
    context = str(request.json['context'])
    if answer and context:
        question = get_question(answer, context)
        return question
        
if __name__ == '__main__':
    app.run()

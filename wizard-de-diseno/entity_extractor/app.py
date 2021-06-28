from flask import Flask, request

import sparknlp
from sparknlp.pretrained import PretrainedPipeline

sparknlp.start()
explain_pipeline = PretrainedPipeline.from_disk('/home/gianluca/PycharmProjects/EntityExtractor/models'
                                                '/explain_document_lg_es')

app = Flask(__name__)


@app.route('/')
def hello_world():
    print(request.json)
    text = str(request.json['text'])
    if isinstance(text, str):
        annotated_text = explain_pipeline.annotate(text)
        print(annotated_text)
        return annotated_text
    else:
        return 'No envio un texto'


if __name__ == '__main__':
    app.run()

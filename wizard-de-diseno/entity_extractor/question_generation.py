# Imports transformers https://huggingface.co/transformers/
from transformers import AutoModelWithLMHead, AutoTokenizer
# Google translate
#from google_trans_new import google_translator 
#translator = google_translator()  
from traductor import translate


# Tokenizer y modelo para question generation (generacion de pregunas)
tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
model = AutoModelWithLMHead.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")

def get_question(answer, context, max_length=64):
  """
  Recibe una respuesta esperada y un contexto que provee info y genera una pregunta
  """
  # String que indica al modeelo la tarea a realizar
  input_text = "answer: %s  context: %s </s>" % (answer, context)
  print("INPUT: " + input_text)
  # Analisis y extracción de features para el modelo
  features = tokenizer([input_text], return_tensors='pt')
  # Genera la salida
  output = model.generate(input_ids=features['input_ids'], 
               attention_mask=features['attention_mask'],
               max_length=max_length)
  # Limpiamos la salida
  question = tokenizer.decode(output[0]).replace("<pad> question:","").replace("</s>","").strip()
  #import pdb; pdb.set_trace()
  # La traducimos a español
  print("PREGUNTA: " +question)
  translation = translate(question)
  print("TRADUCCION: " +translation)
  return translation
  
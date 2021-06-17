#! /bin/bash    

cd modelado-de-objetos

rasa train

cd ..

rm -r wizard-de-diseno/actions/models/modelado
mkdir wizard-de-diseno/actions/models/modelado

archivoNuevo=$(ls -t modelado-de-objetos/models | cut -d'
' -f1)

echo "$archivoNuevo"

mv modelado-de-objetos/models/$archivoNuevo wizard-de-diseno/actions/models/modelado # mueve el archivo

cd wizard-de-diseno/actions/models/modelado
tar -xzvf $archivoNuevo
rm $archivoNuevo

cd ..
cd ..
cd ..

# En caso de querer entrenar y correr wizard, descomentar las siguientes lineas (recordar correr actions)
# rasa train
# rasa shell

import cv2
import os
import numpy as np

DATASET_PATH = "dataset"
nombres_clases = os.listdir(DATASET_PATH)

rostros_data = []
etiquetas = []
label = 0

print("[INFO] Leyendo imágenes del dataset...")

for nombre_persona in nombres_clases:
    ruta_persona = os.path.join(DATASET_PATH, nombre_persona)

    if not os.path.isdir(ruta_persona):
        continue

    print(f"Cargando fotos de: {nombre_persona}")

    for nombre_archivo in os.listdir(ruta_persona):
        ruta_imagen = os.path.join(ruta_persona, nombre_archivo)
    
        imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    
        if imagen is not None:
            imagen = cv2.resize(imagen, (150, 150), interpolation=cv2.INTER_CUBIC)
            rostros_data.append(imagen)
            etiquetas.append(label)

    label += 1

print(f"\n[INFO] Entrenando modelo LBPH con {len(rostros_data)} fotos...")

face_recognizer = cv2.face.LBPHFaceRecognizer_create()
face_recognizer.train(rostros_data, np.array(etiquetas))
face_recognizer.write("modelo_lbph.xml")
print("[INFO] ¡Entrenamiento completado! Modelo guardado como 'modelo_lbph.xml'.")
import base64
import tensorflow as tf
import numpy as np
from pathlib import Path
from PIL import Image
import io
import string
from io import BytesIO
import random
from skimage.io import imsave
from captcha.image import ImageCaptcha
import matplotlib.pyplot as plt
from flask import request, render_template, send_file, jsonify, Flask

app = Flask(__name__)

char_choices = [lwchr for lwchr in string.ascii_lowercase]

def create_model():
    n_classes = 26
    kernel_initializer = tf.keras.initializers.GlorotUniform(seed=1337)
    trained_model = tf.keras.applications.Xception(
        include_top=False,
        weights=None,
        input_shape=[100, 160, 3],
        pooling='max'
    )

    c1 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)
    c2 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)
    c3 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)
    c4 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)
    c5 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)
    c6 = tf.keras.layers.Dense(n_classes, activation='softmax', kernel_initializer=kernel_initializer)(trained_model.output)

    return tf.keras.Model(inputs=trained_model.input, outputs=[c1, c2, c3, c4, c5, c6])

def preprocessImage(image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = tf.keras.preprocessing.image.img_to_array(image)
    
    image /= 255.
    image -= 0.5
    image *= 2.

    return image

print('Loading Model...')

model = create_model()
model.load_weights('03_0.9974.h5')
print('Model Loaded')

@app.route('/predict', methods=['POST'])
def predict():
    message = request.get_json(force=True)
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(decoded))

    processedImage = preprocessImage(image)
    processedImage = np.expand_dims(processedImage, axis=0)

    predicted_prob = np.array(model.predict(processedImage))
    predicted_labels = np.argmax(predicted_prob[:, 0, :], axis=1)
    predicted_captcha = ''.join([chr(int(predicted_labels[i]) + ord('a')) for i in range(predicted_labels.shape[0])])

    response = {
        'prediction': predicted_captcha
    }

    return jsonify(response)

@app.route('/', methods=['POST', 'GET'])
def captcha():
    if request.method == 'POST':
        message = request.get_json(force=True)
        noise = message['noise']

    image = ImageCaptcha(width=160, height=100)
    captcha_text = ''.join([random.choice(char_choices) for n in range(6)])

    captcha = image.generate(captcha_text)
    captcha_image = Image.open(captcha)
    buff = BytesIO()
    captcha_image.save(buff, format="png")
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")

    print(captcha_text)
    response = {
        'image': new_image_string
    }

    if request.method == 'POST':
        return jsonify(response)

    return render_template("predict.html", captcha_image=new_image_string)
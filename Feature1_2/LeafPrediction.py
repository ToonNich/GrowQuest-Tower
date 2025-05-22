from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input
from PIL import Image
import numpy as np
import tensorflow as tf
from flask_cors import CORS
import cv2
import base64

# Limit GPU memory usage here
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=8192)]  # 8GB
        )
    except RuntimeError as e:
        print(e)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

# Load your trained model once when the app starts
model = load_model("C:/xampp/htdocs/GrowQuest-Tower/Feature_1/Processing/final_plant_model_resnet50_V2.h5")

# Class labels in the order your model outputs them
class_labels = ['Anthracnose', 'Healthy_Leaf', 'Pest_Damage']

# Extract the base ResNet50 sub-model named 'resnet50'
base_model = model.get_layer('resnet50')

# Uncomment this to check your conv layers and adjust if needed
# for i, layer in enumerate(base_model.layers):
#     print(i, layer.name, layer.output_shape)

last_conv_layer_name = 'conv5_block3_out'  # Update if different after inspection

def prepare_image(image, target_size=(224, 224)):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image_array = img_to_array(image)
    image_array = np.expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array)  # Use ResNet50 preprocess_input here
    return image_array

def make_gradcam_heatmap(img_array, base_model, last_conv_layer_name, pred_index=None):
    grad_model = tf.keras.models.Model(
        inputs=[base_model.input],
        outputs=[base_model.get_layer(last_conv_layer_name).output, base_model.output]
    )
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_index]

    grads = tape.gradient(class_channel, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()

def save_and_encode_heatmap(heatmap, original_img, alpha=0.4):
    heatmap = cv2.resize(heatmap, (original_img.width, original_img.height))
    heatmap = np.uint8(255 * heatmap)
    heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    original_img_cv = np.array(original_img)[:, :, ::-1]  # RGB to BGR
    superimposed_img = cv2.addWeighted(heatmap_color, alpha, original_img_cv, 1 - alpha, 0)

    _, buffer = cv2.imencode('.png', superimposed_img)
    encoded = base64.b64encode(buffer).decode('utf-8')
    return encoded

@app.route("/api/analyze-plant", methods=["POST"])
def analyze_plant():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    image = Image.open(image_file.stream)

    processed_image = prepare_image(image)

    preds = model.predict(processed_image)
    pred_index = np.argmax(preds[0])
    pred_label = class_labels[pred_index]
    confidence = float(preds[0][pred_index])

    # Generate Grad-CAM heatmap
    heatmap = make_gradcam_heatmap(processed_image, base_model, last_conv_layer_name, pred_index)
    gradcam_encoded = save_and_encode_heatmap(heatmap, image)

    return jsonify({
        "status": pred_label,
        "confidence": confidence,
        "advice": generate_advice(pred_label),
        "gradcam": gradcam_encoded
    })

def generate_advice(pred_label):
    advices = {
        "Anthracnose": "Your plant may have a fungal infection. Consider fungicide treatment.",
        "Healthy_Leaf": "Your plant looks healthy! Keep up the good care.",
        "Pest_Damage": "Your plant shows signs of pests. Inspect and treat accordingly."
    }
    return advices.get(pred_label, "No advice available.")

if __name__ == "__main__":
    app.run(debug=True)

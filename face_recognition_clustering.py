# -*- coding: utf-8 -*-
"""face_recognition_clustering

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1grDpqESQgxFLysLZl8Gvgx9393lSA0iw

## 1> Import Necessary Libraries
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import seaborn as sns
from numpy.linalg import norm
import pickle
from tqdm import tqdm, tqdm_notebook
import os
import random
import time
import math
import tensorflow as tf
from tensorflow import keras
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import sklearn.metrics as metrics
from sklearn.metrics import classification_report
import PIL
from PIL import Image
from sklearn.neighbors import NearestNeighbors
from tensorflow.keras.preprocessing.image import ImageDataGenerator 
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from tensorflow.keras.layers import Input, DepthwiseConv2D
from tensorflow.keras.layers import Conv2D, BatchNormalization
from tensorflow.keras.layers import ReLU, AvgPool2D, Flatten, Dense
from tensorflow.python.keras import regularizers
from tensorflow.keras import Model
import glob
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# %matplotlib inline

"""## 2> Loading the dataset"""

from google.colab import drive
drive.mount('/content/gdrive/',force_remount=True)

#Had problem using "gdown", so ran the below code.
!pip install --upgrade --no-cache-dir gdown

# https://drive.google.com/file/d/1znyJSkgkZQsNY4H5wOh3SeGKIdB4YxiH/view?usp=share_link
!gdown 1znyJSkgkZQsNY4H5wOh3SeGKIdB4YxiH

!unzip archive.zip

"""## 3> Visualizing the dataset"""

class_dirs = os.listdir("105_classes_pins_dataset/") # list all directories inside "product_detection_from_packshots" folder
image_dict = {} # dict to store image array(key) for every class(value)
count_dict = {} # dict to store count of files(key) for every class(value)
# iterate over all class_dirs
for cls in class_dirs:
    # get list of all paths inside the subdirectory
    file_paths = glob.glob(f'105_classes_pins_dataset/{cls}/*')
    # count number of files in each class and add it to count_dict
    count_dict[cls] = len(file_paths)
    # select random item from list of image paths
    image_path = random.choice(file_paths)
    # load image using keras utility function and save it in image_dict
    image_dict[cls] = tf.keras.utils.load_img(image_path)

## Viz Random Sample from each class

plt.figure(figsize=(15, 12))
# iterate over dictionary items (class label, image array)
for i, (cls,img) in enumerate(image_dict.items()): 
    j = i+1   
    # create a subplot axis
    if j<13:
        ax = plt.subplot(3, 4, j)
    # plot each image
    plt.imshow(img)
    # set "class name" along with "image size" as title 
    plt.title(f'{cls}, {img.size}')
    plt.axis("off")

## Let's now Plot the Data Distribution across Classes
df_count_train = pd.DataFrame({
    "class": count_dict.keys(),     # keys of count_dict are class labels
    "count": count_dict.values(),   # value of count_dict contain counts of each class
})
print("Count of training samples per class:\n", df_count_train)

# draw a bar plot using pandas in-built plotting function
df_count_train.plot.bar(x='class', y='count', title="Count per class")

"""## 4> Data Preprocessing: Resizing, Standardization and Data Splitting-Train, CV & Test"""

def preprocess(train_data, test_data, target_height=128, target_width=128):

    # Data Processing Stage with resizing and rescaling operations
    data_preprocess = tf.keras.Sequential(
        name="data_preprocess",
        layers=[
            tf.keras.layers.Resizing(target_height, target_width),
            tf.keras.layers.Rescaling(1.0/255),
        ]
    )

    # Perform Data Processing on the train, test dataset
    train_ds = train_data.map(lambda x, y: (data_preprocess(x), y), num_parallel_calls=tf.data.AUTOTUNE)
    test_ds = test_data.map(lambda x, y: (data_preprocess(x), y), num_parallel_calls=tf.data.AUTOTUNE)

    return train_ds, test_ds



"""## 5> Try 1: Using Pretrained Yoloface Git Repo got Face Detection """

!git clone https://github.com/sthanhng/yoloface

!pip install -r /content/yoloface/requirements.txt

!cp -r "/content/gdrive/MyDrive/face_recognition/pretrained_yolov3/yolov3-wider_16000.weights" /content/yoloface/model-weights

!cd /content/yoloface && python yoloface.py --image "/content/yoloface/samples/meeting_11_304.jpg"





"""## 6> Try 2: Using Pretrained YoloV5 Git Repo got Face Detection"""

# Commented out IPython magic to ensure Python compatibility.
!git clone https://github.com/ultralytics/yolov5  # clone
# %cd yolov5
# %pip install -qr requirements.txt  # install

!pip install -r requirements.txt

!cp -r "/content/gdrive/MyDrive/face_recognition/pretrained_yolov5/face_detection_yolov5s.pt" /content/yolov5/models

!python /content/yolov5/detect.py --weights /content/yolov5/models/face_detection_yolov5s.pt --source "/content/105_classes_pins_dataset/pins_Adriana Lima/Adriana Lima101_3.jpg"





"""## 7> Try 3: Using Mediapipe Library for Face Detection(Got more Accuracy)"""

!pip install mediapipe
!pip install face-detector

import cv2
import mediapipe as mp

def face_detect(IMAGE_FILES):
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        for idx, file in enumerate(IMAGE_FILES):
            image = cv2.imread(file)
            image = cv2.resize(image, (256, 256)) 
            # Convert the BGR image to RGB and process it with MediaPipe Face Detection.
            results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            # Draw face detections of each face.
            if not results.detections:
                return 'Not detected'
            annotated_image = image.copy()
            for detection in results.detections:
                #print('Nose tip:')
                #print(mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.NOSE_TIP))
                #print(detection.location_data.relative_bounding_box)
                mp_drawing.draw_detection(annotated_image, detection)
            cv2.imwrite('/content/out/annotated_image' + str(idx) + '.jpg', annotated_image)
            return (detection.location_data.relative_bounding_box.xmin, detection.location_data.relative_bounding_box.ymin, detection.location_data.relative_bounding_box.width, detection.location_data.relative_bounding_box.height)

IMAGE_FILES = ["/content/105_classes_pins_dataset/pins_Millie Bobby Brown/Millie Bobby Brown155_3808.jpg"]
face_detect(IMAGE_FILES)

"""Observation: Got highest accuracy with Mediapipe, so selecting Mediapipe function for future use.<br>
Why did I use Yolo and Mediapipe only?<br>
Because these 2 are light and fast models
"""



"""## 8> Creating a function to extract feature embedding from an Image using Resnet50 - Method 1"""

import numpy as np
from keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications.resnet50 import ResNet50
from PIL import Image

# Load the ResNet50 model
model = ResNet50(weights='imagenet')

# Get the output of the final global average pooling layer
feature_extractor = Model(inputs=model.input, outputs=model.get_layer('avg_pool').output)

def extract_features(image_paths, bbox):
    # Open the image
    image = Image.open(image_paths)
    # Convert the image to a numpy array
    image_array = np.array(image)
    print(image_array)
    # Crop the image to the bounding box
    x, y, w, h = bbox
    crop = image.crop((x, y, x+w, y+h))

    # Preprocess the cropped image for ResNet50
    crop = preprocess_input(crop)

    # Get the features for the cropped image
    features = feature_extractor.predict(np.expand_dims(crop, axis=0))
    
    return features.flatten()

image_path = ["/content/yolov5/runs/detect/exp/Adriana Lima101_3.jpg"]
bbox = face_detect(image_path)
print(bbox)
extract_features(image_path[0], bbox)



"""## 9> Creating a function to extract feature embedding from an Image using Resnet50 - Method 2"""

import torch
from torchvision import models
from torchvision import transforms
from PIL import Image

# Load a pre-trained model (e.g. ResNet-50)
model = models.resnet50(pretrained=True)
# Remove the last fully connected layer to get the feature embeddings
model = torch.nn.Sequential(*list(model.children())[:-1])
# Set the model to eval mode
model.eval()

# Define the image pre-processing steps
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def extract_embeddings(image, bounding_box):
    try:
        image = Image.open(image)
        # Crop the image to the bounding box
        x, y, w, h = bounding_box
        crop = image.crop((x, y, x+w, y+h))
        # Pre-process the image
        tensor = transform(crop).unsqueeze(0)
        # Extract the feature embeddings
        with torch.no_grad():
            embeddings = model(tensor)
        return embeddings
    except ZeroDivisionError:
        return 'Error'

image_paths = [["/content/105_classes_pins_dataset/pins_Millie Bobby Brown/Millie Bobby Brown155_3808.jpg"]]
bounding_box = face_detect(image_paths[0])
print(len(bounding_box))
extract_embeddings(image_paths[0][0], bounding_box)



"""## 10> Creating a function to return 3 lists - Class of the image, Path of the image & Feature Embedding of the Image"""

from tensorflow.keras.preprocessing.image import img_to_array

from pandas.core.tools.datetimes import Tuple
from torch._C import NoneType
# Function to Extract features from the images
def image_feature(path):
    features = [];
    img_name = [];
    path_names = [];
    #path = "/content/105_classes_pins_dataset"
    for name_folder in os.listdir(path):
        print(name_folder)
        file_path = path+'/'+name_folder+'/'
        for file in os.listdir(file_path):
            image_path = file_path+file
            img=image.load_img(image_path,target_size=(224,224))
            bounding_box = face_detect([image_path])
            if bounding_box!='Not detected':
                #print(bounding_box)
                emb = extract_embeddings(image_path, bounding_box)
                if type(emb) is not str:
                    feat = emb.flatten()
                    print(image_path)
                    print(feat)
                    print(feat.shape)
                    features.append(np.array(feat))
                    img_name.append(name_folder)
                    path_names.append(image_path)
    return path_names, img_name, features

# Function to Extract features from the images
# def extract_image_feature(path):
#     features = [];
#     img_name = [];
#     path = "/content/105_classes_pins_dataset"
#     for name_folder in os.listdir(path):
#         print(name_folder)
#         file_path = path+'/'+name_folder+'/'
#         for file in os.listdir(file_path):
#             image_path = file_path+file
#             img=image.load_img(image_path,target_size=(256,256))
#             x = img_to_array(img)
#             x=np.expand_dims(x,axis=0)
#             x=preprocess_input(x)
#             feat=model.predict(x)
#             feat=feat.flatten()
#             print(feat)
#             print(feat.shape)
#             print(type(feat))
#             features.append(feat)
#             img_name.append(i)
#         return features,img_name

path = "/content/105_classes_pins_dataset"
img_path, img_name, img_features=image_feature(path)

len(img_features)

img_features





"""## 11> Creating the dataframe for the data extracted above"""

df = pd.DataFrame(list(zip(img_path, img_name, img_features)), columns =['Path', 'Celebrity', 'Feature_Embedding'])
df

# saving the dataframe
df.to_csv('/content/gdrive/MyDrive/face_recognition/features_file.csv')

df = pd.read_csv("/content/gdrive/MyDrive/face_recognition/features_file.csv")
df

"""## 12> Storing all the Feature Embeddings extracted to a pickle file"""

# Using pickle to store the feature embeddings
import pickle as pkl

# Store the feature embeddings in pickle format
with open('/content/gdrive/MyDrive/face_recognition/feature_embeddings.pickle', 'wb') as handle:
    pickle.dump(img_features, handle, protocol=pickle.HIGHEST_PROTOCOL)

# load saved model
with open('/content/gdrive/MyDrive/face_recognition/feature_embeddings.pickle' , 'rb') as f:
    all_feature = pickle.load(f)



"""## Generating a KNN model to suggest which celebrity the query image belongs to"""

# Importing necessary dependencies
from sklearn.neighbors import NearestNeighbors

# Define a function to plot the images
def plot_images(filenames, distances, celebrity_name):
    # Create an empty list
    images = []
    # Loop through the filenames
    for filename in filenames:
        # Read the image files
        images.append(mpimg.imread(filename))
    # Create a Plot for displaying images
    plt.figure(figsize=(20, 10))

    

    # Define the no. of images
    columns = 5
    # Loop through the images
    for i, image in enumerate(images):
        # Create a subplot for the images
        ax = plt.subplot(len(images) / columns + 1, columns, i + 1)
        # Set the axis off
        ax.axis('off')
        # Set the name of the image
        ax.set_title(titles[i] + "\nPrice : {} ₹".format(prices[i]), y=-0.05,pad=-14)
        # Display the image inside the subplot
        plt.imshow(image)
        


# Define a function to display similar images
def find_similar_images(img_path, old_features_path, model, sex = 1) :

  if not os.path.exists(img_path) :
    return None

  # Finding the category of the input image using its path
  category = img_path.split('/')[-1].split('.')[0].lower()

  # Defining the sex attribute for the input image
  if category == 'handbag' :
    sex = "Women"

  else:
    if sex == 1:
      sex = 'Men'
    else:
      sex = 'Women'

  # Extract features from the input image
  new_embedding = extract_features(img_path, model)

  # Define a new list
  new_embedding_arr = []

  # Loop through the emebddings
  for i in range(len(new_embedding)) : 
    # Convert the numpy array to a Python list iteratively
    new_embedding_arr.append(new_embedding[i])

  # Make an object of the class StandardScaler()
  scaler = StandardScaler()
  # Scale the extracted features
  new_feature_scaled = scaler.fit_transform(new_embedding.reshape(-1,1))

  # Remove single-dimensional entries from the shape of an array.
  new_feature_scaled = np.array(new_feature_scaled).squeeze()

  # Load the old embeddings from the pre-saved pickle file
  old_features = np.load(old_features_path, allow_pickle = True)

  # Define the NearestNeighbors object for implementing the KNN algorithm
  neighbors = NearestNeighbors(n_neighbors=70, algorithm='brute', metric='euclidean').fit(old_features)
  # Fetch the distances and indices of the 30 closest feature vectors
  distances, indices = neighbors.kneighbors([new_feature_scaled])


  # Define an empty list
  filenames, links, prices, titles = [], [], [], []
  # Define the counter( We'll use this counter to save the first 5 similar images)
  count = 0
  
  # Loop through the indices
  for index in indices[0] :
    # Apply the conditions for sex and category
    if (data_json.iloc[index,:]['sex']==sex ) and (data_json.iloc[index,:]['category'] == category) :
      # Define the image path
      img_path = os.path.join(root_dir, data_json.iloc[index,:]['category'], data_json.iloc[index,:]['name']) + '.jpg'
      
      # Check if the path exists
      if os.path.exists(img_path) :
        # Add the image path to the list if it exists
        filenames.append(img_path)

        links.append(data_json.iloc[index,:]['link'])
        titles.append(data_json.iloc[index,:]['title'])
        prices.append(data_json.iloc[index,: ]['price'])
        # Increment the counter
        count += 1

    # Break the loop if the counter reaches 5    
    if count==5 :
      break
  
  # Use the plot_images function to display the similar image
  plot_images(filenames, distances, titles, prices)



















"""## 13> Generating a Kmeans model to suggest which celebrity the query image belongs to"""

df[['Celebrity']]



import pickle
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

    
# Split the features into training and test sets
X_train, X_test, y_train, y_test = train_test_split(df[['Feature_Embedding','Celebrity']], df[['Celebrity']], test_size=0.2)

print(X_train)

print(y_test)

df

len(X_train["Feature_Embedding"][11499])

embeddings = pd.DataFrame.from_records(df['Feature_Embedding'].values)
print(embeddings)

from sklearn.cluster import KMeans
import pandas as pd

# Initialize and fit k-means model
kmeans = KMeans(n_clusters=105)
clustering = kmeans.fit(embeddings)

import pickle

# Save the model to a pickle file
with open('/content/gdrive/MyDrive/face_recognition/kmeans_weights.pkl', 'wb') as f:
    pickle.dump(clustering, f)



embeddings_test = pd.DataFrame.from_records(X_test['Feature_Embedding'].values)
print(embeddings_test)

# Predict the cluster labels for the test set
y_pred = kmeans.predict(embeddings_test)

# Measure the accuracy of the model
acc = accuracy_score(y_test, y_pred)
print(f'Accuracy: {acc:.2f}')

y_pred

from sklearn.metrics import silhouette_score

silhouette = silhouette_score(embeddings_test, y_pred)
print(silhouette)

# Get the cluster labels for each data point
labels = kmeans.labels_

#Plot the data points, color-coded by cluster label
example = np.concatenate((embeddings.index,labels), axis=0)
print(example)
print(len(example))

embeddings.index

labels

len(labels)

len(embeddings.index)

exp = pd.DataFrame({'embeddings': embeddings.index, 'celebrity_name': X_train.Celebrity, 'labels': labels})
exp

exp = pd.DataFrame({'embeddings': embeddings_test.index, 'celebrity_name': X_test.Celebrity, 'labels': y_pred})
exp



"""## Testing Kmeans with test images"""

#https://drive.google.com/file/d/1m1qNm2oHa-mOfLRnQXLhuhNSPAkEUVX9/view?usp=share_link
!gdown 1m1qNm2oHa-mOfLRnQXLhuhNSPAkEUVX9

!unzip face_cluster_test.zip

path = "/content/yolov5/face_cluster_test"
img_path, img_name, img_features=image_feature(path)

len(img_features)

len(img_features[1])

df_test = pd.DataFrame(list(zip(img_path, img_name, img_features)), columns =['Path', 'Celebrity', 'Feature_Embedding'])
df_test

embeddings_test = pd.DataFrame.from_records(df_test['Feature_Embedding'].values)
print(embeddings_test)

# Predict the cluster labels for the test set
y_pred = kmeans.predict(embeddings_test)

y_pred

from sklearn.metrics import silhouette_score

silhouette = silhouette_score(embeddings_test, y_pred)
print(silhouette)

exp = pd.DataFrame({'embeddings': embeddings_test.index, 'celebrity_name': df_test.Celebrity, 'labels': y_pred})
exp

exp.to_csv('/content/gdrive/MyDrive/face_recognition/test_results.csv')



df_test["clusterid"] = exp["labels"]
df_test

df_test.to_csv('/content/test_results.csv')

import os, shutil

dir = ("/content/gdrive/MyDrive/face_recognition/")

os.mkdir('/content/gdrive/MyDrive/face_recognition/output')
# Made folder to seperate images
for i in range(105):
    if i in list(df_test["clusterid"]):
        os.mkdir(f'/content/gdrive/MyDrive/face_recognition/output/cluster{i}')

# Images will be seperated according to cluster they belong
for j in range(len(df_test)):
    num = int(df_test['clusterid'][j])
    shutil.copy(df_test['Path'][j], f'/content/gdrive/MyDrive/face_recognition/output/cluster{num}/')

# Commented out IPython magic to ensure Python compatibility.
#path that contains folder you want to copy
# %cd '/content/gdrive/MyDrive/face_recognition/'
# %cp -av '/content/sample_data/output' '/content/gdrive/MyDrive/face_recognition/'





"""## 14> Generating a DBSCAN model to suggest which celebrity the query image belongs to"""

from sklearn.cluster import DBSCAN
import numpy as np

# Assume 'X' is your dataset with 105 classes
# Create an instance of DBSCAN with a small eps and min_samples
dbscan = DBSCAN(eps=0.1, min_samples=5)

# Fit the model to your data
y_pred = dbscan.fit_predict(embeddings)

# Get the unique labels in the predicted clusters
labels = np.unique(y_pred)

# Print the number of clusters found
print(f'Number of clusters found: {len(labels)}')

# Print the cluster labels
print(f'Cluster labels: {labels}')

exp = pd.DataFrame({'embeddings': embeddings.index, 'celebrity_name': X_train.Celebrity, 'labels': y_pred})
exp


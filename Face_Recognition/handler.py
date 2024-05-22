import os
import cv2
from PIL import Image, ImageDraw, ImageFont
from facenet_pytorch import MTCNN, InceptionResnetV1
#from shutil import rmtree
#import numpy as np
import torch
import boto3
import urllib.parse

s3 = boto3.client('s3')

os.environ['TORCH_HOME'] = '/tmp/'
mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

def face_recognition_function(key_path):
    # Face extraction
    img = cv2.imread(key_path, cv2.IMREAD_COLOR)
    boxes, _ = mtcnn.detect(img)

    # Face recognition
    key = os.path.splitext(os.path.basename(key_path))[0].split(".")[0]
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    face, prob = mtcnn(img, return_prob=True, save_path=None)
    saved_data = torch.load('data.pt')  # loading data.pt file
    if face != None:
        emb = resnet(face.unsqueeze(0)).detach()  # detech is to make required gradient false
        embedding_list = saved_data[0]  # getting embedding data
        name_list = saved_data[1]  # getting list of names
        dist_list = []  # list of matched distances, minimum distance is used to identify the person
        for idx, emb_db in enumerate(embedding_list):
            dist = torch.dist(emb, emb_db).item()
            dist_list.append(dist)
        idx_min = dist_list.index(min(dist_list))

        # Save the result name in a file
        with open("/tmp/" + key + ".txt", 'w+') as f:
            f.write(name_list[idx_min])
        return key
    else:
        print(f"No face is detected")
    return




def handler(event, context):	
	#print(os.system('ffmpeg'))
    
    # Define the output bucket name
    output_bucket = '1229454514-output'
    
    #Get the Bucket Name and the Key value of the S3 Input Bucket
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("Bucket name: {}, Key: {}".format(bucket_name, key))

    # Download the image File from s3 bucket and store it in tmp directory of Lambda
    s3.download_file(bucket_name, key, "/tmp/" + key)
    

    input_image = os.path.splitext(os.path.basename(key))[0]  # Extract the base name of the input image
    
    # Define the path of the image file stored in tmp directory of Lambda
    Image_filename = '/tmp/' + os.path.basename(key)

    outdir = face_recognition_function(Image_filename)
    #print(os.system('ls -la /tmp '))
    
    #Upload output file to output bucket
    local_path = "/tmp/" + outdir+ ".txt"
    s3_key = outdir + ".txt"
    s3.upload_file(local_path, output_bucket, s3_key)
    
    # Delete the downloaded image file from Lambda's temporary directory
    os.remove(Image_filename)

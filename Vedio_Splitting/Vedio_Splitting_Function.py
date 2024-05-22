import json
import os
import subprocess
import math
import urllib.parse
import boto3

s3 = boto3.client('s3')

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = 'ffmpeg -i ' + video_filename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = '/opt/bin/ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    return outfile

def lambda_handler(event, context):
    #print(os.system('ffmpeg'))
    
    # Define the output bucket name
    output_bucket = '1229454514-stage-1'
    
    #Get the Bucket Name and the Key value of the S3 Input Bucket
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("Bucket name: {}, Key: {}".format(bucket_name, key))

    # Download the Vedio File from s3 bucket and store it in tmp directory of Lambda
    s3.download_file(bucket_name, key, "/tmp/" + key)
    
    # Get the Base name of the input vedio (i.e. test_00 from test_00.mp4)
    input_video = os.path.splitext(os.path.basename(key))[0]  # Extract the base name of the input video
    
    # Define the path of the vedio file stored in tmp directory of Lambda
    video_filename = '/tmp/' + os.path.basename(key)

    # Process the downloaded video file and upload the output images to the specified S3 bucket
    outdir = video_splitting_cmdline(video_filename)
    #print(os.system('ls -la /tmp '))
    
    local_path = '/tmp/' + outdir
    s3_key = outdir
    s3.upload_file(local_path, output_bucket, s3_key)
    # Upload the output images to the specified S3 bucket within the folder named after the input video
    #for root, dirs, files in os.walk(outdir):
    #    for file in files:
    #        local_path = os.path.join(root, file)
    #        s3_key = os.path.join(input_video, file)
    #        s3.upload_file(local_path, output_bucket, s3_key)
    
    # Delete the downloaded video file from Lambda's temporary directory
    os.remove(video_filename)


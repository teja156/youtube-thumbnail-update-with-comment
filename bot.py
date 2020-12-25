from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import sys
import random
import string
from better_profanity import profanity
import pytz
from datetime import datetime
import ast
import os
import googleapiclient.discovery
import google_auth_oauthlib.flow
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors
import time

from googleapiclient.http import MediaFileUpload

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

CYCLE_TIME = 8 #in minutes

# START coords - 36,176
# font size 70 - line break 32 
# MAX CHARS - 175 (including quotations)

profanity.load_censor_words()
IST = pytz.timezone('Asia/Kolkata')
datetime_ist = datetime.now(IST)
VIDEO_ID = 'hJb-D6n5gcU' # Change the video id


def generate_text(size):
	letters = string.ascii_lowercase
	st = ''.join(random.choice(letters) for i in range(size))
	return st


def get_comments():
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
	api_service_name = "youtube"
	api_version = "v3"
	DEVELOPER_KEY = os.getenv("GOOGLE_API_KEY")
	youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = DEVELOPER_KEY)

	request = youtube.commentThreads().list(
	    part="snippet",
	    maxResults=100,
	    order="time",
	    videoId=VIDEO_ID
	)
	response = request.execute()

	comments = []
	for item in response['items']:
	    comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
	    comments.append(comment.strip())



	return comments


def check_eligibility(comment):
	#not more than 175 chars
	#no profanity

	if(len(comment)>175 or profanity.censor(comment)!=comment):
		print("Comment rejected : %s"%comment)
		return False

	return True


def adjust_text(text):
	split = 32
	words = text.split(' ')
	res = ""
	curr_line = ""
	for word in words:
		if(len(curr_line) + len(word)<=32):
			curr_line+=" " + word
		else:
			res+=curr_line.strip() + "\n"
			curr_line=""

	return res



def create_thumbnail(text):
	in_file = 'template1.jpg'

	img = Image.open(in_file)
	draw = ImageDraw.Draw(img)

	font = ImageFont.truetype('Roboto-Medium.ttf', 70)


	text = text.strip()
	split = 32
	# text = '\n'.join([(text[i:i+split]) for i in range(0, len(text), split)])

	text = adjust_text(text)

	draw.text((36,176),text,(255, 255, 255), font=font)
	timestamp = datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
	font2 = ImageFont.truetype('LuckiestGuy-Regular.ttf', 20)
	# 520,682
	draw.text((520,682),timestamp,(255, 255, 255), font=font2)
	# img.save('test2.jpg')
	return img



def set_thumbnail():
	global scopes
	api_service_name = "youtube"
	api_version = "v3"
	client_secrets_file = "client_secret_comment_thumbnail.json"

	# Get credentials and create an API client
	flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)


	f = open('credentials_comment_thumbnail.txt','r')
	creds = ast.literal_eval(f.read())
	f.close()
	credentials = google.oauth2.credentials.Credentials(**creds)
	youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

	request = youtube.thumbnails().set(
	    videoId=VIDEO_ID,
	    media_body=MediaFileUpload("thumbnail.jpg")
	)
	response = request.execute()

	print(response)
	print("thumbnail set.")




def start():
	comments = get_comments()
	thumbnail = None
	for comment in comments:
		if(check_eligibility(comment)):
			#Approved
			thumbnail = create_thumbnail(comment)
			thumbnail.save('thumbnail.jpg')
			print("Setting thumbnail with comment - %s"%comment)
			break

	set_thumbnail()



if __name__=="__main__":
	k = 1
	while True:
		print("Started Cycle %d"%k)
		start()
		k+=1
		time.sleep(CYCLE_TIME*60)

	

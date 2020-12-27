from PIL import Image, ImageOps, ImageFilter
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
import requests
import shutil
# import discord_webhook
import random

from googleapiclient.http import MediaFileUpload

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

CYCLE_TIME = 8 #in minutes

# START coords - 36,176
# font size 70 - line break 32 
# MAX CHARS - 175 (including quotations)

profanity.load_censor_words()
IST = pytz.timezone('Asia/Kolkata')

VIDEO_ID = '' # Change the video id
PREVIOUS_COMMENT = ""


def generate_text(size):
	letters = string.ascii_lowercase
	st = ''.join(random.choice(letters) for i in range(size))
	return st


def get_comments():
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
	api_service_name = "youtube"
	api_version = "v3"
	# DEVELOPER_KEY = os.getenv("GOOGLE_API_KEY")

	try:
		DEVELOPER_KEY = ''
		youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = DEVELOPER_KEY)

		request = youtube.commentThreads().list(
		    part="snippet",
		    maxResults=30,
		    order="time",
		    videoId=VIDEO_ID
		)
		response = request.execute()

		#Comment, Author Name, DP URL
		comments = []
		for item in response['items']:
		    comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
		    author_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
		    author_dp = item['snippet']['topLevelComment']['snippet']['authorProfileImageUrl']
		    comments.append([comment.strip(),author_name.strip(),author_dp])

		return comments

	except Exception as e:
		print("Exception occured - %s"%e)
		# discord_webhook.send_msg(str(e))
		return []


	


def check_eligibility(comment_data):
	#not more than 320 chars
	#no profanity

	try:
		comment = comment_data[0]
		author_name = comment_data[1]

		if(len(comment)>320 or len(comment) < 10 or profanity.censor(comment)!=comment or profanity.censor(author_name)!=author_name or len(comment.split(' '))<6):
			print("Comment rejected : %s"%comment)
			return False
		return True

	except Exception as e:
		# discord_webhook.send_msg(str(e))
		return False


def adjust_text(text):
	text = text.strip()
	split = 70
	words = text.split(' ')
	print(words)
	res = ""
	curr_line = ""
	for word in words:
		if(len(curr_line) + len(word)<=split):
			curr_line+=" " + word
		else:
			res+=curr_line.strip() + "\n" + word + " "
			curr_line=""

	res=res.strip() + " "+curr_line
		# print(word + " - " + res)

	return res


def download_dp(url):
	r = requests.get(url,stream=True)

	if r.status_code==200:
		r.raw.decode_content = True

		with open("dp.jpg",'wb') as f:
			shutil.copyfileobj(r.raw,f)
		print("image successfully downloaded")




def create_thumbnail(comment_data):

	text = comment_data[0]
	author_name = comment_data[1]
	author_dp = comment_data[2]

	download_dp(author_dp)

	im = Image.open('dp.jpg')
	im = im.resize((80, 80));
	bigsize = (im.size[0] * 3, im.size[1] * 3)
	mask = Image.new('L', bigsize, 0)
	draw = ImageDraw.Draw(mask) 
	draw.ellipse((0, 0) + bigsize, fill=255)
	mask = mask.resize(im.size, Image.ANTIALIAS)
	im.putalpha(mask)

	output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
	output.putalpha(mask)
	output.save('output.png')
	im = im.filter(ImageFilter.BLUR)
	background = Image.open('template2.jpg')
	background.paste(im, (60,150), im)
	draw = ImageDraw.Draw(background)
	font = ImageFont.truetype('Rubik-Medium.ttf', 30)
	# 150,162 - > author name 
	draw.text((150,160),author_name,(255, 255, 255), font=font)
	# 141,238 - > comment text
	font2 = ImageFont.truetype('SourceSansPro-Regular.ttf', 35)
	split = 80
	text = adjust_text(text)
	draw.text((150,210),text,(255, 255, 255), font=font2)
	datetime_ist = datetime.now(IST)
	timestamp = datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
	font3 = ImageFont.truetype('Roboto-Medium.ttf', 27)
	draw.text((520,682),timestamp,(255, 255, 255), font=font3)

	background.save('thumbnail.jpg')



def set_thumbnail():
	global scopes
	api_service_name = "youtube"
	api_version = "v3"
	client_secrets_file = "client_secret_comment_thumbnail.json"

	try:

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
		datetime_ist = datetime.now(IST)
		timestamp = datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
		print("thumbnail set at %s"%timestamp)
	except Exception as e:
		print("Exception occured - %s"%e)
		# discord_webhook.send_msg(str(e))




def start():
	global PREVIOUS_COMMENT
	comments = get_comments()
	thumbnail = None
	if(comments==[]):
		return
	# for comment_data in comments:
	# 	comment = comment_data[0]
	# 	if(comment==PREVIOUS_COMMENT):
	# 		continue

		

	# 	if(check_eligibility(comment_data)):
	# 		#Approved
	# 		thumbnail = create_thumbnail(comment_data)
	# 		# thumbnail.save('thumbnail.jpg')
	# 		print("Setting thumbnail with comment - %s"%comment)
	# 		PREVIOUS_COMMENT = comment
	# 		set_thumbnail()
	# 		break

	count = 0
	while count<=30:
		random_comment = random.choices(comments)[0]
		comment = random_comment[0]
		if(comment==PREVIOUS_COMMENT):
			continue
		if(check_eligibility(random_comment)):
			#Approved
			thumbnail = create_thumbnail(random_comment)
			# thumbnail.save('thumbnail.jpg')
			print("Setting thumbnail with comment - %s"%comment)
			PREVIOUS_COMMENT = comment
			set_thumbnail()
			break
		count+=1
	



if __name__=="__main__":
	k = 1
	while True:
		print("Started Cycle %d"%k)
		start()
		k+=1
		time.sleep(CYCLE_TIME*60)

	# print(adjust_text("Comment under this video and your comment will appear on the thumbnail! - First comment"))

	

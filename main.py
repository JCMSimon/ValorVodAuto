from datetime import datetime
from time import localtime
import threading
import time
from tqdm import tqdm

from PIL import Image, ImageDraw, ImageFont
from yt_dlp import YoutubeDL

import pickle
import os

from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


class ValData:
	# TODO | Gather these dynamically
	agents = ["brimstone", "viper", "omen", "killjoy", "cypher", "sova", "sage", "phoenix", "jett","reyna", "raze", "breach", "skye", "yoru", "astra", "kayo", "chamber", "neon", "fade","harbor", "gekko", "deadlock", "iso", "clove"]
	maps = ["bind", "icebox", "split", "ascent", "breeze", "lotus", "sunset", "haven", "fracture", "pearl"]
	

class youtubeVideo():
	def __init__(self,data,description) -> None:
		self.VIDEO_ID:str = data["id"]["videoId"]
		logMessage(f"Getting title for video with videoId {self.VIDEO_ID}")
		self.VIDEO_TITLE:str = data["snippet"]["title"] 
		self.VIDEO_DESCRIPTION:str = "".join([char for char in description.replace("\n","LLBB") if char.isalnum()]) 
		logMessage(f"Getting Valorant map for video with videoId {self.VIDEO_ID}")
		self.VAL_MAP = [vmap for vmap in ValData.maps if vmap in self.VIDEO_DESCRIPTION.lower()]
		logMessage(f"Getting Valorant agent for video with videoId {self.VIDEO_ID}")
		self.VAL_AGENT = [agent for agent in ValData.agents if agent in self.VIDEO_DESCRIPTION.lower()]
		logMessage(f"Getting Valorant player for video with videoId {self.VIDEO_ID}")
		self.VAL_PLAYER = self.VIDEO_DESCRIPTION.split("wwwtwitchtv")[1].split("LLBB")[0]
		
class ValorVod:
	def __init__(self) -> None:
		# Config
		self.CHANNEL_ID = "UCOR8JcMRg_cFKx0etV5zXBQ"
		# %VP: Valorant Player | %VA: Valorant Agent | %VM: Valorant Map
		self.videoTitleTemplate = "[VV] %VP - %VA - %VM" 
		self.videoProcessingDelay = 60 * 60 * 5 # 5 minutes
		self.checkingInterval = int((60 * 60) * 3) # 3 Hours
		self.processedVideoIds = set()
		for line in [
			"---",
			"ValorVod v1.0.0",
		   f"Running on channel {self.CHANNEL_ID}",
		   f"Checking every {self.checkForNewVideos} seconds for new videos",
		   f"Processing delay: {self.videoProcessingDelay}",
			"---"
			]:
			logMessage(line)
		# Init
		self.ytAPI = getAuthenticatedService()
		
	def start(self) -> None:
		self.running = True
		self.newVideoThread:threading.Thread = threading.Thread(target=self.checkForNewVideos)
		self.newVideoThread.start()

	def checkForNewVideos(self,maxHistory:int=5) -> None:
		while self.running:
			latestVideos = self.getLatestVideos(maxResults=maxHistory)
			for video in tqdm(latestVideos,f"Processing latest {len(latestVideos)} videos!"):
				if video["id"]["videoId"] in self.processedVideoIds:
					logMessage(f"Already processed video with videoId {video["id"]["videoId"]} | skipping")
					continue
				vidProcessingThread = threading.Thread(
					target=self.processVid, 
					args=[video],
					daemon=True
				)
				vidProcessingThread.start()
				self.running = False
				time.sleep(self.videoProcessingDelay)
			time.sleep(self.checkingInterval)

	
	def getLatestVideos(self,maxResults=5) -> dict:
		logMessage(f"Getting lates {maxResults} videos")
		request = self.ytAPI.search().list(
				part='snippet',
				channelId=self.CHANNEL_ID,
				order='date',
				type='video',
				maxResults=maxResults,
			)
		response = request.execute()
		return response.get('items', [])
		
	def getVideoDescription(self, videoId) -> str:
		logMessage(f"Getting description for video with videoId {videoId}")
		request = self.ytAPI.videos().list(
			part='snippet',
			id=videoId,
		)
		response = request.execute()
		vid_data = response.get('items', [])
		return vid_data[0]["snippet"]["description"]

	def processVid(self, videoData:dict):
		VIDEO = youtubeVideo(videoData,self.getVideoDescription(videoData["id"]["videoId"]))
		# Start download in background
		vidDownloadThread = threading.Thread(
			target=downloadVideo,
			args=[VIDEO.VIDEO_ID],
			daemon=True
		)
		vidDownloadThread.start()
		# Get the metadata and thumbnail ready
		title = self.videoTitleTemplate.replace(
		"%VP",VIDEO.VAL_PLAYER
		).replace("%VA",VIDEO.VAL_AGENT
		).replace("%VM",VIDEO.VAL_MAP
		)
		logMessage(f"Generated title '{title}' for videoId {VIDEO.VIDEO_ID}")
		description = f"{VIDEO.VAL_PLAYER} playing {VIDEO.VAL_AGENT} on {VIDEO.VAL_MAP}!\n\n\nAll {VIDEO.VAL_PLAYER} VODs here: https://twitch.tv/{VIDEO.VAL_PLAYER}\n\n\n\n\n\n\n\n\nTAGS:\nvalorant Pro Player full twitch vod\nvalorant pro player full twich\nvalorant pro player full\nvalorant pro player\nvalorant pro\nvalorant\n{VIDEO.VAL_PLayer} {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP}\n{VIDEO.VAL_PLayer} {VIDEO.VAL_AGENT}\n{VIDEO.VAL_PLayer} {VIDEO.VAL_MAP}\n{VIDEO.VAL_PLayer}\nValorant Pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP} {VIDEO.VAL_PLAYER}\n\nValorant Pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP}Valorant Pro guide {VIDEO.VAL_AGENT}\nGuide\n{datetime.now().month}/{datetime.now().year}\n{datetime.now().year}"
		logMessage(f"Generated description '{description}' for videoId {VIDEO.VIDEO_ID}")
		tags = f"valorant Pro Player full twitch vod,valorant pro player full twichmvalorant pro player full,valorant pro player,valorant pro,valorant,{VIDEO.VAL_PLayer} {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP},{VIDEO.VAL_PLayer} {VIDEO.VAL_AGENT},{VIDEO.VAL_PLayer} {VIDEO.VAL_MAP},{VIDEO.VAL_PLayer},Valorant Pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP} {VIDEO.VAL_PLAYER},Valorant Pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP}Valorant Pro guide {VIDEO.VAL_AGENT},Guide,{datetime.now().month}/{datetime.now().year},{datetime.now().year}"
		logMessage(f"Generated tags '{tags}' for videoId {VIDEO.VIDEO_ID}")
		genThumbnail(VIDEO)
		logMessage(f"Waiting for video with videoId {VIDEO.VIDEO_ID} to download")
		vidDownloadThread.join()
		# Video is downloaded and all metadata is ready. Upload!
		self.uploadVideo(title,description,tags,VIDEO.VIDEO_ID)

	def uploadVideo(self, title, description, tags, internalVideoId):
		thumbnailFile = f"./assets/vThumbnails/{internalVideoId}.png"
		videoFile = f"./assets/videos/{internalVideoId}.mp4"
		request = {
			"snippet": {
				"title": title,
				"description": description,
				"tags": tags
			},
			"status": {
				"privacyStatus": "public"  # Set the privacy status of the video
			}
		}
		logMessage(f"Starting upload of video with videoId {internalVideoId}")
		# Execute the API request to upload the video
		request = self.ytAPI.videos().insert(
			part="snippet,status",
			body=request,
			media_body=MediaFileUpload(videoFile, chunksize=15 * 1024 * 1024, resumable=True)
		)

		response = None
		while response is None:
			status, response = request.next_chunk()
			if status:
				logMessage(f"({internalVideoId}) Uploaded %d%%." % int(status.progress() * 100))
		
		logMessage(f"Upload of video with videoId {internalVideoId} completed")
		# Now upload the thumbnail
		# self.uploadThumbnail(internalVideoId, thumbnailFile)

	def uploadThumbnail(self, videoId, thumbnailFile):
		request = self.ytAPI.thumbnails().set(
			videoId=videoId,
			media_body=MediaFileUpload(thumbnailFile, chunksize=1 * 1024 * 1024, resumable=True)
		)
		response = request.execute()
		response = None
		while response is None:
			status, response = request.next_chunk()
			if status:
				logMessage("Uploaded %d%%." % int(status.progress() * 100))

def genThumbnail(VIDEO:youtubeVideo):
	logMessage(f"Creating Thumbnail for video with videoId {VIDEO.VIDEO_ID}")
	# Load Assets
	thumbnail:Image = Image.new(size=(1920,1080),color=(000,000,000))
	valMapImage = Image.open(f"./assets/maps/{VIDEO.VAL_MAP}.png")
	thumbnailBase = Image.open("./assets/thumbnailBase.png")
	valAgentImage = Image.open(f"./assets/agents/{VIDEO.VAL_AGENT}.png")
	# Map first as background
	thumbnail.alpha_composite(valMapImage, (0, 0))
	# mext the template i made
	thumbnail.alpha_composite(thumbnailBase, (0, 0))
	# Then the Text
	draw = ImageDraw.Draw(thumbnail)
	# TODO - IMPORTANT | Make the font size dynamic 
	valFont = ImageFont.truetype("./assets/fonts/Valorant Font.ttf", size=140)
	for text, textHeight in zip([VIDEO.VAL_PLAYER, VIDEO.VAL_AGENT, VIDEO.VAL_MAP], [270, 540, 810]):
		_,_,textWidth,_ = draw.textbbox(xy=(0,0),text=text, font=valFont)
		draw.text((485 - (textWidth // 2), textHeight), text, (235, 233, 226), font=valFont)
	# And then agent image
	thumbnail.alpha_composite(valAgentImage, (thumbnail.width - valAgentImage.width - 160, 80))
	logMessage(f"Thumbnail saved fro video with videoId {VIDEO.VIDEO_ID}")
	thumbnail.save(f"./assets/vThumbnails/{VIDEO.VIDEO_ID}.png")

def downloadVideo(videoId) -> None:
	logMessage(f"Downloading video with videoId {videoId}")
	try:
		with YoutubeDL({'outtmpl': f"./assets/videos/{videoId}.mp4"}) as youtubeDownloader:
			youtubeDownloader.download([f"https://youtube.com/watch?v={videoId}"])
	except Exception as e:
		logMessage(f"Something went wrong when downloading the video with videoId {videoId} ({e})")
	return 

def getAuthenticatedService() -> any:
	if os.path.exists("./secrets/creds.pickle"):
		with open("./secrets/creds.pickle", 'rb') as f:
			logMessage("Using saved credentials.")
			credentials = pickle.load(f)
	else:	
		authScopes = ["https://www.googleapis.com/auth/youtube.upload,https://www.googleapis.com/auth/youtube.readonly"]
		flow = InstalledAppFlow.from_client_secrets_file("./secrets/secret.json", scopes=" ".join(authScopes))
		credentials = flow.run_console("","Enter Code: ")
		with open("./secrets/creds.pickle", 'wb') as f:
			pickle.dump(credentials, f)
		logMessage("Saved credentials!")
	return build("youtube", "v3", credentials = credentials)

def logMessage(message:any):
	print(f"[VV][{getTimeStamp()}] -> {message}")

def getTimeStamp() -> str:
		lt = localtime()
		# These 3 line make sure it displays 05:05:05 instead of 5:5:5 (Propper 24 Hour Format)
		hour = lt.tm_hour if str((lt.tm_hour)) == 2 else f"0{lt.tm_hour}"
		minute = lt.tm_min if str((lt.tm_min)) == 2 else f"0{lt.tm_min}"
		second = lt.tm_sec if str((lt.tm_sec)) == 2 else f"0{lt.tm_sec}"
		return ":".join([hour,minute,second])

if __name__ == "__main__":
	ValorVodAuto = ValorVod()
	ValorVodAuto.start()
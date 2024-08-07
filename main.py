from datetime import datetime
from time import localtime
import threading
import time

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ActualImage
from google.oauth2.credentials import Credentials
from yt_dlp import YoutubeDL

import pickle
import os

from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

class ValData:
	agents = ["brimstone", "viper", "omen", "killjoy", "cypher", "sova", "sage", "phoenix", "jett","reyna", "raze", "breach", "skye", "yoru", "astra", "kayo", "chamber", "neon", "fade","harbor", "gekko", "deadlock", "iso", "clove"]
	maps = ["abyss","bind", "icebox", "split", "ascent", "breeze", "lotus", "sunset", "haven", "fracture", "pearl"]	

class youtubeVideo():
	def __init__(self,data,description) -> None:
		self.VIDEO_ID:str = data["id"]["videoId"]
		logMessage(f"[{self.VIDEO_ID}] [✍️] Getting title")
		self.VIDEO_TITLE:str = data["snippet"]["title"] 
		self.VIDEO_DESCRIPTION:str = "".join([char for char in description.replace("\n","LLBB") if char.isalnum()]) 
		logMessage(f"[{self.VIDEO_ID}] [🗺️] Getting valorant map")
		try:
			print(self.VIDEO_DESCRIPTION)
			self.VAL_MAP = [vmap for vmap in ValData.maps if vmap in self.VIDEO_DESCRIPTION.lower()][0]
		except IndexError:
			logMessage(f"[{self.VIDEO_ID}] [❌] Could not get valorant map")
			raise IndexError
		logMessage(f"[{self.VIDEO_ID}] [👤] Getting valorant agent")
		try:
			self.VAL_AGENT = [agent for agent in ValData.agents if agent in self.VIDEO_DESCRIPTION.lower()][0]
		except IndexError:
			logMessage(f"[{self.VIDEO_ID}] [❌] Could not get valorant agent")
			raise IndexError
		logMessage(f"[{self.VIDEO_ID}] [🤺] Getting valorant player")
		try:
			self.VAL_PLAYER = self.VIDEO_DESCRIPTION.split("wwwtwitchtv")[1].split("LLBB")[0]
		except IndexError:
			logMessage(f"[{self.VIDEO_ID}] [❌] Could not get valorant player")
			raise IndexError
		
class ValorVod:
	def __init__(self) -> None:
		# Config
		self.CHANNEL_ID = "UCOR8JcMRg_cFKx0etV5zXBQ"
		# %VP: Valorant Player | %VA: Valorant Agent | %VM: Valorant Map
		self.videoTitleTemplate = "[VV] %VP - %VA - %VM" 
		self.printStart()
		# Init
		self.ytAPI = getAuthenticatedService()
		
	def printStart(self):
		for line in [
				"[⛓️] ---",
				"[⛓️] ValorVod v1.2.0",
			f"[⛓️] Running on channel {self.CHANNEL_ID}",
				"[⛓️] ---"
				]:
			logMessage(line)
		
	def start(self) -> None:
		self.SomethingWentWrong = False
		self.running = True
		self.newVideoThread:threading.Thread = threading.Thread(target=self.checkForNewVideo,daemon=True)
		self.newVideoThread.start()

	def checkForNewVideo(self) -> None:
		while self.running:
			video = self.getLatestVideo()
			logMessage("[⏳] Processing latest video!")
			vidProcessingThread = threading.Thread(
				target=self.processVid, 
				args=[video],
				daemon=True
			)
			vidProcessingThread.start()
			time.sleep(3 * 60 * 60 + 180) # 3 hours (+ 3 minutes just because)

	def getLatestVideo(self) -> dict:
		logMessage(f"[🔎] Getting latest video")
		request = self.ytAPI.search().list(
				part='snippet',
				channelId=self.CHANNEL_ID,
				order='date',
				type='video',
				maxResults=1,
			)
		response = request.execute()
		return response.get('items', [])
		
	def getVideoDescription(self, videoId) -> str:
		logMessage(f"[{videoId}] [📖] Getting description")
		request = self.ytAPI.videos().list(
			part='snippet',
			id=videoId,
		)
		response = request.execute()
		vid_data = response.get('items', [])
		return vid_data[0]["snippet"]["description"]

	def processVid(self, videoData:dict):
		videoData = videoData[0]
		try:
			VIDEO = youtubeVideo(videoData,self.getVideoDescription(videoData[0]["id"]["videoId"]))
		except Exception as e:
			logMessage(f"[{videoData["id"]["videoId"]}] [❌] Error processing video. ({e})")
			return
		# Start download in background
		vidDownloadThread = threading.Thread(
			target=downloadVideo,
			args=[VIDEO.VIDEO_ID],
			daemon=True
		)
		vidDownloadThread.start()
		# Get the metadata and thumbnail ready
		title = self.videoTitleTemplate.replace(
			"%VP",VIDEO.VAL_PLAYER.capitalize()).replace(
			"%VA",VIDEO.VAL_AGENT.capitalize()).replace(
			"%VM",VIDEO.VAL_MAP.capitalize()
		)
		logMessage(f"[{VIDEO.VIDEO_ID}] [🖊️] Generated title '{title}'")
		description = f"{VIDEO.VAL_PLAYER.capitalize()} playing {VIDEO.VAL_AGENT} on {VIDEO.VAL_MAP}!\n\n\nAll {VIDEO.VAL_PLAYER.capitalize()} VODs here: https://twitch.tv/{VIDEO.VAL_PLAYER}/videos\n\n\n\n\n\n\n\n\nTAGS:\nvalorant pro player full twitch vod\nvalorant pro player full twich\nvalorant pro player full\nvalorant pro player\nvalorant pro\nvalorant\n{VIDEO.VAL_PLAYER} {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP}\n{VIDEO.VAL_PLAYER} {VIDEO.VAL_AGENT}\n{VIDEO.VAL_PLAYER} {VIDEO.VAL_MAP}\n{VIDEO.VAL_PLAYER}\nvalorant pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP} {VIDEO.VAL_PLAYER}\nvalorant pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP}\nvalorant pro guide {VIDEO.VAL_AGENT}\nvalorant pro guide\npro Guide\n{datetime.now().month}/{datetime.now().year}\n{datetime.now().year}"
		logMessage(f"[{VIDEO.VIDEO_ID}] [🧾] Generated description")
		tags = f"valorant pro player full twitch vod,valorant pro player full twitch,valorant pro player full,valorant pro player,valorant pro,valorant,{VIDEO.VAL_PLAYER} {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP},{VIDEO.VAL_PLAYER} {VIDEO.VAL_AGENT},{VIDEO.VAL_PLAYER} {VIDEO.VAL_MAP},{VIDEO.VAL_PLAYER},valorant Pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP} {VIDEO.VAL_PLAYER},valorant pro guide {VIDEO.VAL_AGENT} {VIDEO.VAL_MAP},valorant pro guide {VIDEO.VAL_AGENT},guide,{datetime.now().month}/{datetime.now().year},{datetime.now().year}"
		logMessage(f"[{VIDEO.VIDEO_ID}] [🏷️] Generated {len(tags.split(","))} tags")
		genThumbnail(VIDEO)
		logMessage(f"[{VIDEO.VIDEO_ID}] [🕒] Waiting for video to download")
		vidDownloadThread.join()
		# Video is downloaded and all metadata is ready. Upload!
		# uploadedVideoId = self.uploadVideo(title,description,tags,VIDEO.VIDEO_ID)
		# Now upload the thumbnail
		# self.uploadThumbnail(VIDEO.VIDEO_ID,uploadedVideoId,f"./assets/vThumbnails/{VIDEO.VIDEO_ID}.png")
		# cleanup function for video and thumbnail
		time.sleep(5)
		cleanUp(VIDEO)
	
	
	def uploadVideo(self, title, description, tags, internalVideoId):
		videoFile = f"{'.' if os.name == 'nt' else ''}/assets/videos/{internalVideoId}.mp4"
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
		logMessage(f"[{internalVideoId}] [🆙] Starting video upload")
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
				logMessage(f"[{internalVideoId}] [⚡] Uploaded {int(status.progress() * 100)}%.")
		logMessage(f"[{internalVideoId}] [✅] Video Upload completed with new id: {response['id']}")
		return response["id"]

	def uploadThumbnail(self, internalVideoId, uploadedVideoId, thumbnailFile):
		logMessage(f"[{internalVideoId}] [🆙] Starting thumbnail upload")
		request = self.ytAPI.thumbnails().set(
			videoId=uploadedVideoId,
			media_body=MediaFileUpload(thumbnailFile, chunksize=1 * 1024 * 1024, resumable=True)
		)
		response = request.execute()
		response = None
		while response is None:
			status, response = request.next_chunk()
			if status:
				logMessage(f"[{internalVideoId}] [⚡] Uploaded {int(status.progress() * 100)}%.")
		logMessage(f"[{internalVideoId}] [✅] Thumbnail Upload completed")

def genThumbnail(VIDEO:youtubeVideo):
	logMessage(f"[{VIDEO.VIDEO_ID}] [🖼️] Creating Thumbnail")
	# Load Assets
	ytThumbnail:ActualImage = Image.open(f"{'.' if os.name == 'nt' else ''}/assets/maps/{VIDEO.VAL_MAP}.png")
	thumbnailBase = Image.open(f"{'.' if os.name == 'nt' else ''}/assets/vThumbnails/thumbnailBase.png")
	valAgentImage = Image.open(f"{'.' if os.name == 'nt' else ''}/assets/agents/{VIDEO.VAL_AGENT}.png")
	# first the template i made
	ytThumbnail.alpha_composite(thumbnailBase, (0, 0))
	# Then the Text
	draw = ImageDraw.Draw(ytThumbnail)
	valFont = ImageFont.truetype("{'.' if os.name == 'nt' else ''}/assets/fonts/Valorant Font.ttf", size=140)
	for text, textHeight in zip([VIDEO.VAL_PLAYER, VIDEO.VAL_AGENT, VIDEO.VAL_MAP], [170, 500, 810]):
		_,_,textWidth,_ = draw.textbbox(xy=(0,0),text=text, font=valFont)
		draw.text((600 - (textWidth // 2), textHeight), text, (235, 233, 226), font=valFont)
	# And then agent image
	ytThumbnail.alpha_composite(valAgentImage, (ytThumbnail.width - valAgentImage.width - 120, 80))
	ytThumbnail.thumbnail((1820,720),Image.LANCZOS)
	ytThumbnail.save(f"{'.' if os.name == 'nt' else ''}/assets/vThumbnails/{VIDEO.VIDEO_ID}.png")

def downloadVideo(videoId) -> None:
	logMessage(f"[{videoId}] [⤵️] Downloading video")
	with YoutubeDL({
			'outtmpl'     : f"{'.' if os.name == 'nt' else ''}/assets/videos/{videoId}.mp4",
			'quiet'       : True,
			'no_warnings' : True
		}) as youtubeDownloader: 
		youtubeDownloader.download([f"https://youtube.com/watch?v={videoId}"])
	logMessage(f"[{videoId}] [✅] Download completed")

def getAuthenticatedService() -> any:
	credentials = None
	# Check if credentials pickle file exists
	if os.path.exists(f"{'.' if os.name == 'nt' else ''}/secrets/creds.pickle"):
		with open(f"{'.' if os.name == 'nt' else ''}/secrets/creds.pickle", 'rb') as savedCredsFile:
			logMessage("[💾] Using saved credentials")
			credentials = pickle.load(savedCredsFile)
	# If there are no valid credentials or they are expired, perform the OAuth flow
	if not credentials or not credentials.valid:
		if credentials and credentials.expired and credentials.refresh_token:
			logMessage("[♻️] Trying to refresh expired credentials")
			try:
				credentials.refresh(Request())
			except RefreshError:
				logMessage("[❌] Refresh token expired!")
				credentials = getCredsManually()
		else:
				credentials = getCredsManually()
		# Save the credentials for the next run
		with open(f"{'.' if os.name == 'nt' else ''}/secrets/creds.pickle", 'wb') as savedCredsFile:
			pickle.dump(credentials, savedCredsFile)
		logMessage("[🏦] Saved credentials")
	return build("youtube", "v3", credentials=credentials)
	
def getCredsManually() -> Credentials:
	logMessage("[❗] Manual verification needed!")
	auth_scopes = ["https://www.googleapis.com/auth/youtube.upload",  # Upload Videos and thumbnails
					"https://www.googleapis.com/auth/youtube.readonly" # read video data of the leeched channel
				]
	flow = InstalledAppFlow.from_client_secrets_file(f"{'.' if os.name == 'nt' else ''}/secrets/secret.json", scopes=auth_scopes)
	credentials = flow.run_console()
	return credentials

def cleanUp(VIDEO:youtubeVideo):
	os.remove(f"{'.' if os.name == 'nt' else ''}/assets/videos/{VIDEO.VIDEO_ID}.mp4")
	os.remove(f"{'.' if os.name == 'nt' else ''}/assets/vThumbnails/{VIDEO.VIDEO_ID}.png")
	logMessage(f"[{VIDEO.VIDEO_ID}] [🥳] Processing done!")
	del VIDEO

def logMessage(message:any):
	print(f"[VV][{getTimeStamp()}] -> {message}")

def getTimeStamp() -> str:
		lt = localtime()
		return ":".join([str(lt.tm_hour),str(lt.tm_min),str(lt.tm_sec)])

if __name__ == "__main__":
	ValorVodAuto = ValorVod()
	ValorVodAuto.start()
	while True:
		time.sleep(1)

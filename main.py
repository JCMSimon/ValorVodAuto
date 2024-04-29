import datetime
import os
import time
import threading
from PIL import Image,ImageDraw,ImageFont
from dotenv import load_dotenv

from yt_dlp import YoutubeDL
from googleapiclient.discovery import build


class ValorVod:
	def __init__(self) -> None:
		self.data = dict()
		self.data["agents"] = ["brimstone","viper","omen","killjoy","cypher","sova","sage","phoenix","jett","reyna","raze","breach","skye","yoru","astra","kayo","chamber","neon","fade","harbor","gekko","deadlock","iso","clove"]
		self.data["maps"] = ["bind","haven","split","ascent","icebox","breeze","fracture","pearl","lotus","sunset"]
		# ---
		self.processed_vids = list()
		# Load api key from .env
		load_dotenv()
		API_KEY:str = os.environ.get("API_KEY")
		self.ytAPI = build('youtube', 'v3', developerKey=API_KEY)
		self.C_ID:str = os.environ.get("C_ID") 
		# ---
		self.STARTUP_TIME:int = time.time()
		
	def start(self):
		self.newVideoThread = threading.Thread(target=self.checkForNewVideos,daemon=True)
		self.newVideoThread.start()

	def checkForNewVideos(self):
		request = self.ytAPI.search().list(
		part='snippet',
		channelId=self.C_ID,
		order='date',
		type='video',
		maxResults=4,
		)
		response = request.execute()
		ytData = response.get('items', [])
		for video in ytData:
			# if video is newer than startup and id not in processed 
			# if int(datetime.datetime.strptime((video["snippet"]["publishTime"]),"%Y-%m-%dT%H:%M:%SZ").timestamp()) > self.STARTUP_TIME and video["id"]["videoId"] not in self.processed_vids:
			if video["id"]["videoId"] not in self.processed_vids:
				vidThread = threading.Thread(target=self.processVid,args=[video["id"]["videoId"]],daemon=True)
				vidThread.start()
				time.sleep(10)
		time.sleep(((60 * 60) * 3) + (60 * 10))
		self.checkForNewVideos()

	def processVid(self, id:str):
		# Title
		description = self.getVideoDescription(id)
		description_words = set(word.lower() for word in description.replace("kay/o","kayo").split(" "))
		try:
			player = description.split("twitch.tv/")[1].split("\n")[0].capitalize().replace("official","")
			agent:str = [agent for agent in self.data["agents"] if agent in description_words][0].capitalize()
			vmap:str = [vmap for vmap in self.data["maps"] if vmap in description_words][0].capitalize()
		except Exception as  e:
			print("skipping",id)
			# unsupported map or agent or player didnt work, skip
			return		
		title= f"[VV] {player} - {vmap} - {agent}"
		# Download video
		with YoutubeDL({'outtmpl': f"./assets/videos/{id}.mp4",}) as ydl:
			ydl.download([f"https://youtube.com/watch?v={id}"])
		# Thumbnail
		base = Image.open("./assets/thumbnail_base.png")
		draw = ImageDraw.Draw(base)
		font = ImageFont.truetype("./assets/fonts/Valorant Font.ttf",size=145)
		_, _, w, h = draw.textbbox(xy=(0,0),text=player,font=font)
		draw.text((485 - (w / 2),180),player,(235,233,226),font=font)
		_, _, w, h = draw.textbbox(xy=(0,0),text=agent,font=font)
		draw.text((485 - (w / 2),490),agent,(235,233,226),font=font)
		_, _, w, h = draw.textbbox(xy=(0,0),text=vmap,font=font)
		draw.text((485 - (w / 2),800),vmap,(235,233,226),font=font)		
		agentImage = Image.open(f"./assets/agents/{agent.lower()}.png")
		base.alpha_composite(agentImage,(1000,80))
		base.save(f"./assets/vThumbnails/{id}.png")		
		self.processed_vids.append(id)
		print(title)
		base.show()
		# upload video here once its downloaded
		
	def getVideoDescription(self,id):
		request = self.ytAPI.videos().list(
		part='snippet',
		id=id,
		)
		response = request.execute()
		vidData = response.get('items', [])
		return vidData[0]["snippet"]["description"].replace("!","")

if __name__ == "__main__":
	myapp = ValorVod()
	# myapp.start()
	myapp.processVid("MQs5Lzo13_E")
	while True:
		time.sleep(60)
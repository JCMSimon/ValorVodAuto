import os
import threading
import time
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont
from yt_dlp import YoutubeDL
from google.oauth2 import service_account




class ValorVod:
	def __init__(self) -> None:
		self.data = {
			"agents": ["brimstone", "viper", "omen", "killjoy", "cypher", "sova", "sage", "phoenix", "jett",
					   "reyna", "raze", "breach", "skye", "yoru", "astra", "kayo", "chamber", "neon", "fade",
					   "harbor", "gekko", "deadlock", "iso", "clove"],
			"maps": ["bind", "haven", "split", "ascent", "icebox", "breeze", "fracture", "pearl", "lotus", "sunset"]
		}
		self.processed_vids = set()
		# Load API key from .env
		load_dotenv()
		self.API_KEY = os.environ.get("API_KEY")
		self.ytAPI = build('youtube', 'v3', developerKey=self.API_KEY)
		self.C_ID = os.environ.get("C_ID")
		self.STARTUP_TIME = time.time()

	def start(self):
		self.newVideoThread = threading.Thread(target=self.check_for_new_videos, daemon=True)
		self.newVideoThread.start()

	def check_for_new_videos(self):
		while True:
			request = self.ytAPI.search().list(
				part='snippet',
				channelId=self.C_ID,
				order='date',
				type='video',
				maxResults=4,
			)
			response = request.execute()
			yt_data = response.get('items', [])
			for video in yt_data:
				if video["id"]["videoId"] not in self.processed_vids:
					vid_thread = threading.Thread(target=self.process_vid, args=[video["id"]["videoId"]],
												  daemon=True)
					vid_thread.start()
					time.sleep(10)
			time.sleep(((60 * 60) * 3) + (60 * 10))

	def process_vid(self, id: str, download=True):
		try:
			description = self.get_video_description(id)
			description_words = set(word.lower() for word in description.replace("kay/o", "kayo").split(" "))
			player = description.split("twitch.tv/")[1].split("\n")[0].capitalize().replace("official", "")
			agent = [agent for agent in self.data["agents"] if agent in description_words][0].capitalize()
			vmap = [vmap for vmap in self.data["maps"] if vmap in description_words][0].capitalize()
		except Exception as e:
			print(f"Skipping {id}: {e}")
			return
		title = f"[VV] {player} - {vmap} - {agent}"
		# Download video
		if download:
			with YoutubeDL({'outtmpl': f"./assets/videos/{id}.mp4"}) as ydl:
				ydl.download([f"https://youtube.com/watch?v={id}"])
		# Thumbnail
		map_image = Image.open(f"./assets/maps/{vmap.lower()}.png")
		map_image.alpha_composite(Image.open("./assets/thumbnail_base.png"), (0, 0))
		draw = ImageDraw.Draw(map_image)
		font = ImageFont.truetype("./assets/fonts/Valorant Font.ttf", size=145)
		for text, y_coord in zip([player, agent, vmap], [180, 495, 810]):
			_,_,text_width,_ = draw.textbbox(xy=(0,0),text=text, font=font)
			draw.text((485 - (text_width // 2), y_coord), text, (235, 233, 226), font=font)
		agent_image = Image.open(f"./assets/agents/{agent.lower()}.png")
		map_image.alpha_composite(agent_image, (map_image.width - agent_image.width - 160, 80))
		map_image.save(f"./assets/vThumbnails/{id}.png")
		self.processed_vids.add(id)
		print(title)
		map_image.show()

		SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
		creds = service_account.Credentials.from_service_account_file("./valorvod-4b0252c4525b.json")
		creds = creds.with_scopes(SCOPES)
		self.ytAPI2 = build('youtube', 'v3', credentials=creds)

		# Upload video
		file_path = f"./assets/videos/{id}.mp4"
		chunk_size = 10 * 1024 * 1024  # 10 MB chunk size
		media = MediaFileUpload(file_path, chunksize=chunk_size, resumable=False)
		request = self.ytAPI2.videos().insert(
			part="snippet,status",
			body={
				"snippet": {
					"categoryId": "20",  # Gaming
					"description": f"[VV] {player} playing {agent} on {vmap}",
					"title": f"{title}"
				},
				"status": {
					"privacyStatus": "private"
				}
			},
			media_body=media
		)
		request.execute()
		print("Video upload complete!")
			
	def get_video_description(self, id):
		request = self.ytAPI.videos().list(
			part='snippet',
			id=id,
		)
		response = request.execute()
		vid_data = response.get('items', [])
		return vid_data[0]["snippet"]["description"].replace("!", "")


if __name__ == "__main__":
	my_app = ValorVod()
	# my_app.start()
	my_app.process_vid("MQs5Lzo13_E",download=False)
	while True:
		time.sleep(60)
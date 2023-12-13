
import sys
import os
import asyncio
import requests
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from discord import Intents
import discord
import subprocess


class DiscordBotWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, token, guild_id, download_directory):
        super().__init__()
        self.token = token
        self.guild_id = guild_id
        self.download_directory = download_directory

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def download_emojis():
            intents = Intents.all()
            bot = discord.Client(intents=intents)

            try:
                @bot.event
                async def on_ready():
                    print("Started")
                    for guild in bot.guilds:
                        if guild.id == self.guild_id:
                            emojis = guild.emojis
                            for each in emojis:
                                if each.animated:
                                    await self.download_image(f"https://cdn.discordapp.com/emojis/{each.id}.gif", each.name)
                                else:
                                    await self.download_image(f"https://cdn.discordapp.com/emojis/{each.id}.png", each.name)
                            print("Finished")
                            self.finished.emit()
                            await bot.close()
            except Exception as e:
                print(f"An error occurred in on_ready: {str(e)}")

            await bot.start(self.token)

        loop.run_until_complete(download_emojis())

    async def download_image(self, url, name):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36'}
            response = requests.get(url, stream=True, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            extension = url[-3:]
            with open(os.path.join(self.download_directory, f"{name}.{extension}"), 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            print(f"Downloaded: {name}")
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            print(f"Request Exception: {err}")


class DiscordBotDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.token_label = QLabel('봇 토큰을 입력해 주세요.:')
        self.token_entry = QLineEdit(self)
        self.guild_id_label = QLabel('서버 아이디를 입력해 주세요.:')
        self.guild_id_entry = QLineEdit(self)
        self.directory_label = QLabel('다운로드 경로:')
        self.directory_entry = QLineEdit(self)
        self.directory_button = QPushButton('경로 선택', self)
        self.directory_button.clicked.connect(self.choose_directory)
        self.confirm_button = QPushButton('다운로드', self)
        self.confirm_button.clicked.connect(self.start_download)

        layout = QVBoxLayout()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_entry)
        layout.addWidget(self.guild_id_label)
        layout.addWidget(self.guild_id_entry)
        layout.addWidget(self.directory_label)
        layout.addWidget(self.directory_entry)
        layout.addWidget(self.directory_button)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)

        self.setWindowTitle('Discord Bot Emoji Downloader')
        self.setGeometry(300, 300, 400, 250)

    def choose_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.directory_entry.setText(directory)

    def start_download(self):
        token = self.token_entry.text().strip()
        guild_id = self.guild_id_entry.text().strip()
        download_directory = self.directory_entry.text().strip()

        if not token or not guild_id or not download_directory:
            self.show_message('Error', 'Token, Guild ID, and Download Directory are required.')
            return

        # Save the download directory path to a text file
        with open('download_directory.txt', 'w') as file:
            file.write(download_directory)

        self.worker = DiscordBotWorker(token, int(guild_id), download_directory)
        self.worker.finished.connect(self.download_finished)
        self.worker.run()

    def download_finished(self):
        self.show_message('Success', 'Emoji download completed.')

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DiscordBotDownloader()
    window.show()
    sys.exit(app.exec_())




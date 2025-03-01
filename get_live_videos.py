import json
import logging
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Lock

import requests
import concurrent.futures


def get_match_list(match_date='2025-02-16'):
    headers = {
        'Host': 'api.itf-production.sports-data.stadion.io',
        'sec-ch-ua-platform': '"Windows"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'origin': 'https://www.itftennis.com',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-IN,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ml;q=0.6,hi;q=0.5',
        'priority': 'u=4, i',
    }

    response = requests.get(
        f'https://api.itf-production.sports-data.stadion.io/custom/wttCompleteMatchList/{match_date}',
        headers=headers, verify=False
    )

    jsn = response.json()
    matches_map = {}

    for event in jsn['data'].values():
        event_name = event['_name']
        event_category = event['eventCategory']['name']

        event_name = re.sub('[^A-Za-z0-9]+', ' ', event_name)
        event_category = re.sub('[^A-Za-z0-9]+', ' ', event_category)

        for court_name, court_values in event['courts'].items():
            court_name = re.sub('[^A-Za-z0-9]+', ' ', court_name)
            for court_value in court_values:
                court_id = court_value['id']
                dateStartLocal = court_value['dateStartLocal']
                try:
                    dateStartLocal = datetime.strptime(dateStartLocal, '%Y-%m-%d')
                except:
                    pass
                try:
                    matchStatus = court_value['matchStatus']['_name']
                except:
                    matchStatus = ""
                try:
                    isLiveStreamed = court_value['isLiveStreamed']
                except:
                    isLiveStreamed = False
                tennisId = court_value['tennisId']
                _drawDiscipline = court_value['_drawDiscipline']['type']

                if matchStatus.upper() == 'COMPLETE' and isLiveStreamed and _drawDiscipline.upper() == 'SINGLES':
                    player_names = []
                    for side in court_value['sides']:
                        side_players = []
                        for sidePlayer in side['sidePlayer']:
                            side_player_name = sidePlayer['player']['_name']
                            side_player_name = re.sub('[^A-Za-z0-9]+', ' ', side_player_name)
                            side_players.append(side_player_name)
                        side_player_key = " & ".join(sorted(side_players))
                        player_names.append(side_player_key)

                    player_names_key = " vs ".join(sorted(player_names))
                    match_file_key = f"{player_names_key}-{event_name} - {event_category} - {court_name}-{court_id}"
                    matches_map[tennisId] = {
                        'dateStartLocal': dateStartLocal,
                        'file_key': match_file_key  # using 'file_key' for consistency
                    }

    return matches_map


def get_live_stream_id(match_map):
    download_args = {}
    headers = {
        'Host': 'api.staylive.tv',
        'sec-ch-ua-platform': '"Windows"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'content-type': 'application/json',
        'sec-ch-ua-mobile': '?0',
        'origin': 'https://www.itftennis.com',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-IN,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ml;q=0.6,hi;q=0.5',
        'priority': 'u=1, i',
    }

    json_data = {
        'livestream_external_ids': list(match_map.keys()),
    }

    response = requests.post('https://api.staylive.tv//live-scheduler/item-by-external-id',
                             headers=headers, json=json_data, verify=False)
    jsn = response.json()
    for i in jsn["message"]:
        try:
            external_id = i['external_id']
            livestream_id = f"{i['livestream_id']}"
            exists = i['exists']

            if exists:
                download_args[livestream_id] = {
                    'external_id': external_id,
                    'livestream_id': livestream_id,
                    'file_key': match_map[external_id]['file_key'],
                    'dateStartLocal': match_map[external_id]['dateStartLocal']
                }
        except:
            print("Error in processing data", i)

    return download_args


def get_live_video_url(livestream_id):
    headers = {
        'Host': 'itf.content-checker.staylive.cloud',
        'sec-ch-ua-platform': '"Windows"',
        'authorization': 'Bearer undefined',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'content-type': 'application/x-www-form-urlencoded',
        'sec-ch-ua-mobile': '?0',
        'origin': 'https://www.itftennis.com',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-IN,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ml;q=0.6,hi;q=0.5',
        'priority': 'u=1, i',
    }

    response = requests.post(
        f'https://itf.content-checker.staylive.cloud/platforms/platform_UvtcjZ0tuwSV/content-check/livestream/{livestream_id}',
        headers=headers, verify=False
    )

    jsn = response.json()
    try:
        playback_url = jsn['message']['content']['playback_url']
    except:
        playback_url = None

    return dict(
        livestream_id=livestream_id,
        playback_url=playback_url
    )


def basic_logging():
    Path('itf-logs').mkdir(parents=True, exist_ok=True)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    fileHandler = logging.FileHandler("{0}/{1}.log".format('itf-logs',
                                                           f"itf-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
    return rootLogger


class ItfStreamDownloader:
    def __init__(self):
        self.stream_logger = basic_logging()
        self.stream_logger.info("ITF Stream Downloader started")
        self.download_lock = Lock()
        self.downloaded_file = 'downloaded.json'
        if Path(self.downloaded_file).exists():
            with open(self.downloaded_file, 'r') as f:
                try:
                    self.downloaded = json.load(f)
                except Exception as e:
                    self.stream_logger.error(f"Error loading downloaded.json: {e}")
                    self.downloaded = {}
        else:
            self.downloaded = {}

    def mark_downloaded(self, file_key):
        with self.download_lock:
            self.downloaded[file_key] = datetime.now().isoformat()
            with open(self.downloaded_file, "w") as f:
                json.dump(self.downloaded, f, indent=2)

    def backgrounddownloader(self, url, file_path, file_key):
        self.stream_logger.info(f"Downloading started for {file_key}")
        command = (f'yt-dlp "{url}" '
                   f'--external-downloader ffmpeg '
                   f'--external-downloader-args "ffmpeg:-t 04:00:00" '
                   f'--add-header="Accept:*/*" '
                   f'--add-header="Origin:https://www.itftennis.com" '
                   f'--add-header="Connection:keep-alive" '
                   f'--add-header="Referer:https://www.itftennis.com/" '
                   f'--add-header="User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36" '
                   f'--abort-on-unavailable-fragment '
                   f'-o "{file_path}.%(ext)s"')
        try:
            process_output = subprocess.check_output(command, shell=True, universal_newlines=True)
            self.stream_logger.info('Subprocess output: ' + str(process_output))
            self.stream_logger.info(f"Downloading finished for {file_key}")
            # Mark as downloaded in the JSON file
            self.mark_downloaded(file_key)
        except subprocess.CalledProcessError as e:
            self.stream_logger.error(f"Download failed for {file_key}: {e}")

    def scrape(self):
        date_today = datetime.today()

        match_dates_list = []
        for i in range(14):
            match_dt = date_today - timedelta(days=i)
            match_date = match_dt.strftime('%Y-%m-%d')
            match_dates_list.append(match_date)

        for match_date in reversed(match_dates_list):

            match_list_map = get_match_list(match_date)
            if len(match_list_map.keys()) > 0:
                livestream_id_map_full = get_live_stream_id(match_list_map)

                # Retrieve playback URLs and collect matches
                matches = []
                for livestream_id, match_data in livestream_id_map_full.items():
                    res = get_live_video_url(livestream_id)
                    playback_url = res.get('playback_url')
                    if playback_url:
                        match_data['playback_url'] = playback_url
                        matches.append(match_data)
                    else:
                        self.stream_logger.info(f"No playback URL for match {match_data['file_key']}")

                # Sort matches by date (oldest first)
                matches.sort(key=lambda x: x['dateStartLocal'])

                # Filter out matches that have been downloaded already (using the file_key)
                matches_to_download = [m for m in matches if m['file_key'] not in self.downloaded]
                self.stream_logger.info(
                    f"Found {len(matches_to_download)} matches to download after filtering downloaded ones.")

                # Ensure output directory exists
                #Path('itf-videos').mkdir(parents=True, exist_ok=True)
                Path('tennisvideos/final').mkdir(parents=True, exist_ok=True)

                # Use ThreadPoolExecutor to download 5 matches at a time
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    future_to_match = {}
                    for match in matches_to_download:
                        file_key = match['file_key']
                        playback_url = match['playback_url']
                        # Create a sanitized file name
                        file_name = re.sub('[^A-Za-z0-9]+', ' ', file_key)
                        #file_path = f"itf-videos/{file_name}"
                        file_path = f"tennisvideos/final/{file_name}"
                        self.stream_logger.info(f"Scheduling download for match: {file_key}")
                        future = executor.submit(self.backgrounddownloader, playback_url, file_path, file_key)
                        future_to_match[future] = match
                    # Wait for all downloads to complete
                    for future in concurrent.futures.as_completed(future_to_match):
                        match = future_to_match[future]
                        try:
                            future.result()
                        except Exception as e:
                            self.stream_logger.error(f"Error downloading match {match['file_key']}: {e}")

    def finish(self):
        self.stream_logger.info("All downloads finished")


if __name__ == '__main__':
    itf = ItfStreamDownloader()
    itf.scrape()
    itf.finish()

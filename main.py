#このツールはあくまでも、あくまでもウェブサイトのテストを行うツールであります。
#イラついたからとか言って撃ったらあかんて

#作成元: Myamya-wiki
#Twitter名: myamya_wiki
#github: https://github.com/myamya-wiki


import threading
import requests
import logging
import coloredlogs
import time
import os

# ログの設定
coloredlogs.install(level=logging.INFO, format='%(asctime)s - %(message)s', level_styles={'info': {'color': 'green'}})

# ログカウンター
log_counter = 0
lock = threading.Lock()
max_threads = 2000

# スレッド制御用のセマフォ
semaphore = threading.Semaphore(max_threads)

def make_requests(url, interval, timeout, log_to_file=False):
    global log_counter
    log_format = "%(asctime)s - %(message)s"

    logger = logging.getLogger()  # ルートロガーを取得

    if log_to_file:
        # ログファイルが存在しない場合は新規作成する
        if not os.path.isfile("requests.log"):
            open("requests.log", "w").close()

        handler = logging.FileHandler("requests.log")
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    with lock:
        logger.addHandler(handler)

    while True:
        with semaphore:
            with lock:
                log_counter += 1
                request_count = log_counter

            try:
                start_time = time.time()  # リクエストの開始時刻を記録
                if timeout is None:
                    response = requests.get(url)
                else:
                    response = requests.get(url, timeout=timeout/1000)  # タイムアウトをミリ秒から秒に変換して設定
                end_time = time.time()  # レスポンスの受信時刻を記録
                response_time = end_time - start_time  # レスポンスタイムの計算

                status_code = response.status_code
                request_url = response.url

                if response.ok:
                    with lock:
                        logger.info("{} {} {} (Response Time: {:.3f}s)".format(request_count, request_url, status_code, response_time))
                else:
                    with lock:
                        logger.error("{} {} {} (Response Time: {:.3f}s)".format(request_count, request_url, status_code, response_time))

                    # エラーレスポンスを受けた場合にリトライする
                    retry_count = 3  # リトライ回数の設定
                    for _ in range(retry_count):
                        time.sleep(interval / 1000)  # リトライ間隔待機
                        try:
                            start_time = time.time()
                            if timeout is None:
                                response = requests.get(url)
                            else:
                                response = requests.get(url, timeout=timeout / 1000)
                            end_time = time.time()
                            response_time = end_time - start_time
                            status_code = response.status_code
                            request_url = response.url

                            if response.ok:
                                with lock:
                                    logger.info(
                                        "{} {} {} (Response Time: {:.3f}s) - Retry".format(request_count, request_url,
                                                                                            status_code, response_time))
                                break  # 成功した場合はループを抜ける
                            else:
                                with lock:
                                    logger.error("{} {} {} (Response Time: {:.3f}s) - Retry".format(request_count,
                                                                                                      request_url,
                                                                                                      status_code,
                                                                                                      response_time))
                        except requests.exceptions.RequestException as e:
                            with lock:
                                logger.error("{} {} (Response Time: N/A) - Retry".format(request_count, e))
            except requests.exceptions.RequestException as e:
                with lock:
                    logger.error("{} {} (Response Time: N/A)".format(request_count, e))

            if interval:
                time.sleep(interval / 1000)  # ミリ秒を秒に変換して待機
            else:
                time.sleep(0)  # 無限に続けるための短時間の待機

# スレッド数を取得
while True:
    num_threads = int(input("スレッド数を入力してください: "))
    if num_threads <= max_threads:
        break
    else:
        print(f"最大スレッド数は{max_threads}です。再度入力してください。")

# リクエストするURLを取得
request_url = input("リクエストするURLを入力してください: ")

# リクエスト間隔を取得
interval_input = input("リクエスト間隔をミリ秒単位で入力してください (無指定の場合はEnterキー): ")
interval = int(interval_input) if interval_input else None

# タイムアウトを取得
timeout_input = input("タイムアウトをミリ秒単位で入力してください (無指定の場合はEnterキー): ")
timeout = int(timeout_input) if timeout_input else None

# ログをファイルに保存するかどうかを取得
log_to_file_input = input("ログをファイルに保存しますか？ (y/n): ")
log_to_file = log_to_file_input.lower() == "y"

# スレッドを作成して開始する
threads = []
for _ in range(num_threads):
    thread = threading.Thread(target=make_requests, args=(request_url, interval, timeout, log_to_file))
    thread.start()
    threads.append(thread)

# Ctrl+Cが押されるまで待機
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

# スレッドの終了を待つ
for thread in threads:
    thread.join()

import requests
import urllib
import time
import argparse
import csv
import os

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def get_data(url):
    resp = requests.get(url)
    if resp.status_code >= 300:
        print("HTTP ERROR:", resp.status_code)
        return False
    json_data = resp.json()
    if "data" not in json_data:
        print("找不到数据")
        return False
    return resp.json()['data']


def get_cid_and_title(bvid, p=1):
    url = 'https://api.bilibili.com/x/web-interface/view?bvid=' + bvid
    data = get_data(url)
    if data != False:
        title = data['title']
        cid = data['pages'][p - 1]['cid']
        return str(cid), title
    else:
        return False, False


def get_information(bvList):
    infoList = []
    for bvid in bvList:
        item = []
        if len(bvid) < 12:
            print("BVID 格式错误")
            continue
        elif len(bvid) == 12:
            cid, title = get_cid_and_title(bvid)
            if cid == False:
                continue
            item.append(bvid)
        else:
            cid, title = get_cid_and_title(bvid[:12], int(bvid[13:]))
            if cid == False:
                continue
            item.append(bvid[:12])
        item.append(cid)
        item.append(title)
        infoList.append(item)

    return infoList


def get_audio(info_list, subtitle_list=None):
    base_url = 'https://api.bilibili.com/x/player/playurl?fnval=16&'

    for idx, item in enumerate(info_list):
        st = time.time()
        bvid, cid, title = item[0], item[1], item[2]

        if "/" in title:
            title = " ".join(title.split("/"))
        if '\\' in title:
            title = " ".join(title.split("\\"))

        if subtitle_list is None:
            file_name = "{}.mp3".format(title)
        else:
            file_name = "{}- {} - {} .mp3".format(title, 'P' + str(idx + 1), subtitle_list[idx])
        path = 'download/' + file_name

        if os.path.exists(path):
            continue

        url = base_url + 'bvid=' + bvid + '&cid=' + cid

        audioUrl = requests.get(url).json()['data']['dash']['audio'][0]['baseUrl']

        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),
            ('Referer', 'https://api.bilibili.com/x/web-interface/view?bvid=' + bvid),  # 注意修改referer,必须要加的!
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive'),
        ]
        urllib.request.install_opener(opener)

        try:
            urllib.request.urlretrieve(url=audioUrl, filename=path)
        except Exception as e:
            print("下载失败，因为：", e)
            os.remove(path)

        ed = time.time()
        print(str(round(ed - st, 2)) + ' seconds download finish:', file_name)
        time.sleep(1)


def get_bv_list(arg, extra_args):
    bv_list = []
    if arg.f:
        with open(extra_args[0], 'r') as f:
            reader = csv.reader(f)
            for line in reader:
                bv_list.append(line[0])
    elif arg.c:
        bv_list = [i for i in extra_args]

    else:
        raise 'Please select an input method.'

    return bv_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store_true')
    parser.add_argument('-c', action='store_true')
    args, extra_args = parser.parse_known_args()
    BVList = get_bv_list(args, extra_args)

    print(f'Downloader Start! {BVList}')
    st = time.time()
    get_audio(get_information(BVList))
    ed = time.time()
    print('Download Finish All! Time consuming:', str(round(ed - st, 2)) + ' seconds')

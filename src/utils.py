import base64
import json
import os
import re
from io import BytesIO
from collections import defaultdict
import numpy as np
import pandas as pd
from opencc import OpenCC
from glob import glob
import requests
from moviepy.editor import VideoFileClip
from PIL import Image

def get_cropped_image(image, box):
    img_width, img_height = image.size
    width = box[0]
    height = box[1]
    offset_top = box[2]
    offset_start = box[3]

    cropped_image = image.crop(
        (offset_start, offset_top, offset_start + width, offset_top + height)
    )
    # cropped_image.save(f'cropped_image_{i}.png')
    return cropped_image


def get_base64_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def get_taglist(csv_path):
    df = pd.read_csv(csv_path)
    keys = df.iloc[0, 1:]
    values = df.iloc[8:, 1:]
    keys = df.iloc[0, 1:].tolist()
    values = df.iloc[8:, 1:]
    result_dict = {
        key: [val for val in values.iloc[:, idx].tolist() if not pd.isna(val)]
        for idx, key in enumerate(keys)
    }
    return result_dict


def parse_filepath(file):
    json_files = []
    if os.path.isdir(file):
        json_files = glob.glob(os.path.join(file, "*.json"))
    elif os.path.isfile(file):
        if file.endswith(".json"):
            json_files.append(file)
        else:
            raise ValueError("Provided file is not a JSON file")
    else:
        raise ValueError("Please provide a valid file or folder path")

    if not json_files:
        raise ValueError("Please provide at least one JSON file")

    data_frames = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.json_normalize(data)
            data_frames.append(df)
    return data_frames


def text_clean(text, num=5):
    cc = OpenCC("s2t")
    text = re.split(r"[:：]+", text)[-1]
    text = re.sub(r"[：:,，\n\[\]\'【]+|\d+\.", " ", text)
    text = cc.convert(text)
    text = re.sub(r"[\|\｜】]+", "_", text).split()
    # for i, t in enumerate(text[1:], start=1):
    #     if "_" not in t:
    #         text[i - 1] = text[i - 1] + " " + t
    #         text.remove(t)
    return ",".join(text[-num:])

def get_audio(url, filename="temp.mp4", max_duration=30):
    response = requests.get(url, stream=True)

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    video_clip = VideoFileClip(filename)
    audio_clip = video_clip.audio

    if audio_clip.duration > max_duration:
        audio_clip = audio_clip.subclip(0, max_duration)
    audio_clip.write_audiofile(filename.split(".")[0] + ".mp3")

def parse_message(df):
    """ TODO: 
    1. add default value after list if the length of list is not alike (remove src.util.get_list function)
    """
    name = df["name"]
    mes = df["messages"]
    brand = df["brand"]
    # for name, mes in zip(name,message):
    mes = json.loads(mes)
    modules = []
    broadcast_text = ""
    for item in mes:
        module_id = item.get("module_id")
        module = {
            "brand": brand,
            "name": name,
            "id": module_id,
            "urls": [],
            "tags": [],
            "raw_message": "[" + json.dumps(item, ensure_ascii=False) + "]",
            "text": "",
            "notification_text": "",
            "image_url": [],
            "action_text": ""
        }
        # Text module (module_id = 1)
        if module_id == 1:
            text = item["data"].get("text", "")
            module["text"] = text
            broadcast_text = text
            for param in item.get("parameters", []):
                url = param["data"].get("url", "")
                if url:
                    module["urls"].append(url)
                tags = param["data"].get(
                    "tag_list",
                )
                if tags:
                    module["tags"].append(tags)
            notification_text = item["data"].get("notification_text", "")
            if notification_text:
                module["notification_text"] = notification_text
        # Image carousel module (module_id = 9)
        elif module_id == 9:
            for content in item["data"]["contents"]:
                for hero_content in content["hero"]["contents"]:
                    url = hero_content.get("url", "")
                    if url:
                        module["image_url"].append(url)
                msg_text = content["hero"]["action"].get("text", "")
                if msg_text:
                    module["action_text"] = msg_text

            for param in item.get("parameters", []):
                url = param["data"].get("url", "")
                if url:
                    module["urls"].append(url)
                tags = param["data"].get(
                    "tag_list",
                )
                if tags:
                    module["tags"].append(tags)

            notification_text = item["data"].get("notification_text", "")
            if notification_text:
                module["notification_text"] = notification_text
        # Card module (module_id = 4)
        elif module_id == 4:
            body_contents = item["data"]["contents"]["body"]["contents"]
            module["text_title"] = body_contents[0].get("text", "")
            module["text_desc"] = body_contents[1].get("text", "")
            hero_url = item["data"]["contents"]["hero"].get("url", "")
            if hero_url:
                module["image_url"] = hero_url

            notification_text = item["data"].get("notification_text", "")
            if notification_text:
                module["notification_text"] = notification_text

            for footer_content in item["data"]["contents"]["footer"]["contents"]:
                action_label = footer_content["action"].get("label", "")
                if action_label:
                    if "action_label" not in module:
                        module["action_label"] = []
                    module["action_label"].append(action_label)
                action_text = footer_content["action"].get("text", "")
                if action_text:
                    if "action_text" not in module:
                        module["action_text"] = []
                    module["action_text"].append(action_text)
            for param in item.get("parameters", []):
                url = param["data"].get("url", "")
                if url:
                    module["urls"].append(url)
                tags = param["data"].get(
                    "tag_list",
                )
                if tags:
                    module["tags"].append(tags)
        # Imagemap module (module_id = 14)
        elif module_id == 14:
            body_contents = item["data"]["contents"]["body"]["contents"]
            for body_content in body_contents:
                if body_content["type"] == "image":
                    url = body_content.get("url", "")
                    if url:
                        module["image_url"] = url
                    if len(body_contents) > 2:
                        response = requests.get(url)
                        image = Image.open(BytesIO(response.content))
                        img_width, img_height = image.size
                elif body_content["type"] == "box" and len(body_contents) > 2:
                    width = int(
                        float(body_content["width"].replace("%", "")) / 100 * img_width
                    )
                    height = int(
                        float(body_content["height"].replace("%", ""))
                        / 100
                        * img_height
                    )
                    offset_top = int(
                        float(body_content["offsetTop"].replace("%", ""))
                        / 100
                        * img_height
                    )
                    offset_start = int(
                        float(body_content["offsetStart"].replace("%", ""))
                        / 100
                        * img_width
                    )
                    if "boxes" not in module:
                        module["boxes"] = []
                    module["boxes"].append([width, height, offset_top, offset_start])

            for param in item.get("parameters", []):
                url = param["data"].get("url", "")
                if url:
                    module["urls"].append(url)
                tags = param["data"].get(
                    "tag_list",
                )
                if tags:
                    module["tags"].append(tags)

            notification_text = item["data"].get("notification_text", "")
            if notification_text:
                module["notification_text"] = notification_text

        # Video module (module_id = 8)
        elif module_id == 8:
            video_url = item["data"]["video"]["originalContentUrl"]
            if video_url:
                module["video_url"] = video_url

            notification_text = item["data"].get("notification_text", "")
            if notification_text:
                module["notification_text"] = notification_text

            label = item["data"].get("externalLink", {}).get("label", "")
            if label:
                module["action_label"] = label

            for param in item.get("parameters", []):
                url = param["data"].get("url", "")
                if url:
                    module["urls"].append(url)
                tags = param["data"].get(
                    "tag_list",
                )
                if tags:
                    module["tags"].append(tags)
        modules.append(module)
    if broadcast_text:
        for module in modules:
            module["text"] = broadcast_text
    return modules
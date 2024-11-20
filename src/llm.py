import base64
import json
import os
import re
from collections import defaultdict
from io import BytesIO
from openai import OpenAI
import numpy as np
import pandas as pd
import requests
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from PIL import Image
from tenacity import retry, stop_after_attempt
from src.utils import *
# from dotenv import load_dotenv

# load_dotenv()




class LLMClient:
    def __init__(self, model : str = "gpt-4o", instruction : dict = None, api_key : str = None):
        api_key = "sk-xxx"
        self.llm = ChatOpenAI(model=model, api_key=api_key)
        self.audio_llm = OpenAI(api_key=api_key)
        self.instruction = instruction

    def getPrompt(self, module):
        prompts = []
        if module["id"] == 1:
            prompt = [
                {
                    "type": "text",
                    "text": "活動或商品標題:{name}, 活動或商品內容:{text} 你建議的標籤："
                }
            ]

            prompts.append(prompt)
        # Image carousel module (module_id = 9)
        elif module["id"] == 9:
            for image_url in module["image_url"]:
                prompt = [
                            {
                                "type": "text",
                                "text": "活動或商品標題:{name}\n活動或商品內容:{text}\n活動或商品互動按鈕:{action_text}\n 活動或商品圖片敘述:{image_desc} \n你建議的標籤：",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"{image_url}", "detail": "high"},
                            },
                        ]
                prompts.append(prompt)
        # Card module (module_id = 4)
        elif module["id"] == 4:
            for action_label in module["action_label"]:
                prompt = [
                            {
                                "type": "text",
                                "text": "活動或商品標題:{name}\n活動或商品名稱: {text_title}\n活動或商品內容: {text_desc}, {text}\n**活動或商品互動按鈕**:" + f"{action_label}" + "\n**活動或商品互動描述**: {action_text}\n 活動或商品圖片敘述:{image_desc} \n你建議的標籤：",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": "{image_url}", "detail": "high"},
                            },
                        ]
                prompts.append(prompt)
        # Imagemap module (module_id = 14)
        elif module["id"] == 14:
            if "boxes" in module:
                response = requests.get(module["image_url"])
                image = Image.open(BytesIO(response.content))
                for box in module["boxes"]:
                    cropped_image = get_cropped_image(image, box)
                    img64 = get_base64_image(cropped_image)
                    prompt = [
                                {
                                    "type": "text",
                                    "text": "活動或商品標題:{name}\n活動或商品內容:{text}\n 活動或商品圖片敘述:{image_desc} \n你建議的標籤：",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img64}",
                                        "detail": "high",
                                    },
                                },
                            ]
                    prompts.append(prompt)
            else:
                prompt = [
                            {
                                "type": "text",
                                "text": "活動或商品標題:{name}\n活動或商品內容:{text}\n 活動或商品圖片敘述:{image_desc} \n你建議的標籤：",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": "{image_url}", "detail": "high"},
                            }
                        ]
                prompts.append(prompt)
        elif module["id"] == 8:
            get_audio(module["video_url"])
            transcription = self.getTranscript("temp.mp3")
            prompt = [
                        {
                            "type": "text",
                            "text": "活動或商品標題:{name}, 活動或商品內容:{text}, 活動或商品影片內容:"+ f"{transcription}",
                        },
                    ]
            prompts.append(prompt)

        return prompts
    
    @retry(stop=stop_after_attempt(5))
    def path1(self, keywords, module, clean=False):
        prompts = self.getPrompt(module)
        results = []
        for prompt in prompts:
            chain = self.getChain(prompt, self.instruction["PATH1"], module)
            res = chain.invoke(input = {}, configurable={"llm_temperature": 1.0})
            if clean:
                res = text_clean(res)
                res = self.correctTag(res)
            results.append(res.split(","))
        return results

    @retry(stop=stop_after_attempt(5))
    def path2(self, module, clean=False):
        prompts = self.getPrompt(module)
        results = []
        for prompt in prompts:
            chain = self.getChain(prompt, self.instruction["PATH2"], module)
            res = chain.invoke(input = {}, configurable={"llm_temperature": 1.0})
            if clean:
                res = text_clean(res)
                res = self.correctTag(res)
            results.append(res.split(","))
        return results
    
    @retry(stop=stop_after_attempt(5))
    def path3(self, module, clean=False):
        prompts = self.getPrompt(module)
        results = []
        for prompt in prompts:
            chain = self.getChain(prompt, self.instruction["PATH3"], module)
            res = chain.invoke(input = {}, configurable={"llm_temperature": 1.8})
            if clean:
                res = text_clean(res)
                res = self.correctTag(res)
            results.append(res.split(","))
        return results
    
    def getChain(self, prompt, system_prompt, module):
        if len(prompt) == 1:
            template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", prompt),
            ])
            chain = template.partial(**module) | self.llm | StrOutputParser()
        elif len(prompt) == 2:
            text_prompt, image_prompt = prompt
            image_template = ChatPromptTemplate.from_messages([
                ("system", self.instruction["IMAGE"]),
                ("human", [image_prompt]),
            ])
            image_chain = image_template.partial(**module) | self.llm | StrOutputParser()
            text_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", [text_prompt]),
            ])

            chain = {'image_desc': image_chain} | text_template.partial(**module) | self.llm | StrOutputParser()
        return chain


    @retry(stop=stop_after_attempt(5))
    def getTranscript(self, audio_path):
        audio_file = open(audio_path, "rb")
        transcription = self.audio_llm.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        return transcription.text

    @retry(stop=stop_after_attempt(5))
    def getKeywords(self, history_tags):
        prompt = """
        過去用戶使用過的標籤:
        <歷史標籤>
        {history_tags}
        </歷史標籤>
        你產生的關鍵字：
        """
        template = ChatPromptTemplate.from_messages([
            ("system", self.instruction["HISTORY"]),
            ("human", prompt),
        ])
        chain = template | self.llm | StrOutputParser()
        prompt = {"history_tags": history_tags}
        return chain.invoke(prompt)

    @retry(stop=stop_after_attempt(5))
    def correctTag(self, tag_list):
        prompt = """
        用戶輸入的標籤:
        <用戶標籤>
        {tag_list}
        </用戶標籤>
        你的矯正後的標籤:
        """
        template = ChatPromptTemplate.from_messages([
            ("system", self.instruction["CORRECT"]),
            ("human", "紅心火龍果_水果,台南_地點,活動_醫美節,燒肉_食品,免運_促銷"),
            ("ai", "水果_紅心火龍果, 地點_台南, 活動_醫美節, 食品_燒肉, 促銷_免運"),
            ("user", prompt),
        ])
        chain = template | self.llm | StrOutputParser()
        prompt = {"tag_list": tag_list}
        return chain.invoke(prompt)

    def historyKeywords(self, history_tags, iteration=3):
        keywords = []
        for _ in range(iteration):
            keywords = keywords + self.getKeywords(history_tags).split(",")
        return np.unique(keywords)
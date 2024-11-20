from pydantic import BaseModel, ValidationError
from typing import List, Optional, Union
from fastapi import HTTPException

class ModuleData(BaseModel):
    id: int
    num: int
    name: str
    brand: str
    text: Optional[str] = None

class Text(ModuleData):
    """id = 1"""
    text: str

class ImageCarousel(ModuleData):
    """id = 9"""
    image_url: List[str]
    action_text: Optional[str] = ""

class Card(ModuleData):
    """id = 4"""
    action_label: List[str]
    text_title: Optional[str] = ""
    text_desc: Optional[str] = ""
    action_text: Optional[str] = ""
    image_url: str = ""

class Imagemap(ModuleData):
    """id = 14"""
    image_url: str
    boxes: Optional[List[List[int]]] = None

class Video(ModuleData):
    """id = 8"""
    video_url: str

def create_module(data: dict) -> ModuleData:
    id = data.get('id')
    if id == 1:
        return Text(**data)
    elif id == 4:
        return Card(**data)
    elif id == 8:
        return Video(**data)
    elif id == 9:
        return ImageCarousel(**data)
    elif id == 14:
        return Imagemap(**data)
    else:
        raise ValueError("Invalid ID")

async def get_module_data(module: dict) -> Union[Text, ImageCarousel, Card, Imagemap, Video]:
    try:
        return create_module(module)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class Response(BaseModel):
    tags: List[List[str]]

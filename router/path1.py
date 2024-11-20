from fastapi import APIRouter, Depends, HTTPException
from typing import Union
from src.llm import LLMClient
from .schema import *
import yaml
with open("./src/instruction.yaml", "r") as f:
    instructions = yaml.safe_load(f)
llm = LLMClient(instruction=instructions)
router = APIRouter(
    prefix="/path1",    
    tags=["tag"],
)

class Path1Module(ModuleData):
    keywords: List[str]

@router.post("/")
async def path1(data: Union[Text, ImageCarousel, Card, Imagemap, Video] = Depends(get_module_data)):
    res = llm.path1(data.model_dump())
    return Response(tags=res)

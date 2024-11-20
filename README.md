# FastAPI Marketing Content Tagging API

A FastAPI service that provides intelligent tagging for marketing content through three different paths, each with its own tagging strategy.

## Overview

This API processes marketing content (text, images, videos) and generates relevant tags using different strategies:

- **Path1**: Tag generation based on specific keywords
- **Path2**: Tag generation based on predefined marketing strategies
- **Path3**: Creative tag generation with higher variability

## Installation

```bash
# Install dependencies using pipenv
pipenv install

# Start the server
uvicorn main:app --reload
```

Required Python version: 3.10 (See Pipfile for details)

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. POST /path1
Generate tags based on specific keywords.

#### 2. POST /path2
Generate tags based on marketing strategies focusing on:
- Product preferences and brands
- Audience characteristics
- LINE official account interaction

#### 3. POST /path3
Generate creative tags with higher variability.

## Request Format

All endpoints accept POST requests with the following content types:
- Text
- Image Carousel
- Card
- Imagemap
- Video

### Example Request

```json
{
  "id": 1,
  "num": 5,
  "brand": "愛上新鮮",
  "name": "77-240725-燒肉片",
  "text": "大包燒肉片！免調味，開袋就下鍋！鹹甜醬汁濃濃日式風味..."
}
```

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Content type identifier (1=Text, 4=Card, 8=Video, 9=Image Carousel, 14=Imagemap) |
| num | integer | Number of tags to generate |
| brand | string | Brand name |
| name | string | Content name/identifier |
| text | string | Main content text |

### Additional Parameters by Content Type

#### Card (id: 4)
- action_label: string[]
- image_url: string
- text_desc: string
- text_title: string

#### Video (id: 8)
- video_url: string
- notification_text: string
- action_text: string

#### Image Carousel (id: 9)
- image_url: string[]
- action_text: string

## Response Format

```json
{
  "tags": [
    ["tag1_attribute1", "tag2_attribute2", "tag3_attribute3"]
  ]
}
```

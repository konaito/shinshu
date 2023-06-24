from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pytz

cred = credentials.Certificate(
    './to/calender-e9496-firebase-adminsdk-jrt2f-6156b769a6.json')
firebase = firebase_admin.initialize_app(cred)
db = firestore.client(firebase)

openai.api_key = os.getenv("OPENAI_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

weekdays_jp = ['月', '火', '水', '木', '金', '土', '日']

# 現在の日付を取得
now = datetime.now(pytz.timezone('Asia/Tokyo'))


class ChatMessage(BaseModel):
    message: str = ""
    userid: str = ""


def process_add_schedule(data):
    data = {
        "title": data["title"],
        "body": data["body"],
        "time": data["time"],
        "date": data["date"],
        "startTime": data["startTime"],
        "written": datetime.now(pytz.timezone('Asia/Tokyo'))
    }
    userid=data["userid"]
    doc_ref = db.collection(u'calenAll').document("tasks").collection(f"{userid}").document()
    doc_ref.set(data)
    return doc_ref.id

@app.get("/")
def index():
    return "returnschedule"


@app.post("/inputForAI")
def ask_chat_gpt(data: ChatMessage):
    message = data.message
    userid=data.userid
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[

            {
                "role": "system",
                "content": "あなたはメッセージやメールから重要な情報を抽出する高度なAIです。具体的には、メッセージから日付、時間、タイトル、およびイベントの概要を抽出して、Pythonの辞書形式で出力します。"
            },
            {
                "role": "system",
                "content": '日付は必ず抽出し、MM月DD日の形式で出力します。時間は可能な場合に抽出し、HH:MMの形式で出力します。開始時間は必ず抽出し、時間情報から開始時間を抽出します、含まれていない場合は00:00を出力します。タイトルは必ず抽出します。そして、概要情報には、可能な限り多くの詳細（人、場所、URLなど）を含めます。'
            },
            {
                "role": "system",
                "content": 'データはこの形式で返して下さい。{"date":String(MM月DD日),"time":String(任意だが、HH時MM分よりもHH:MM),"startTime":String(HH:MM),"title":String,"body":String}'
            },
            {
                "role": "system",
                "content": "ちなみに、今日は{}年{}月{}日({})です。今週の水曜日などの情報はこれから類推して下さい。".format(now.year, now.month, now.day, weekdays_jp[now.weekday()])
            },
            {
                "role": "user",
                "content": message,
            }
        ],
    )
    try:
        response = completion.choices[0].message.content
        response = "{" + response.split("{")[1].split("}")[0] + "}"
        data_dict = json.loads(response)
        data_dict["userid"]=userid
        docID=process_add_schedule(data_dict)
        data_dict["docID"]=docID
        return data_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
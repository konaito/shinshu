import openai
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
now = datetime.now(pytz.timezone('Asia/Tokyo'))

def process_add_schedule(data):
    data = {
        "title": data["title"],
        "body": data["body"],
        "time": data["time"],
        "date": data["date"],
        # datetimeという名前のdateとtimeを合わせてdatetime型にしたパラメータも追加しておく
        "startTime": data["startTime"],
        "written": now
    }
    userid=data["userid"]
    doc_ref = db.collection(u'calenAll').document("tasks").collection(f"{userid}").document()
    doc_ref.set(data)
    return doc_ref.id

def extract_all_data(userid):
    doc_ref = db.collection(u'calenAll').document("tasks").collection(f"{userid}")
    docs = doc_ref.stream()
    
    data = []
    for doc in docs:
        data.append(doc.to_dict())
    
    return data
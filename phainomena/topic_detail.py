import pymongo
from download.eastmoney.stock import db


def match_topic_detail(topics):
    stocks = db.Stock.find(
        projection=["code", "name", "topic", "topic_detail"],
    )
    for st in stocks:
        for topic_detail in st["topic_detail"]:
            for t in topics:
                if t in topic_detail["content"]:
                    print(st["code"], st["name"])
        for topic in st.get("topic", []):
            for t in topics:
                if t in topic["name"] or t in topic["reason"]:
                    print(st["code"], st["name"])


if __name__ == "__main__":
    topics = ["快手"]
    match_topic_detail(topics)

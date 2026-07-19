from textblob import TextBlob

def analyze_sentiment(text: str) -> dict:
    """分析文本情绪"""
    if not text:
        return {"polarity": 0.0, "subjectivity": 0.0}
    
    analysis = TextBlob(text)
    return {
        "polarity": analysis.sentiment.polarity,
        "subjectivity": analysis.sentiment.subjectivity
    }

# 测试代码
if __name__ == "__main__":
    print(analyze_sentiment("今天天气真好，我很开心"))
    print(analyze_sentiment("今天心情不太好"))
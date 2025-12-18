import requests
from bs4 import BeautifulSoup

def get_last_messages(channel_name="aguasantiago", n=15):
    url = f"https://t.me/s/{channel_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.select('div.tgme_widget_message_wrap')
    
    if not messages:
        return []

    result = []
    for msg in messages[-n:]:
        text_div = msg.select_one('div.tgme_widget_message_text')
        text = text_div.get_text(separator="\n").strip() if text_div else ""
        
        time_tag = msg.select_one('time.time')
        datetime_str = time_tag.get('datetime') if time_tag else None
        
        result.append({
            "text": text,
            "datetime": datetime_str
        })

    return result

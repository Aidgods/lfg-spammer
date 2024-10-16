import requests
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import random
session_ids = []

def read_tokens(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

session_ids = []
current_token_index = 0
consecutive_401_errors = 0
max_consecutive_401_errors = 10
tokens = read_tokens('tokens.txt')
delay = input("what do you want the delay to be? ")
threads = input("How many threads do you want? (i suggest 50 if you want a flooder and 5 if you want it to be normal) ")
text =  input("What do you want as the text? ")
threads = int(threads)

def worker():
    global session_ids, current_token_index, consecutive_401_errors, tokens
    lock = threading.Lock()
    
    for _ in range(5000):  
        try:
            with lock: 
                session_id = str(uuid4())
                session_ids.append(session_id)
            
            payload = {
                "properties": {
                    "system": {
                        "joinRestriction": "followed",
                        "readRestriction": "followed",
                        "description": {
                            "locale": "en-US",
                            "text": text
                        },
                        "searchHandleVisibility": "xboxlive"
                    }
                },
                "members": {
                    "me": {
                        "constants": {
                            "system": {
                                "initialize": True,
                                "xuid": "2535436196910107"
                            }
                        }
                    }
                },
                "roleTypes": {
                    "lfg": {
                        "roles": {
                            "confirmed": {
                                "target": 15
                            }
                        }
                    }
                }
            }

            headers = {
                'x-xbl-contract-version': '107',
                'authorization': random.choice(tokens),
                'User-Agent': 'okhttp/3.12.1',
                'X-UserAgent': 'Android/191121000 SM-A715F.AndroidPhone'
            }
            scid = "93ac0100-efec-488c-af85-e5850ff4b5bd"
            response = requests.put(f'https://sessiondirectory.xboxlive.com/serviceconfigs/{scid}/sessiontemplates/global(lfg)/sessions/{session_id}', json=payload, headers=headers)
            
            if response.status_code in [401, 403]:
                consecutive_401_errors += 1
                if consecutive_401_errors >= max_consecutive_401_errors:
                    current_token_index = (current_token_index + 1) % len(tokens)
                    consecutive_401_errors = 0
            else:
                consecutive_401_errors = 0
            
            # Change color based on status code
            if response.status_code in [201, 204]:
                print("\033[92mSent request for session ID:", session_id, "\033[0m")
            elif response.status_code in [401, 403]:
                print("\033[91mToken is dead\033[0m")

            payload2 = {
                "type": "search",
                "sessionRef": {
                    "scid": scid,
                    "templateName": "global(lfg)",
                    "name": session_id
                },
                "searchAttributes": {
                    "tags": [
                        "micrequired",
                        "textchatrequired"
                    ],
                    "achievementIds": [],
                    "locale": "en"
                }
            }

            response2 = requests.post('https://sessiondirectory.xboxlive.com/handles?include=relatedInfo', json=payload2, headers=headers)
            
            if len(session_ids) >= 2:
                with lock:  
                    oldest_session_id = session_ids.pop(0)
                time.sleep(delay)  
                
                delete_url = f'https://sessiondirectory.xboxlive.com/serviceconfigs/{scid}/sessiontemplates/global(lfg)/sessions/{oldest_session_id}/members/me'
                delete_response = requests.delete(delete_url, headers=headers)
            
        except requests.exceptions.RequestException as error:
            print('Error:', error)

def main():
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for _ in range(5000):  
            executor.submit(worker)

if __name__ == "__main__":
    main()

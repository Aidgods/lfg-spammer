import requests
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import threading
import time

session_ids = []
def read_tokens(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]


session_ids = []
current_token_index = 0
consecutive_401_errors = 0
max_consecutive_401_errors = 10
tokens = read_tokens('tokens.txt')
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
                            "text": "join discordgg/shadowgarden for the best party tools"
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
                'authorization': tokens[current_token_index],
                'User-Agent': 'okhttp/3.12.1',
                'X-UserAgent': 'Android/191121000 SM-A715F.AndroidPhone'
            }
            scid = "00000000-0000-0000-0000-00006cfa0c1e"
            response = requests.put(f'https://sessiondirectory.xboxlive.com/serviceconfigs/{scid}/sessiontemplates/global(lfg)/sessions/{session_id}', json=payload, headers=headers)
            
            if response.status_code in [401, 403]:
                consecutive_401_errors += 1
                if consecutive_401_errors >= max_consecutive_401_errors:
                    current_token_index = (current_token_index + 1) % len(tokens)
                    consecutive_401_errors = 0
            else:
                consecutive_401_errors = 0
            print('PUT Status Code:', response.status_code)
            print('PUT Data:', response.json())
            
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
            print('POST Status Code:', response2.status_code)
            print('POST Data:', response2.json())
            
            if len(session_ids) >= 2:
                with lock:  
                    oldest_session_id = session_ids.pop(0)
                time.sleep(10)  
                
                delete_url = f'https://sessiondirectory.xboxlive.com/serviceconfigs/{scid}/sessiontemplates/global(lfg)/sessions/{oldest_session_id}/members/me'
                delete_response = requests.delete(delete_url, headers=headers)
                print('DELETE Status Code:', delete_response.status_code)
                print('DELETE Data:', delete_response.json())
            
        except requests.exceptions.RequestException as error:
            print('Error:', error)

def main():
    with ThreadPoolExecutor(max_workers=300) as executor:
        for _ in range(5000):  
            executor.submit(worker)

if __name__ == "__main__":
    main()

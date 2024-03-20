import requests
import logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(message)s")

gpt_url = 'http://localhost:1234/v1/chat/completions'
headers = {"Content-Type": "application/json"}
temperature = 1
max_tokens = 200

system_content = "Ты — дружелюбный помощник и умеешь поддерживать диалог, отвечай кратко"


def ask_chatgpt(message):
    resp = requests.post(
        gpt_url,
        headers=headers,

        json={
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    )

    answer = None

    if resp.status_code == 200:
        json_data = resp.json()
        if "choices" in json_data and json_data["choices"]:
            answer = json_data["choices"][0]["message"]["content"]
            logging.debug(f"Got a response from GPT: {answer}")
        else:
            logging.error(f"No response from GPT: {json_data}")
    else:
        logging.error(
            f"Bad answer from GPT server, response code: {str(resp.status_code)}"
        )

    return answer

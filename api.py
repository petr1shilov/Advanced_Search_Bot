import pandas as pd
from openai import OpenAI
import config


class AnswerApi:
    def __init__(self, api_key=config.api_key, model="gpt-4o"):
        self.api_key = api_key
        self.model = model

        self.client = OpenAI(api_key=self.api_key)
        self.kwargs = {
            "temperature": 0.2,
            "max_tokens": 200,
            "top_p": 0.0,
            "frequency_penalty": 0.0,
            "presence_penalty": -0.5,
        }

    def api_answer(self, doc_path: str, key_word: str):
        df = pd.read_excel(f"files/{doc_path}")
        df = df[["Authors", "Title", "Abstract"]]
        responce_col = []
        for i in range(len(df)):
            text = f"{df.iloc[i]['Title']}\n{df.iloc[i]['Abstract']}"
            system_prompt = f"Ты опытный учений.\nТебе нужно проанализиовать текст, где материалы {key_word} упоминаются в контексте.\nНужно понять, играют ли эти материлы {key_word} ключевую роль и являются ли материалы {key_word} основными в исследовани.\n"
            user_prompt = f'{text}.\nОтветь "да" или "нет"'

            responce = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            responce_col.append(responce.choices[0].message.content)

        df["ModelAnswer"] = responce_col

        df.to_excel(f"files/{doc_path[:-5]}_response.xlsx")

        return True

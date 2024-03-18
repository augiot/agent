"""
适配新版openai包的接口
"""

import os
import openai
from openai import OpenAI

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://10.20.216.187:8020/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "xxx")

# openai.api_type = "azure"
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY

MODEL_NAME = "/mnt/user2/workspace/model/Qwen-7B-Chat"
temperature = 0

client = OpenAI(
    api_key=openai.api_key,
    base_url=openai.api_base
)


def llm(query,history=[],user_stop_words=[]):    # 调用api_server

    try:
        messages=[{'role':'system','content':'You are a helpful assistant.'}]
        for hist in history:
            messages.append({'role':'user','content':hist[0]})
            messages.append({'role':'assistant','content':hist[1]})
        messages.append({'role':'user','content':query})

        # 2.模型推理
        completion = client.chat.completions.create(
            model = MODEL_NAME,
            messages = messages,
            stream=False,
            temperature = temperature,
            stop = ["<|im_end|>","<|endoftext|>"] + user_stop_words
        )
        content = completion.choices[0].message.content
        # print(resp)
        # content=resp.get("Data", {}).get("Choices", [])[0].get("Message", {}).get("Content")
        return content
    except Exception as e:
        return str(e)

if __name__=="__main__":
    prompt = "你好！"
    print(llm(prompt))
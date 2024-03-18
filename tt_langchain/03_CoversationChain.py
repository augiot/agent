import os
from langchain import OpenAI, ConversationChain


API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY

llm = OpenAI(temperature=0)
conversation = ConversationChain(llm=llm, verbose=True)
output = conversation.predict(input="Hi there!")
print(output)
output = conversation.predict(input="1—1=")
print(output)
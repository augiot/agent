"""
https://blog.csdn.net/shebao3333/article/details/135989409
"""

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
# from text2sql import DQuestionChat
load_dotenv()
from langchain_openai import ChatOpenAI

import pandas as pd
from langchain.vectorstores import DeepLake
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders.csv_loader import CSVLoader

# 1.定义LLM
openai_api_key="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"
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key = openai_api_key)

# print(llm.invoke("hello"))

# 2.创建工具

# 2.1 实例化 OpenAIEmbeddings 以用于从文档上下文创建嵌入：
# instantiate OpenAIEmbeddings to use to create embeddings from document context
embeddings = OpenAIEmbeddings(deployment="EMBEDDING_DEPLOYMENT_NAME", chunk_size=16)

# 2.2 实例化 CSV 加载器并加载食品评论，并将评论链接作为源：
# instantiate CSV loader and load food reviews with review link as source
loader = CSVLoader(file_path='final_data.csv', csv_args={
        "delimiter": ",",
}, encoding='utf-8', source_column='review_link')
data = loader.load()

# 使用纬度和经度值扩充数据的元数据，这是我们稍后的工具之一所需要的：
# augment data's metadata with lat and long values; this is needed for one of our tools later on
df = pd.read_csv("final_data.csv", index_col=False)
 
df_lat = df.lat.values.tolist()
df_long = df.long.values.tolist()
 
for lat, long, item in zip(df_lat, df_long, data):
    item.metadata["lat"] = lat
    item.metadata["long"] = long

# 创建deeplake数据库：
# create deeplake db
db = DeepLake(
    dataset_path="./my_deeplake/", embedding=embeddings, overwrite=True
)
db.add_documents(data)

# 2.3 数据库检索器






from langchain_community.chat_models import ChatOpenAI
from langchain.chains import create_sql_query_chain
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

openai_api_key="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"

chain = create_sql_query_chain(ChatOpenAI(temperature=0, openai_api_key=openai_api_key), db)
response = chain.invoke({"question":"有多少员工"})
print(response)
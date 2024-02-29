from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
# from text2sql import DQuestionChat
load_dotenv()
from langchain_openai import ChatOpenAI

# llm = DQuestionChat(temperature=0)
openai_api_key="sess-f8mdgXPs7GzCop5fKZN0R6GLKmEW4qRAvzS2SBIT"
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key = openai_api_key)

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
agent_executor.invoke({"input": "列出每个国家的总销售额。哪个国家的客户消费最多？"})

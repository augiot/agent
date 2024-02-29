from langchain_community.utilities import SQLDatabase
from langchain.llms import OpenAI
from langchain_experimental.sql import SQLDatabaseChain

db = SQLDatabase.from_uri("sqlite:///Chinook.db")
openai_api_key="sess-f8mdgXPs7GzCop5fKZN0R6GLKmEW4qRAvzS2SBIT"

llm = OpenAI(temperature=0, verbose=True, openai_api_key=openai_api_key)
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

db_chain.run("有多少员工？")

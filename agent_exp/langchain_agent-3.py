from langchain.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

openai_api_key="sess-f8mdgXPs7GzCop5fKZN0R6GLKmEW4qRAvzS2SBIT"

llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name='gpt-3.5-turbo')

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

question = "帮我查询用户对应订单和订单中产品的信息"
agent_executor.run(question)


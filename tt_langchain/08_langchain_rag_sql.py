import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


# 准备llm key
import os
API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY
OPENAI_API_BASE='http://10.20.216.187:8020/v1'
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

# "/mnt/user2/workspace/model/Qwen-7B-Chat"



# 1.构建一个知识库内容
few_shots = {
    "How many employees are there?": "SELECT COUNT(*) FROM employee;",
    "在订单表中，连续两个月都下订单的客户有哪些?":"SELECT DISTINCT a.'CustomerId', a.'FirstName', a.'LastName' FROM 'Customer' a JOIN 'Invoice' b ON a.'CustomerId' = b.'CustomerId' JOIN 'Invoice' c ON a.'CustomerId' = c.'CustomerId' AND ((strftime('%Y-%m', b.'InvoiceDate') = strftime('%Y-%m', date(c.'InvoiceDate', '-1 month'))) OR (strftime('%Y-%m', b.'InvoiceDate') = strftime('%Y-%m', date(c.'InvoiceDate', '+1 month'))))",
    "同一客户的订单中连续两笔订单金额都大于1的客户有哪些?":"SELECT DISTINCT c.'CustomerId', c.'FirstName', c.'LastName' FROM 'Invoice' a JOIN 'Invoice' b ON a.'CustomerId' = b.'CustomerId' AND a.'InvoiceId' < b.'InvoiceId' JOIN 'Customer' c ON a.'CustomerId' = c.'CustomerId' WHERE a.'Total' > 1 AND b.'Total' > 1 AND NOT EXISTS ( SELECT 1 FROM 'Invoice' i WHERE i.'CustomerId' = a.'CustomerId' AND i.'InvoiceId' > a.'InvoiceId' AND i.'InvoiceId' < b.'InvoiceId')",
}

# 2.创建检索器
from langchain.schema import Document
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = OpenAIEmbeddings()

# 此处为手动构造知识库，而没有用到文本切分
few_shot_docs = [
    Document(page_content=question, metadata={"sql_query": few_shots[question]})
    for question in few_shots.keys()
]
vector_db = FAISS.from_documents(few_shot_docs, embeddings)
retriever = vector_db.as_retriever()

# 3.创建自定义工具
# from langchain_community.agent_toolkits import create_retriever_tool
from langchain.agents.agent_toolkits import create_retriever_tool

# description注意要加 in Chinese,使用中文检索,切记!
tool_description = """
This tool will help you understand similar examples to adapt them to the user question in Chinese.
Input to this tool should be the user question.
"""

retriever_tool = create_retriever_tool(
    retriever, name="sql_get_similar_examples", description=tool_description
)
custom_tool_list = [retriever_tool]

# 4.创建代理
from langchain.agents import AgentType, create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase

database = 'mydb'
db_port = 8012
db_host = '10.20.216.187'
dbPassword = 'postgres'


# Initialize database
# db = SQLDatabase.from_uri("sqlite:///xxx/Chinook.db")
db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://postgres:{dbPassword}@{db_host}:{db_port}/{database}",
)
# db = SQLDatabase.from_uri("sqlite:///xxxx/Chinook.db")
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# 注意要加 in Chinese,使用中文检索,切记!
custom_suffix = """
I should first get the similar examples in Chinese I know.
If the examples are enough to construct the query, I can build it.
Otherwise, I can then look at the tables in the database to see what I can query.
Then I should query the schema of the most relevant tables
"""

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    extra_tools=custom_tool_list,
    suffix=custom_suffix,
)

# 5. 执行提问：
agent.run("连续两个月都有下订单的客户有哪些?")
# agent.run("找出哪些客户连续两个月都有下订单?")









from langchain.utilities import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain import hub

import os
API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY
OPENAI_API_BASE='http://10.20.216.187:8020/v1'
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE
MODEL_NAME =  "/mnt/user2/workspace/model/Qwen-7B-Chat" # "gpt-3.5-turbo"



database = 'mydb'
db_port = 8012
db_host = '10.20.216.187'
dbPassword = 'postgres'


# Initialize database
# db = SQLDatabase.from_uri("sqlite:///xxx/Chinook.db")
db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://postgres:{dbPassword}@{db_host}:{db_port}/{database}",
)

# Pull down prompt
prompt = hub.pull("rlm/text-to-sql")
# Initialize model
# model = ChatOpenAI()
# model = ChatOpenAI(model_name=MODEL_NAME,temperature=0.0)
model = ChatOpenAI(model_name=MODEL_NAME,temperature=0.0)

# few shot examples
few_shots = {
    "List all artists.": "SELECT * FROM artists;",
    "Find all albums for the artist 'AC/DC'.": "SELECT * FROM albums WHERE ArtistId = (SELECT ArtistId FROM artists WHERE Name = 'AC/DC');",
    "连续两个月都下订单的客户有哪些?":"SELECT DISTINCT a.'CustomerId', a.'FirstName', a.'LastName' FROM 'Customer' a JOIN 'Invoice' b ON a.'CustomerId' = b.'CustomerId' JOIN 'Invoice' c ON a.'CustomerId' = c.'CustomerId' AND ((strftime('%Y-%m', b.'InvoiceDate') = strftime('%Y-%m', date(c.'InvoiceDate', '-1 month'))) OR (strftime('%Y-%m', b.'InvoiceDate') = strftime('%Y-%m', date(c.'InvoiceDate', '+1 month'))))"
}

# Create chain with LangChain Expression Language
inputs = {
    "table_info": lambda x: db.get_table_info(),
    "input": lambda x: x["question"],
    "few_shot_examples": lambda x: few_shots,
    "dialect": lambda x: db.dialect,
}
sql_response = (
    inputs
    | prompt
    | model.bind(stop=["\nSQLResult:","<|im_end|>"])
    | StrOutputParser()
)

# Call with a given question
print(sql_response.invoke({"question": "连续两个月都下订单的客户有哪些?"}))

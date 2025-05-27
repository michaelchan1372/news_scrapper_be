import os
from langchain_ollama import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.database import fetch_pages_text, get_articles_for_summarize, saveSummary

ENABLE_OLLAMA = os.getenv('ENABLE_OLLAMA')
DEFAULT_MODEL = "llama3.3:70b-instruct-q4_0"

def init_llm():
    if ENABLE_OLLAMA == "1":
        llm = ChatOllama(model=DEFAULT_MODEL)
        return llm
    else:
        return None
    
def test():
    llm = init_llm()
    
    messages = [
    ("system", "You are a helpful news analysts who summarize the given news articles."),
    ("human", "I love programming."),
    ]

    response = llm.invoke(messages)
    print(response.content)

async def summary():
    if ENABLE_OLLAMA == "1":
        news_article_groups = get_articles_for_summarize()
        try:
            for news_article_group in news_article_groups:
                ni_ids = news_article_group["ni_ids"]
                texts = fetch_pages_text(ni_ids)
                llm = init_llm()
                messages = []
                messages.append(("system", "You are a helpful news analysts who summarize the given news articles searched with some keyword."))
                article_concat = ""
                for text in texts:
                    article_concat = article_concat + text + "\nnext article:\n"
                messages.append(("human", "Below are the news to summarize, please ignore some irelevant information that are irrelevant to the keywords. If the news article is totally irrelevant, please reply [NOT RELEVANT]" +
                "I only need max two sentence sentences from you and the keyword is " + news_article_group["keyword"] + ": \n\n" + article_concat))
                response = llm.invoke(messages)
                print(response)
                news_article_group["summary"] = response.content
                news_article_group["model_name"] = DEFAULT_MODEL
                news_article_group["input_tokens"] = response.usage_metadata["input_tokens"]
                news_article_group["output_tokens"] = response.usage_metadata["output_tokens"]
                saveSummary(news_article_group)
        except Exception as e:
            print(news_article_group["ni_ids"])
    
    
    
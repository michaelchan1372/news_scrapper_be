import os
from langchain_ollama import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.database import fetch_pages_summary, fetch_pages_text, get_daily_summarize_article, get_summarize_article, save_summary, save_summary_daily

ENABLE_OLLAMA = os.getenv('ENABLE_OLLAMA')
DEFAULT_MODEL = "llama3.3:70b-instruct-q4_0"

def init_llm():
    if ENABLE_OLLAMA == "1":
        llm = ChatOllama(model=DEFAULT_MODEL,  num_ctx=4096)
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

async def daily_article_summary():
    if ENABLE_OLLAMA == "1":
        news_article_groups = get_daily_summarize_article()
        total = str(len(news_article_groups))
        finished = 0
        for news_article_group in news_article_groups:
            try:
                ni_ids = news_article_group["ni_ids"]
                print("starting daily summary of " + ni_ids)
                # to do: change this function
                texts = fetch_pages_summary(ni_ids)
                print(texts)
                if len(texts) != 0:
                    llm = init_llm()
                    messages = []
                    print("getting daily summary for ids: " + ni_ids)
                    messages.append(("system", "You are a helpful news analysts who summarize a list of news summary into one."))
                    article_concat = ""
                    for text in texts:
                        article_concat = article_concat + text + "\nnext article:\n"
                    messages.append(("human", "Below are the news summary for you to summarize, they should be related to some keywords. If the news article is totally irrelevant, please reply [NOT RELEVANT]" +
                    "I only need max two sentence sentences from you and the keyword is " + news_article_group["keyword"] + ": \n\n" + article_concat))
                    response = llm.invoke(messages, config={"max_tokens": 1024})
                    finished = finished + 1
                    print("Finished AI daily summary for " + str(ni_ids) + ":" + str(finished) + "/" + total)
                    news_article_group["summary"] = response.content
                    news_article_group["model_name"] = DEFAULT_MODEL
                    news_article_group["input_tokens"] = response.usage_metadata["input_tokens"]
                    news_article_group["output_tokens"] = response.usage_metadata["output_tokens"]
                    save_summary_daily(news_article_group)
                else:
                    print("summary of all aritcles are not finished")
            except Exception as e:
                print(e)
                print(news_article_group["ni_ids"])

async def article_summary():
    if ENABLE_OLLAMA == "1":
        news_articles = get_summarize_article()
        total = str(len(news_articles))
        finished = 0
        print(total + " of articles require summary")

        for news_article in news_articles:
            try:
                ni_id = news_article["ni_id"]
                texts = fetch_pages_text(ni_id)
                messages = []
                messages.append(("system", "You are a helpful news analysts who summarize the give article."))
                article_concat = ""
                for text in texts:
                    article_concat = text
                messages.append(("human", "Below are the new article to summarize, please ignore some irelevant information that are irrelevant to the keywords. If the news article is totally irrelevant, please reply [NOT RELEVANT]" +
                "The title of the article is " +  news_article["title"] + "I only need max two sentence sentences from you and the keyword is " + news_article["keyword"] + ": \n\n" + article_concat))
                llm = init_llm()
                print("Getting AI response for " + str(ni_id))
                response = llm.invoke(messages, config={"max_tokens": 1024})
                finished = finished + 1
                print("Finished AI response " + str(ni_id) + ":" + str(finished) + "/" + total)
                news_article["summary"] = response.content
                news_article["model_name"] = DEFAULT_MODEL
                news_article["input_tokens"] = response.usage_metadata["input_tokens"]
                news_article["output_tokens"] = response.usage_metadata["output_tokens"]
                save_summary(news_article)
            except Exception as e:
                print(e)
                print(news_article["ni_id"])
    
    
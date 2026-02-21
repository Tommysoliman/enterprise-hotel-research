import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# =====================================================
# MUST BE FIRST STREAMLIT COMMAND
# =====================================================
st.set_page_config(
    page_title="Enterprise Research Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# DARK MODE STYLING
# =====================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    section[data-testid="stSidebar"] {
        background-color: #161B22;
    }

    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
    }

    .stTextInput>div>div>input {
        background-color: #1E2228;
        color: white;
    }

    .stTextArea textarea {
        background-color: #1E2228;
        color: white;
    }

    .stMarkdown, .stText {
        color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD API KEY
# =====================================================
load_dotenv(r"C:\Users\tommy\OneDrive\Desktop\Agentic ai\Key.env")

# =====================================================
# TITLES
# =====================================================
st.title("Hii Toots , I'm your AI Agent 🤖🧠")
st.subheader("Mr Tommy says Hello ")
st.title("Enterprise News Agent (Enterprise Only)")

# =====================================================
# LLM
# =====================================================
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# =====================================================
# ENTERPRISE TOOL
# =====================================================
@tool
def enterprise_search_tool(query: str) -> str:
    """Search up to 40 Enterprise Egypt articles matching the query."""

    base_url = "https://enterpriseam.com/egypt/"
    articles = []
    collected_links = set()

    page = 1
    MAX_ARTICLES = 40
    MAX_PAGES = 20

    while len(articles) < MAX_ARTICLES and page <= MAX_PAGES:

        if page == 1:
            search_url = f"{base_url}?s={query.replace(' ', '+')}"
        else:
            search_url = f"{base_url}page/{page}/?s={query.replace(' ', '+')}"

        try:
            response = requests.get(search_url, timeout=10)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")

            for link_tag in soup.select("article h2 a, .entry-title a"):
                link = link_tag.get("href")
                if not link or link in collected_links:
                    continue

                if "/egypt/" not in link:
                    continue

                collected_links.add(link)
                title = link_tag.get_text(strip=True)

                try:
                    article_response = requests.get(link, timeout=10)
                    article_soup = BeautifulSoup(article_response.text, "html.parser")
                    paragraphs = article_soup.select("article p")
                    content = "\n".join([p.get_text() for p in paragraphs])
                except Exception:
                    content = "Failed to scrape article."

                articles.append(
                    f"TITLE: {title}\nURL: {link}\nCONTENT:\n{content[:6000]}"
                )

                if len(articles) >= MAX_ARTICLES:
                    break

            page += 1

        except Exception:
            break

    if not articles:
        return "No relevant articles found."

    return "\n\n".join(articles)

# =====================================================
# AGENT SETUP
# =====================================================
tools = [enterprise_search_tool]
agent = create_react_agent(llm, tools)

# =====================================================
# SEARCH SECTION
# =====================================================
query = st.sidebar.text_input(
    "Search Enterprise Website",
    value="hotel expansion Egypt 2025"
)

if st.sidebar.button("🔍 Search Enterprise"):
    with st.spinner("Researching Enterprise articles..."):
        try:
            result = agent.invoke({
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
Use the enterprise_search_tool to search Enterprise Egypt articles.

Search query: {query}

Extract:
1. Title
2. Key entities involved (companies, people, projects, locations)
3. Main announcement or development
4. Dates mentioned
4. Financial figures (if any)
6. Strategic impact / sector relevance
7. Source link

Only use Enterprise website data.
Return results in structured format.
"""
                    }
                ]
            })

            final_answer = result["messages"][-1].content

            st.session_state["research_content"] = final_answer
            st.session_state["qa_answer"] = None

        except Exception as e:
            st.error(f"Error occurred: {e}")

# =====================================================
# DISPLAY RESEARCH
# =====================================================
if "research_content" in st.session_state:
    st.subheader("📰 Enterprise Research Results")
    st.write(st.session_state["research_content"])

# =====================================================
# Q&A SECTION
# =====================================================
st.markdown("---")
st.header("💬 Ask Questions About the Research")

if "research_content" not in st.session_state:
    st.info("Run a search first to enable Q&A.")
else:
    user_question = st.text_input("Ask a question about the results:")

    if st.button("Ask Question"):
        with st.spinner("Analyzing..."):
            qa_response = llm.invoke([
                {
                    "role": "system",
                    "content": "Only answer using the provided research content. Do not invent information."
                },
                {
                    "role": "user",
                    "content": f"""
Research Data:

{st.session_state['research_content']}

Question:
{user_question}
"""
                }
            ])

            st.session_state["qa_answer"] = qa_response.content

    if st.session_state.get("qa_answer"):
        st.subheader("📌 Answer")
        st.write(st.session_state["qa_answer"])

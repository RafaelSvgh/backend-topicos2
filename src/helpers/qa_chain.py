from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def setup_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    template = """Eres un vendedor de una tienda de ropa virtual. 
    Responde a la pregunta del usuario basándote en el siguiente contexto y en el historial de conversación.
    Si no sabes la respuesta, simplemente di que no lo sabes, no intentes inventar una respuesta.

    Contexto: {context}
    
    Pregunta: {question}"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    qa_chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return qa_chain
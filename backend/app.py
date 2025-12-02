from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_ollama import OllamaEmbeddings  # (not used, safe to remove if unused)
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import pandas as pd

load_dotenv()


NVIDIA_API_KEY = os.getenv("nvidia_api_key")
db_folder_name = "vector_store"

prompt = """
You are an AI assistant for Kerala police Website. You are created for assisting users in finding information on the Kerala police Website.

There is a vector database that contains the information from the Kerala police Website. When a user asks a question, give a brief reply by assessing the retrieved information attached with the question
from the vectordb.

If you cannot find any information or retrievals, you will respond with "I'm sorry, I don't know the answer to that question".

You will always respond in a polite and professional manner.
Analyze each context from retrieved information and provide a detailed answer to the user's question.

User Question: {question}

Retrieved Information: {context}
Your Answer:

Your answer should be very brief and concise.
As streaming is enabled, please respond in a streaming manner.
Dont include any words other than the answer in your response.
"""

prompt_template = PromptTemplate(template=prompt)


embeddings = NVIDIAEmbeddings(
    model="nvidia/llama-3.2-nemoretriever-300m-embed-v2",
    api_key=NVIDIA_API_KEY,
    truncate="END"
)

llm = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)


if not os.path.exists(db_folder_name):
    os.makedirs(db_folder_name)
    df = pd.read_csv("dataset.csv")
    df = df.sort_values(by="Title").reset_index(drop=True)

    docs = []
    for _, row in df.iterrows():
        doc = Document(
            page_content=row['Content'],
            metadata={"title": row["Title"], "content": row["Content"]}
        )
        docs.append(doc)

    print(f"Total documents prepared: {len(docs)}")

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="vector_store",
        persist_directory=db_folder_name
    )
    print("Vector store created with NVIDIA embeddings and persisted.")
else:
    vectorstore = Chroma(
        embedding_function=embeddings,
        collection_name="vector_store",
        persist_directory=db_folder_name
    )
    print("Vector store loaded from persistence.")


app = FastAPI(
    title="Kerala Police AI Assistant",
    description="WebSocket AI assistant using NVIDIA NIM and Chroma"
)

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            query = message.strip()
            print("Processing query:", query, flush=True)

            if not query:
                await websocket.send_text("I'm sorry, I don't know the answer to that question")
                await websocket.send_text("[END]")
                continue

    
            responses = vectorstore.similarity_search(query, k=15)
            print(f"Retrieved {len(responses)} documents", flush=True)

            if not responses:
                await websocket.send_text("I'm sorry, I don't know the answer to that question")
                await websocket.send_text("[END]")
                continue

            context_parts = []
            for doc in responses:
                md = doc.metadata
                part = f"Title: {md.get('title', 'N/A')}\nContent: {md.get('content', '')}"
                context_parts.append(part)
            context = "\n---\n".join(context_parts)

      
            final_prompt = prompt_template.format(question=query, context=context)
            print("Final Prompt (truncated):", final_prompt[:200] + "...", flush=True)

            stream = llm.chat.completions.create(
                model="qwen/qwen3-235b-a22b",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=512,
                stream=True,
                extra_body={"chat_template_kwargs": {"thinking": False}}
            )

            completed_response = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    completed_response += content
                    await websocket.send_text(content)

            print("Completed response:", completed_response.strip(), flush=True)
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print("Client disconnected", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        try:
            await websocket.send_text("I'm sorry, an error occurred while processing your request.")
            await websocket.send_text("[END]")
        except:
            pass
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
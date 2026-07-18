import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableWithFallbacks

def get_llm(temperature: float = 0.2):
    model_name = "gemini-2.0-flash"
    
    primary_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    fallback_key_1 = os.getenv("GEMINI_FALLBACK_API_KEY")
    fallback_key_2 = os.getenv("GEMINI_FALLBACK_API_KEY_2")
    
    # Set max_retries=20 to allow tenacity to outlast the 60s+ rate limit delays.
    llm = ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=temperature,
        api_key=primary_key,
        max_retries=20
    )
    
    fallbacks = []
    if fallback_key_1:
        fallbacks.append(ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=fallback_key_1,
            max_retries=20
        ))
    if fallback_key_2:
        fallbacks.append(ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=fallback_key_2,
            max_retries=20
        ))
        
    if fallbacks:
        return llm.with_fallbacks(fallbacks)
        
    return llm

import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature: float = 0.2):
    model_name = "gemini-flash-latest"

    primary_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    fallback_key_1 = os.getenv("GEMINI_FALLBACK_API_KEY")
    fallback_key_2 = os.getenv("GEMINI_FALLBACK_API_KEY_2")

    # Google's SDK backs off up to 60s between retries (attempts=20 could hang
    # ~15min on one key alone). Keep retries low and per-call timeout short so a
    # rate-limited key fails fast and falls over to the next key instead of
    # stalling the whole chat turn.
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        api_key=primary_key,
        max_retries=2,
        timeout=20,
    )

    fallbacks = []
    if fallback_key_1:
        fallbacks.append(ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=fallback_key_1,
            max_retries=2,
            timeout=20,
        ))
    if fallback_key_2:
        fallbacks.append(ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=fallback_key_2,
            max_retries=2,
            timeout=20,
        ))

    # All 3 Gemini keys above share one project's quota pool (confirmed
    # empirically — see DECISIONS.md DEC-021), so they protect against one key
    # being transiently unhealthy but NOT against quota exhaustion, which is
    # the failure mode that actually happens on this free tier. Groq is a
    # genuinely independent provider/quota — the real last-resort fallback.
    for groq_key in (os.getenv("GROQ_API_KEY"), os.getenv("GROQ_FALLBACK_API_KEY")):
        if not groq_key:
            continue
        try:
            from langchain_groq import ChatGroq
            fallbacks.append(ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=temperature,
                api_key=groq_key,
                max_retries=1,
                timeout=20,
            ))
        except Exception:
            pass

    if fallbacks:
        return llm.with_fallbacks(fallbacks)

    return llm

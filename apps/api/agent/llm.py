import os
from langchain_google_genai import ChatGoogleGenerativeAI


def _log_model_choice(tier: str, model_name: str) -> None:
    """Tag the current Langfuse span with which model tier this node picked
    (Part D2: model routing). Best-effort — Langfuse is optional and a node
    may call this outside an @observe() span, so failures are swallowed."""
    try:
        from langfuse import get_client
        get_client().update_current_span(metadata={"model_tier": tier, "model": model_name})
    except Exception:
        pass


def get_llm(temperature: float = 0.2):
    model_name = "gemini-flash-latest"
    _log_model_choice("long-form (gemini-primary)", model_name)

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


def get_fast_llm(temperature: float = 0.0):
    """Groq-primary, Gemini-fallback — for short, structured, latency-sensitive
    jobs (topic extraction, quiz JSON) where Groq's speed matters and the
    output format is plain JSON. Long-form generation (lecture flow, W-A-S,
    research synthesis) stays on get_llm() (Gemini-primary): DEC-023 found
    Groq unreliable at following the custom <artifact type="..."> tag
    wrapper those nodes need, so this tier is deliberately scoped to jobs
    that only need plain JSON out."""
    groq_key = os.getenv("GROQ_API_KEY")
    groq_fallback_key = os.getenv("GROQ_FALLBACK_API_KEY")

    if not groq_key:
        # No Groq configured — fall back to the standard Gemini-primary chain.
        return get_llm(temperature=temperature)

    _log_model_choice("fast (groq-primary)", "llama-3.3-70b-versatile")

    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=groq_key,
        max_retries=1,
        timeout=15,
    )

    fallbacks = []
    if groq_fallback_key:
        fallbacks.append(ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            api_key=groq_fallback_key,
            max_retries=1,
            timeout=15,
        ))
    # Gemini as the final fallback, same as the reverse direction in get_llm.
    fallbacks.append(get_llm(temperature=temperature))

    return llm.with_fallbacks(fallbacks)

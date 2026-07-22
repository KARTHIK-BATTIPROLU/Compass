import os
import time
from typing import Any, List, Optional
from langchain_core.runnables import Runnable, RunnableConfig

# Global in-memory cooldown state: provider_name -> timestamp when cooldown ends
_cooldowns = {}
COOLDOWN_SECONDS = 300  # 5 minutes

def set_cooldown(provider: str, seconds: int = COOLDOWN_SECONDS):
    _cooldowns[provider] = time.time() + seconds

def is_on_cooldown(provider: str) -> bool:
    if provider in _cooldowns:
        if time.time() < _cooldowns[provider]:
            return True
        else:
            del _cooldowns[provider]
    return False

def get_provider_status():
    """Returns the current cooldown status for /api/health."""
    return {
        "gemini": "cooldown" if is_on_cooldown("gemini") else "ok",
        "groq": "cooldown" if is_on_cooldown("groq") else "ok",
    }

def _log_actual_provider(provider_name: str, model_name: str) -> None:
    """Tag the current Langfuse span with which provider actually served the request."""
    try:
        from langfuse import get_client
        span = get_client().get_current_span()
        if span:
            span.update(metadata={"actual_provider": provider_name, "actual_model": model_name})
    except Exception:
        pass


class ProviderChain(Runnable):
    """
    A custom Runnable that routes requests through an ordered list of providers,
    respecting cooldowns for quota-exhausted providers, distinguishing between
    fatal, quota, and transient errors.
    """
    def __init__(self, providers: List[dict]):
        # providers is a list of dicts: {"name": "gemini", "model": BaseChatModel, "model_name": "gemini-flash-latest"}
        self.providers = providers

    def _is_quota_error(self, error_str: str) -> bool:
        return any(k in error_str for k in ("429", "quota", "resource_exhausted", "too_many_requests"))

    def _is_fatal_error(self, error_str: str) -> bool:
        return any(k in error_str for k in ("401", "unauthorized", "invalid_api_key"))

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ProviderChain":
        bound_providers = []
        for p in self.providers:
            bound_providers.append({
                "name": p["name"],
                "model_name": p["model_name"],
                "model": p["model"].bind_tools(tools, **kwargs)
            })
        return ProviderChain(bound_providers)

    def with_structured_output(self, schema: Any, **kwargs: Any) -> "ProviderChain":
        bound_providers = []
        for p in self.providers:
            bound_providers.append({
                "name": p["name"],
                "model_name": p["model_name"],
                "model": p["model"].with_structured_output(schema, **kwargs)
            })
        return ProviderChain(bound_providers)

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        import time as ptime
        last_err = None
        for p in self.providers:
            name = p["name"]
            model = p["model"]
            
            if is_on_cooldown(name):
                continue
                
            attempts = 0
            while attempts < 2:
                attempts += 1
                try:
                    res = model.invoke(input, config=config, **kwargs)
                    _log_actual_provider(name, p["model_name"])
                    if hasattr(res, "response_metadata"):
                        if res.response_metadata is None: res.response_metadata = {}
                        res.response_metadata["actual_provider"] = name
                    return res
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if self._is_quota_error(err_str):
                        print(f"[{name}] Quota exhausted. Placing on cooldown.")
                        set_cooldown(name)
                        break  # Next provider
                    elif self._is_fatal_error(err_str):
                        print(f"[{name}] Fatal error: {e}. Skipping provider.")
                        break  # Next provider
                    else:
                        print(f"[{name}] Transient error: {e}. Attempt {attempts}/2.")
                        if attempts < 2:
                            ptime.sleep(1)
                            continue
                        else:
                            break  # Next provider
        
        raise Exception(f"All providers failed or on cooldown. Last error: {last_err}")

    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        import asyncio
        last_err = None
        for p in self.providers:
            name = p["name"]
            model = p["model"]
            
            if is_on_cooldown(name):
                continue
                
            attempts = 0
            while attempts < 2:
                attempts += 1
                try:
                    res = await model.ainvoke(input, config=config, **kwargs)
                    _log_actual_provider(name, p["model_name"])
                    if hasattr(res, "response_metadata"):
                        if res.response_metadata is None: res.response_metadata = {}
                        res.response_metadata["actual_provider"] = name
                    return res
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if self._is_quota_error(err_str):
                        print(f"[{name}] Quota exhausted. Placing on cooldown.")
                        set_cooldown(name)
                        break
                    elif self._is_fatal_error(err_str):
                        print(f"[{name}] Fatal error: {e}. Skipping provider.")
                        break
                    else:
                        print(f"[{name}] Transient error: {e}. Attempt {attempts}/2.")
                        if attempts < 2:
                            await asyncio.sleep(1)
                            continue
                        else:
                            break
        
        raise Exception(f"All providers failed or on cooldown. Last error: {last_err}")

    def stream(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        import time as ptime
        last_err = None
        for p in self.providers:
            name = p["name"]
            model = p["model"]
            
            if is_on_cooldown(name):
                continue
                
            attempts = 0
            while attempts < 2:
                attempts += 1
                try:
                    iterator = model.stream(input, config=config, **kwargs)
                    # Get first chunk to confirm connection
                    first = next(iterator)
                    _log_actual_provider(name, p["model_name"])
                    yield first
                    yield from iterator
                    return
                except StopIteration:
                    # Stream was just empty
                    _log_actual_provider(name, p["model_name"])
                    return
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if self._is_quota_error(err_str):
                        print(f"[{name}] Quota exhausted during stream start. Placing on cooldown.")
                        set_cooldown(name)
                        break
                    elif self._is_fatal_error(err_str):
                        print(f"[{name}] Fatal error: {e}. Skipping provider.")
                        break
                    else:
                        print(f"[{name}] Transient error: {e}. Attempt {attempts}/2.")
                        if attempts < 2:
                            ptime.sleep(1)
                            continue
                        else:
                            break
        
        raise Exception(f"All providers failed or on cooldown. Last error: {last_err}")

    async def astream(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        import asyncio
        last_err = None
        for p in self.providers:
            name = p["name"]
            model = p["model"]
            
            if is_on_cooldown(name):
                continue
                
            attempts = 0
            while attempts < 2:
                attempts += 1
                try:
                    iterator = model.astream(input, config=config, **kwargs)
                    # Get first chunk to confirm connection
                    first = await iterator.__anext__()
                    _log_actual_provider(name, p["model_name"])
                    yield first
                    async for chunk in iterator:
                        yield chunk
                    return
                except StopAsyncIteration:
                    # Stream was just empty
                    _log_actual_provider(name, p["model_name"])
                    return
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if self._is_quota_error(err_str):
                        print(f"[{name}] Quota exhausted during astream start. Placing on cooldown.")
                        set_cooldown(name)
                        break
                    elif self._is_fatal_error(err_str):
                        print(f"[{name}] Fatal error: {e}. Skipping provider.")
                        break
                    else:
                        print(f"[{name}] Transient error: {e}. Attempt {attempts}/2.")
                        if attempts < 2:
                            await asyncio.sleep(1)
                            continue
                        else:
                            break
                            
        raise Exception(f"All providers failed or on cooldown. Last error: {last_err}")


def get_llm(temperature: float = 0.2) -> ProviderChain:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    providers = []
    
    # 1. Primary: Gemini
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        providers.append({
            "name": "gemini",
            "model_name": "gemini-flash-latest",
            "model": ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                temperature=temperature,
                api_key=gemini_key,
                # Let our chain handle retries
                max_retries=0,
                timeout=20,
            )
        })
        
    # 2. Secondary: Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from langchain_groq import ChatGroq
        providers.append({
            "name": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "model": ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=temperature,
                api_key=groq_key,
                max_retries=0,
                timeout=20,
            )
        })
        
    # 3. Tertiary: OpenRouter or other free provider, if present
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        from langchain_openai import ChatOpenAI
        providers.append({
            "name": "openrouter",
            "model_name": "openrouter/free-model",
            "model": ChatOpenAI(
                model="google/gemini-2.5-flash-free",  # Or another reliable free model
                temperature=temperature,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=0,
                timeout=20,
            )
        })

    if not providers:
        raise Exception("No LLM keys configured (need GEMINI_API_KEY or GROQ_API_KEY)")
        
    return ProviderChain(providers)

def get_fast_llm(temperature: float = 0.0) -> ProviderChain:
    """
    Groq-primary, Gemini-fallback.
    For short, structured, latency-sensitive jobs (topic extraction, quiz JSON).
    """
    providers = []
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from langchain_groq import ChatGroq
        providers.append({
            "name": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "model": ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=temperature,
                api_key=groq_key,
                max_retries=0,
                timeout=15,
            )
        })
        
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        providers.append({
            "name": "gemini",
            "model_name": "gemini-flash-latest",
            "model": ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                temperature=temperature,
                api_key=gemini_key,
                max_retries=0,
                timeout=15,
            )
        })
        
    if not providers:
        raise Exception("No LLM keys configured")
        
    return ProviderChain(providers)

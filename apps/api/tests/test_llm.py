import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agent.llm import ProviderChain, is_on_cooldown, set_cooldown

@pytest.fixture(autouse=True)
def reset_cooldowns():
    import agent.llm
    agent.llm._cooldowns = {}
    yield

def test_provider_chain_success():
    """Test that a successful call returns immediately from the first provider."""
    mock_model1 = MagicMock()
    mock_model1.invoke.return_value = "success1"
    
    mock_model2 = MagicMock()
    mock_model2.invoke.return_value = "success2"
    
    chain = ProviderChain([
        {"name": "test1", "model_name": "model1", "model": mock_model1},
        {"name": "test2", "model_name": "model2", "model": mock_model2}
    ])
    
    res = chain.invoke("hello")
    assert res == "success1"
    mock_model1.invoke.assert_called_once_with("hello", config=None)
    mock_model2.invoke.assert_not_called()

def test_provider_chain_quota_error_fallback():
    """Test that a quota error on provider 1 falls back to provider 2 and sets cooldown."""
    mock_model1 = MagicMock()
    mock_model1.invoke.side_effect = Exception("429 resource_exhausted")
    
    mock_model2 = MagicMock()
    mock_model2.invoke.return_value = "success2"
    
    chain = ProviderChain([
        {"name": "test1", "model_name": "model1", "model": mock_model1},
        {"name": "test2", "model_name": "model2", "model": mock_model2}
    ])
    
    res = chain.invoke("hello")
    assert res == "success2"
    
    # Provider 1 should be called once, fail with quota, and be put on cooldown
    mock_model1.invoke.assert_called_once()
    assert is_on_cooldown("test1") is True
    
    # Provider 2 should be called once
    mock_model2.invoke.assert_called_once()

def test_provider_chain_transient_error_retry(mocker):
    """Test that a transient error retries on the same provider."""
    mocker.patch("time.sleep", return_value=None)
    
    mock_model1 = MagicMock()
    # Fails first time, succeeds second time
    mock_model1.invoke.side_effect = [Exception("timeout"), "success1"]
    
    chain = ProviderChain([
        {"name": "test1", "model_name": "model1", "model": mock_model1}
    ])
    
    res = chain.invoke("hello")
    assert res == "success1"
    assert mock_model1.invoke.call_count == 2
    assert is_on_cooldown("test1") is False

@pytest.mark.asyncio
async def test_provider_chain_async_fatal_error():
    """Test that a fatal error skips the provider immediately."""
    mock_model1 = AsyncMock()
    mock_model1.ainvoke.side_effect = Exception("401 unauthorized")
    
    mock_model2 = AsyncMock()
    mock_model2.ainvoke.return_value = "success2"
    
    chain = ProviderChain([
        {"name": "test1", "model_name": "model1", "model": mock_model1},
        {"name": "test2", "model_name": "model2", "model": mock_model2}
    ])
    
    res = await chain.ainvoke("hello")
    assert res == "success2"
    
    # Model 1 was called once and skipped
    mock_model1.ainvoke.assert_called_once()
    assert is_on_cooldown("test1") is False
    
    mock_model2.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_provider_chain_all_fail():
    """Test that it raises an exception if all providers fail."""
    mock_model1 = AsyncMock()
    mock_model1.ainvoke.side_effect = Exception("401 unauthorized")
    
    mock_model2 = AsyncMock()
    mock_model2.ainvoke.side_effect = Exception("429 resource_exhausted")
    
    chain = ProviderChain([
        {"name": "test1", "model_name": "model1", "model": mock_model1},
        {"name": "test2", "model_name": "model2", "model": mock_model2}
    ])
    
    with pytest.raises(Exception, match="All providers failed or on cooldown"):
        await chain.ainvoke("hello")
    
    assert is_on_cooldown("test2") is True

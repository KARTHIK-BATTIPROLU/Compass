import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from agent.auth import verify_user, user_owns_session

@pytest.mark.asyncio
async def test_verify_user_missing_credentials():
    with pytest.raises(HTTPException) as exc:
        await verify_user(None)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
@patch("agent.auth.get_supabase")
async def test_verify_user_no_supabase(mock_get_supabase):
    mock_get_supabase.return_value = None
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="abc")
    with pytest.raises(HTTPException) as exc:
        await verify_user(creds)
    assert exc.value.status_code == 500

@pytest.mark.asyncio
@patch("agent.auth.get_supabase")
async def test_verify_user_success(mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.auth.get_user.return_value = MagicMock(user="test_user")
    mock_get_supabase.return_value = mock_sb
    
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="abc")
    user = await verify_user(creds)
    assert user == "test_user"
    mock_sb.auth.get_user.assert_called_once_with("abc")

@pytest.mark.asyncio
@patch("agent.auth.get_supabase")
async def test_verify_user_invalid(mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.auth.get_user.side_effect = Exception("invalid")
    mock_get_supabase.return_value = mock_sb
    
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="abc")
    with pytest.raises(HTTPException) as exc:
        await verify_user(creds)
    assert exc.value.status_code == 401

@patch("agent.auth.get_supabase")
def test_user_owns_session_success(mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_id": "u1"})
    mock_get_supabase.return_value = mock_sb
    
    assert user_owns_session("u1", "s1") is True

@patch("agent.auth.get_supabase")
def test_user_owns_session_fail(mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"user_id": "u2"})
    mock_get_supabase.return_value = mock_sb
    
    assert user_owns_session("u1", "s1") is False

@patch("agent.auth.get_supabase")
def test_user_owns_session_error(mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("error")
    mock_get_supabase.return_value = mock_sb
    
    assert user_owns_session("u1", "s1") is False

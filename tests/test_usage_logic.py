import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from agents.core.usage import usage_manager

@pytest.mark.asyncio
async def test_check_limit_success():
    """Test check_limit returns True when subscription is valid"""
    with patch('api.utils.subscription_enforcement.check_subscription_active') as mock_check:
        # Mock successful await
        mock_check.return_value = True
        
        result = await usage_manager.check_limit("user_active")
        assert result is True

@pytest.mark.asyncio
async def test_check_limit_failure_403():
    """Test check_limit returns False when subscription is expired or limit reached"""
    with patch('api.utils.subscription_enforcement.check_subscription_active') as mock_check:
        # Mock raising HTTPException
        mock_check.side_effect = HTTPException(status_code=403, detail="Limit Reached")
        
        result = await usage_manager.check_limit("user_limit_reached")
        assert result is False

@pytest.mark.asyncio
async def test_check_limit_failure_generic():
    """Test check_limit returns False on unexpected error"""
    with patch('api.utils.subscription_enforcement.check_subscription_active') as mock_check:
        mock_check.side_effect = Exception("Database Down")
        
        result = await usage_manager.check_limit("user_error")
        assert result is False

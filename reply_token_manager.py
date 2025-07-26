# reply_token_manager.py - 管理 LINE Bot Reply Token 的工具
import time
import logging
from typing import Set, Dict
from datetime import datetime, timedelta

class ReplyTokenManager:
    """管理 LINE Bot Reply Token，防止重複使用和追蹤過期"""
    
    def __init__(self, token_lifetime_minutes: int = 60):
        """
        初始化 Reply Token 管理器
        
        Args:
            token_lifetime_minutes: Reply token 的生命週期（分鐘）
        """
        self.used_tokens: Dict[str, datetime] = {}
        self.token_lifetime = timedelta(minutes=token_lifetime_minutes)
        self.logger = logging.getLogger(__name__)
    
    def is_token_used(self, token: str) -> bool:
        """
        檢查 token 是否已經使用過
        
        Args:
            token: Reply token
            
        Returns:
            bool: True 如果已使用，False 如果未使用
        """
        if not token:
            return True  # 空 token 視為已使用
        
        # 清理過期的 token
        self._cleanup_expired_tokens()
        
        return token in self.used_tokens
    
    def mark_token_used(self, token: str, request_id: str = None) -> bool:
        """
        標記 token 為已使用
        
        Args:
            token: Reply token
            request_id: 請求 ID（用於日誌）
            
        Returns:
            bool: True 如果成功標記，False 如果 token 已使用或無效
        """
        if not token:
            return False
        
        if self.is_token_used(token):
            if request_id:
                self.logger.warning(f"[{request_id}] Reply token 已使用過: {token[:10]}...")
            return False
        
        self.used_tokens[token] = datetime.utcnow()
        if request_id:
            self.logger.info(f"[{request_id}] 標記 reply token 為已使用: {token[:10]}...")
        
        return True
    
    def is_test_token(self, token: str) -> bool:
        """
        檢查是否為測試用的假 token
        
        Args:
            token: Reply token
            
        Returns:
            bool: True 如果是測試 token
        """
        if not token:
            return False
        
        test_tokens = [
            'test_reply_token',
            'mock_reply_token',
            'fake_reply_token',
            'dummy_reply_token'
        ]
        
        return token in test_tokens or token.startswith('test_') or token.startswith('mock_')
    
    def _cleanup_expired_tokens(self):
        """清理過期的 token"""
        current_time = datetime.utcnow()
        expired_tokens = [
            token for token, used_time in self.used_tokens.items()
            if current_time - used_time > self.token_lifetime
        ]
        
        for token in expired_tokens:
            del self.used_tokens[token]
        
        if expired_tokens:
            self.logger.debug(f"清理了 {len(expired_tokens)} 個過期的 reply token")
    
    def get_stats(self) -> dict:
        """
        取得統計資訊
        
        Returns:
            dict: 包含統計資訊的字典
        """
        self._cleanup_expired_tokens()
        
        return {
            "active_tokens_count": len(self.used_tokens),
            "token_lifetime_minutes": self.token_lifetime.total_seconds() / 60,
            "oldest_token_age_minutes": (
                (datetime.utcnow() - min(self.used_tokens.values())).total_seconds() / 60
                if self.used_tokens else 0
            )
        }

# 全域 reply token 管理器實例
reply_token_manager = ReplyTokenManager()

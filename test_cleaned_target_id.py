#!/usr/bin/env python3
# test_cleaned_target_id.py - 測試清理後的 TARGET_ID

import os

def test_cleaned_target_id():
    """測試清理後的 TARGET_ID"""
    target_id_raw = os.getenv("TARGET_ID", "").strip()
    target_id_no_comment = target_id_raw.split('#')[0].strip()
    target_id_cleaned = target_id_no_comment.strip("'\"")
    
    print("TARGET_ID 清理測試：")
    print("=" * 50)
    print(f"原始值: '{target_id_raw}'")
    print(f"移除註解後: '{target_id_no_comment}'")
    print(f"最終清理值: '{target_id_cleaned}'")
    print(f"最終長度: {len(target_id_cleaned)}")
    
    # 驗證是否是有效的 LINE ID
    if target_id_cleaned and len(target_id_cleaned) == 33 and target_id_cleaned[0] in ['U', 'C', 'R']:
        print(f"✓ 有效的 LINE ID (類型: {'用戶' if target_id_cleaned[0] == 'U' else '群組' if target_id_cleaned[0] == 'C' else '聊天室'})")
    else:
        print(f"✗ 無效的 LINE ID 格式")
    
    print("=" * 50)

if __name__ == "__main__":
    test_cleaned_target_id()

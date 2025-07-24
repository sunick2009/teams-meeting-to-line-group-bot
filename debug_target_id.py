#!/usr/bin/env python3
# debug_target_id.py - 調試 TARGET_ID

import os

def debug_target_id():
    """調試 TARGET_ID 的值"""
    target_id_raw = os.getenv("TARGET_ID")
    target_id_cleaned = os.getenv("TARGET_ID", "").strip().strip("'\"")
    
    print("TARGET_ID 調試資訊：")
    print("=" * 50)
    print(f"原始值: '{target_id_raw}'")
    print(f"原始值長度: {len(target_id_raw) if target_id_raw else 'None'}")
    print(f"原始值類型: {type(target_id_raw)}")
    print(f"清理後值: '{target_id_cleaned}'")
    print(f"清理後長度: {len(target_id_cleaned)}")
    print(f"清理後類型: {type(target_id_cleaned)}")
    
    # 檢查是否包含特殊字元
    if target_id_raw:
        special_chars = []
        for i, char in enumerate(target_id_raw):
            if ord(char) < 32 or ord(char) > 126:  # 非可見 ASCII 字元
                special_chars.append(f"位置 {i}: {repr(char)} (ASCII {ord(char)})")
        
        if special_chars:
            print(f"發現特殊字元: {special_chars}")
        else:
            print("未發現特殊字元")
    
    # 測試是否是有效的 LINE ID 格式
    if target_id_cleaned:
        if target_id_cleaned.startswith('U') or target_id_cleaned.startswith('C') or target_id_cleaned.startswith('R'):
            print(f"✓ 看起來是有效的 LINE ID 格式 (開頭: {target_id_cleaned[0]})")
        else:
            print(f"✗ 可能不是有效的 LINE ID 格式 (開頭: {target_id_cleaned[0] if target_id_cleaned else 'None'})")
    
    print("=" * 50)

if __name__ == "__main__":
    debug_target_id()

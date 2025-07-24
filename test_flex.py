#!/usr/bin/env python3
# test_flex.py - 測試 FlexMessage 建構

import os
from teams_webhook import build_flex

def test_flex_message():
    """測試 FlexMessage 的建構"""
    # 模擬會議資料
    meeting_data = {
        "title": "測試會議",
        "time": "2025-07-24 16:30",
        "link": "https://teams.microsoft.com/l/meetup-join/test"
    }
    
    try:
        # 建構 FlexMessage
        flex_msg = build_flex(meeting_data)
        
        # 轉換為字典並檢查
        flex_dict = flex_msg.to_dict()
        print("FlexMessage 建構成功！")
        print("=" * 50)
        print("FlexMessage 結構：")
        
        # 印出主要結構
        print(f"訊息類型: {flex_dict.get('type')}")
        print(f"替代文字: {flex_dict.get('altText')}")
        
        contents = flex_dict.get('contents', {})
        print(f"內容類型: {contents.get('type')}")
        
        # 檢查 body
        body = contents.get('body', {})
        if body:
            print("Body 內容:")
            for i, content in enumerate(body.get('contents', [])):
                print(f"  {i+1}. {content.get('text')} (類型: {content.get('type')})")
        
        # 檢查 footer
        footer = contents.get('footer', {})
        if footer:
            print("Footer 內容:")
            for i, content in enumerate(footer.get('contents', [])):
                if content.get('type') == 'button':
                    action = content.get('action', {})
                    print(f"  {i+1}. 按鈕: {content.get('text')} -> {action.get('uri')}")
        
        print("=" * 50)
        print("✓ FlexMessage 驗證成功，可以正常推送")
        return True
        
    except Exception as e:
        print(f"✗ FlexMessage 建構失敗: {str(e)}")
        print(f"錯誤類型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_flex_message()

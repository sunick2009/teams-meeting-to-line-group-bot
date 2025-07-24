# Azure Function 入口點
import azure.functions as func
from app_unified import app
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function 的主要入口點"""
    logging.info('Python HTTP trigger function processed a request.')
    
    # 將 Azure Function 請求轉換為 WSGI 請求
    import azure.functions.wsgi as wsgi
    return wsgi.WsgiMiddleware(app).handle(req)

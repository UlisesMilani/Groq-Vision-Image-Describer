# groqVision.py
# Un complemento global de NVDA para describir imágenes usando Groq Llama 3.2 Vision

import globalPluginHandler
import api
import ui
import core
import wx
import urllib.request
import urllib.error
import json
import base64
import threading
import os
import io
from logHandler import log

# ==========================================
# CONFIGURACIÓN DEL USUARIO
# ==========================================
# Pega tu API Key de OpenRouter entre las comillas simples de abajo
OPENROUTER_API_KEY = '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'
# ==========================================

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def script_describeFocusedImage(self, gesture):
        if not OPENROUTER_API_KEY:
            ui.message("Error: API Key de OpenRouter no configurada.")
            return

        ui.message("Analizando imagen...")
        
        # Obtener el objeto actualmente enfocado
        focus_obj = api.getFocusObject()
        
        # Iniciar el proceso en un hilo separado para no congelar NVDA
        threading.Thread(target=self.processImage, args=(focus_obj,)).start()

    def processImage(self, focus_obj):
        try:
            image_bytes = self.captureImage(focus_obj)
            if not image_bytes:
                core.callLater(10, ui.message, "No se pudo obtener una imagen del elemento actual.")
                return

            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            description = self.callAI(image_base64)
            
            # Hablar la respuesta en el hilo principal
            core.callLater(10, ui.message, description)
            
        except Exception as e:
            log.error(f"Vision error: {str(e)}")
            core.callLater(10, ui.message, f"Error al procesar la imagen.")

    def captureImage(self, focus_obj):
        # 1. Intentar ver si el objeto es un archivo local usando Windows Shell
        try:
            app_name = ""
            if hasattr(focus_obj, 'appModule') and focus_obj.appModule:
                app_name = focus_obj.appModule.appName.lower()
            
            if app_name == "explorer":
                import ctypes
                import comtypes.client
                import os
                
                # Inicializar COM para este hilo de fondo
                ctypes.windll.ole32.CoInitialize(None)
                try:
                    shell = comtypes.client.CreateObject("Shell.Application")
                    
                    # Buscar en todas las ventanas del explorador
                    for i in range(shell.Windows().Count):
                        try:
                            window = shell.Windows().Item(i)
                            items = window.Document.SelectedItems()
                            for j in range(items.Count):
                                item = items.Item(j)
                                val = item.Path
                                if val and os.path.isfile(val):
                                    ext = val.lower().split('.')[-1]
                                    if ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp']:
                                        log.info(f"Vision: Leyendo archivo local {val}")
                                        with open(val, 'rb') as f:
                                            return f.read()
                        except Exception:
                            pass
                finally:
                    # Siempre desinicializar COM
                    ctypes.windll.ole32.CoUninitialize()
                
                log.info("Vision: No se encontró path del archivo en explorer, aplicando fallback de pantalla.")
        except Exception as e:
            log.debug(f"Vision: Error al obtener archivo de explorer ({e})")
            pass

        # 2. Capturar recuadro del objeto, y si falla (o si es Explorer), la ventana completa.
        try:
            import ctypes
            import ctypes.wintypes
            location = focus_obj.location
            left, top, width, height = 0, 0, 0, 0
            
            # Si tenemos ubicación válida y NO estamos en explorer (para evitar recortar solo el icono)
            if location and len(location) == 4 and location[2] > 0 and location[3] > 0 and app_name != "explorer":
                left, top, width, height = location
            else:
                # Fallback extremo: Capturar la ventana activa completa
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                left = rect.left
                top = rect.top
                width = rect.right - rect.left
                height = rect.bottom - rect.top

            if width > 0 and height > 0:
                log.info(f"Vision: Capturando pantalla ({left}, {top}, {width}, {height})")
                bmp = wx.Bitmap(width, height)
                mem_dc = wx.MemoryDC()
                mem_dc.SelectObject(bmp)
                screen_dc = wx.ScreenDC()
                mem_dc.Blit(0, 0, width, height, screen_dc, left, top)
                mem_dc.SelectObject(wx.NullBitmap)
                
                img = bmp.ConvertToImage()
                stream = io.BytesIO()
                img.SaveFile(stream, wx.BITMAP_TYPE_PNG)
                return stream.getvalue()
        except Exception as e:
            log.error(f"Vision: Error al capturar la pantalla: {e}")
            pass
            
        return None

    def callAI(self, base64_image):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/nvdaaddons",
            "X-Title": "NVDA Vision Addon",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Usamos el modelo gratuito de Nvidia Vision en OpenRouter
        payload = {
            "model": "nvidia/nemotron-nano-12b-v2-vl:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe esta imagen detalladamente en español. Tu objetivo es que una persona ciega pueda imaginarse la escena. No saludes, empieza la descripción directamente."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.5
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            log.error(f"Vision API Error: {e.code} - {error_body}")
            return f"Error de la API: {e.code}"
        except Exception as e:
            log.error(f"Vision API Exception: {str(e)}")
            return "Error de conexión con la API."

    # Vincular el script al atajo NVDA+Shift+V
    __gestures = {
        "kb:NVDA+shift+v": "describeFocusedImage",
    }

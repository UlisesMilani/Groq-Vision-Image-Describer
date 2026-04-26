# Groq Vision Image Describer (NVDA Add-on)

Un complemento global para el lector de pantalla NVDA que permite obtener descripciones de imágenes detalladas mediante Inteligencia Artificial.

## Funcionalidades
*   **Captura de Archivos Originales**: Si te encuentras sobre un archivo de imagen en el Explorador de Archivos de Windows, el complemento lee directamente el archivo para enviarlo en máxima resolución.
*   **Captura de Interfaz/Pantalla**: Si estás navegando por la web, en WhatsApp o cualquier otra aplicación, captura el recorte exacto del elemento que tiene el foco de NVDA.
*   **Inteligencia Artificial de Visión**: Se integra con OpenRouter usando el modelo `nvidia/nemotron-nano-12b-v2-vl:free` para proporcionar descripciones ricas pensadas para que una persona ciega pueda imaginarse la escena.

## Uso
Una vez instalado, pulsa el atajo `NVDA + Shift + V` estando parado sobre una imagen.

## Instalación
Empaqueta el contenido de este repositorio en un archivo `.zip` y cámbiale la extensión a `.nvda-addon`, o descarga directamente el instalador si está disponible en la sección de *Releases*.

## Requisitos y Configuración de API
Este complemento requiere una clave de API de **OpenRouter** para funcionar.
Para insertarla, abre el archivo `globalPlugins/groqVision.py`, busca la variable `OPENROUTER_API_KEY` en la cabecera y pega tu clave.

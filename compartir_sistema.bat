@echo off
echo ===================================================
echo   COMPARTIR SISTEMA DE LOGISTICA (Ngrok)
echo ===================================================
echo.
echo Este script generara un enlace publico para tu sistema.
echo.

if not exist ngrok.exe (
    echo [ERROR] No se encontro ngrok.exe. 
    echo Por favor descarga ngrok de https://ngrok.com/download 
    echo y coloca el archivo ngrok.exe en esta carpeta.
    pause
    exit
)

echo Iniciando Ngrok en el puerto 8501...
echo.
echo COPIA EL ENLACE QUE APARECE ABAJO (ej. https://xxxx.ngrok-free.app)
echo Y MANDA ESE ENLACE A TUS TRABAJADORES.
echo.
echo (Para detener, cierra esta ventana)
echo.

ngrok http 8501
pause
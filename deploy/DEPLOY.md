# Despliegue en un Windows-server (acceso por web en la LAN)

El backend queda en `http://IP_DEL_SERVER:8000` y el frontend en
`http://IP_DEL_SERVER:3000`. El frontend detecta solo la IP del backend según
el host desde el que entrás, así que **funciona desde cualquier dispositivo de
la red sin reconfigurar**.

## 1. Requisitos en el servidor

Instalar (una vez):
- [Python 3.12+](https://www.python.org/downloads/) — marcá "Add to PATH".
- [Node.js 20+ LTS](https://nodejs.org/) — incluye npm.

Verificá en PowerShell: `python --version` y `node --version`.

## 2. Copiar el proyecto

Cloná o copiá la carpeta `predictor` al servidor (ej. `C:\predictor`).
No copies `backend\.env`, `backend\.token_cache.txt`, `node_modules`, `.venv`
ni `.next` (se generan en el server).

## 3. Instalación

En PowerShell, dentro de la carpeta del proyecto:

```powershell
.\deploy\setup.ps1
```

Esto crea el venv, instala dependencias, compila el frontend y crea
`backend\.env`. **Editá `backend\.env`** con tus credenciales del API
worldcup26.ir (WC_EMAIL / WC_PASSWORD).

Si PowerShell bloquea los scripts:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## 4. Abrir el firewall (como administrador)

```powershell
.\deploy\open-firewall.ps1
```

## 5. Arrancar

```powershell
.\deploy\start.ps1
```

Te imprime la URL de acceso, ej. `http://192.168.1.50:3000`.
Abrila desde el celular o cualquier PC de la red.

Para detener: `.\deploy\stop.ps1`

## 6. (Opcional) Que arranque solo al prender el server

Como administrador:

```powershell
.\deploy\register-autostart.ps1
```

Crea una tarea que ejecuta `start.ps1` al iniciar sesión. Para quitarla:
`schtasks /Delete /TN PredictorMundial /F`

## Actualizar a una versión nueva

```powershell
git pull
.\deploy\stop.ps1
.\deploy\setup.ps1     # reinstala deps y recompila
.\deploy\start.ps1
```

## Problemas comunes

- **No abre desde otra PC**: revisá el firewall (paso 4) y que ambos estén en la
  misma red. Probá primero `http://localhost:3000` en el propio server.
- **La página carga pero no trae datos**: el backend no arrancó o `backend\.env`
  no tiene credenciales válidas. Probá `http://IP_DEL_SERVER:8000/api/health`.
- **Quiero fijar una URL de API distinta**: creá `frontend\.env.local` con
  `NEXT_PUBLIC_API_URL=http://mi-host:8000` y recompilá (`npm run build`).

# 🖥️ SISTEMA DE MONITOREO Y CONTROL DE PCs EN RED

Sistema completo para monitorear múltiples computadoras conectadas en red desde un núcleo central. Obtén datos de CPU, RAM, disco, procesos y mucho más.

## 📋 Características

✅ **Monitoreo en Tiempo Real**
- CPU y Memoria
- Uso de disco
- Procesos activos
- Conexiones de red

✅ **Control Remoto**
- Ejecutar comandos en PCs remotas
- Shutdown, reinicio, etc.

✅ **Almacenamiento de Datos**
- Guardado automático en JSON
- Exportación a Excel
- Historial de consultas

✅ **Interfaz Fácil**
- Menú interactivo en consola
- Registro de PCs por IP
- Estados actualizados en tiempo real

---

## 🚀 INSTALACIÓN RÁPIDA

### Opción 1: Instalación Automática (RECOMENDADO)

1. Abre una terminal/PowerShell en la carpeta del proyecto
2. Ejecuta: `python instalar.py`
3. Sigue las instrucciones
4. Se crearán accesos directos automáticamente

### Opción 2: Instalación Manual

```bash
pip install flask psutil requests openpyxl pandas
```

---

## 📖 CÓMO USAR

### PASO 1: Configurar Servidores (en cada PC a monitorear)

**En CADA computadora que quieras monitorear:**

Opción A - Ejecutar directamente:
```bash
python agent_servidor.py
```

Opción B - Usar el lanzador:
- Ejecuta `Iniciar_Servidor.bat`
- Deja la ventana activa (puedes minimizarla)

**Verás algo como:**
```
🚀 Servidor de Agente iniciado
📍 Escuchando en http://192.168.1.105:5000
```

✅ **EL SERVIDOR DEBE ESTAR ACTIVO PARA PODER MONITOREARLO**

---

### PASO 2: Abrir Panel Central (en el núcleo de control)

**En la PC que será el control central:**

Opción A - Ejecutar directamente:
```bash
python cliente_central.py
```

Opción B - Usar el lanzador:
- Ejecuta `Abrir_Monitor.bat`
- O haz doble clic en el acceso directo de escritorio

---

### PASO 3: Registrar PCs en el Panel

Cuando se abra el panel, verás:

```
==================================================
🖥️  PANEL CENTRAL DE MONITOREO
==================================================
1. Registrar nueva PC
2. Ver todas las PCs
3. Ver datos de una PC específica
4. Ejecutar comando remoto
5. Exportar a Excel
6. Verificar estado de todas
7. Salir
==================================================
```

**Para registrar una PC:**
1. Selecciona opción `1`
2. Ingresa la IP (ejemplo: `192.168.1.105`)
3. Ingresa un nombre amigable (ejemplo: `PC-Escritorio`)
4. ¡Listo! Aparecerá en tu lista

---

## 🔍 ENCONTRAR IPS DE LAS PCs

### En Windows:
```bash
ipconfig
```
Busca la línea: `IPv4 Address: 192.168.X.X`

### En Linux/Mac:
```bash
ip addr
```

### Desde el Panel Central:
Opción 1 del menú (verificar conexión)

---

## 📊 FUNCIONES PRINCIPALES

### 1. Ver Datos de una PC
- CPU, RAM, Disco
- Sistema Operativo
- Procesos principales
- Conexiones activas

Ejemplo de salida:
```
🖥️  COMPUTADORA-01
==================================================
IP: 192.168.1.105
SO: Windows 10 10.0.19041
CPU: Intel(R) Core(TM) i7-8700K

📊 CPU: 25%
   Núcleos: 12 (Físicos: 6)

💾 MEMORIA: 45%
   Usada: 7.2 GB
   Total: 16 GB

💿 DISCO:
   C:\: 65% (300GB / 500GB)
   D:\: 30% (200GB / 600GB)

⚙️  PROCESOS: 156 activos
   Top 5 por CPU:
   - chrome.exe: CPU 15%, RAM 500MB
   - python.exe: CPU 8%, RAM 200MB
   ...
```

### 2. Ejecutar Comandos Remotos
Comandos permitidos:
- `dir` - Listar archivos
- `tasklist` - Ver procesos
- `ipconfig` - Configuración de red
- `systeminfo` - Info del sistema
- `taskkill` - Terminar procesos
- `shutdown` - Apagar/reiniciar

Ejemplo:
```
Ingresa el comando: dir C:\
📤 Salida:
Volume in drive C is System
...
```

### 3. Exportar a Excel
Crea un archivo `inventario_YYYYMMDD_HHMMSS.xlsx` con:
- IP de cada PC
- Nombre
- Estado (En línea / Desconectada)
- % CPU y Memoria
- Sistema Operativo
- Timestamp

---

## 🔧 CONFIGURACIÓN AVANZADA

### Cambiar Puerto del Servidor
En `agent_servidor.py`, línea final:
```python
app.run(host='0.0.0.0', port=5000)  # Cambiar 5000 por otro puerto
```

### Aumentar Timeout
En `cliente_central.py`:
```python
self.timeout = 5  # segundos (aumenta si hay lag)
```

### Agregar Más Comandos Permitidos
En `agent_servidor.py`, función `ejecutar_comando()`:
```python
comandos_permitidos = ['dir', 'tasklist', 'ipconfig', 'tu_comando']
```

---

## ⚠️ SEGURIDAD

⚠️ **IMPORTANTE**: Este sistema está diseñado para redes locales de confianza.

Para producción:
- Usa autenticación (JWT)
- Encripta las comunicaciones (HTTPS)
- Implementa lista blanca de IPs
- Audita comandos ejecutados

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### ❌ "No se puede conectar a IP"
- Verifica que el servidor esté activo (`agent_servidor.py` corriendo)
- Comprueba la IP correcta: `ipconfig`
- Firewall: Permite puerto 5000
- Mismo router/red: Las PCs deben estar en la misma red

### ❌ "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask psutil requests openpyxl pandas
```

### ❌ El servidor dice "Address already in use"
El puerto 5000 está ocupado. Cambia el puerto en el código.

### ❌ Los datos no se actualizan
Los datos se obtienen EN VIVO. Selecciona la opción 3 del menú nuevamente.

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
proyecto/
├── agent_servidor.py          # Se instala en cada PC
├── cliente_central.py         # Panel de control (en el núcleo)
├── instalar.py               # Instalador y configurador
├── inventario_core.py        # Archivo reservado (proyecto anterior)
├── ips_registradas.json      # Guarda las IPs (se crea automáticamente)
└── inventario_YYYYMMDD_HHMMSS.xlsx  # Exportaciones (se crean automáticamente)
```

---

## 💡 EJEMPLOS DE USO

### Ejemplo 1: Monitoreo Simple
```
1. Ejecuta: Iniciar_Servidor.bat (en 3 PCs)
2. Ejecuta: Abrir_Monitor.bat (en PC central)
3. Registra las 3 IPs
4. Opción 6: Verifica que todas estén en línea ✅
5. Opción 3: Inspecciona datos de cada una
```

### Ejemplo 2: Control Remoto
```
1. Opción 4: Ejecutar comando remoto
2. Ingresa IP y comando: taskkill /IM chrome.exe /F
3. ¡Chrome se cerrará en esa PC!
```

### Ejemplo 3: Reporte Diario
```
1. Opción 5: Exportar a Excel
2. Se crea archivo con datos actuales
3. Comparte con tu jefe/cliente
```

---

## 🎓 APRENDIZAJE

**Conceptos técnicos cubiertos:**

- 🌐 Comunicación HTTP (REST API)
- 🔌 Sockets y networking
- 📊 Lectura de datos del sistema (psutil)
- 🗄️ Almacenamiento JSON y Excel
- 🎮 Menú interactivo
- ⚙️ Procesos y control remoto

Este proyecto es excelente para aprender sobre:
- APIs REST
- Comunicación en red
- Administración de sistemas
- Procesamiento de datos

---

## 📞 SOPORTE

Si algo no funciona:
1. Verifica que Python 3.7+ esté instalado
2. Comprueba que las librerías estén instaladas
3. Revisa que no haya puertos bloqueados
4. Lee los mensajes de error completamente

---

**¡Listo para empezar!** 🚀

Ejecuta: `python instalar.py` para comenzar.

# Usa una imagen oficial de Python ligera
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero solo los archivos de dependencias para optimizar caché
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Luego copia el resto del proyecto
COPY . .

# Expone el puerto que Flask usará
EXPOSE 5000

# Ejecuta la aplicación
CMD sh -c "python wait-for-mysql.py && python run.py"

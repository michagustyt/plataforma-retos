from fastapi import FastAPI
from pydantic import BaseModel
import subprocess, tempfile, os

app = FastAPI()

class Submission(BaseModel):
    reto_id: int
    codigo: str

RETOS = {
    1: {
        "titulo": "Hola Mundo",
        "descripcion": "Escribe un programa que imprima exactamente: Hola Mundo",
        "esperado": "Hola Mundo"
    },
    2: {
        "titulo": "Suma",
        "descripcion": "Imprime el resultado de sumar 5 + 3",
        "esperado": "8"
    },
    3: {
        "titulo": "Área de rectángulo",
        "descripcion": "Imprime el área de un rectángulo de 4 × 6",
        "esperado": "24"
    },
    4: {
        "titulo": "Celsius a Fahrenheit",
        "descripcion": "Convierte 100°C a Fahrenheit e imprímelo. Fórmula: (C × 9/5) + 32",
        "esperado": "212.0"
    },
    5: {
        "titulo": "Conteo",
        "descripcion": "Imprime los números del 1 al 5, uno por línea",
        "esperado": "1\n2\n3\n4\n5"
    }
}

def ejecutar_codigo(codigo: str, timeout: int = 5):
    BLOQUEADOS = ["import os", "import sys", "import subprocess",
                  "import socket", "open(", "__import__"]
    for bloque in BLOQUEADOS:
        if bloque in codigo:
            return None, f"Error: uso de '{bloque}' no permitido"
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w",
                                         delete=False) as f:
            f.write(codigo)
            ruta = f.name
        resultado = subprocess.run(
            ["python3", ruta],
            capture_output=True, text=True, timeout=timeout
        )
        os.unlink(ruta)
        if resultado.returncode != 0:
            return None, resultado.stderr.strip()
        return resultado.stdout.strip(), None
    except subprocess.TimeoutExpired:
        return None, "Error: tiempo límite excedido (5 segundos)"
    except Exception as e:
        return None, str(e)

@app.get("/")
def root():
    return {"mensaje": "Plataforma de Retos — API funcionando v2.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/retos")
def listar_retos():
    return [{"id": k, "titulo": v["titulo"],
             "descripcion": v["descripcion"]} for k, v in RETOS.items()]

@app.get("/retos/{reto_id}")
def obtener_reto(reto_id: int):
    if reto_id not in RETOS:
        return {"error": "Reto no encontrado"}
    r = RETOS[reto_id]
    return {"id": reto_id, "titulo": r["titulo"],
            "descripcion": r["descripcion"]}

@app.post("/evaluar")
def evaluar(submission: Submission):
    if submission.reto_id not in RETOS:
        return {"error": "Reto no encontrado"}
    output, error = ejecutar_codigo(submission.codigo)
    if error:
        return {"resultado": "error", "mensaje": error}
    esperado = RETOS[submission.reto_id]["esperado"]
    aprobado = output == esperado
    return {
        "resultado": "aprobado" if aprobado else "reprobado",
        "output":    output,
        "esperado":  esperado if not aprobado else None
    }

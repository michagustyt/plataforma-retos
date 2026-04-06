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
        "titulo": "FizzBuzz",
        "descripcion": "Imprime los números del 1 al 20. Múltiplos de 3 → 'Fizz', múltiplos de 5 → 'Buzz', múltiplos de ambos → 'FizzBuzz'.",
        "esperado": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n16\n17\nFizz\n19\nBuzz"
    },
    3: {
        "titulo": "Palíndromo",
        "descripcion": "Escribe una función es_palindromo(palabra) que retorne True si es palíndromo, False si no. Luego imprímela con: print(es_palindromo('racecar')) y print(es_palindromo('hello'))",
        "esperado": "True\nFalse"
    },
    4: {
        "titulo": "Fibonacci",
        "descripcion": "Imprime los primeros 10 números de la serie Fibonacci, uno por línea.",
        "esperado": "0\n1\n1\n2\n3\n5\n8\n13\n21\n34"
    },
    5: {
        "titulo": "Ordenamiento",
        "descripcion": "Ordena esta lista sin usar sorted() ni .sort(): [64, 34, 25, 12, 22, 11, 90]. Imprime los elementos separados por coma.",
        "esperado": "11,12,22,25,34,64,90"
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

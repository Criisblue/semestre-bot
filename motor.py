from pathlib import Path
import yaml

from datetime import date, timedelta

from datetime import date

# Carpeta config, calculada relativa a este archivo (funciona en cualquier compu)
CONFIG = Path(__file__).parent / "config"


def cargar_yaml(ruta):
    """Abre un archivo YAML y devuelve su contenido como diccionario."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_cronograma():
    return cargar_yaml(CONFIG / "cronograma.yaml")

def cargar_horario(nombre):
    return cargar_yaml(CONFIG / "horarios" / f"{nombre}.yaml")

def cargar_materia(semestre, materia):
    return cargar_yaml(CONFIG / "materias" / semestre / f"{materia}.yaml")

def semana_actual(fecha, crono):
    """Devuelve el número de semana (1-16) en que cae la fecha, o None si no cae en ninguna."""
    for semana in crono["semanas"]:
        if semana["inicio"] <= fecha <= semana["fin"]:
            return semana["numero"]
    return None

def deadline_task(numero_semana, crono):
    """Devuelve la fecha de vencimiento del TASK para esa semana."""
    for bloque in crono["entregables"]["task"]:
        if numero_semana in bloque["semanas"]:
            return bloque["vence"]
    return None


def deadline_aa(numero_semana, crono):
    """Devuelve el vencimiento de la Actividad Autónoma, o None si la semana no tiene AA."""
    if numero_semana % 2 != 0:
        return None
    for semana in crono["semanas"]:
        if semana["numero"] == numero_semana:
            return semana["fin"]            # el domingo de esa semana
    return None

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def primer_dia_en_vivo(materia, horario):
    """Devuelve el primer día (lun-dom) con clase en_vivo de esa materia, o None."""
    for dia in DIAS:
        for clase in horario["horario"].get(dia, []):
            if clase["materia"] == materia and clase["tipo"] == "en_vivo":
                return dia
    return None

def deadline_quiz(numero_semana, materia, crono, horario):
    """Vence a medianoche antes de la primera sesión en vivo de la materia."""
    # 1. Excepciones con fecha fija (semanas 1 y 2)
    for q in crono["entregables"]["quiz_fijos"]:
        if q["semana"] == numero_semana:
            return q["vence"]
    # 2. Buscar la semana en el cronograma
    semana = None
    for s in crono["semanas"]:
        if s["numero"] == numero_semana:
            semana = s
    if semana is None:
        return None
    # 3. Día de la primera clase en vivo -> fecha dentro de esa semana
    dia = primer_dia_en_vivo(materia, horario)
    if dia is None:
        return None
    offset = DIAS.index(dia)                    # lunes=0, martes=1, ...
    return semana["inicio"] + timedelta(days=offset)

def unidad_de_semana(numero_semana, crono):
    """Devuelve el id de la unidad (U1-U4) a la que pertenece la semana."""
    for u in crono["unidades"]:
        if numero_semana in u["semanas"]:
            return u["id"]
    return None


def unidad_que_cierra(fecha, crono):
    """Si la fecha es el domingo que cierra una unidad, devuelve su id; si no, None."""
    for semana in crono["semanas"]:
        if semana["fin"] == fecha:
            uid = unidad_de_semana(semana["numero"], crono)
            u = next(x for x in crono["unidades"] if x["id"] == uid)
            if semana["numero"] == max(u["semanas"]):
                return uid
    return None


def es_feriado(fecha, crono):
    """Devuelve el nombre del feriado si la fecha es feriado, o None."""
    for f in crono["feriados"]:
        if f["fecha"] == fecha:
            return f["nombre"]
    return None

def materias_del_horario(horario):
    """Devuelve la lista de materias que aparecen en el horario."""
    ms = set()
    for dia, clases in horario["horario"].items():
        for c in clases:
            ms.add(c["materia"])
    return sorted(ms)

def proximo_parcial(fecha, crono):
    """Devuelve el próximo parcial cuya fecha de inicio es >= fecha, o None."""
    futuros = [p for p in crono["parciales"] if p["inicio"] >= fecha]
    if not futuros:
        return None
    return min(futuros, key=lambda p: p["inicio"])	

def tema_de_semana(numero_semana, crono):
    """Devuelve 1 o 2 según la posición de la semana dentro de su unidad."""
    for u in crono["unidades"]:
        semanas = sorted(u["semanas"])
        if numero_semana in semanas:
            return 1 if semanas.index(numero_semana) < 2 else 2
    return None

if __name__ == "__main__":
    crono = cargar_cronograma()
    print("26 abr (fin S4):", unidad_que_cierra(date(2026, 4, 26), crono))  # esperado: U1
    print("19 abr (fin S3):", unidad_que_cierra(date(2026, 4, 19), crono))  # esperado: None
    print("24 may (fin S8):", unidad_que_cierra(date(2026, 5, 24), crono))  # esperado: U2
    print("26 jul (fin S16):", unidad_que_cierra(date(2026, 7, 26), crono)) # esperado: U4
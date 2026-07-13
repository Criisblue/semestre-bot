import os
import argparse
import requests
import motor
from datetime import date, timedelta

CHAT_ID = 8887727426   # en la Fase 6 esto será la lista de usuarios registrados


def enviar_mensaje(chat_id, texto):
    """Envía un mensaje a Telegram. Lee el token solo cuando se usa."""
    token = os.environ["BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = {"chat_id": chat_id, "text": texto}
    return requests.post(url, data=datos).json()


def clases_de_hoy(fecha, horario):
    dia = motor.DIAS[fecha.weekday()]
    return horario["horario"].get(dia, [])


def entregables_en_fecha(fecha, crono, horario):
    items = []
    sem = motor.semana_actual(fecha, crono)
    if sem is not None:
        for m in motor.materias_del_horario(horario):
            if motor.deadline_quiz(sem, m, crono, horario) == fecha:
                items.append(f"QUIZ de {m}")
        if motor.deadline_aa(sem, crono) == fecha:
            items.append("Actividad Autónoma (AA)")
    for bloque in crono["entregables"]["task"]:
        if bloque["vence"] == fecha:
            items.append("TASK (H5P) de todas las materias")
    return items


def texto_diario(fecha, crono, horario):
    dia_nombre = motor.DIAS[fecha.weekday()].capitalize()
    lineas = [f"☀️ Buenos días — {dia_nombre} {fecha.strftime('%d/%m')}"]
    sem = motor.semana_actual(fecha, crono)
    lineas.append(f"Semana {sem} de 16" if sem else "Fuera de semanas de contenido")
    feriado = motor.es_feriado(fecha, crono)
    if feriado:
        lineas.append(f"🎉 Hoy es feriado: {feriado}")
    clases = clases_de_hoy(fecha, horario)
    if clases:
        lineas.append("\n📚 Clases de hoy:")
        for c in clases:
            lineas.append(f"  {c['hora']}h — {c['materia']} ({c['tipo']})")
    else:
        lineas.append("\nHoy no tienes clases 🎈")
    hoy = entregables_en_fecha(fecha, crono, horario)
    if hoy:
        lineas.append("\n⏰ Vence HOY (medianoche):")
        for e in hoy:
            lineas.append(f"  • {e}")
    manana = entregables_en_fecha(fecha + timedelta(days=1), crono, horario)
    if manana:
        lineas.append("\n👀 Vence MAÑANA:")
        for e in manana:
            lineas.append(f"  • {e}")
    return "\n".join(lineas)


def barra_progreso(sem, total=16):
    llenos = round(sem / total * 10)
    return "[" + "█" * llenos + "░" * (10 - llenos) + f"] {sem}/{total}"


def texto_semanal(fecha, crono, horario):
    inicio = fecha + timedelta(days=1)
    sem = motor.semana_actual(inicio, crono)
    lineas = ["🗓️ Resumen semanal"]
    if sem is None:
        lineas.append("La próxima semana no es de contenido (parcial o receso).")
        return "\n".join(lineas)
    lineas.append(f"Empieza la Semana {sem} de 16")
    lineas.append(barra_progreso(sem))
    lineas.append("\n📋 QUIZ por materia:")
    for m in motor.materias_del_horario(horario):
        q = motor.deadline_quiz(sem, m, crono, horario)
        lineas.append(f"  {m}: {q.strftime('%d/%m') if q else '—'}")
    task = motor.deadline_task(sem, crono)
    lineas.append(f"\n📝 TASK (H5P): {task.strftime('%d/%m') if task else '—'}")
    aa_esta = motor.deadline_aa(sem, crono)
    aa_sig = motor.deadline_aa(sem + 1, crono)
    if aa_esta:
        lineas.append(f"📌 Actividad Autónoma: TOCA esta semana (vence {aa_esta.strftime('%d/%m')})")
    elif aa_sig:
        lineas.append(f"📌 Actividad Autónoma: NO esta semana; toca la próxima (vence {aa_sig.strftime('%d/%m')})")
    else:
        lineas.append("📌 Actividad Autónoma: no aplica")
    p = motor.proximo_parcial(inicio, crono)
    if p:
        dias = (p["inicio"] - inicio).days
        lineas.append(f"\n🎯 {p['nombre']} en {dias} días ({p['inicio'].strftime('%d/%m')})")
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Envía alertas del Semestre Bot")
    parser.add_argument("tipo", choices=["diaria", "semanal"])
    parser.add_argument("--dry-run", action="store_true", help="Solo imprime, no envía")
    parser.add_argument("--fecha", help="YYYY-MM-DD para simular (por defecto hoy)")
    args = parser.parse_args()

    crono = motor.cargar_cronograma()
    horario = motor.cargar_horario("2026-1S_segundo_A")
    fecha = date.fromisoformat(args.fecha) if args.fecha else date.today()

    texto = texto_diario(fecha, crono, horario) if args.tipo == "diaria" else texto_semanal(fecha, crono, horario)

    if args.dry_run:
        print("[DRY-RUN] No se envía. Texto:\n")
        print(texto)
    else:
        print(enviar_mensaje(CHAT_ID, texto))


if __name__ == "__main__":
    main()
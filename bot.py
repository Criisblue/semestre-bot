import os
import motor
import db
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
CRONO = motor.cargar_cronograma()


def horario_de(chat_id):
    reg = db.obtener_usuario(chat_id)
    if reg is None:
        return None
    nombre = f"{CRONO['semestre']}_{reg['semestre']}_{reg['paralelo']}"
    return motor.cargar_horario(nombre)


async def start(update, context):
    botones = [[InlineKeyboardButton("Segundo", callback_data="sem:segundo")]]
    await update.message.reply_text(
        "¡Bienvenido a Tukey! 🤖\nElige tu semestre:",
        reply_markup=InlineKeyboardMarkup(botones),
    )


async def boton(update, context):
    query = update.callback_query
    await query.answer()
    dato = query.data
    if dato.startswith("sem:"):
        semestre = dato.split(":")[1]
        context.user_data["semestre"] = semestre
        botones = [[
            InlineKeyboardButton("Paralelo A", callback_data="par:A"),
            InlineKeyboardButton("Paralelo B", callback_data="par:B"),
        ]]
        await query.edit_message_text(
            f"Semestre: {semestre}. Ahora elige tu paralelo:",
            reply_markup=InlineKeyboardMarkup(botones),
        )
    elif dato.startswith("par:"):
        paralelo = dato.split(":")[1]
        semestre = context.user_data.get("semestre", "segundo")
        db.guardar_usuario(query.message.chat_id, semestre, paralelo)
        await query.edit_message_text(
            f"✅ Registrado: {semestre} paralelo {paralelo}.\n"
            "Comandos: /donde /horario /semana /unidad"
        )


async def donde(update, context):
    hoy = date.today()
    sem = motor.semana_actual(hoy, CRONO)
    if sem is None:
        await update.message.reply_text("Hoy no es semana de contenido (parcial o receso).")
        return
    uid = motor.unidad_de_semana(sem, CRONO)
    tema = motor.tema_de_semana(sem, CRONO)
    pct = round(sem / 16 * 100)
    lineas = [f"📍 Semana {sem} de 16 ({pct}% del semestre)",
              f"Unidad {uid} — Tema {tema}"]
    p = motor.proximo_parcial(hoy, CRONO)
    if p:
        dias = (p["inicio"] - hoy).days
        lineas.append(f"🎯 {p['nombre']} en {dias} días")
    await update.message.reply_text("\n".join(lineas))


async def horario(update, context):
    hor = horario_de(update.message.chat_id)
    if hor is None:
        await update.message.reply_text("Primero regístrate con /start.")
        return
    args = context.args
    if args and args[0].lower() == "semana":
        lineas = ["🗓️ Horario de la semana:"]
        for dia in motor.DIAS:
            clases = hor["horario"].get(dia, [])
            if clases:
                lineas.append(f"\n{dia.capitalize()}:")
                for c in clases:
                    lineas.append(f"  {c['hora']}h — {c['materia']} ({c['tipo']})")
    else:
        dia = args[0].lower() if args else motor.DIAS[date.today().weekday()]
        clases = hor["horario"].get(dia, [])
        if not clases:
            await update.message.reply_text(f"No hay clases el {dia}.")
            return
        lineas = [f"📚 {dia.capitalize()}:"]
        for c in clases:
            lineas.append(f"  {c['hora']}h — {c['materia']} ({c['tipo']})")
    await update.message.reply_text("\n".join(lineas))


async def semana(update, context):
    hor = horario_de(update.message.chat_id)
    if hor is None:
        await update.message.reply_text("Primero regístrate con /start.")
        return
    sem = motor.semana_actual(date.today(), CRONO)
    if sem is None:
        await update.message.reply_text("Esta no es semana de contenido.")
        return
    lineas = [f"📋 Entregables — Semana {sem}:", "\nQUIZ:"]
    for m in motor.materias_del_horario(hor):
        q = motor.deadline_quiz(sem, m, CRONO, hor)
        lineas.append(f"  {m}: {q.strftime('%d/%m') if q else '—'}")
    task = motor.deadline_task(sem, CRONO)
    lineas.append(f"\n📝 TASK (H5P): {task.strftime('%d/%m') if task else '—'}")
    aa = motor.deadline_aa(sem, CRONO)
    lineas.append(f"📌 AA: {'vence ' + aa.strftime('%d/%m') if aa else 'no toca esta semana'}")
    await update.message.reply_text("\n".join(lineas))


async def unidad(update, context):
    reg = db.obtener_usuario(update.message.chat_id)
    if reg is None:
        await update.message.reply_text("Primero regístrate con /start.")
        return
    materia = context.args[0].lower() if context.args else "fundamentos"
    try:
        mat = motor.cargar_materia(reg["semestre"], materia)
    except FileNotFoundError:
        await update.message.reply_text(f"No tengo el sílabo de '{materia}' todavía.")
        return
    sem = motor.semana_actual(date.today(), CRONO)
    uid = motor.unidad_de_semana(sem, CRONO) if sem else None
    unidades = mat["unidades"]
    actual = next((u for u in unidades if u["id"] == uid), None)
    if actual is None:
        await update.message.reply_text("Ahora no estás dentro de una unidad de contenido.")
        return
    lineas = [f"📘 {mat['nombre']}",
              f"\nUnidad {actual['id']}: {actual['nombre']}",
              f"🎯 {actual['objetivo']}"]
    idx = unidades.index(actual)
    if idx + 1 < len(unidades):
        sig = unidades[idx + 1]
        lineas.append(f"\n➡️ Luego viene {sig['id']}: {sig['nombre']}")
    await update.message.reply_text("\n".join(lineas))


def main():
    db.init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("donde", donde))
    app.add_handler(CommandHandler("horario", horario))
    app.add_handler(CommandHandler("semana", semana))
    app.add_handler(CommandHandler("unidad", unidad))
    app.add_handler(CallbackQueryHandler(boton))
    print("Bot corriendo... (Ctrl+C para detener)")
    app.run_polling()


if __name__ == "__main__":
    main()
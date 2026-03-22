#!/usr/bin/env python3
"""
Import QuitTxt Protocol into EzMsg Database.

This script creates:
- QuitTxt project
- System variables (quit_date, preferred_time, language, etc.)
- Message templates with EN/ES localizations
- Messaging nodes with workflow connections
- Keywords (EXIT, SALIR, STOP, HELP, etc.)
"""

import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5433/ezmsg"

# Project config
PROJECT_NAME = "QuitTxt UTSA Study"
PROJECT_DESCRIPTION = """
QuitTxt Smoking Cessation Messaging Protocol - UTSA Research Study

A comprehensive bilingual (English/Spanish) text messaging intervention
for smoking cessation targeting young adult smokers (18-30 years).

Protocol includes:
- Intake sequence with quit date selection
- Pre-quit preparation messages (-6 to -1 days)
- Quit day messages (Q1-Q21+)
- Intermittent motivational messages
- Weekly checkout surveys
- HELPNOW/AYUDAYA crisis support
"""

# Variables to create
VARIABLES = [
    # System variables
    {"name": "quit_date", "display_name": "Quit Date", "type": "DATETIME", "description": "Participant's selected quit date"},
    {"name": "preferred_time", "display_name": "Preferred Message Time", "type": "STRING", "default_value": "08:00", "description": "Preferred time for morning messages (7-10 AM)"},
    {"name": "language", "display_name": "Language", "type": "STRING", "default_value": "en", "description": "Participant language preference (en/es)"},
    {"name": "cigarettes_per_day", "display_name": "Cigarettes Per Day", "type": "INTEGER", "description": "Daily cigarette consumption"},
    {"name": "days_until_quit", "display_name": "Days Until Quit", "type": "INTEGER", "default_value": "7", "description": "Days selected until quit date (7-14)"},
    {"name": "cost_per_pack", "display_name": "Cost Per Pack", "type": "DECIMAL", "default_value": "8.00", "description": "Local cost of cigarettes per pack"},
    {"name": "participant_name", "display_name": "Participant Name", "type": "STRING", "description": "Participant's first name for personalization"},
    {"name": "money_saved", "display_name": "Money Saved", "type": "DECIMAL", "description": "Calculated money saved since quitting"},
    {"name": "support_person", "display_name": "Support Person", "type": "STRING", "description": "Name of support person identified"},
    {"name": "enrolled_date", "display_name": "Enrollment Date", "type": "DATETIME", "description": "Date participant enrolled in study"},
    {"name": "current_day", "display_name": "Current Day", "type": "INTEGER", "description": "Current day in the quit journey"},
    {"name": "last_checkout_response", "display_name": "Last Checkout Response", "type": "STRING", "description": "Response from last weekly checkout"},
    {"name": "slip_reason", "display_name": "Slip Reason", "type": "STRING", "description": "Reason for smoking slip (if applicable)"},
]

# Keywords for message routing
KEYWORDS = [
    # Opt-out keywords
    {"keyword_text": "EXIT", "action_type": "OPT_OUT", "language": "en"},
    {"keyword_text": "SALIR", "action_type": "OPT_OUT", "language": "es"},
    {"keyword_text": "STOP", "action_type": "OPT_OUT", "language": "en"},
    {"keyword_text": "QUIT", "action_type": "OPT_OUT", "language": "en"},
    # Help keywords
    {"keyword_text": "HELP", "action_type": "HELP", "language": "en"},
    {"keyword_text": "AYUDA", "action_type": "HELP", "language": "es"},
    {"keyword_text": "HELPNOW", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_RESPONSE", "language": "en"},
    {"keyword_text": "AYUDAYA", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_RESPONSE", "language": "es"},
    # Response keywords for checkout
    {"keyword_text": "YES", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "yes", "language": "en"},
    {"keyword_text": "SI", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "yes", "language": "es"},
    {"keyword_text": "NO", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "no", "language": None},
    # Slip reasons
    {"keyword_text": "BADMOOD", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "badmood", "language": "en"},
    {"keyword_text": "MALHUMOR", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "badmood", "language": "es"},
    {"keyword_text": "STRESS", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "stress", "language": "en"},
    {"keyword_text": "ESTRES", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "stress", "language": "es"},
    {"keyword_text": "SMOKERS", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "smokers", "language": "en"},
    {"keyword_text": "FUMADORES", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "smokers", "language": "es"},
    {"keyword_text": "ALCOHOL", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "alcohol", "language": None},
]

# Message templates - Intake sequence
INTAKE_TEMPLATES = [
    {
        "name": "INTAKE_WELCOME",
        "description": "Welcome message with YouTube link",
        "en": {
            "text": "Welcome to the Quitxt study! Watch this brief video and then we'll get started: https://youtu.be/XdMGxLzuaLA",
            "media_url": "https://youtu.be/XdMGxLzuaLA",
        },
        "es": {
            "text": "Bienvenido al estudio Quitxt! Mira este breve video y luego empezamos: https://youtu.be/oKl_PvYXQ58",
            "media_url": "https://youtu.be/oKl_PvYXQ58",
        },
    },
    {
        "name": "INTAKE_STUDY_INFO",
        "description": "Study information with EXIT/SALIR option",
        "en": {
            "text": "Quitxt is a text message study to help you quit smoking. You'll receive short messages over the next few weeks to help you quit. If at any time you want to leave the study, respond EXIT.",
        },
        "es": {
            "text": "Quitxt es un estudio por mensaje de texto para ayudarte a dejar de fumar. Recibirás mensajes cortos por las próximas semanas. Si deseas dejar el estudio en cualquier momento responde SALIR.",
        },
    },
    {
        "name": "INTAKE_QUIZ_CPD",
        "description": "Pop quiz - cigarettes per day",
        "en": {
            "text": "How many cigarettes do you smoke per day?",
            "quick_replies": [
                {"label": "1-5", "value": "1-5"},
                {"label": "6-10", "value": "6-10"},
                {"label": "11-20", "value": "11-20"},
                {"label": "21+", "value": "21+"},
            ],
        },
        "es": {
            "text": "¿Cuántos cigarrillos fumas al día?",
            "quick_replies": [
                {"label": "1-5", "value": "1-5"},
                {"label": "6-10", "value": "6-10"},
                {"label": "11-20", "value": "11-20"},
                {"label": "21+", "value": "21+"},
            ],
        },
    },
    {
        "name": "INTAKE_NICOTINE_INFO",
        "description": "Nicotine replacement therapy information",
        "en": {
            "text": "Using nicotine replacement (patches, gum, lozenges) can double your chances of quitting. Tap pic below for more info: https://quitxtstudy.org/helpful-resources/nicotine-replacement",
            "media_url": "https://quitxtstudy.org/helpful-resources/nicotine-replacement",
        },
        "es": {
            "text": "Usar reemplazo de nicotina (parches, chicles, pastillas) puede duplicar tus probabilidades de dejar de fumar. Clic el pic abajo: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/terapia-de-reemplazo-de-nicotina",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/terapia-de-reemplazo-de-nicotina",
        },
    },
    {
        "name": "INTAKE_REASONS",
        "description": "Link to reasons for quitting",
        "en": {
            "text": "Think about all the reasons you want to quit smoking. Write them down and keep them with you. Tap pic below: https://quitxtstudy.org/reasons",
            "media_url": "https://quitxtstudy.org/reasons",
        },
        "es": {
            "text": "Piensa en todas las razones por las que quieres dejar de fumar. Escríbelas y guárdalas. Clic el pic abajo: https://quitxtstudy.org/spanish/razones",
            "media_url": "https://quitxtstudy.org/spanish/razones",
        },
    },
    {
        "name": "INTAKE_SUPPORT",
        "description": "Support person question",
        "en": {
            "text": "Who will support your decision to quit? Think of someone who can help encourage you.",
        },
        "es": {
            "text": "¿Quién apoyará tu decisión de dejar de fumar? Piensa en alguien que pueda animarte.",
        },
    },
    {
        "name": "INTAKE_READY_CHECK",
        "description": "Ready to quit tomorrow?",
        "en": {
            "text": "Are you ready to quit smoking tomorrow?",
            "quick_replies": [
                {"label": "Yes, let's do it!", "value": "YES_TOMORROW"},
                {"label": "Not yet, need more time", "value": "NEED_TIME"},
            ],
        },
        "es": {
            "text": "¿Estás listo para dejar de fumar mañana?",
            "quick_replies": [
                {"label": "Sí, ¡hagámoslo!", "value": "YES_TOMORROW"},
                {"label": "Todavía no, necesito más tiempo", "value": "NEED_TIME"},
            ],
        },
    },
    {
        "name": "INTAKE_SET_QUIT_DATE",
        "description": "Select quit date (7-14 days)",
        "en": {
            "text": "No problem! Let's set a quit date. When would you like to quit? (Choose 7-14 days from today)",
            "quick_replies": [
                {"label": "7 days", "value": "7"},
                {"label": "10 days", "value": "10"},
                {"label": "14 days", "value": "14"},
            ],
        },
        "es": {
            "text": "¡No hay problema! Vamos a fijar una fecha para dejar de fumar. ¿Cuándo te gustaría dejarlo? (Elige 7-14 días a partir de hoy)",
            "quick_replies": [
                {"label": "7 días", "value": "7"},
                {"label": "10 días", "value": "10"},
                {"label": "14 días", "value": "14"},
            ],
        },
    },
    {
        "name": "INTAKE_SET_TIME",
        "description": "Set preferred message time",
        "en": {
            "text": "What time would you like to receive your morning messages?",
            "quick_replies": [
                {"label": "7:00 AM", "value": "07:00"},
                {"label": "7:30 AM", "value": "07:30"},
                {"label": "8:00 AM", "value": "08:00"},
                {"label": "8:30 AM", "value": "08:30"},
                {"label": "9:00 AM", "value": "09:00"},
                {"label": "9:30 AM", "value": "09:30"},
                {"label": "10:00 AM", "value": "10:00"},
            ],
        },
        "es": {
            "text": "¿A qué hora te gustaría recibir tus mensajes de la mañana?",
            "quick_replies": [
                {"label": "7:00 AM", "value": "07:00"},
                {"label": "7:30 AM", "value": "07:30"},
                {"label": "8:00 AM", "value": "08:00"},
                {"label": "8:30 AM", "value": "08:30"},
                {"label": "9:00 AM", "value": "09:00"},
                {"label": "9:30 AM", "value": "09:30"},
                {"label": "10:00 AM", "value": "10:00"},
            ],
        },
    },
    {
        "name": "INTAKE_CONFIRMATION",
        "description": "Quit date confirmation",
        "en": {
            "text": "Great! Your quit date is set for {{quit_date}}. We'll start sending you messages to help you prepare. You've got this!",
        },
        "es": {
            "text": "¡Genial! Tu fecha para dejar de fumar es {{quit_date}}. Empezaremos a enviarte mensajes para ayudarte a prepararte. ¡Tú puedes!",
        },
    },
]

# Quit Day templates (Q1-Q7 morning sequences)
QUIT_DAY_TEMPLATES = [
    # Q1 - Quit Day 1
    {
        "name": "Q1_MORNING_1",
        "description": "Q1 - Today is the day!",
        "en": {
            "text": "Today is the day! Now the journey to a smokefree life begins. You can do it! Watch video: https://youtu.be/A2c3AJUvXLQ",
            "media_url": "https://youtu.be/A2c3AJUvXLQ",
        },
        "es": {
            "text": "¡Hoy es el día! Hoy empieza la jornada hacia una vida libre del tabaco. ¡Tú puedes hacerlo! Mira video: https://youtu.be/2ROMdVXWy6M",
            "media_url": "https://youtu.be/2ROMdVXWy6M",
        },
    },
    {
        "name": "Q1_TRIGGERS",
        "description": "Q1 - Triggers information",
        "en": {
            "text": "Get started with some info about triggers – things and situations that make you feel like smoking. Tap pic: https://quitxtstudy.org/helpful-resources/triggers",
            "media_url": "https://quitxtstudy.org/helpful-resources/triggers",
        },
        "es": {
            "text": "Comienza con información sobre las cosas y situaciones que te provocan antojos de fumar. Clic el pic: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/disparadores",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/disparadores",
        },
    },
    {
        "name": "Q1_BD",
        "description": "Q1 - Binge drinking warning",
        "en": {
            "text": "If you drink, you might want to smoke. Here are some ideas for managing alcohol: https://quitxtstudy.org/helpful-resources/binge-drinking",
            "media_url": "https://quitxtstudy.org/helpful-resources/binge-drinking",
        },
        "es": {
            "text": "Si tomas, posiblemente querrás fumar. Aquí ideas para controlar la bebida: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/consumo-intensivo-de-alcohol",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/consumo-intensivo-de-alcohol",
        },
    },
    # Q2 - Quit Day 2
    {
        "name": "Q2_BREATHING",
        "description": "Q2 - Breathing exercises",
        "en": {
            "text": "Start today with breathing exercises to help you cope with the urge to smoke. Relax away the craving! Breathe in VERY SLOWLY through your nose, fill your lungs from bottom up, then exhale VERY SLOWLY through your mouth. Do it 3 times. Tap pic: https://quitxtstudy.org/helpful-resources/breathing-exercises",
            "media_url": "https://quitxtstudy.org/helpful-resources/breathing-exercises",
        },
        "es": {
            "text": "Empieza el día con ejercicios de respiración para ayudarte con los antojos de fumar. Para relajar el antojo: Respira MUY LENTAMENTE por la nariz y llena tus pulmones de abajo hacia arriba. Después, MUY LENTAMENTE sopla el aire por la boca. Hazlo 3 veces. Clic el pic: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/ejercicios-de-respiracion",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/ejercicios-de-respiracion",
        },
    },
    # Q3 - Quit Day 3
    {
        "name": "Q3_INSTEAD",
        "description": "Q3 - Instead of smoking",
        "en": {
            "text": "Chew gum instead of smoking when you want to smoke the most. Tap pic for more ideas: https://quitxtstudy.org/helpful-resources/instead-of-smoking",
            "media_url": "https://quitxtstudy.org/helpful-resources/instead-of-smoking",
        },
        "es": {
            "text": "Mastica chicle en lugar de fumar cuando tengas antojo de un cigarrillo. Para más ideas: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/en-lugar-de-fumar",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/en-lugar-de-fumar",
        },
    },
    {
        "name": "Q3_SUPPORT",
        "description": "Q3 - Support from family/friends",
        "en": {
            "text": "You can get support from family and friends. Get in touch with them today to tell them how you're doing. Tap pic: https://quitxtstudy.org/helpful-resources/support",
            "media_url": "https://quitxtstudy.org/helpful-resources/support",
        },
        "es": {
            "text": "Puedes recibir apoyo de tu familia y amigos. Comunícate con ellos hoy y déjales saber cómo estás. Clic el pic: https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/apoyo",
            "media_url": "https://quitxtstudy.org/spanish/recursos-%C3%BAtiles/apoyo",
        },
    },
    {
        "name": "Q3_HELPNOW",
        "description": "Q3 - HELPNOW prompt",
        "en": {
            "text": "If you are having a hard time, text HELPNOW and we will answer.",
        },
        "es": {
            "text": "Si estás pasando por un mal momento envía AYUDAYA y te responderemos.",
        },
    },
    # Q7 - Weekly checkout
    {
        "name": "Q7_CHECKOUT",
        "description": "Q7 - Weekly checkout survey",
        "en": {
            "text": "During the past 7 days, have you smoked a cigarette, even a puff?",
            "quick_replies": [
                {"label": "Yes, It was hard.", "value": "YES_SMOKED"},
                {"label": "No, I did not smoke!", "value": "NO_SMOKEFREE"},
            ],
        },
        "es": {
            "text": "Durante los últimos 7 días, ¿ha fumado cigarrillos de tabaco, aunque fuera una sola fumada?",
            "quick_replies": [
                {"label": "Si, fue difícil.", "value": "YES_SMOKED"},
                {"label": "No, ¡No fumé!", "value": "NO_SMOKEFREE"},
            ],
        },
    },
    {
        "name": "Q7_CHECKOUT_SMOKEFREE",
        "description": "Q7 - Congrats for staying smokefree",
        "en": {
            "text": "CONGRATS from Quitxt! You're awesome! Tomorrow's a new day… let's touch base in the morning and make it smokefree!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_8pm_checkout_Minions.gif",
        },
        "es": {
            "text": "¡FELICITACIONES de Quitxt! Mañana es un nuevo día… hagamos que sea un día ¡libre de cigarrillos!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_8pm_checkout_bravo_esp.gif",
        },
    },
    {
        "name": "Q7_CHECKOUT_SLIP",
        "description": "Q7 - Response if slipped",
        "en": {
            "text": "That's OK. Remember, it takes practice. What caused you to start smoking again?",
            "quick_replies": [
                {"label": "Bad mood", "value": "BADMOOD"},
                {"label": "Stress", "value": "STRESS"},
                {"label": "Smokers", "value": "SMOKERS"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Other", "value": "OTHER"},
            ],
        },
        "es": {
            "text": "Es OK. Recuerda, toma práctica. ¿Qué te hizo fumar de nuevo?",
            "quick_replies": [
                {"label": "Mal humor", "value": "MALHUMOR"},
                {"label": "Estrés", "value": "ESTRES"},
                {"label": "Fumadores", "value": "FUMADORES"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Otra", "value": "OTRA"},
            ],
        },
    },
]

# Intermittent messages (1pm, 4pm, 7pm motivational)
INTERMITTENT_TEMPLATES = [
    # Q1 Intermittent
    {
        "name": "Q1_IM_1PM",
        "description": "Q1 1pm - Hours smokefree",
        "en": {
            "text": "12+ hours smokefree! Great job! Keep it up!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_1pm_dance_winner.gif",
        },
        "es": {
            "text": "¡12+ horas sin fumar! ¡Buen trabajo! ¡Sigue así!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_1pm_dance_winner.gif",
        },
    },
    {
        "name": "Q1_IM_4PM",
        "description": "Q1 4pm - Cravings tip",
        "en": {
            "text": "Any cravings? Remember, they pass! Delay, Drink water, Deep breathe, Do something else. You got this!",
        },
        "es": {
            "text": "¿Tienes antojos? ¡Recuerda, pasan! Demora, bebe agua, respira profundo y haz alguna otra cosa. ¡Tú puedes!",
        },
    },
    {
        "name": "Q1_IM_7PM",
        "description": "Q1 7pm - Evening motivation",
        "en": {
            "text": "You made it through day 1! Get some sleep and tomorrow we'll tackle day 2 together.",
        },
        "es": {
            "text": "¡Lo lograste, día 1! Descansa bien y mañana enfrentamos el día 2 juntos.",
        },
    },
    # Q2 Intermittent
    {
        "name": "Q2_IM_1PM",
        "description": "Q2 1pm - 24 hours",
        "en": {
            "text": "24 hours smokefree and counting!!! Be sure to reward yourself. Each hour you're smokefree, say or do something nice for yourself.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_1pm_male_relaxing.gif",
        },
        "es": {
            "text": "¡24 horas sin fumar y contando! Asegúrate de premiarte. Cada hora sin fumar haz algo que te agrade.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_1pm_male_relaxing.gif",
        },
    },
    {
        "name": "Q2_IM_4PM",
        "description": "Q2 4pm - Lung function",
        "en": {
            "text": "Health experts say smoking weakens the function of the lungs. Quitting smoking… Best decision ever!!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_4pm_Thumbup.gif",
        },
        "es": {
            "text": "Los expertos de salud dicen que fumar debilita la función de los pulmones. Dejar de fumar…¡La mejor decisión de tu vida!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_4pm_Thumbup.gif",
        },
    },
    {
        "name": "Q2_IM_7PM",
        "description": "Q2 7pm - Got your back",
        "en": {
            "text": "Quitting is hard, but YOU CAN DO IT! Make yourself proud & ditch tobacco for good. We got your back!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_7pm_Gotyourback_LebronJames.gif",
        },
        "es": {
            "text": "Dejar de fumar es difícil, pero ¡TÚ PUEDES LOGRARLO! Haz que te sientas orgulloso de ti mismo y abandona el tabaco. ¡Estamos contigo!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q2_7pm_Gotyourback_LebronJames.gif",
        },
    },
]

# HELPNOW Response template
HELPNOW_TEMPLATE = {
    "name": "HELPNOW_RESPONSE",
    "description": "Response to HELPNOW/AYUDAYA keyword",
    "en": {
        "text": "We're here for you! Try these tips:\n1. Take 3 deep breaths\n2. Drink a glass of water\n3. Go for a short walk\n4. Call a supportive friend\n\nRemember: cravings pass in 5 minutes. You've got this!\n\nFor immediate help, call 1-800-QUIT-NOW",
    },
    "es": {
        "text": "¡Estamos aquí para ti! Prueba estos consejos:\n1. Respira profundo 3 veces\n2. Bebe un vaso de agua\n3. Da una caminata corta\n4. Llama a un amigo que te apoye\n\nRecuerda: los antojos pasan en 5 minutos. ¡Tú puedes!\n\nPara ayuda inmediata, llama 1-800-QUIT-NOW",
    },
}


async def create_project(session: AsyncSession, user_id: int) -> int:
    """Create the QuitTxt project."""
    from app.models import Project

    # Check if project exists
    result = await session.execute(
        select(Project).where(Project.name == PROJECT_NAME)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"Project '{PROJECT_NAME}' already exists (ID: {existing.id})")
        return existing.id

    project = Project(
        user_id=user_id,
        name=PROJECT_NAME,
        description=PROJECT_DESCRIPTION,
        status="ACTIVE",
        settings={
            "default_language": "en",
            "supported_languages": ["en", "es"],
            "default_message_time": "08:00",
            "timezone": "America/Chicago",
        },
    )
    session.add(project)
    await session.flush()
    print(f"Created project '{PROJECT_NAME}' (ID: {project.id})")
    return project.id


async def create_variables(session: AsyncSession, project_id: int) -> dict[str, int]:
    """Create project variables."""
    from app.models import Variable

    variable_ids = {}

    for var_def in VARIABLES:
        result = await session.execute(
            select(Variable).where(
                Variable.project_id == project_id,
                Variable.name == var_def["name"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            variable_ids[var_def["name"]] = existing.id
            continue

        variable = Variable(
            project_id=project_id,
            name=var_def["name"],
            display_name=var_def.get("display_name", var_def["name"]),
            type=var_def.get("type", "STRING"),
            source_type=var_def.get("source_type", "MANUAL"),
            default_value=var_def.get("default_value"),
            description=var_def.get("description"),
        )
        session.add(variable)
        await session.flush()
        variable_ids[var_def["name"]] = variable.id
        print(f"  Created variable: {var_def['name']}")

    return variable_ids


async def create_template(
    session: AsyncSession,
    project_id: int,
    template_def: dict,
    en_lang_id: int,
    es_lang_id: int,
) -> int:
    """Create a message template with localizations."""
    from app.models import MessageTemplate, MessageTemplateText

    # Check if template exists
    result = await session.execute(
        select(MessageTemplate).where(
            MessageTemplate.project_id == project_id,
            MessageTemplate.name == template_def["name"],
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing.id

    template = MessageTemplate(
        project_id=project_id,
        name=template_def["name"],
        description=template_def.get("description"),
        type="STANDARD",
    )
    session.add(template)
    await session.flush()

    # Create English text
    if "en" in template_def:
        en_text = MessageTemplateText(
            template_id=template.id,
            language_id=en_lang_id,
            message_text=template_def["en"].get("text"),
            media_url=template_def["en"].get("media_url"),
            media_type="image" if template_def["en"].get("media_url") else None,
            quick_replies=template_def["en"].get("quick_replies", []),
        )
        session.add(en_text)

    # Create Spanish text
    if "es" in template_def:
        es_text = MessageTemplateText(
            template_id=template.id,
            language_id=es_lang_id,
            message_text=template_def["es"].get("text"),
            media_url=template_def["es"].get("media_url"),
            media_type="image" if template_def["es"].get("media_url") else None,
            quick_replies=template_def["es"].get("quick_replies", []),
        )
        session.add(es_text)

    print(f"  Created template: {template_def['name']}")
    return template.id


async def create_templates(
    session: AsyncSession, project_id: int, en_lang_id: int, es_lang_id: int
) -> dict[str, int]:
    """Create all message templates."""
    template_ids = {}

    all_templates = (
        INTAKE_TEMPLATES + QUIT_DAY_TEMPLATES + INTERMITTENT_TEMPLATES + [HELPNOW_TEMPLATE]
    )

    for template_def in all_templates:
        template_id = await create_template(
            session, project_id, template_def, en_lang_id, es_lang_id
        )
        template_ids[template_def["name"]] = template_id

    return template_ids


async def create_timing_elements(session: AsyncSession, project_id: int) -> dict[str, int]:
    """Create timing elements for message delays."""
    from app.models import TimingElement

    timing_ids = {}

    timing_defs = [
        {"name": "NO_DELAY", "offset_minutes": 0, "description": "No delay"},
        {"name": "2_MIN_DELAY", "offset_minutes": 2, "description": "2 minute delay between messages"},
        {"name": "1_HOUR_DELAY", "offset_hours": 1, "description": "1 hour delay"},
        {"name": "MORNING_8AM", "overwrite_time": True, "overwritten_hours": 8, "overwritten_minutes": 0, "description": "Send at 8 AM"},
        {"name": "INTERMITTENT_1PM", "overwrite_time": True, "overwritten_hours": 13, "overwritten_minutes": 0, "description": "Send at 1 PM"},
        {"name": "INTERMITTENT_4PM", "overwrite_time": True, "overwritten_hours": 16, "overwritten_minutes": 0, "description": "Send at 4 PM"},
        {"name": "INTERMITTENT_7PM", "overwrite_time": True, "overwritten_hours": 19, "overwritten_minutes": 0, "description": "Send at 7 PM"},
        {"name": "CHECKOUT_8PM", "overwrite_time": True, "overwritten_hours": 20, "overwritten_minutes": 0, "description": "Send at 8 PM for checkout"},
    ]

    for timing_def in timing_defs:
        result = await session.execute(
            select(TimingElement).where(
                TimingElement.project_id == project_id,
                TimingElement.name == timing_def["name"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            timing_ids[timing_def["name"]] = existing.id
            continue

        timing = TimingElement(
            project_id=project_id,
            name=timing_def["name"],
            description=timing_def.get("description"),
            offset_days=timing_def.get("offset_days", 0),
            offset_hours=timing_def.get("offset_hours", 0),
            offset_minutes=timing_def.get("offset_minutes", 0),
            overwrite_time=timing_def.get("overwrite_time", False),
            overwritten_hours=timing_def.get("overwritten_hours"),
            overwritten_minutes=timing_def.get("overwritten_minutes"),
        )
        session.add(timing)
        await session.flush()
        timing_ids[timing_def["name"]] = timing.id
        print(f"  Created timing: {timing_def['name']}")

    return timing_ids


async def create_nodes_and_edges(
    session: AsyncSession,
    project_id: int,
    template_ids: dict[str, int],
    timing_ids: dict[str, int],
) -> dict[str, int]:
    """Create messaging nodes and workflow edges."""
    from app.models import MessagingNode, MessagingNodeEdge

    node_ids = {}

    # Define nodes with their templates and timing
    node_defs = [
        # Intake flow
        {"name": "INTAKE_START", "display_name": "Intake Start", "is_entry_node": True, "template": "INTAKE_WELCOME", "timing": "NO_DELAY"},
        {"name": "INTAKE_STUDY_INFO", "display_name": "Study Info", "template": "INTAKE_STUDY_INFO", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_QUIZ", "display_name": "Cigarettes Quiz", "template": "INTAKE_QUIZ_CPD", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_NICOTINE", "display_name": "Nicotine Info", "template": "INTAKE_NICOTINE_INFO", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_REASONS", "display_name": "Reasons to Quit", "template": "INTAKE_REASONS", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_SUPPORT", "display_name": "Support Person", "template": "INTAKE_SUPPORT", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_READY", "display_name": "Ready Check", "template": "INTAKE_READY_CHECK", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_SET_DATE", "display_name": "Set Quit Date", "template": "INTAKE_SET_QUIT_DATE", "timing": "NO_DELAY"},
        {"name": "INTAKE_SET_TIME", "display_name": "Set Preferred Time", "template": "INTAKE_SET_TIME", "timing": "NO_DELAY"},
        {"name": "INTAKE_CONFIRM", "display_name": "Confirmation", "template": "INTAKE_CONFIRMATION", "timing": "NO_DELAY"},

        # Q1 Flow
        {"name": "Q1_MORNING_START", "display_name": "Q1 Morning", "template": "Q1_MORNING_1", "timing": "MORNING_8AM"},
        {"name": "Q1_TRIGGERS", "display_name": "Q1 Triggers", "template": "Q1_TRIGGERS", "timing": "2_MIN_DELAY"},
        {"name": "Q1_BD", "display_name": "Q1 Binge Drinking", "template": "Q1_BD", "timing": "2_MIN_DELAY"},
        {"name": "Q1_IM_1PM", "display_name": "Q1 1PM Message", "template": "Q1_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q1_IM_4PM", "display_name": "Q1 4PM Message", "template": "Q1_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q1_IM_7PM", "display_name": "Q1 7PM Message", "template": "Q1_IM_7PM", "timing": "INTERMITTENT_7PM"},

        # Q2 Flow
        {"name": "Q2_MORNING_START", "display_name": "Q2 Morning", "template": "Q2_BREATHING", "timing": "MORNING_8AM"},
        {"name": "Q2_IM_1PM", "display_name": "Q2 1PM Message", "template": "Q2_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q2_IM_4PM", "display_name": "Q2 4PM Message", "template": "Q2_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q2_IM_7PM", "display_name": "Q2 7PM Message", "template": "Q2_IM_7PM", "timing": "INTERMITTENT_7PM"},

        # Q3 Flow
        {"name": "Q3_MORNING_START", "display_name": "Q3 Morning", "template": "Q3_INSTEAD", "timing": "MORNING_8AM"},
        {"name": "Q3_SUPPORT", "display_name": "Q3 Support", "template": "Q3_SUPPORT", "timing": "2_MIN_DELAY"},
        {"name": "Q3_HELPNOW", "display_name": "Q3 HELPNOW Prompt", "template": "Q3_HELPNOW", "timing": "2_MIN_DELAY"},

        # Q7 Checkout
        {"name": "Q7_CHECKOUT", "display_name": "Q7 Weekly Checkout", "template": "Q7_CHECKOUT", "timing": "CHECKOUT_8PM"},
        {"name": "Q7_SMOKEFREE", "display_name": "Q7 Smokefree Response", "template": "Q7_CHECKOUT_SMOKEFREE", "timing": "NO_DELAY"},
        {"name": "Q7_SLIP", "display_name": "Q7 Slip Response", "template": "Q7_CHECKOUT_SLIP", "timing": "NO_DELAY"},

        # HELPNOW
        {"name": "HELPNOW_RESPONSE", "display_name": "HELPNOW Response", "template": "HELPNOW_RESPONSE", "timing": "NO_DELAY"},

        # Terminal nodes
        {"name": "EXIT_STUDY", "display_name": "Exit Study", "is_terminal_node": True},
        {"name": "COMPLETE_STUDY", "display_name": "Complete Study", "is_terminal_node": True},
    ]

    # Create nodes
    for node_def in node_defs:
        result = await session.execute(
            select(MessagingNode).where(
                MessagingNode.project_id == project_id,
                MessagingNode.name == node_def["name"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            node_ids[node_def["name"]] = existing.id
            continue

        node = MessagingNode(
            project_id=project_id,
            name=node_def["name"],
            display_name=node_def.get("display_name"),
            is_entry_node=node_def.get("is_entry_node", False),
            is_terminal_node=node_def.get("is_terminal_node", False),
            template_id=template_ids.get(node_def.get("template")),
            timing_element_id=timing_ids.get(node_def.get("timing")),
        )
        session.add(node)
        await session.flush()
        node_ids[node_def["name"]] = node.id
        print(f"  Created node: {node_def['name']}")

    # Define edges (workflow connections)
    edge_defs = [
        # Intake flow
        ("INTAKE_START", "INTAKE_STUDY_INFO"),
        ("INTAKE_STUDY_INFO", "INTAKE_QUIZ"),
        ("INTAKE_QUIZ", "INTAKE_NICOTINE"),
        ("INTAKE_NICOTINE", "INTAKE_REASONS"),
        ("INTAKE_REASONS", "INTAKE_SUPPORT"),
        ("INTAKE_SUPPORT", "INTAKE_READY"),
        # Branching from ready check
        ("INTAKE_READY", "Q1_MORNING_START", "YES_TOMORROW"),  # Ready tomorrow
        ("INTAKE_READY", "INTAKE_SET_DATE", "NEED_TIME"),  # Need more time
        ("INTAKE_SET_DATE", "INTAKE_SET_TIME"),
        ("INTAKE_SET_TIME", "INTAKE_CONFIRM"),

        # Q1 day flow
        ("Q1_MORNING_START", "Q1_TRIGGERS"),
        ("Q1_TRIGGERS", "Q1_BD"),
        ("Q1_BD", "Q1_IM_1PM"),
        ("Q1_IM_1PM", "Q1_IM_4PM"),
        ("Q1_IM_4PM", "Q1_IM_7PM"),
        ("Q1_IM_7PM", "Q2_MORNING_START"),

        # Q2 day flow
        ("Q2_MORNING_START", "Q2_IM_1PM"),
        ("Q2_IM_1PM", "Q2_IM_4PM"),
        ("Q2_IM_4PM", "Q2_IM_7PM"),
        ("Q2_IM_7PM", "Q3_MORNING_START"),

        # Q3 day flow
        ("Q3_MORNING_START", "Q3_SUPPORT"),
        ("Q3_SUPPORT", "Q3_HELPNOW"),

        # Q7 checkout branching
        ("Q7_CHECKOUT", "Q7_SMOKEFREE", "NO_SMOKEFREE"),
        ("Q7_CHECKOUT", "Q7_SLIP", "YES_SMOKED"),
    ]

    # Create edges
    for edge_def in edge_defs:
        parent_name = edge_def[0]
        child_name = edge_def[1]
        edge_label = edge_def[2] if len(edge_def) > 2 else None

        if parent_name not in node_ids or child_name not in node_ids:
            continue

        # Check if edge exists
        result = await session.execute(
            select(MessagingNodeEdge).where(
                MessagingNodeEdge.parent_node_id == node_ids[parent_name],
                MessagingNodeEdge.child_node_id == node_ids[child_name],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        edge = MessagingNodeEdge(
            parent_node_id=node_ids[parent_name],
            child_node_id=node_ids[child_name],
            edge_label=edge_label,
        )
        session.add(edge)
        print(f"  Created edge: {parent_name} -> {child_name}")

    return node_ids


async def create_keywords(
    session: AsyncSession,
    project_id: int,
    node_ids: dict[str, int],
    variable_ids: dict[str, int],
    en_lang_id: int,
    es_lang_id: int,
) -> None:
    """Create SMS keywords."""
    from app.models import SmsKeyword

    for kw_def in KEYWORDS:
        # Check if keyword exists
        result = await session.execute(
            select(SmsKeyword).where(
                SmsKeyword.project_id == project_id,
                SmsKeyword.keyword_text == kw_def["keyword_text"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        lang_id = None
        if kw_def.get("language") == "en":
            lang_id = en_lang_id
        elif kw_def.get("language") == "es":
            lang_id = es_lang_id

        keyword = SmsKeyword(
            project_id=project_id,
            language_id=lang_id,
            keyword_action_type=kw_def["action_type"],
            keyword_name=kw_def["keyword_text"],
            keyword_text=kw_def["keyword_text"],
            messaging_node_id=node_ids.get(kw_def.get("node_name")),
            variable_id=variable_ids.get(kw_def.get("variable")),
            variable_value=kw_def.get("value"),
            is_active=True,
        )
        session.add(keyword)
        print(f"  Created keyword: {kw_def['keyword_text']}")


async def main():
    """Main import function."""
    print("=" * 60)
    print("QuitTxt Protocol Import Script")
    print("=" * 60)

    # Create engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # Get admin user
            from app.models import User, AvailableLanguage

            result = await session.execute(select(User).where(User.email == "admin@example.com"))
            admin = result.scalar_one_or_none()

            if not admin:
                print("ERROR: Admin user not found!")
                return

            # Get language IDs
            result = await session.execute(select(AvailableLanguage).where(AvailableLanguage.short_name == "en"))
            en_lang = result.scalar_one_or_none()
            result = await session.execute(select(AvailableLanguage).where(AvailableLanguage.short_name == "es"))
            es_lang = result.scalar_one_or_none()

            if not en_lang or not es_lang:
                print("ERROR: Languages not found!")
                return

            print(f"\nAdmin user: {admin.email} (ID: {admin.id})")
            print(f"Languages: EN={en_lang.id}, ES={es_lang.id}")

            # Create project
            print("\n1. Creating project...")
            project_id = await create_project(session, admin.id)

            # Create variables
            print("\n2. Creating variables...")
            variable_ids = await create_variables(session, project_id)
            print(f"   Created {len(variable_ids)} variables")

            # Create timing elements
            print("\n3. Creating timing elements...")
            timing_ids = await create_timing_elements(session, project_id)
            print(f"   Created {len(timing_ids)} timing elements")

            # Create templates
            print("\n4. Creating message templates...")
            template_ids = await create_templates(session, project_id, en_lang.id, es_lang.id)
            print(f"   Created {len(template_ids)} templates")

            # Create nodes and edges
            print("\n5. Creating nodes and edges...")
            node_ids = await create_nodes_and_edges(session, project_id, template_ids, timing_ids)
            print(f"   Created {len(node_ids)} nodes")

            # Create keywords
            print("\n6. Creating keywords...")
            await create_keywords(session, project_id, node_ids, variable_ids, en_lang.id, es_lang.id)

            # Set initial node
            from app.models import Project
            result = await session.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one()
            project.initial_triggering_node_id = node_ids.get("INTAKE_START")

            print("\n" + "=" * 60)
            print("Import completed successfully!")
            print(f"Project ID: {project_id}")
            print(f"Templates: {len(template_ids)}")
            print(f"Variables: {len(variable_ids)}")
            print(f"Nodes: {len(node_ids)}")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

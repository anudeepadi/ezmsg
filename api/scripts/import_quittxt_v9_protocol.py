#!/usr/bin/env python3
"""
Import QuitTxt V9 Protocol into EzMsg Database.

This script creates:
- QuitTxt V9 project (UTSA study with YouTube links)
- System variables (quit_date, preferred_time, language, etc.)
- Message templates with EN/ES localizations (intake, pre-quit, quit days, intermittent, checkout)
- Messaging nodes with workflow connections
- Keywords (EXIT, SALIR, HELPNOW, AYUDAYA, etc.)
- Timing elements for message scheduling
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
PROJECT_NAME = "QuitTxt V9 UTSA Study"
PROJECT_DESCRIPTION = """
QuitTxt V9 Smoking Cessation Messaging Protocol - UTSA Research Study

A comprehensive bilingual (English/Spanish) text messaging intervention
for smoking cessation targeting young adult smokers (18-30 years).

Protocol Version: V9 (December 2025 - New Study with YouTube Links)

Protocol includes:
- Intake sequence with quit date selection (immediate or 7-14 days)
- Pre-quit preparation messages (-6 to -1 days)
- Quit day messages (Q1-Q21+)
- Morning sessions on select days
- Intermittent motivational messages throughout each day
- Weekly checkout surveys (Q7, Q14, Q21)
- HELPNOW/AYUDAYA crisis support
- Bilingual content (English/Spanish)
"""

# Variables to create
VARIABLES = [
    {"name": "quit_date", "display_name": "Quit Date", "type": "DATETIME", "description": "Participant's selected quit date"},
    {"name": "preferred_time", "display_name": "Preferred Message Time", "type": "STRING", "default_value": "08:00", "description": "Preferred time for morning messages (7-10 AM)"},
    {"name": "language", "display_name": "Language", "type": "STRING", "default_value": "en", "description": "Participant language preference (en/es)"},
    {"name": "cigarettes_per_day", "display_name": "Cigarettes Per Day", "type": "STRING", "description": "Daily cigarette consumption range"},
    {"name": "days_until_quit", "display_name": "Days Until Quit", "type": "INTEGER", "default_value": "1", "description": "Days until quit date (1 for immediate, 7-14 for delayed)"},
    {"name": "participant_name", "display_name": "Participant Name", "type": "STRING", "description": "Participant's first name for personalization"},
    {"name": "money_saved", "display_name": "Money Saved", "type": "DECIMAL", "description": "Calculated money saved since quitting"},
    {"name": "enrolled_date", "display_name": "Enrollment Date", "type": "DATETIME", "description": "Date participant enrolled in study"},
    {"name": "current_quit_day", "display_name": "Current Quit Day", "type": "INTEGER", "description": "Current day number in quit journey (Q1, Q2, etc.)"},
    {"name": "last_checkout_response", "display_name": "Last Checkout Response", "type": "STRING", "description": "Response from last weekly checkout (YES_SMOKED/NO_SMOKEFREE)"},
    {"name": "slip_reason", "display_name": "Slip Reason", "type": "STRING", "description": "Reason for smoking slip (badmood/stress/smokers/alcohol/other)"},
    {"name": "ready_to_quit", "display_name": "Ready to Quit", "type": "STRING", "description": "Whether participant is ready to quit tomorrow (YES_TOMORROW/NEED_TIME)"},
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
    # Response keywords
    {"keyword_text": "YES", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "YES_SMOKED", "language": "en"},
    {"keyword_text": "SI", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "YES_SMOKED", "language": "es"},
    {"keyword_text": "NO", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "NO_SMOKEFREE", "language": None},
    # Slip reasons
    {"keyword_text": "BADMOOD", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "badmood", "language": "en"},
    {"keyword_text": "MALHUMOR", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "badmood", "language": "es"},
    {"keyword_text": "STRESS", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "stress", "language": "en"},
    {"keyword_text": "ESTRES", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "stress", "language": "es"},
    {"keyword_text": "SMOKERS", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "smokers", "language": "en"},
    {"keyword_text": "FUMADORES", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "smokers", "language": "es"},
    {"keyword_text": "ALCOHOL", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "alcohol", "language": None},
    {"keyword_text": "OTHER", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "other", "language": "en"},
    {"keyword_text": "OTRA", "action_type": "SET_VARIABLE", "variable": "slip_reason", "value": "other", "language": "es"},
]

# ============================================================================
# INTAKE SEQUENCE TEMPLATES
# ============================================================================
INTAKE_TEMPLATES = [
    {
        "name": "INTAKE_WELCOME",
        "description": "Welcome message with YouTube video link",
        "en": {
            "text": "Welcome to Quitxt from the UT Health Science Center! Congrats on your decision to quit smoking! See why we think you're awesome, Tap pic below https://youtu.be/F_NhIMsHBf8",
            "media_url": "https://youtu.be/F_NhIMsHBf8",
        },
        "es": {
            "text": "¡Bienvenido a Quitxt del UT Health Science Center! ¡Felicitaciones por decidir dejar de fumar! Mira por qué pensamos que ¡eres genial! Clic el pic abajo https://youtu.be/2BkaHT5IhXM",
            "media_url": "https://youtu.be/2BkaHT5IhXM",
        },
    },
    {
        "name": "INTAKE_STUDY_INFO",
        "description": "Study information with EXIT/SALIR option",
        "en": {
            "text": "We'll help you quit smoking with fun messages. For more info Tap pic below. https://quitxtstudy.org/\nIf you want to leave the study, type EXIT.",
            "media_url": "https://quitxtstudy.org/",
        },
        "es": {
            "text": "Te ayudaremos a dejar de fumar con fun texts. Para más información Clic el pic abajo https://quitxtstudy.org/spanish\nSi deseas dejar el estudio, envía SALIR.",
            "media_url": "https://quitxtstudy.org/spanish",
        },
    },
    {
        "name": "INTAKE_EXIT_RESPONSE",
        "description": "Response when participant sends EXIT/SALIR",
        "en": {
            "text": "We are sorry you want to leave the study. A team member will reach out to you to talk about your reasons and complete the process. You can also contact the Quitxt study team at quitxt@uthscsa.edu to let us know your decision.",
        },
        "es": {
            "text": "Lamentamos que quieras dejar el estudio. Un miembro del equipo de investigación se comunicará contigo para hablar sobre tus razones y completar el proceso. También puedes contactar al equipo del estudio Quitxt en quitxt@uthscsa.edu para informarnos tu decisión.",
        },
    },
    {
        "name": "INTAKE_QUIZ_INTRO",
        "description": "Pop quiz introduction",
        "en": {"text": "Pop quiz before we start, just 1 easy question!"},
        "es": {"text": "Pop quiz antes de empezar, solo 1 pregunta fácil."},
    },
    {
        "name": "INTAKE_CPD",
        "description": "Cigarettes per day question",
        "en": {
            "text": "About how many cigarettes do you smoke on an average day?",
            "quick_replies": [
                {"label": "1-5", "value": "1-5"},
                {"label": "6-10", "value": "6-10"},
                {"label": "11-20", "value": "11-20"},
                {"label": "21 or more", "value": "21+"},
            ],
        },
        "es": {
            "text": "¿Cuántos cigarrillos te fumas en promedio por día?",
            "quick_replies": [
                {"label": "1-5", "value": "1-5"},
                {"label": "6-10", "value": "6-10"},
                {"label": "11-20", "value": "11-20"},
                {"label": "21 o más", "value": "21+"},
            ],
        },
    },
    {
        "name": "INTAKE_NICOTINE",
        "description": "Nicotine replacement therapy information",
        "en": {
            "text": "If you smoke a pack of cigarettes a day or more, have a cigarette within 30 minutes after waking up, or feel like you are addicted to smoking, you may benefit from nicotine replacement therapy.\nIt can help you quit smoking. Tap pic below https://quitxtstudy.org/helpful-resources/nicotine-replacement",
            "media_url": "https://quitxtstudy.org/helpful-resources/nicotine-replacement",
        },
        "es": {
            "text": "Si fumas un paquete o más de cigarrillos al día, fumas durante los primeros 30min después de despertar o sientes adicción a fumar… la terapia de reemplazo de nicotina puede beneficiarte.\nPuede ayudarte a dejar de fumar. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
        },
    },
    {
        "name": "INTAKE_REASONS",
        "description": "Reasons to quit smoking",
        "en": {
            "text": "Think about your reasons to stop smoking. You may be worried about your health, doing it for your family, to save money or other. Tap pic below https://quitxtstudy.org/reasons",
            "media_url": "https://quitxtstudy.org/reasons",
        },
        "es": {
            "text": "Piensa en tus razones para dejar de fumar. Por tu salud, por tu familia, para ahorrar dinero o por otras razones. Clic el pic abajo https://quitxtstudy.org/spanish/razones",
            "media_url": "https://quitxtstudy.org/spanish/razones",
        },
    },
    {
        "name": "INTAKE_SUPPORT",
        "description": "Support person identification",
        "en": {
            "text": "Now, think about who will support your decision to quit smoking. For example, your padres, spouse/partner, brother or sister, or your friends. You should tell them you are quitting! Tap pic below https://quitxtstudy.org/helpful-resources/support",
            "media_url": "https://quitxtstudy.org/helpful-resources/support",
        },
        "es": {
            "text": "Ahora piensa en quién apoyará tu decisión de dejar de fumar: Por ejemplo, tus padres, esposo(a)/pareja, novio(a), hermanos(as) o tus amigos. Déjales saber tu decisión de dejar de fumar. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/apoyo",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/apoyo",
        },
    },
    {
        "name": "INTAKE_READY_CHECK",
        "description": "Ready to quit tomorrow?",
        "en": {
            "text": "Are you ready to quit smoking tomorrow?",
            "quick_replies": [
                {"label": "Yes, let's do it!", "value": "YES_TOMORROW"},
                {"label": "No, not yet", "value": "NEED_TIME"},
            ],
        },
        "es": {
            "text": "¿Estás listo para dejar de fumar mañana?",
            "quick_replies": [
                {"label": "¡Si, hagámoslo!", "value": "YES_TOMORROW"},
                {"label": "No, aún no.", "value": "NEED_TIME"},
            ],
        },
    },
    {
        "name": "INTAKE_YES_TIME_SELECT",
        "description": "Time selection for those ready tomorrow",
        "en": {
            "text": "Great! This week we'll spend 5 to 10 minutes chatting with you each morning. Earlier is better. Select the time you want to do this.",
            "quick_replies": [
                {"label": "7:00 am", "value": "07:00"},
                {"label": "7:30 am", "value": "07:30"},
                {"label": "8:00 am", "value": "08:00"},
                {"label": "8:30 am", "value": "08:30"},
                {"label": "9:00 am", "value": "09:00"},
                {"label": "9:30 am", "value": "09:30"},
                {"label": "10:00 am", "value": "10:00"},
            ],
        },
        "es": {
            "text": "¡Estupendo! Esta semana tomaremos 5 o 10 minutos para chatear contigo cada mañana. Selecciona la hora de tu preferencia. Entre más temprano lo hagamos mejor.",
            "quick_replies": [
                {"label": "7:00 am", "value": "07:00"},
                {"label": "7:30 am", "value": "07:30"},
                {"label": "8:00 am", "value": "08:00"},
                {"label": "8:30 am", "value": "08:30"},
                {"label": "9:00 am", "value": "09:00"},
                {"label": "9:30 am", "value": "09:30"},
                {"label": "10:00 am", "value": "10:00"},
            ],
        },
    },
    {
        "name": "INTAKE_SET_QUIT_DATE",
        "description": "Quit date selection for those not ready",
        "en": {
            "text": "The first step is to set a quit date on a day when you will not have much stress, maybe a weekend. It should be between 7 and 14 days from today.\nThink about it and select a number between 7 and 14 for your quit date.",
            "quick_replies": [
                {"label": "7", "value": "7"},
                {"label": "8", "value": "8"},
                {"label": "9", "value": "9"},
                {"label": "10", "value": "10"},
                {"label": "11", "value": "11"},
                {"label": "12", "value": "12"},
                {"label": "13", "value": "13"},
                {"label": "14", "value": "14"},
            ],
        },
        "es": {
            "text": "El primer paso es fijar un día para dejar de fumar cuando no tengas mucho estrés, tal vez un fin de semana. Debe ser entre 7 y 14 días a partir de hoy.\nPiénsalo y selecciona un número entre 7 y 14 para tu día de dejar de fumar.",
            "quick_replies": [
                {"label": "7", "value": "7"},
                {"label": "8", "value": "8"},
                {"label": "9", "value": "9"},
                {"label": "10", "value": "10"},
                {"label": "11", "value": "11"},
                {"label": "12", "value": "12"},
                {"label": "13", "value": "13"},
                {"label": "14", "value": "14"},
            ],
        },
    },
    {
        "name": "INTAKE_QUIT_DATE_CONFIRM",
        "description": "Quit date confirmation",
        "en": {
            "text": "OK your quit day is {{quit_date}}. To help you get ready, we'll send you a few helpful messages every day, beginning tomorrow morning.",
        },
        "es": {
            "text": "OK tu día para dejar de fumar es {{quit_date}}. Para ayudarte a preparar, te enviaremos algunos textos útiles, empezando mañana en la mañana.",
        },
    },
    {
        "name": "INTAKE_TIME_SELECT",
        "description": "Time selection for delayed quit date",
        "en": {
            "text": "What time should we send the first text? The earlier the better!",
            "quick_replies": [
                {"label": "7:00 am", "value": "07:00"},
                {"label": "7:30 am", "value": "07:30"},
                {"label": "8:00 am", "value": "08:00"},
                {"label": "8:30 am", "value": "08:30"},
                {"label": "9:00 am", "value": "09:00"},
                {"label": "9:30 am", "value": "09:30"},
                {"label": "10:00 am", "value": "10:00"},
            ],
        },
        "es": {
            "text": "¿A qué hora debemos enviarte el primer texto? ¡Entre más temprano es mejor!",
            "quick_replies": [
                {"label": "7:00 am", "value": "07:00"},
                {"label": "7:30 am", "value": "07:30"},
                {"label": "8:00 am", "value": "08:00"},
                {"label": "8:30 am", "value": "08:30"},
                {"label": "9:00 am", "value": "09:00"},
                {"label": "9:30 am", "value": "09:30"},
                {"label": "10:00 am", "value": "10:00"},
            ],
        },
    },
    {
        "name": "INTAKE_END",
        "description": "End of intake message",
        "en": {"text": "OK that's it for today. We'll be back tomorrow!"},
        "es": {"text": "OK eso es todo por hoy. Volveremos a hablar mañana!"},
    },
]

# ============================================================================
# PRE-QUIT DAY TEMPLATES (-6 to -1)
# ============================================================================
PRE_QUIT_TEMPLATES = [
    # PQ-6 Messages
    {
        "name": "PQ6_MOTIV1",
        "description": "PQ-6 Morning motivation - flying car",
        "en": {
            "text": "Reason #1 to quit smoking while you're young: You'll live longer to enjoy the future's coolest tech, like robot assistants and flying cars.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ6_Motiv1_flying_car.gif",
        },
        "es": {
            "text": "Razón #1 para dejar de fumar siendo joven: Vivirás más tiempo para disfrutar la tec del futuro como robots asistentes y carros voladores.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ6_Motiv1_flying_car.gif",
        },
    },
    {
        "name": "PQ6_MOTIV4",
        "description": "PQ-6 Noon - Stranger Things tobacco",
        "en": {
            "text": "\"Stranger Things\" is tackling the real monster: Tobacco! It kills more people than AIDS, alcohol, car accidents, murder, drugs, suicides, and fires COMBINED!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ6_Motiv4_Smoke_skull.gif",
        },
        "es": {
            "text": "\"Stranger Things\" ataca al verdadero monstruo: ¡El tabaco! Porque ¡mata más personas que el SIDA, el alcohol, las drogas, los asesinatos, los suicidios, los incendios y los accidentes de carro JUNTOS!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ6_Motiv4_Smoke_skull.gif",
        },
    },
    # PQ-5 Messages
    {
        "name": "PQ5_BD",
        "description": "PQ-5 Binge drinking warning",
        "en": {
            "text": "Drinking alcohol can trigger cravings for a cigarette and makes it harder for you to quit smoking. Tap pic below https://quitxtstudy.org/helpful-resources/binge-drinking",
            "media_url": "https://quitxtstudy.org/helpful-resources/binge-drinking",
        },
        "es": {
            "text": "Beber alcohol puede provocar los deseos de fumar y te hace más difícil dejar el cigarrillo. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/consumo-intensivo-de-alcohol",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/consumo-intensivo-de-alcohol",
        },
    },
    {
        "name": "PQ5_CUE1",
        "description": "PQ-5 Noon - Mandalorian lungs",
        "en": {
            "text": "Just like \"The Mandalorian\" fights to protect Grogu, you can defend your lungs from cancer and disease. Stay strong – quit smoking and be your own hero!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ5_Cue1_noon_Mandalorian_Grogu.gif",
        },
        "es": {
            "text": "Como El Mandalorian lucha y protege a Grogu, tú puedes proteger tus pulmones del cáncer y enfermedades. ¡Deja de fumar y sé tu propio héroe!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ5_Cue1_noon_Mandalorian_Grogu.gif",
        },
    },
    {
        "name": "PQ5_MOTIV2",
        "description": "PQ-5 4pm - Robot butler",
        "en": {
            "text": "Reason #2 to quit smoking while you're young: Add a decade to your life and get yourself an AI-powered robot butler!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ5_Motiv2_automated.gif",
        },
        "es": {
            "text": "Razón #2 para dejar de fumar siendo joven: ¡Ganarás 10 años de vida y podrás disfrutar los mayordomos robot con inteligencia artificial!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ5_Motiv2_automated_esp.gif",
        },
    },
    # PQ-4 Messages
    {
        "name": "PQ4_GETTING_ACTIVE",
        "description": "PQ-4 Morning - Getting active",
        "en": {
            "text": "You'll find it easier to quit if you get more active. There are lots of ways to get active. Just take walks, play ball with friends or exercise. Tap pic below https://quitxtstudy.org/helpful-resources/getting-active",
            "media_url": "https://quitxtstudy.org/helpful-resources/getting-active",
        },
        "es": {
            "text": "Será más fácil dejar de fumar si eres más activo. Hay muchas formas de hacerlo. Solo camina o haz ejercicio. Clic el pic abajo https://quitxtstudy.org/spanish/mantenerte-activo",
            "media_url": "https://quitxtstudy.org/spanish/mantenerte-activo",
        },
    },
    {
        "name": "PQ4_CUE3",
        "description": "PQ-4 Noon - Google maps directions",
        "en": {
            "text": "If we've learned one thing from Google maps, it's to always follow directions. Do the same when using nicotine patches, gum or lozenges.",
        },
        "es": {
            "text": "Si hemos aprendido algo de los mapas de Google, es siempre seguir las indicaciones. Haz lo mismo cuando uses reemplazo de nicotina.",
        },
    },
    {
        "name": "PQ4_MOTIV3",
        "description": "PQ-4 4pm - Family proud",
        "en": {
            "text": "Quitting is hard, but YOU CAN DO IT! Make your family proud and quit tobacco!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ4_Motiv3_ImRooting4U.gif",
        },
        "es": {
            "text": "Dejar de fumar es duro, pero ¡TÚ PUEDES HACERLO! Haz sentir orgullosa a tu familia y ¡deja de fumar!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ4_Motiv3_tupuedes_esp.gif",
        },
    },
    # PQ-3 Messages
    {
        "name": "PQ3_BREATHING",
        "description": "PQ-3 Morning - Breathing exercises",
        "en": {
            "text": "There are breathing exercises that can help you stop smoking. One can help you relax. One can perk you up.\nTo relax: Breathe in VERY SLOWLY through your nose, fill your lungs from bottom up, then exhale VERY SLOWLY through your mouth. Do it 3 times. Practice daily.\nTo perk up: Take a deep breath QUICKLY and DEEPLY through your nose, then blow it QUICKLY out your mouth. Do it 3 times. Practice daily. https://quitxtstudy.org/helpful-resources/breathing-exercises",
            "media_url": "https://quitxtstudy.org/helpful-resources/breathing-exercises",
        },
        "es": {
            "text": "Hay ejercicios de respiración que pueden ayudarte a dejar de fumar. Uno puede ayudarte a relajar y otro puede darte ánimo.\nPara relajarte: Respira MUY LENTAMENTE por la nariz y llena tus pulmones de abajo hacia arriba. Después, MUY LENTAMENTE sopla el aire por la boca. Hazlo 3 veces. Practica diariamente.\nPara animarte: Respira RÁPIDA y PROFUNDAMENTE por la nariz y luego sopla el aire RÁPIDAMENTE por la boca. Hazlo 3 veces. Practica varias veces al día. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/ejercicios-de-respiracion",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/ejercicios-de-respiracion",
        },
    },
    {
        "name": "PQ3_CUE4",
        "description": "PQ-3 11am - Uncle Iroh",
        "en": {
            "text": "Uncle Iroh Word of wisdom: Practice deep breathing to relax without smoking.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ3_Cue4_11am_UncleIroh_English.gif",
        },
        "es": {
            "text": "Palabras sabias del tío Iroh: Practica respiración profunda para relajarte sin necesidad de fumar.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ3_Cue4_11am_UncleIroh_Spanish.gif",
        },
    },
    {
        "name": "PQ3_CUE5",
        "description": "PQ-3 2pm - Deadpool recovery",
        "en": {
            "text": "Because we're not all Deadpool, getting active when you quit smoking will help your body recover better AND make it easier to stay away from tobacco. You're the real hero!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ3_Cue5_2pm_deadpool.gif",
        },
        "es": {
            "text": "Porque no todos somos Deadpool, estar más activo ayudará a tu cuerpo a recuperarse mejor y será más fácil mantenerte alejado del tabaco.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ3_Cue5_2pm_deadpool.gif",
        },
    },
    # PQ-2 Messages
    {
        "name": "PQ2_NICOTINE",
        "description": "PQ-2 Morning - Nicotine replacement ready",
        "en": {
            "text": "Did you decide to use nicotine replacement? If so, have your patch / gum / lozenge ready by tomorrow. Read the label and use as directed: https://quitxtstudy.org/helpful-resources/nicotine-replacement",
            "media_url": "https://quitxtstudy.org/helpful-resources/nicotine-replacement",
        },
        "es": {
            "text": "Si decidiste usar reemplazo de nicotina, recuerda tenerlo listo para mañana. Lee y sigue las indicaciones con cuidado: https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
        },
    },
    {
        "name": "PQ2_CUE6",
        "description": "PQ-2 11am - Get body moving",
        "en": {
            "text": "Get your body moving: Play your favorite song and dance or simply walk around the block. It only takes 30 minutes to help you stay away from tobacco.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ2_Cue6_11am_soccer_players.gif",
        },
        "es": {
            "text": "Mueve tu cuerpo: Toca tu canción favorita y baila o simplemente sal a caminar. Sólo 30 minutos te ayudarán a mantenerte alejado del tabaco.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ2_Cue6_11am_soccer_players.gif",
        },
    },
    {
        "name": "PQ2_MOTIV5",
        "description": "PQ-2 2pm - Respiratory virus",
        "en": {
            "text": "What's worse than catching a respiratory virus? Catching a severe case with breathing complications due to smoking!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ2_Motiv5_JimCarrey.gif",
        },
        "es": {
            "text": "¿Qué es peor que contraer un virus respiratorio? ¡Que por fumar tengas un caso severo con complicaciones respiratorias!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ2_Motiv5_JimCarrey.gif",
        },
    },
    # PQ-1 Messages
    {
        "name": "PQ1_INSTEAD",
        "description": "PQ-1 Morning - Instead of smoking",
        "en": {
            "text": "Think about times or places you will want to smoke the most and what can you do instead… Go here for ideas: https://quitxtstudy.org/helpful-resources/instead-of-smoking",
            "media_url": "https://quitxtstudy.org/helpful-resources/instead-of-smoking",
        },
        "es": {
            "text": "Piensa cuándo y dónde es que deseas fumar más y qué puedes hacer en lugar de fumar. Clic el pic abajo para más ideas: https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
        },
    },
    {
        "name": "PQ1_MOTIV6",
        "description": "PQ-1 11am - Traffic jams",
        "en": {
            "text": "You already deal with traffic jams, work, school, and seeing ads on YouTube and Instagram… why would you want to deal with smoking? YOU CAN BE FREE from tobacco!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ1_Motiv6_11am_TrafficJam.gif",
        },
        "es": {
            "text": "Ya te aguantas el tráfico, el trabajo, la escuela y los comerciales en YouTube y en Instagram… ¿Por qué el lío de fumar? ¡LIBERATE del tabaco!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/PQ1_Motiv6_11am_TrafficJam.gif",
        },
    },
]

# ============================================================================
# QUIT DAY TEMPLATES (Q1-Q21+)
# ============================================================================
QUIT_DAY_TEMPLATES = [
    # Q1 - Quit Day 1
    {
        "name": "Q1_MORNING",
        "description": "Q1 - It's quit day!",
        "en": {
            "text": "It's quit day! To start on the road to a smokefree life, get rid of cigarettes, butts, matches, lighters and ashtrays. Here is why you're ready: https://youtu.be/bEcWW5agFDs",
            "media_url": "https://youtu.be/bEcWW5agFDs",
        },
        "es": {
            "text": "¡Hoy es el día! Empieza tu nueva vida sin fumar, tira los cigs, las colillas, las cerillas, los encendedores y los ceniceros. Clic el pic abajo https://youtu.be/REZF-OEUYGE",
            "media_url": "https://youtu.be/REZF-OEUYGE",
        },
    },
    {
        "name": "Q1_REASONS",
        "description": "Q1 - Make a list of reasons",
        "en": {
            "text": "Make a list with the reasons you are quitting: Your family, your health... carry it with you and read it when you feel tempted. Tap pic below https://quitxtstudy.org/reasons",
            "media_url": "https://quitxtstudy.org/reasons",
        },
        "es": {
            "text": "Escribe las razones por las que estás dejando de fumar: Tu familia, tu salud... llévalas contigo y léelas cuando sientas antojo. Clic el pic abajo https://quitxtstudy.org/spanish/razones",
            "media_url": "https://quitxtstudy.org/spanish/razones",
        },
    },
    {
        "name": "Q1_INSTEAD",
        "description": "Q1 - Instead of smoking",
        "en": {
            "text": "Think about the times or places you will want to smoke the most and what you can do instead… Go here for ideas https://quitxtstudy.org/helpful-resources/instead-of-smoking",
            "media_url": "https://quitxtstudy.org/helpful-resources/instead-of-smoking",
        },
        "es": {
            "text": "Piensa cuándo y dónde es que deseas fumar más y qué puedes hacer en lugar de fumar. Clic el pic abajo para más ideas https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
        },
    },
    {
        "name": "Q1_NICOTINE",
        "description": "Q1 - Nicotine replacement",
        "en": {
            "text": "If you decided to use nicotine replacement, it is time to do it. Be sure to read and follow the directions carefully: https://quitxtstudy.org/helpful-resources/nicotine-replacement",
            "media_url": "https://quitxtstudy.org/helpful-resources/nicotine-replacement",
        },
        "es": {
            "text": "Si decidiste usar reemplazo de nicotina, es hora de comenzar a usarlo. Lee y sigue con cuidado las indicaciones: https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/terapia-de-reemplazo-de-nicotina",
        },
    },
    {
        "name": "Q1_HELPNOW_PROMPT",
        "description": "Q1 - HELPNOW prompt",
        "en": {
            "text": "If you are having a hard time, text HELPNOW and we will answer.",
            "quick_replies": [
                {"label": "Yes, I need help", "value": "HELPNOW"},
                {"label": "No, I am doing OK!", "value": "OK"},
            ],
        },
        "es": {
            "text": "Si estás pasando por un mal momento envía AYUDAYA y te responderemos.",
            "quick_replies": [
                {"label": "Si, necesito ayuda", "value": "AYUDAYA"},
                {"label": "No ¡estoy bien!", "value": "OK"},
            ],
        },
    },
    {
        "name": "Q1_IM_1PM",
        "description": "Q1 1pm - Strength in numbers",
        "en": {
            "text": "There is strength in numbers: Text your supporters and let them know you are quitting! Encouraging words can go a long way.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_1pm_strength_in_numbers.gif",
        },
        "es": {
            "text": "La unión hace la fuerza. Comunícate con las personas que te apoyan y déjales saber que dejaste de fumar. Las palabras de aliento son de gran ayuda.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_1pm_strength_in_numbers.gif",
        },
    },
    {
        "name": "Q1_IM_4PM",
        "description": "Q1 4pm - Spider-Man preparation",
        "en": {
            "text": "Miles Morales spent a lot of time preparing to become Spider-Man. Quitting smoking is no different. We can show you how to quit 1 craving at a time.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_4PM_Spiderman.gif",
        },
        "es": {
            "text": "Miles Morales practicó mucho tiempo para ser el Hombre Araña. Dejar de fumar no es diferente. Te mostraremos cómo dejar de fumar 1 antojo a la vez.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_4PM_Spiderman.gif",
        },
    },
    {
        "name": "Q1_CHECKOUT",
        "description": "Q1 8pm - Daily checkout",
        "en": {
            "text": "During the day, did you smoke a tobacco cigarette, even a puff?",
            "quick_replies": [
                {"label": "Yes, it was hard.", "value": "YES_SMOKED"},
                {"label": "No, I did not smoke!", "value": "NO_SMOKEFREE"},
            ],
        },
        "es": {
            "text": "Durante el día de hoy, ¿fumaste cigarrillos de tabaco, aunque fuera una fumada?",
            "quick_replies": [
                {"label": "Si, fue difícil.", "value": "YES_SMOKED"},
                {"label": "No, ¡No fumé!", "value": "NO_SMOKEFREE"},
            ],
        },
    },
    {
        "name": "Q1_CHECKOUT_YES",
        "description": "Q1 - Response if smoked",
        "en": {
            "text": "That is OK. It takes practice. Treat this as a slip. Each slip is an opportunity to learn. You CAN do this!",
        },
        "es": {
            "text": "Es OK. Requiere práctica. Toma esto como un desliz. Cada desliz es una oportunidad de aprender. ¡Tú PUEDES lograrlo!",
        },
    },
    {
        "name": "Q1_CHECKOUT_NO",
        "description": "Q1 - Congrats smokefree",
        "en": {
            "text": "CONGRATULATIONS! You got the mojo! We'll text you again tomorrow…",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_checkout_Celebration.gif",
        },
        "es": {
            "text": "¡FELICITACIONES! ¡Tú tienes la magia! Hablamos de nuevo en la mañana…",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q1_checkout_Celebration.gif",
        },
    },
    # Q2 - Quit Day 2
    {
        "name": "Q2_BREATHING",
        "description": "Q2 - Breathing exercises morning",
        "en": {
            "text": "Start today with breathing exercises to help you cope with the urge to smoke.\nRelax away the craving! Breathe in VERY SLOWLY through your nose, fill your lungs from bottom up, then exhale VERY SLOWLY through your mouth. Do it 3 times.\nTo perk up: Take a deep breath QUICKLY and DEEPLY through your nose, then blow it QUICKLY out your mouth. Do it 3 times. Practice daily. Tap pic below https://quitxtstudy.org/helpful-resources/breathing-exercises",
            "media_url": "https://quitxtstudy.org/helpful-resources/breathing-exercises",
        },
        "es": {
            "text": "Empieza el día con ejercicios de respiración para ayudarte con los antojos de fumar.\nPara relajar el antojo: Respira MUY LENTAMENTE por la nariz y llena tus pulmones de abajo hacia arriba. Después, MUY LENTAMENTE sopla el aire por la boca. Hazlo 3 veces.\nPara animarte: Respira RÁPIDA y PROFUNDAMENTE por la nariz y luego sopla el aire RÁPIDAMENTE por la boca. Hazlo 3 veces. Practica varias veces al día. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/ejercicios-de-respiracion",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/ejercicios-de-respiracion",
        },
    },
    {
        "name": "Q2_BD",
        "description": "Q2 - Binge drinking warning",
        "en": {
            "text": "Drinking makes it harder to quit smoking… Here are some ideas on how to control drinking. Tap pic below https://quitxtstudy.org/helpful-resources/binge-drinking",
            "media_url": "https://quitxtstudy.org/helpful-resources/binge-drinking",
        },
        "es": {
            "text": "Tomar te hace más difícil dejar de fumar. Para ideas sobre cómo controlar la bebida Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/consumo-intensivo-de-alcohol",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/consumo-intensivo-de-alcohol",
        },
    },
    {
        "name": "Q2_IM_1PM",
        "description": "Q2 1pm - 24 hours smokefree",
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
    # Q3 - Quit Day 3
    {
        "name": "Q3_INSTEAD",
        "description": "Q3 - Instead of smoking",
        "en": {
            "text": "Chew gum instead of smoking when you want to smoke the most. Tap pic below for more ideas https://quitxtstudy.org/helpful-resources/instead-of-smoking",
            "media_url": "https://quitxtstudy.org/helpful-resources/instead-of-smoking",
        },
        "es": {
            "text": "Mastica chicle en lugar de fumar cuando tengas antojo de un cigarrillo. Para más ideas Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/en-lugar-de-fumar",
        },
    },
    {
        "name": "Q3_SUPPORT",
        "description": "Q3 - Support from family/friends",
        "en": {
            "text": "You can get support from family and friends. Get in touch with them today to tell them how you're doing. Tap pic below https://quitxtstudy.org/helpful-resources/support",
            "media_url": "https://quitxtstudy.org/helpful-resources/support",
        },
        "es": {
            "text": "Puedes recibir apoyo de tu familia y amigos. Comunícate con ellos hoy y déjales saber cómo estás. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/apoyo",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/apoyo",
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
    {
        "name": "Q3_IM_1PM",
        "description": "Q3 1pm - 72 hours lung improvement",
        "en": {
            "text": "Do you know that within 72 hours of quitting smoking, healthy cells begin to replace damaged ones in the lungs, and lung function starts to improve?\nThere is no time like the present — this means NOW is a good time to quit smoking! You can do it and be tobacco-free!",
        },
        "es": {
            "text": "¿Sabías que en las primeras 72 horas sin fumar, las células sanas empiezan a reemplazar las dañadas en los pulmones y la función pulmonar empieza a mejorar?\nNo hay tiempo como el presente… ¡AHORA es el momento perfecto para dejar de fumar! ¡Tú puedes hacerlo y estar libre del tabaco!",
        },
    },
    {
        "name": "Q3_IM_4PM",
        "description": "Q3 4pm - Get help",
        "en": {
            "text": "Don't be afraid to get help to stay away from smoking. It's a brave step towards a healthier you. You're not alone in this journey!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q3_4pm_Gethelp2.gif",
        },
        "es": {
            "text": "No temas pedir ayuda para mantenerte alejado de fumar. Es un paso valiente hacia una vida saludable. ¡Tú no estás solo en esta jornada!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q3_4pm_Gethelp2.gif",
        },
    },
    {
        "name": "Q3_IM_7PM",
        "description": "Q3 7pm - Avatar nicotine plan",
        "en": {
            "text": "Nicotine is addictive! You need a plan to fight cravings: Be ready with nicotine patches, gum, or lozenges. Even the Avatar needs a plan to defeat his enemies!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q3_7pm_firebending.gif",
        },
        "es": {
            "text": "¡La nicotina es adictiva! Necesitas un plan para combatir los antojos: ¡Prepárate con parches, chicles o pastillas de nicotina! Hasta el Avatar necesita prepararse para vencer a sus enemigos.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q3_7pm_firebending.gif",
        },
    },
    # Q7 - Weekly Checkout
    {
        "name": "Q7_MORNING",
        "description": "Q7 - Money saved + YouTube video",
        "en": {
            "text": "${{money_saved}}. That's how much you've saved since quitting smoking. Go, you! Here's why your wallet is getting bigger: https://youtu.be/wQc2qfXWCCE",
            "media_url": "https://youtu.be/wQc2qfXWCCE",
        },
        "es": {
            "text": "${{money_saved}}. Esto es lo que has ahorrado desde que dejaste de fumar. ¡Bravo! Mira por qué tu billetera está más grande: https://youtu.be/VCHx7R3Kxr8",
            "media_url": "https://youtu.be/VCHx7R3Kxr8",
        },
    },
    {
        "name": "Q7_GETTING_ACTIVE",
        "description": "Q7 - Getting active",
        "en": {
            "text": "You'll find it easier to quit if you start getting more active... even a short walk will help. Just go for it!! Tap pic below https://quitxtstudy.org/helpful-resources/getting-active",
            "media_url": "https://quitxtstudy.org/helpful-resources/getting-active",
        },
        "es": {
            "text": "Será más fácil dejar de fumar si te mantienes más activo… incluso las caminatas cortas te ayudarán. ¡Muévete ya! Clic el pic abajo https://quitxtstudy.org/spanish/mantenerte-activo",
            "media_url": "https://quitxtstudy.org/spanish/mantenerte-activo",
        },
    },
    {
        "name": "Q7_PREDICT_PLAN",
        "description": "Q7 - Predict and Plan",
        "en": {
            "text": "To quit for good, you need to be prepared to cope with some tough situations: If you get yelled at by your boss, get stressed, and feel the need for a cigarette…\nTake a walk, call a friend, use breathing exercises… you'll feel even worse if you start smoking again. Tap pic below https://quitxtstudy.org/helpful-resources/predict-and-plan",
            "media_url": "https://quitxtstudy.org/helpful-resources/predict-and-plan",
        },
        "es": {
            "text": "Para dejar de fumar debes prepararte para enfrentar situaciones difíciles: Si tu jefe te regaña, te estresas y sientes la necesidad de fumarte un cigarrillo…\nSal a caminar, llama a un amigo, haz ejercicios de respiración… te sentirás peor si empiezas a fumar de nuevo. Clic el pic abajo https://quitxtstudy.org/spanish/recursos-útiles/predecir-y-planear",
            "media_url": "https://quitxtstudy.org/spanish/recursos-útiles/predecir-y-planear",
        },
    },
    {
        "name": "Q7_IM_1PM",
        "description": "Q7 1pm - Day 7 counting",
        "en": {
            "text": "Day 7 & counting!!! Stay strong, you can do it!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_1pm_Youcandoit.gif",
        },
        "es": {
            "text": "¡Día 7 y contando!! Mantente fuerte ¡tú puedes lograrlo!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_1pm_tupuedes_Spanish.gif",
        },
    },
    {
        "name": "Q7_IM_4PM",
        "description": "Q7 4pm - Cancer risk reduction",
        "en": {
            "text": "By not smoking you are reducing your risk of 13 types of cancer, lung disease and heart disease! Congrats!!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_4pm_Fistbump.gif",
        },
        "es": {
            "text": "¡Al no fumar estás reduciendo tu riesgo de 13 tipos de cáncer, enfermedades pulmonares y del corazón! ¡Felicitaciones!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_4pm_Fistbump.gif",
        },
    },
    {
        "name": "Q7_IM_7PM",
        "description": "Q7 7pm - Get body moving",
        "en": {
            "text": "Get your body moving: Go for a hike at the park or go play soccer with friends. Just 30 minutes a day helps you stay away from tobacco.",
        },
        "es": {
            "text": "Mueve tu cuerpo: Da una caminata en el parque o juega fútbol con tus amigos. Solo 30 minutos al día ayudará a mantenerte alejado del tabaco.",
        },
    },
    {
        "name": "Q7_CHECKOUT",
        "description": "Q7 8pm - Weekly checkout",
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
        "name": "Q7_CHECKOUT_YES",
        "description": "Q7 - Slip response with reasons",
        "en": {
            "text": "That's OK. Remember, it takes practice. What caused you to start smoking again? Send one of these reasons:",
            "quick_replies": [
                {"label": "Badmood", "value": "BADMOOD"},
                {"label": "Stress", "value": "STRESS"},
                {"label": "Smokers", "value": "SMOKERS"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Other", "value": "OTHER"},
            ],
        },
        "es": {
            "text": "Es OK. Recuerda, toma práctica. ¿Qué te hizo fumar de nuevo? Envía una de estas razones:",
            "quick_replies": [
                {"label": "Malhumor", "value": "MALHUMOR"},
                {"label": "Estrés", "value": "ESTRES"},
                {"label": "Fumadores", "value": "FUMADORES"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Otra", "value": "OTRA"},
            ],
        },
    },
    {
        "name": "Q7_CHECKOUT_NO",
        "description": "Q7 - Congrats smokefree",
        "en": {
            "text": "CONGRATS from Quitxt! You're awesome! Tomorrow's a new day… let's touch base in the morning and make it smokefree!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_8pm_checkout_Minions.gif",
        },
        "es": {
            "text": "¡FELICITACIONES de Quitxt! Mañana es un nuevo día… hagamos que sea un día ¡libre de cigarrillos!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q7_8pm_checkout_bravo_esp.gif",
        },
    },
]

# ============================================================================
# HELPNOW RESPONSE TEMPLATE
# ============================================================================
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
    """Create the QuitTxt V9 project."""
    from app.models import Project

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
            "protocol_version": "V9",
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
        INTAKE_TEMPLATES +
        PRE_QUIT_TEMPLATES +
        QUIT_DAY_TEMPLATES +
        [HELPNOW_TEMPLATE]
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
        # Morning times
        {"name": "MORNING_DEFAULT", "overwrite_time": True, "overwritten_hours": 8, "overwritten_minutes": 0, "description": "Send at 8 AM (default morning)"},
        # Intermittent times for session days
        {"name": "INTERMITTENT_1PM", "overwrite_time": True, "overwritten_hours": 13, "overwritten_minutes": 0, "description": "Send at 1 PM"},
        {"name": "INTERMITTENT_4PM", "overwrite_time": True, "overwritten_hours": 16, "overwritten_minutes": 0, "description": "Send at 4 PM"},
        {"name": "INTERMITTENT_7PM", "overwrite_time": True, "overwritten_hours": 19, "overwritten_minutes": 0, "description": "Send at 7 PM"},
        # Intermittent times for non-session days
        {"name": "INTERMITTENT_11AM", "overwrite_time": True, "overwritten_hours": 11, "overwritten_minutes": 0, "description": "Send at 11 AM"},
        {"name": "INTERMITTENT_3PM", "overwrite_time": True, "overwritten_hours": 15, "overwritten_minutes": 0, "description": "Send at 3 PM"},
        {"name": "INTERMITTENT_5PM", "overwrite_time": True, "overwritten_hours": 17, "overwritten_minutes": 0, "description": "Send at 5 PM"},
        # Checkout time
        {"name": "CHECKOUT_8PM", "overwrite_time": True, "overwritten_hours": 20, "overwritten_minutes": 0, "description": "Send at 8 PM for checkout"},
        # Day offsets for pre-quit
        {"name": "NEXT_DAY_MORNING", "offset_days": 1, "overwrite_time": True, "overwritten_hours": 8, "overwritten_minutes": 0, "description": "Next day at 8 AM"},
        {"name": "NOON", "overwrite_time": True, "overwritten_hours": 12, "overwritten_minutes": 0, "description": "Send at noon"},
        {"name": "2PM", "overwrite_time": True, "overwritten_hours": 14, "overwritten_minutes": 0, "description": "Send at 2 PM"},
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
        # ========== INTAKE FLOW ==========
        {"name": "INTAKE_START", "display_name": "Intake Start", "is_entry_node": True, "template": "INTAKE_WELCOME", "timing": "NO_DELAY"},
        {"name": "INTAKE_STUDY_INFO", "display_name": "Study Info", "template": "INTAKE_STUDY_INFO", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_EXIT_RESPONSE", "display_name": "Exit Response", "template": "INTAKE_EXIT_RESPONSE", "timing": "NO_DELAY"},
        {"name": "INTAKE_QUIZ_INTRO", "display_name": "Quiz Intro", "template": "INTAKE_QUIZ_INTRO", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_CPD", "display_name": "Cigarettes/Day", "template": "INTAKE_CPD", "timing": "NO_DELAY"},
        {"name": "INTAKE_NICOTINE", "display_name": "Nicotine Info", "template": "INTAKE_NICOTINE", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_REASONS", "display_name": "Reasons to Quit", "template": "INTAKE_REASONS", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_SUPPORT", "display_name": "Support Person", "template": "INTAKE_SUPPORT", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_READY", "display_name": "Ready Check", "template": "INTAKE_READY_CHECK", "timing": "2_MIN_DELAY"},
        {"name": "INTAKE_YES_TIME", "display_name": "Time Select (Ready)", "template": "INTAKE_YES_TIME_SELECT", "timing": "NO_DELAY"},
        {"name": "INTAKE_SET_DATE", "display_name": "Set Quit Date", "template": "INTAKE_SET_QUIT_DATE", "timing": "NO_DELAY"},
        {"name": "INTAKE_DATE_CONFIRM", "display_name": "Date Confirmation", "template": "INTAKE_QUIT_DATE_CONFIRM", "timing": "NO_DELAY"},
        {"name": "INTAKE_TIME", "display_name": "Time Select (Delayed)", "template": "INTAKE_TIME_SELECT", "timing": "NO_DELAY"},
        {"name": "INTAKE_END", "display_name": "Intake End", "template": "INTAKE_END", "timing": "NO_DELAY"},

        # ========== PRE-QUIT DAYS ==========
        # PQ-6
        {"name": "PQ6_MOTIV1", "display_name": "PQ-6 Morning", "template": "PQ6_MOTIV1", "timing": "MORNING_DEFAULT"},
        {"name": "PQ6_MOTIV4", "display_name": "PQ-6 Noon", "template": "PQ6_MOTIV4", "timing": "NOON"},
        # PQ-5
        {"name": "PQ5_BD", "display_name": "PQ-5 Morning", "template": "PQ5_BD", "timing": "MORNING_DEFAULT"},
        {"name": "PQ5_CUE1", "display_name": "PQ-5 Noon", "template": "PQ5_CUE1", "timing": "NOON"},
        {"name": "PQ5_MOTIV2", "display_name": "PQ-5 4pm", "template": "PQ5_MOTIV2", "timing": "INTERMITTENT_4PM"},
        # PQ-4
        {"name": "PQ4_GETTING_ACTIVE", "display_name": "PQ-4 Morning", "template": "PQ4_GETTING_ACTIVE", "timing": "MORNING_DEFAULT"},
        {"name": "PQ4_CUE3", "display_name": "PQ-4 Noon", "template": "PQ4_CUE3", "timing": "NOON"},
        {"name": "PQ4_MOTIV3", "display_name": "PQ-4 4pm", "template": "PQ4_MOTIV3", "timing": "INTERMITTENT_4PM"},
        # PQ-3
        {"name": "PQ3_BREATHING", "display_name": "PQ-3 Morning", "template": "PQ3_BREATHING", "timing": "MORNING_DEFAULT"},
        {"name": "PQ3_CUE4", "display_name": "PQ-3 11am", "template": "PQ3_CUE4", "timing": "INTERMITTENT_11AM"},
        {"name": "PQ3_CUE5", "display_name": "PQ-3 2pm", "template": "PQ3_CUE5", "timing": "2PM"},
        # PQ-2
        {"name": "PQ2_NICOTINE", "display_name": "PQ-2 Morning", "template": "PQ2_NICOTINE", "timing": "MORNING_DEFAULT"},
        {"name": "PQ2_CUE6", "display_name": "PQ-2 11am", "template": "PQ2_CUE6", "timing": "INTERMITTENT_11AM"},
        {"name": "PQ2_MOTIV5", "display_name": "PQ-2 2pm", "template": "PQ2_MOTIV5", "timing": "2PM"},
        # PQ-1
        {"name": "PQ1_INSTEAD", "display_name": "PQ-1 Morning", "template": "PQ1_INSTEAD", "timing": "MORNING_DEFAULT"},
        {"name": "PQ1_MOTIV6", "display_name": "PQ-1 11am", "template": "PQ1_MOTIV6", "timing": "INTERMITTENT_11AM"},

        # ========== QUIT DAY 1 ==========
        {"name": "Q1_MORNING", "display_name": "Q1 Morning", "template": "Q1_MORNING", "timing": "MORNING_DEFAULT"},
        {"name": "Q1_REASONS", "display_name": "Q1 Reasons", "template": "Q1_REASONS", "timing": "2_MIN_DELAY"},
        {"name": "Q1_INSTEAD", "display_name": "Q1 Instead", "template": "Q1_INSTEAD", "timing": "2_MIN_DELAY"},
        {"name": "Q1_NICOTINE", "display_name": "Q1 Nicotine", "template": "Q1_NICOTINE", "timing": "2_MIN_DELAY"},
        {"name": "Q1_HELPNOW_PROMPT", "display_name": "Q1 HELPNOW Prompt", "template": "Q1_HELPNOW_PROMPT", "timing": "2_MIN_DELAY"},
        {"name": "Q1_IM_1PM", "display_name": "Q1 1pm", "template": "Q1_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q1_IM_4PM", "display_name": "Q1 4pm", "template": "Q1_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q1_CHECKOUT", "display_name": "Q1 Checkout", "template": "Q1_CHECKOUT", "timing": "CHECKOUT_8PM"},
        {"name": "Q1_CHECKOUT_YES", "display_name": "Q1 Checkout Yes", "template": "Q1_CHECKOUT_YES", "timing": "NO_DELAY"},
        {"name": "Q1_CHECKOUT_NO", "display_name": "Q1 Checkout No", "template": "Q1_CHECKOUT_NO", "timing": "NO_DELAY"},

        # ========== QUIT DAY 2 ==========
        {"name": "Q2_MORNING", "display_name": "Q2 Morning", "template": "Q2_BREATHING", "timing": "MORNING_DEFAULT"},
        {"name": "Q2_BD", "display_name": "Q2 BD", "template": "Q2_BD", "timing": "2_MIN_DELAY"},
        {"name": "Q2_IM_1PM", "display_name": "Q2 1pm", "template": "Q2_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q2_IM_4PM", "display_name": "Q2 4pm", "template": "Q2_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q2_IM_7PM", "display_name": "Q2 7pm", "template": "Q2_IM_7PM", "timing": "INTERMITTENT_7PM"},

        # ========== QUIT DAY 3 ==========
        {"name": "Q3_MORNING", "display_name": "Q3 Morning", "template": "Q3_INSTEAD", "timing": "MORNING_DEFAULT"},
        {"name": "Q3_SUPPORT", "display_name": "Q3 Support", "template": "Q3_SUPPORT", "timing": "2_MIN_DELAY"},
        {"name": "Q3_HELPNOW", "display_name": "Q3 HELPNOW", "template": "Q3_HELPNOW", "timing": "2_MIN_DELAY"},
        {"name": "Q3_IM_1PM", "display_name": "Q3 1pm", "template": "Q3_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q3_IM_4PM", "display_name": "Q3 4pm", "template": "Q3_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q3_IM_7PM", "display_name": "Q3 7pm", "template": "Q3_IM_7PM", "timing": "INTERMITTENT_7PM"},

        # ========== QUIT DAY 7 (Weekly Checkout) ==========
        {"name": "Q7_MORNING", "display_name": "Q7 Morning", "template": "Q7_MORNING", "timing": "MORNING_DEFAULT"},
        {"name": "Q7_GETTING_ACTIVE", "display_name": "Q7 Active", "template": "Q7_GETTING_ACTIVE", "timing": "2_MIN_DELAY"},
        {"name": "Q7_PP", "display_name": "Q7 Predict/Plan", "template": "Q7_PREDICT_PLAN", "timing": "2_MIN_DELAY"},
        {"name": "Q7_IM_1PM", "display_name": "Q7 1pm", "template": "Q7_IM_1PM", "timing": "INTERMITTENT_1PM"},
        {"name": "Q7_IM_4PM", "display_name": "Q7 4pm", "template": "Q7_IM_4PM", "timing": "INTERMITTENT_4PM"},
        {"name": "Q7_IM_7PM", "display_name": "Q7 7pm", "template": "Q7_IM_7PM", "timing": "INTERMITTENT_7PM"},
        {"name": "Q7_CHECKOUT", "display_name": "Q7 Checkout", "template": "Q7_CHECKOUT", "timing": "CHECKOUT_8PM"},
        {"name": "Q7_CHECKOUT_YES", "display_name": "Q7 Checkout Yes", "template": "Q7_CHECKOUT_YES", "timing": "NO_DELAY"},
        {"name": "Q7_CHECKOUT_NO", "display_name": "Q7 Checkout No", "template": "Q7_CHECKOUT_NO", "timing": "NO_DELAY"},

        # ========== HELPNOW ==========
        {"name": "HELPNOW_RESPONSE", "display_name": "HELPNOW Response", "template": "HELPNOW_RESPONSE", "timing": "NO_DELAY"},

        # ========== TERMINAL NODES ==========
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
        # ========== INTAKE FLOW ==========
        ("INTAKE_START", "INTAKE_STUDY_INFO"),
        ("INTAKE_STUDY_INFO", "INTAKE_QUIZ_INTRO"),
        ("INTAKE_QUIZ_INTRO", "INTAKE_CPD"),
        ("INTAKE_CPD", "INTAKE_NICOTINE"),
        ("INTAKE_NICOTINE", "INTAKE_REASONS"),
        ("INTAKE_REASONS", "INTAKE_SUPPORT"),
        ("INTAKE_SUPPORT", "INTAKE_READY"),
        # Branching from ready check
        ("INTAKE_READY", "INTAKE_YES_TIME", "YES_TOMORROW"),
        ("INTAKE_READY", "INTAKE_SET_DATE", "NEED_TIME"),
        # Ready tomorrow path -> Q1
        ("INTAKE_YES_TIME", "INTAKE_END"),
        ("INTAKE_END", "Q1_MORNING"),  # Next day
        # Not ready path -> Pre-quit
        ("INTAKE_SET_DATE", "INTAKE_DATE_CONFIRM"),
        ("INTAKE_DATE_CONFIRM", "INTAKE_TIME"),
        ("INTAKE_TIME", "INTAKE_END"),
        # Pre-quit days flow (7-day default)
        ("INTAKE_END", "PQ6_MOTIV1"),  # For delayed quit

        # ========== PRE-QUIT FLOW ==========
        # PQ-6
        ("PQ6_MOTIV1", "PQ6_MOTIV4"),
        ("PQ6_MOTIV4", "PQ5_BD"),  # Next day
        # PQ-5
        ("PQ5_BD", "PQ5_CUE1"),
        ("PQ5_CUE1", "PQ5_MOTIV2"),
        ("PQ5_MOTIV2", "PQ4_GETTING_ACTIVE"),  # Next day
        # PQ-4
        ("PQ4_GETTING_ACTIVE", "PQ4_CUE3"),
        ("PQ4_CUE3", "PQ4_MOTIV3"),
        ("PQ4_MOTIV3", "PQ3_BREATHING"),  # Next day
        # PQ-3
        ("PQ3_BREATHING", "PQ3_CUE4"),
        ("PQ3_CUE4", "PQ3_CUE5"),
        ("PQ3_CUE5", "PQ2_NICOTINE"),  # Next day
        # PQ-2
        ("PQ2_NICOTINE", "PQ2_CUE6"),
        ("PQ2_CUE6", "PQ2_MOTIV5"),
        ("PQ2_MOTIV5", "PQ1_INSTEAD"),  # Next day
        # PQ-1
        ("PQ1_INSTEAD", "PQ1_MOTIV6"),
        ("PQ1_MOTIV6", "Q1_MORNING"),  # QUIT DAY!

        # ========== Q1 FLOW ==========
        ("Q1_MORNING", "Q1_REASONS"),
        ("Q1_REASONS", "Q1_INSTEAD"),
        ("Q1_INSTEAD", "Q1_NICOTINE"),
        ("Q1_NICOTINE", "Q1_HELPNOW_PROMPT"),
        ("Q1_HELPNOW_PROMPT", "Q1_IM_1PM"),
        ("Q1_IM_1PM", "Q1_IM_4PM"),
        ("Q1_IM_4PM", "Q1_CHECKOUT"),
        ("Q1_CHECKOUT", "Q1_CHECKOUT_YES", "YES_SMOKED"),
        ("Q1_CHECKOUT", "Q1_CHECKOUT_NO", "NO_SMOKEFREE"),
        ("Q1_CHECKOUT_YES", "Q2_MORNING"),  # Next day
        ("Q1_CHECKOUT_NO", "Q2_MORNING"),  # Next day

        # ========== Q2 FLOW ==========
        ("Q2_MORNING", "Q2_BD"),
        ("Q2_BD", "Q2_IM_1PM"),
        ("Q2_IM_1PM", "Q2_IM_4PM"),
        ("Q2_IM_4PM", "Q2_IM_7PM"),
        ("Q2_IM_7PM", "Q3_MORNING"),  # Next day

        # ========== Q3 FLOW ==========
        ("Q3_MORNING", "Q3_SUPPORT"),
        ("Q3_SUPPORT", "Q3_HELPNOW"),
        ("Q3_HELPNOW", "Q3_IM_1PM"),
        ("Q3_IM_1PM", "Q3_IM_4PM"),
        ("Q3_IM_4PM", "Q3_IM_7PM"),
        # Continue to Q4... (simplified for now, goes to Q7)
        ("Q3_IM_7PM", "Q7_MORNING"),

        # ========== Q7 FLOW (Weekly Checkout) ==========
        ("Q7_MORNING", "Q7_GETTING_ACTIVE"),
        ("Q7_GETTING_ACTIVE", "Q7_PP"),
        ("Q7_PP", "Q7_IM_1PM"),
        ("Q7_IM_1PM", "Q7_IM_4PM"),
        ("Q7_IM_4PM", "Q7_IM_7PM"),
        ("Q7_IM_7PM", "Q7_CHECKOUT"),
        ("Q7_CHECKOUT", "Q7_CHECKOUT_YES", "YES_SMOKED"),
        ("Q7_CHECKOUT", "Q7_CHECKOUT_NO", "NO_SMOKEFREE"),
    ]

    # Create edges
    for edge_def in edge_defs:
        parent_name = edge_def[0]
        child_name = edge_def[1]
        edge_label = edge_def[2] if len(edge_def) > 2 else None

        if parent_name not in node_ids or child_name not in node_ids:
            continue

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
        print(f"  Created edge: {parent_name} -> {child_name}" + (f" [{edge_label}]" if edge_label else ""))

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
    print("QuitTxt V9 Protocol Import Script")
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
                print("ERROR: Admin user not found! Make sure to run database seed first.")
                return

            # Get language IDs
            result = await session.execute(select(AvailableLanguage).where(AvailableLanguage.short_name == "en"))
            en_lang = result.scalar_one_or_none()
            result = await session.execute(select(AvailableLanguage).where(AvailableLanguage.short_name == "es"))
            es_lang = result.scalar_one_or_none()

            if not en_lang or not es_lang:
                print("ERROR: Languages not found! Make sure EN and ES languages exist.")
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
            print(f"Project Name: {PROJECT_NAME}")
            print(f"Templates: {len(template_ids)}")
            print(f"Variables: {len(variable_ids)}")
            print(f"Nodes: {len(node_ids)}")
            print(f"Timing Elements: {len(timing_ids)}")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

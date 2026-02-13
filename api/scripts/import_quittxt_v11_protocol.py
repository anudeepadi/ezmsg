#!/usr/bin/env python3
"""
Import QuitTxt V11 Protocol into EzMsg Database.

V11 is a 180-day smoking cessation program with:
- Intake sequence (Welcome, CPD, Nicotine, Reasons, Support, Ready)
- Pre-quit days PQ-6 to PQ-1
- 180 quit days with daily sessions, intermittent messages, and checkout
- HELPNOW rotating pools (Crave: 23, BadMood: 24, Stress: 13, Smokers: 20, Alcohol: 12)
- SLIP escalation (1st, 2nd, 3rd+ different responses)
- Bilingual EN/ES throughout
- Intermittent messages at 1pm/4pm/7pm
- 8pm nightly checkout
"""

import asyncio
import os
from itertools import cycle
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5433/ezmsg")

PROJECT_NAME = "QuitTxt V11 Protocol"
PROJECT_DESCRIPTION = """
QuitTxt V11 Smoking Cessation Messaging Protocol

A comprehensive bilingual (English/Spanish) text messaging intervention
for smoking cessation (180-day program).

Protocol Version: V11 (2026)

Features:
- Intake sequence with quit date selection (immediate or 7-14 days)
- Pre-quit preparation messages (PQ-6 to PQ-1)
- 180 quit days with structured daily sessions
- HELPNOW crisis support with rotating message pools
- SLIP tracking with escalating responses
- Intermittent motivational messages (1pm/4pm/7pm)
- Nightly 8pm checkout
- Bilingual content (English/Spanish)
"""

# ============================================================================
# VARIABLES
# ============================================================================
VARIABLES = [
    {"name": "quit_date", "display_name": "Quit Date", "type": "DATETIME"},
    {"name": "preferred_time", "display_name": "Preferred Message Time", "type": "STRING", "default_value": "08:00"},
    {"name": "language", "display_name": "Language", "type": "STRING", "default_value": "en"},
    {"name": "cigarettes_per_day", "display_name": "Cigarettes Per Day", "type": "STRING"},
    {"name": "days_until_quit", "display_name": "Days Until Quit", "type": "INTEGER", "default_value": "1"},
    {"name": "participant_name", "display_name": "Participant Name", "type": "STRING"},
    {"name": "money_saved", "display_name": "Money Saved", "type": "DECIMAL"},
    {"name": "enrolled_date", "display_name": "Enrollment Date", "type": "DATETIME"},
    {"name": "current_quit_day", "display_name": "Current Quit Day", "type": "INTEGER"},
    {"name": "last_checkout_response", "display_name": "Last Checkout Response", "type": "STRING"},
    {"name": "slip_count", "display_name": "Slip Count", "type": "INTEGER", "default_value": "0"},
    {"name": "slip_reason", "display_name": "Slip Reason", "type": "STRING"},
    {"name": "ready_to_quit", "display_name": "Ready to Quit", "type": "STRING"},
    {"name": "helpnow_crave_index", "display_name": "HELPNOW Crave Index", "type": "INTEGER", "default_value": "0"},
    {"name": "helpnow_badmood_index", "display_name": "HELPNOW BadMood Index", "type": "INTEGER", "default_value": "0"},
    {"name": "helpnow_stress_index", "display_name": "HELPNOW Stress Index", "type": "INTEGER", "default_value": "0"},
    {"name": "helpnow_smokers_index", "display_name": "HELPNOW Smokers Index", "type": "INTEGER", "default_value": "0"},
    {"name": "helpnow_alcohol_index", "display_name": "HELPNOW Alcohol Index", "type": "INTEGER", "default_value": "0"},
]

# ============================================================================
# KEYWORDS
# ============================================================================
KEYWORDS = [
    {"keyword_text": "EXIT", "action_type": "OPT_OUT", "language": "en"},
    {"keyword_text": "SALIR", "action_type": "OPT_OUT", "language": "es"},
    {"keyword_text": "STOP", "action_type": "OPT_OUT", "language": "en"},
    {"keyword_text": "QUIT", "action_type": "OPT_OUT", "language": "en"},
    {"keyword_text": "HELP", "action_type": "HELP", "language": "en"},
    {"keyword_text": "AYUDA", "action_type": "HELP", "language": "es"},
    {"keyword_text": "HELPNOW", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_RESPONSE", "language": "en"},
    {"keyword_text": "AYUDAYA", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_RESPONSE", "language": "es"},
    {"keyword_text": "CRAVE", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_CRAVE", "language": "en"},
    {"keyword_text": "ANTOJO", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_CRAVE", "language": "es"},
    {"keyword_text": "BADMOOD", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_BADMOOD", "language": "en"},
    {"keyword_text": "MALHUMOR", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_BADMOOD", "language": "es"},
    {"keyword_text": "STRESS", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_STRESS", "language": "en"},
    {"keyword_text": "ESTRES", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_STRESS", "language": "es"},
    {"keyword_text": "SMOKERS", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_SMOKERS", "language": "en"},
    {"keyword_text": "FUMADORES", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_SMOKERS", "language": "es"},
    {"keyword_text": "ALCOHOL", "action_type": "TRIGGER_NODE", "node_name": "HELPNOW_ALCOHOL", "language": None},
    {"keyword_text": "YES", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "YES_SMOKED", "language": "en"},
    {"keyword_text": "SI", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "YES_SMOKED", "language": "es"},
    {"keyword_text": "NO", "action_type": "SET_VARIABLE", "variable": "last_checkout_response", "value": "NO_SMOKEFREE", "language": None},
]

# ============================================================================
# INTAKE TEMPLATES (same structure as V9)
# ============================================================================
INTAKE_TEMPLATES = [
    {
        "name": "INTAKE_WELCOME",
        "description": "Welcome message",
        "en": {"text": "Welcome to QuitTxt! Congrats on your decision to quit smoking! We're here to support you every step of the way over the next 6 months."},
        "es": {"text": "¡Bienvenido a QuitTxt! ¡Felicitaciones por decidir dejar de fumar! Estamos aquí para apoyarte en cada paso durante los próximos 6 meses."},
    },
    {
        "name": "INTAKE_STUDY_INFO",
        "description": "Study information",
        "en": {"text": "We'll help you quit smoking with daily messages, tips, and support. If you want to leave the study at any time, type EXIT."},
        "es": {"text": "Te ayudaremos a dejar de fumar con mensajes diarios, consejos y apoyo. Si deseas dejar el estudio en cualquier momento, envía SALIR."},
    },
    {
        "name": "INTAKE_EXIT_RESPONSE",
        "description": "Response when participant opts out",
        "en": {"text": "We're sorry to see you go. A team member will reach out. You can also contact us at quitxt@uthscsa.edu."},
        "es": {"text": "Lamentamos que te vayas. Un miembro del equipo se comunicará contigo. También puedes contactarnos en quitxt@uthscsa.edu."},
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
                {"label": "21+", "value": "21+"},
            ],
        },
        "es": {
            "text": "¿Cuántos cigarrillos fumas en promedio por día?",
            "quick_replies": [
                {"label": "1-5", "value": "1-5"},
                {"label": "6-10", "value": "6-10"},
                {"label": "11-20", "value": "11-20"},
                {"label": "21+", "value": "21+"},
            ],
        },
    },
    {
        "name": "INTAKE_NICOTINE",
        "description": "Nicotine replacement therapy info",
        "en": {"text": "If you smoke frequently or feel addicted, nicotine replacement therapy (patches, gum, lozenges) can help. Talk to your doctor about options."},
        "es": {"text": "Si fumas con frecuencia o sientes adicción, la terapia de reemplazo de nicotina (parches, chicles, pastillas) puede ayudar. Habla con tu médico sobre las opciones."},
    },
    {
        "name": "INTAKE_REASONS",
        "description": "Reasons to quit",
        "en": {"text": "Think about your reasons to quit. Health? Family? Saving money? Whatever your reason, it's a good one. Keep it close as motivation!"},
        "es": {"text": "Piensa en tus razones para dejar de fumar. ¿Salud? ¿Familia? ¿Ahorrar dinero? Cualquiera sea tu razón, es buena. ¡Tenla cerca como motivación!"},
    },
    {
        "name": "INTAKE_SUPPORT",
        "description": "Support system",
        "en": {"text": "Think about who will support your decision to quit. Tell your family and friends — having support makes a big difference!"},
        "es": {"text": "Piensa en quién apoyará tu decisión de dejar de fumar. Cuéntale a tu familia y amigos — ¡tener apoyo hace una gran diferencia!"},
    },
    {
        "name": "INTAKE_READY_CHECK",
        "description": "Ready to quit tomorrow?",
        "en": {
            "text": "Are you ready to quit smoking tomorrow?",
            "quick_replies": [
                {"label": "Yes, let's do it!", "value": "YES_TOMORROW"},
                {"label": "No, I need more time", "value": "NEED_TIME"},
            ],
        },
        "es": {
            "text": "¿Estás listo para dejar de fumar mañana?",
            "quick_replies": [
                {"label": "¡Sí, hagámoslo!", "value": "YES_TOMORROW"},
                {"label": "No, necesito más tiempo", "value": "NEED_TIME"},
            ],
        },
    },
    {
        "name": "INTAKE_TIME_SELECT",
        "description": "Time selection",
        "en": {
            "text": "Great! Each morning we'll chat for 5-10 minutes. Earlier is better. Pick your preferred time:",
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
            "text": "¡Genial! Cada mañana hablaremos 5-10 minutos. Entre más temprano mejor. Escoge tu hora preferida:",
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
        "name": "INTAKE_SET_QUIT_DATE",
        "description": "Quit date selection",
        "en": {
            "text": "Set a quit date on a low-stress day, between 7 and 14 days from now. Pick a number:",
            "quick_replies": [{"label": str(d), "value": str(d)} for d in range(7, 15)],
        },
        "es": {
            "text": "Fija un día para dejar de fumar sin mucho estrés, entre 7 y 14 días. Selecciona un número:",
            "quick_replies": [{"label": str(d), "value": str(d)} for d in range(7, 15)],
        },
    },
    {
        "name": "INTAKE_QUIT_DATE_CONFIRM",
        "description": "Quit date confirmation",
        "en": {"text": "OK, your quit day is {{quit_date}}. We'll send helpful messages starting tomorrow morning to get you ready."},
        "es": {"text": "OK, tu día para dejar de fumar es {{quit_date}}. Te enviaremos mensajes útiles empezando mañana en la mañana."},
    },
    {
        "name": "INTAKE_END",
        "description": "Intake completion",
        "en": {"text": "You're all set! Remember: if you need help at any time, text HELPNOW. You've got this! 💪"},
        "es": {"text": "¡Estás listo! Recuerda: si necesitas ayuda en cualquier momento, envía AYUDAYA. ¡Tú puedes! 💪"},
    },
]

# ============================================================================
# PRE-QUIT TEMPLATES (PQ-6 through PQ-1)
# ============================================================================
PRE_QUIT_TEMPLATES = [
    # PQ-6
    {"name": "PQ6_MORNING", "en": {"text": "Good morning! Your quit day is coming up in 6 days. Today, think about why you want to quit. Write down your top 3 reasons."}, "es": {"text": "¡Buenos días! Tu día para dejar de fumar es en 6 días. Hoy, piensa por qué quieres dejar de fumar. Escribe tus 3 razones principales."}},
    {"name": "PQ6_AFTERNOON", "en": {"text": "Tip: Start paying attention to when and why you smoke. Understanding your triggers is the first step to beating them."}, "es": {"text": "Consejo: Empieza a notar cuándo y por qué fumas. Entender tus disparadores es el primer paso para vencerlos."}},
    # PQ-5
    {"name": "PQ5_MORNING", "en": {"text": "5 days to go! Today, tell someone you trust that you're quitting. Having a support person makes you twice as likely to succeed."}, "es": {"text": "¡Faltan 5 días! Hoy, cuéntale a alguien de confianza que vas a dejar de fumar. Tener apoyo duplica tu probabilidad de éxito."}},
    {"name": "PQ5_AFTERNOON", "en": {"text": "Think about your smoking triggers: stress, boredom, after meals? For each one, plan a replacement activity."}, "es": {"text": "Piensa en tus disparadores: ¿estrés, aburrimiento, después de comer? Para cada uno, planea una actividad de reemplazo."}},
    # PQ-4
    {"name": "PQ4_MORNING", "en": {"text": "4 days left! Today, get active. Even a 10-minute walk can reduce cravings. Movement is one of the best tools against smoking urges."}, "es": {"text": "¡Faltan 4 días! Hoy, haz ejercicio. Incluso una caminata de 10 minutos puede reducir las ganas de fumar."}},
    {"name": "PQ4_AFTERNOON", "en": {"text": "Remove cigarettes, lighters, and ashtrays from your home and car. Out of sight, out of mind."}, "es": {"text": "Saca los cigarrillos, encendedores y ceniceros de tu casa y carro. Ojos que no ven, corazón que no siente."}},
    # PQ-3
    {"name": "PQ3_MORNING", "en": {"text": "3 days to your quit date! Try deep breathing: breathe in for 4 counts, hold for 4, breathe out for 6. This helps with cravings."}, "es": {"text": "¡3 días para dejar de fumar! Prueba respirar profundo: inhala 4 tiempos, sostén 4, exhala 6. Esto ayuda con las ganas."}},
    {"name": "PQ3_AFTERNOON", "en": {"text": "Stock up on healthy snacks, gum, or hard candy. Having something for your hands and mouth helps when cravings hit."}, "es": {"text": "Compra snacks saludables, chicle o caramelos. Tener algo para las manos y la boca ayuda cuando llegan las ganas."}},
    # PQ-2
    {"name": "PQ2_MORNING", "en": {"text": "2 days to go! If you haven't already, talk to your doctor about nicotine replacement (patches, gum, lozenges) to help manage withdrawal."}, "es": {"text": "¡Faltan 2 días! Si aún no lo has hecho, habla con tu médico sobre reemplazo de nicotina (parches, chicle, pastillas)."}},
    {"name": "PQ2_AFTERNOON", "en": {"text": "Plan your quit day morning: what will you do instead of smoking? Have water, gum, and a plan ready."}, "es": {"text": "Planea tu mañana del día de dejar de fumar: ¿qué harás en vez de fumar? Ten agua, chicle y un plan listo."}},
    # PQ-1
    {"name": "PQ1_MORNING", "en": {"text": "Tomorrow is your QUIT DAY! Tonight, throw away all remaining cigarettes and lighters. You're ready for this."}, "es": {"text": "¡Mañana es tu DÍA DE DEJAR DE FUMAR! Esta noche, tira todos los cigarrillos y encendedores que te queden. Estás listo."}},
    {"name": "PQ1_AFTERNOON", "en": {"text": "Set your alarm. Tomorrow morning starts your smoke-free life. Remember: cravings only last 3-5 minutes. You can do this!"}, "es": {"text": "Pon tu alarma. Mañana empieza tu vida sin humo. Recuerda: las ganas solo duran 3-5 minutos. ¡Tú puedes!"}},
]

# ============================================================================
# HELPNOW POOL MESSAGES
# These rotate when participants text HELPNOW + category keyword.
# Pool sizes per V11 spec: Crave: 23, BadMood: 24, Stress: 13, Smokers: 20, Alcohol: 12
# ============================================================================
HELPNOW_CRAVE_POOL = [
    {"en": "Craving? Drink a full glass of cold water right now. It passes in 3-5 minutes.", "es": "¿Antojo? Toma un vaso lleno de agua fría ahora. Pasa en 3-5 minutos."},
    {"en": "Put your hands in cold water or hold an ice cube. The sensation distracts your brain from the craving.", "es": "Pon las manos en agua fría o sostén un hielo. La sensación distrae tu cerebro del antojo."},
    {"en": "Take 10 deep breaths. Breathe in through your nose, out through your mouth. Feel the craving fade.", "es": "Toma 10 respiraciones profundas. Inhala por la nariz, exhala por la boca. Siente cómo el antojo se va."},
    {"en": "Go for a quick walk, even just around the block. Movement is one of the best craving fighters.", "es": "Sal a caminar rápido, aunque sea alrededor de la manzana. El movimiento es uno de los mejores contra los antojos."},
    {"en": "Chew gum or eat a crunchy snack like carrots or an apple. Keep your mouth busy!", "es": "Mastica chicle o come un snack crujiente como zanahorias o una manzana. ¡Mantén tu boca ocupada!"},
    {"en": "Text or call your support person. Just talking to someone can make the craving weaker.", "es": "Envía un mensaje o llama a tu persona de apoyo. Solo hablar con alguien puede debilitar el antojo."},
    {"en": "Remember WHY you quit. Picture the life you're building without cigarettes.", "es": "Recuerda POR QUÉ dejaste de fumar. Imagina la vida que estás construyendo sin cigarrillos."},
    {"en": "Do the 4-7-8 breathing: breathe in for 4, hold for 7, breathe out for 8. Repeat 3 times.", "es": "Haz la respiración 4-7-8: inhala 4, sostén 7, exhala 8. Repite 3 veces."},
    {"en": "Wash your hands or splash water on your face. A physical reset can break the craving cycle.", "es": "Lávate las manos o échate agua en la cara. Un reset físico puede romper el ciclo del antojo."},
    {"en": "Count backwards from 100 by 7s. By the time you finish, the craving will be weaker.", "es": "Cuenta hacia atrás desde 100 de 7 en 7. Para cuando termines, el antojo será más débil."},
    {"en": "Smell something strong: coffee beans, peppermint oil, or a lemon. It overrides the cigarette craving.", "es": "Huele algo fuerte: granos de café, aceite de menta o un limón. Anula el antojo de cigarrillo."},
    {"en": "Do 20 jumping jacks or pushups right now. The endorphin boost fights the craving.", "es": "Haz 20 saltos o lagartijas ahora mismo. La descarga de endorfinas combate el antojo."},
    {"en": "Look at a photo of someone you love. You're quitting for them too.", "es": "Mira una foto de alguien que amas. También dejas de fumar por ellos."},
    {"en": "Open your phone's calculator and add up how much money you've saved since quitting.", "es": "Abre la calculadora de tu teléfono y suma cuánto dinero has ahorrado desde que dejaste de fumar."},
    {"en": "Brush your teeth. That fresh, clean feeling makes you not want to ruin it with smoke.", "es": "Cepíllate los dientes. Esa sensación fresca y limpia hace que no quieras arruinarla con humo."},
    {"en": "Play a game on your phone for 5 minutes. Distraction is a proven craving buster.", "es": "Juega un juego en tu teléfono por 5 minutos. La distracción es un probado destructor de antojos."},
    {"en": "Stretch your whole body for 2 minutes. Reach up high, then touch your toes.", "es": "Estira todo tu cuerpo por 2 minutos. Estírate hacia arriba, luego toca tus pies."},
    {"en": "Eat a piece of dark chocolate. It triggers similar pleasure chemicals as nicotine.", "es": "Come un pedazo de chocolate oscuro. Activa químicos de placer similares a la nicotina."},
    {"en": "Write down 3 things you're grateful for right now. Gratitude reduces craving intensity.", "es": "Escribe 3 cosas por las que estás agradecido ahora. La gratitud reduce la intensidad del antojo."},
    {"en": "Squeeze a stress ball or rubber band on your wrist. Physical sensation distracts from cravings.", "es": "Aprieta una pelota de estrés o una banda en tu muñeca. La sensación física distrae de los antojos."},
    {"en": "Listen to your favorite upbeat song. Music activates reward pathways that compete with nicotine.", "es": "Escucha tu canción favorita. La música activa vías de recompensa que compiten con la nicotina."},
    {"en": "Remind yourself: you've already survived hundreds of cravings. This one will pass too.", "es": "Recuérdate: ya has sobrevivido cientos de antojos. Este también pasará."},
    {"en": "Sip on herbal tea. The warmth and flavor give your mouth something to do besides crave.", "es": "Toma un té herbal. El calor y el sabor le dan a tu boca algo que hacer además de desear fumar."},
]

HELPNOW_BADMOOD_POOL = [
    {"en": "Bad mood? That's your brain adjusting to life without nicotine. It gets better — usually within 2-4 weeks.", "es": "¿Mal humor? Es tu cerebro ajustándose a la vida sin nicotina. Mejora — usualmente en 2-4 semanas."},
    {"en": "Step outside and take 5 slow, deep breaths. Fresh air and oxygen can shift your mood fast.", "es": "Sal y toma 5 respiraciones lentas y profundas. El aire fresco y el oxígeno pueden cambiar tu humor rápido."},
    {"en": "Write down what's bothering you. Getting it on paper gets it out of your head.", "es": "Escribe lo que te molesta. Ponerlo en papel lo saca de tu cabeza."},
    {"en": "Call or text someone who makes you laugh. Laughter is a natural mood booster.", "es": "Llama o envía un mensaje a alguien que te haga reír. La risa es un elevador natural del humor."},
    {"en": "Put on your favorite music. It can change your brain chemistry in minutes.", "es": "Pon tu música favorita. Puede cambiar la química de tu cerebro en minutos."},
    {"en": "Go for a walk, even just 5 minutes. Moving your body moves your mood.", "es": "Sal a caminar, aunque sea 5 minutos. Mover tu cuerpo mueve tu humor."},
    {"en": "Eat something healthy. Low blood sugar makes bad moods worse.", "es": "Come algo saludable. El azúcar baja empeora el mal humor."},
    {"en": "Take a warm shower. Water therapy is a real thing — it calms your nervous system.", "es": "Toma una ducha caliente. La terapia de agua es real — calma tu sistema nervioso."},
    {"en": "Watch a funny video. Even 2 minutes of laughing helps reset your mood.", "es": "Mira un video chistoso. Incluso 2 minutos de risa ayudan a reiniciar tu humor."},
    {"en": "Remind yourself: a cigarette won't fix your mood. It will just add guilt to the bad feeling.", "es": "Recuérdate: un cigarrillo no arreglará tu humor. Solo añadirá culpa al mal sentimiento."},
    {"en": "Try the \"5 senses\" exercise: notice 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste.", "es": "Prueba el ejercicio \"5 sentidos\": nota 5 cosas que ves, 4 que oyes, 3 que sientes, 2 que hueles, 1 que saboreas."},
    {"en": "Drink a glass of cold water slowly. Hydration affects mood more than most people realize.", "es": "Toma un vaso de agua fría lentamente. La hidratación afecta el humor más de lo que la gente cree."},
    {"en": "Do something kind for someone else. Helping others is one of the fastest mood lifters.", "es": "Haz algo amable por alguien. Ayudar a otros es uno de los elevadores de humor más rápidos."},
    {"en": "Feeling irritable? That's a sign your body is healing from nicotine. It's temporary.", "es": "¿Irritable? Es señal de que tu cuerpo se está curando de la nicotina. Es temporal."},
    {"en": "Tidy up a small area — your desk, a drawer. Organizing your space can organize your thoughts.", "es": "Ordena un área pequeña — tu escritorio, un cajón. Organizar tu espacio puede organizar tus pensamientos."},
    {"en": "Play with a pet if you have one. Animal interaction reduces stress hormones.", "es": "Juega con una mascota si tienes una. La interacción con animales reduce las hormonas de estrés."},
    {"en": "Stretch your neck and shoulders for 2 minutes. Tension in your body creates tension in your mood.", "es": "Estira tu cuello y hombros por 2 minutos. La tensión en tu cuerpo crea tensión en tu humor."},
    {"en": "Look at old photos that make you happy. Nostalgia is a scientifically proven mood booster.", "es": "Mira fotos viejas que te hagan feliz. La nostalgia es un elevador de humor comprobado científicamente."},
    {"en": "Make yourself a warm drink — tea, cocoa, or warm water with lemon. Warmth soothes.", "es": "Prepárate una bebida caliente — té, chocolate o agua tibia con limón. El calor reconforta."},
    {"en": "Close your eyes and imagine your happiest memory in detail. Your brain responds as if it's happening now.", "es": "Cierra los ojos e imagina tu recuerdo más feliz en detalle. Tu cerebro responde como si estuviera pasando ahora."},
    {"en": "Bad moods come and go like waves. This one is already cresting. Let it pass.", "es": "Los malos humores van y vienen como olas. Este ya está en su punto más alto. Déjalo pasar."},
    {"en": "Say out loud: \"I am stronger than this feeling.\" Your brain believes what you tell it.", "es": "Di en voz alta: \"Soy más fuerte que este sentimiento.\" Tu cerebro cree lo que le dices."},
    {"en": "Splash cold water on your face. It triggers the dive reflex and calms your nervous system instantly.", "es": "Échate agua fría en la cara. Activa el reflejo de inmersión y calma tu sistema nervioso al instante."},
    {"en": "You've made it this far without smoking. Your bad mood is proof you're winning. Keep going.", "es": "Has llegado hasta aquí sin fumar. Tu mal humor es prueba de que estás ganando. Sigue adelante."},
]

HELPNOW_STRESS_POOL = [
    {"en": "Stressed? Try box breathing: breathe in 4 counts, hold 4, out 4, hold 4. Repeat 4 times.", "es": "¿Estresado? Prueba respiración cuadrada: inhala 4, sostén 4, exhala 4, sostén 4. Repite 4 veces."},
    {"en": "Stress is a top smoking trigger. But a cigarette only masks stress — it doesn't fix it.", "es": "El estrés es un disparador principal del fumar. Pero un cigarrillo solo enmascara el estrés — no lo arregla."},
    {"en": "Name what's stressing you. Just identifying it reduces its power over you.", "es": "Nombra lo que te estresa. Solo identificarlo reduce su poder sobre ti."},
    {"en": "Tense every muscle in your body for 5 seconds, then release. Progressive relaxation works.", "es": "Tensa todos los músculos de tu cuerpo por 5 segundos, luego suelta. La relajación progresiva funciona."},
    {"en": "Ask yourself: will this matter in 5 years? If not, it's not worth a cigarette.", "es": "Pregúntate: ¿esto importará en 5 años? Si no, no vale un cigarrillo."},
    {"en": "Go outside. Sunlight and fresh air lower cortisol (stress hormone) levels.", "es": "Sal afuera. La luz del sol y el aire fresco bajan los niveles de cortisol (hormona del estrés)."},
    {"en": "Put on calm music or nature sounds. Your brain will sync to the peaceful rhythm.", "es": "Pon música calmada o sonidos de la naturaleza. Tu cerebro se sincronizará con el ritmo pacífico."},
    {"en": "Talk to someone about what's stressing you. Don't carry it alone.", "es": "Habla con alguien sobre lo que te estresa. No lo cargues solo."},
    {"en": "Take a 10-minute walk. Physical movement is the fastest natural stress reducer.", "es": "Camina 10 minutos. El movimiento físico es el reductor de estrés natural más rápido."},
    {"en": "Write a to-do list. Getting tasks out of your head and onto paper reduces overwhelm.", "es": "Escribe una lista de pendientes. Sacar las tareas de tu cabeza y ponerlas en papel reduce el agobio."},
    {"en": "Drink water. Dehydration increases cortisol, which increases stress.", "es": "Toma agua. La deshidratación aumenta el cortisol, que aumenta el estrés."},
    {"en": "Remember: you've handled stressful situations before without smoking. You can do it again.", "es": "Recuerda: has manejado situaciones estresantes antes sin fumar. Puedes hacerlo de nuevo."},
    {"en": "Focus on what you CAN control right now. Let go of what you can't.", "es": "Enfócate en lo que PUEDES controlar ahora. Deja ir lo que no puedes."},
]

HELPNOW_SMOKERS_POOL = [
    {"en": "Around smokers? Excuse yourself for a few minutes. Distance is your best defense.", "es": "¿Con fumadores? Discúlpate unos minutos. La distancia es tu mejor defensa."},
    {"en": "If you can't leave, keep your hands busy: hold a drink, check your phone, fidget with something.", "es": "Si no puedes irte, mantén las manos ocupadas: sostén una bebida, revisa tu teléfono, juega con algo."},
    {"en": "Chew gum or suck on a mint. Having something in your mouth helps when others are smoking.", "es": "Mastica chicle o chupa un caramelo de menta. Tener algo en la boca ayuda cuando otros fuman."},
    {"en": "Stand upwind from smokers. The less you smell smoke, the weaker the trigger.", "es": "Ponte contra el viento de los fumadores. Mientras menos huelas el humo, más débil el disparador."},
    {"en": "Remind yourself: they wish they could do what you're doing right now.", "es": "Recuérdate: ellos desearían poder hacer lo que tú estás haciendo ahora."},
    {"en": "Text your support person: \"I'm around smokers and staying strong.\" Accountability helps.", "es": "Envía un mensaje a tu persona de apoyo: \"Estoy con fumadores y me mantengo fuerte.\" La responsabilidad ayuda."},
    {"en": "Take slow breaths through your nose. Focus on the clean air going into your lungs.", "es": "Respira lento por la nariz. Concéntrate en el aire limpio entrando a tus pulmones."},
    {"en": "Think about how your lungs are healing. In just 2 weeks, lung function improves significantly.", "es": "Piensa en cómo tus pulmones se están sanando. En solo 2 semanas, la función pulmonar mejora significativamente."},
    {"en": "If they offer you a cigarette, say: \"No thanks, I quit.\" Saying it out loud makes it real.", "es": "Si te ofrecen un cigarrillo, di: \"No gracias, lo dejé.\" Decirlo en voz alta lo hace real."},
    {"en": "Notice how cigarettes smell to you now as a non-smoker. Less appealing, right?", "es": "Nota cómo te huelen los cigarrillos ahora como no fumador. Menos atractivo, ¿verdad?"},
    {"en": "Count the cigarettes they smoke while you're there. Multiply by $0.50 each. That's money you're saving.", "es": "Cuenta los cigarrillos que fuman mientras estás ahí. Multiplica por $0.50 cada uno. Ese es dinero que tú ahorras."},
    {"en": "Every time you're around smokers and don't smoke, your quitting muscles get stronger.", "es": "Cada vez que estás con fumadores y no fumas, tus músculos para dejar de fumar se fortalecen."},
    {"en": "Think about your reasons to quit. Would smoking right now serve those reasons? No.", "es": "Piensa en tus razones para dejar de fumar. ¿Fumar ahora serviría a esas razones? No."},
    {"en": "Get a non-smoking buddy at the gathering. You're probably not the only one who quit.", "es": "Busca un compañero no fumador en la reunión. Probablemente no eres el único que dejó de fumar."},
    {"en": "If the group goes outside to smoke, stay inside. Protect your progress.", "es": "Si el grupo sale a fumar, quédate adentro. Protege tu progreso."},
    {"en": "Drink water while they smoke. Hydration reduces cravings and gives you something to do.", "es": "Toma agua mientras ellos fuman. La hidratación reduce los antojos y te da algo que hacer."},
    {"en": "You're the strongest person at this gathering. Not smoking while others do takes real willpower.", "es": "Eres la persona más fuerte en esta reunión. No fumar mientras otros lo hacen requiere verdadera fuerza de voluntad."},
    {"en": "Play the tape forward: if you smoke one, will you stop at one? Protect your streak.", "es": "Piensa en lo que sigue: si fumas uno, ¿pararás en uno? Protege tu racha."},
    {"en": "Leave the situation if you need to. Your health is worth more than any social moment.", "es": "Vete de la situación si lo necesitas. Tu salud vale más que cualquier momento social."},
    {"en": "You've got this. Being around smokers without smoking is one of the hardest things — and you're doing it.", "es": "Tú puedes. Estar con fumadores sin fumar es una de las cosas más difíciles — y tú lo estás haciendo."},
]

HELPNOW_ALCOHOL_POOL = [
    {"en": "Drinking? Alcohol weakens willpower. Switch to water or a non-alcoholic drink.", "es": "¿Tomando? El alcohol debilita la voluntad. Cambia a agua o una bebida sin alcohol."},
    {"en": "Alcohol + smoking urges are linked in your brain. Break the link by not giving in tonight.", "es": "Alcohol + ganas de fumar están conectados en tu cerebro. Rompe la conexión no cediendo esta noche."},
    {"en": "If you're at a bar, step outside for fresh air (not a smoke). Reset your brain.", "es": "Si estás en un bar, sal por aire fresco (no a fumar). Reinicia tu cerebro."},
    {"en": "Each drink makes it harder to say no. Set a drink limit before you start.", "es": "Cada trago hace más difícil decir no. Pon un límite de tragos antes de empezar."},
    {"en": "Chew gum between sips. It keeps your mouth busy and reduces the smoking urge.", "es": "Mastica chicle entre tragos. Mantiene tu boca ocupada y reduce las ganas de fumar."},
    {"en": "Tell your friends you've quit. Social accountability is extra powerful when alcohol is involved.", "es": "Dile a tus amigos que dejaste de fumar. La responsabilidad social es extra poderosa cuando hay alcohol."},
    {"en": "Alternate: one alcoholic drink, one glass of water. Less alcohol = less craving.", "es": "Alterna: un trago de alcohol, un vaso de agua. Menos alcohol = menos antojos."},
    {"en": "Avoid your usual smoking spots (patio, smoking area). Stay where non-smokers are.", "es": "Evita tus lugares habituales de fumar (patio, área de fumadores). Quédate donde están los no fumadores."},
    {"en": "A cigarette will make tomorrow worse: hangover AND guilt. Skip it.", "es": "Un cigarrillo hará que mañana sea peor: resaca Y culpa. Pásalo por alto."},
    {"en": "Play the tape forward: morning you will thank tonight you for not smoking.", "es": "Piensa en lo que sigue: el tú de mañana le agradecerá al tú de esta noche por no fumar."},
    {"en": "Keep a drink in your smoking hand. It physically blocks the habit.", "es": "Mantén una bebida en tu mano de fumar. Bloquea físicamente el hábito."},
    {"en": "You've made it this far. One night out won't break you unless you let it.", "es": "Has llegado hasta aquí. Una noche fuera no te va a vencer a menos que lo permitas."},
]

# ============================================================================
# HELPNOW DISPATCH + SLIP ESCALATION
# ============================================================================
HELPNOW_DISPATCH_TEMPLATE = {
    "name": "HELPNOW_RESPONSE",
    "description": "HELPNOW dispatch - ask what they need help with",
    "en": {"text": "I'm here to help! What are you dealing with? Reply with one of these:\nCRAVE - Craving a cigarette\nBADMOOD - Feeling down\nSTRESS - Feeling stressed\nSMOKERS - Around smokers\nALCOHOL - Drinking alcohol", "quick_replies": [{"label": "Crave", "value": "CRAVE"}, {"label": "Bad Mood", "value": "BADMOOD"}, {"label": "Stress", "value": "STRESS"}, {"label": "Smokers", "value": "SMOKERS"}, {"label": "Alcohol", "value": "ALCOHOL"}]},
    "es": {"text": "¡Estoy aquí para ayudar! ¿Qué necesitas? Responde con una de estas:\nANTOJO - Antojo de cigarrillo\nMALHUMOR - Sintiéndote mal\nESTRES - Sintiéndote estresado\nFUMADORES - Cerca de fumadores\nALCOHOL - Tomando alcohol", "quick_replies": [{"label": "Antojo", "value": "ANTOJO"}, {"label": "Mal Humor", "value": "MALHUMOR"}, {"label": "Estrés", "value": "ESTRES"}, {"label": "Fumadores", "value": "FUMADORES"}, {"label": "Alcohol", "value": "ALCOHOL"}]},
}

SLIP_TEMPLATES = [
    {
        "name": "SLIP_FIRST",
        "description": "First slip response",
        "en": {"text": "Hey, one slip doesn't erase your progress. Most people who quit successfully have slips along the way. What matters is that you don't give up. You're still in this! What caused the slip?\nReply: STRESS, BADMOOD, SMOKERS, ALCOHOL, or CRAVE", "quick_replies": [{"label": "Stress", "value": "STRESS"}, {"label": "Bad Mood", "value": "BADMOOD"}, {"label": "Smokers", "value": "SMOKERS"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Craving", "value": "CRAVE"}]},
        "es": {"text": "Hey, un desliz no borra tu progreso. La mayoría de las personas que dejan de fumar exitosamente tienen deslices. Lo que importa es que no te rindas. ¡Sigues en esto! ¿Qué causó el desliz?\nResponde: ESTRES, MALHUMOR, FUMADORES, ALCOHOL, o ANTOJO", "quick_replies": [{"label": "Estrés", "value": "ESTRES"}, {"label": "Mal Humor", "value": "MALHUMOR"}, {"label": "Fumadores", "value": "FUMADORES"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Antojo", "value": "ANTOJO"}]},
    },
    {
        "name": "SLIP_SECOND",
        "description": "Second slip response",
        "en": {"text": "I know this is hard. A second slip is common and it does NOT mean failure. Let's figure out your pattern. What triggered it this time?\nReply: STRESS, BADMOOD, SMOKERS, ALCOHOL, or CRAVE", "quick_replies": [{"label": "Stress", "value": "STRESS"}, {"label": "Bad Mood", "value": "BADMOOD"}, {"label": "Smokers", "value": "SMOKERS"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Craving", "value": "CRAVE"}]},
        "es": {"text": "Sé que esto es difícil. Un segundo desliz es común y NO significa fracaso. Vamos a encontrar tu patrón. ¿Qué lo causó esta vez?\nResponde: ESTRES, MALHUMOR, FUMADORES, ALCOHOL, o ANTOJO", "quick_replies": [{"label": "Estrés", "value": "ESTRES"}, {"label": "Mal Humor", "value": "MALHUMOR"}, {"label": "Fumadores", "value": "FUMADORES"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Antojo", "value": "ANTOJO"}]},
    },
    {
        "name": "SLIP_THIRD_PLUS",
        "description": "Third+ slip response (consider NRT)",
        "en": {"text": "I see a pattern forming. It's time to bring in extra support. Have you considered nicotine replacement therapy (patches, gum, lozenges)? Talk to your doctor — it can make a huge difference. Meanwhile, what triggered this one?\nReply: STRESS, BADMOOD, SMOKERS, ALCOHOL, or CRAVE", "quick_replies": [{"label": "Stress", "value": "STRESS"}, {"label": "Bad Mood", "value": "BADMOOD"}, {"label": "Smokers", "value": "SMOKERS"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Craving", "value": "CRAVE"}]},
        "es": {"text": "Veo un patrón formándose. Es hora de buscar apoyo extra. ¿Has considerado la terapia de reemplazo de nicotina (parches, chicle, pastillas)? Habla con tu médico — puede hacer una gran diferencia. Mientras tanto, ¿qué causó este desliz?\nResponde: ESTRES, MALHUMOR, FUMADORES, ALCOHOL, o ANTOJO", "quick_replies": [{"label": "Estrés", "value": "ESTRES"}, {"label": "Mal Humor", "value": "MALHUMOR"}, {"label": "Fumadores", "value": "FUMADORES"}, {"label": "Alcohol", "value": "ALCOHOL"}, {"label": "Antojo", "value": "ANTOJO"}]},
    },
]

# ============================================================================
# CHECKOUT TEMPLATE
# ============================================================================
CHECKOUT_TEMPLATE = {
    "name": "DAILY_CHECKOUT",
    "description": "Nightly 8pm checkout",
    "en": {"text": "Daily check-in: Did you smoke today?", "quick_replies": [{"label": "Yes, I smoked", "value": "YES_SMOKED"}, {"label": "No, smoke-free!", "value": "NO_SMOKEFREE"}]},
    "es": {"text": "Check-in diario: ¿Fumaste hoy?", "quick_replies": [{"label": "Sí, fumé", "value": "YES_SMOKED"}, {"label": "No, ¡libre de humo!", "value": "NO_SMOKEFREE"}]},
}

CHECKOUT_SMOKEFREE_TEMPLATE = {
    "name": "CHECKOUT_SMOKEFREE",
    "description": "Response when participant reports smoke-free day",
    "en": {"text": "Amazing! Another smoke-free day in the books. You're doing great. Keep it up! 🎉"},
    "es": {"text": "¡Increíble! Otro día sin fumar. ¡Lo estás haciendo genial! ¡Sigue así! 🎉"},
}

# ============================================================================
# INTERMITTENT MESSAGE POOLS (rotating motivational content)
# These are sent at 1pm, 4pm, 7pm each quit day.
# ============================================================================
INTERMITTENT_POOL_EN = [
    "Every cigarette you don't smoke is a victory. Keep collecting those wins.",
    "Your body is healing right now. Lung function improves every day you stay smoke-free.",
    "Think about what you'll do with the money you're saving. It adds up fast!",
    "Cravings are like waves — they rise, peak, and fall. Ride it out.",
    "You've already made it through the hardest part. Don't give that up.",
    "Your sense of taste and smell are getting better. Notice the difference!",
    "Deep breaths: in through the nose, out through the mouth. Feel the calm.",
    "You're reducing your risk of heart disease right now. Your heart thanks you.",
    "Remember your reasons. Write them where you can see them every day.",
    "Each day smoke-free is a gift to your future self. Keep giving.",
    "Drink water when cravings hit. Hydration is your secret weapon.",
    "Your blood pressure is normalizing. Your body knows what to do when you let it.",
    "You're proving to yourself that you're stronger than a cigarette.",
    "Move your body! Even a 5-minute walk reduces craving intensity.",
    "Your teeth are getting whiter and your breath is fresher. Smile!",
    "You're not just quitting something bad — you're starting something good.",
    "Think of one thing that went well today. Focus on progress, not perfection.",
    "Your lungs are clearing out tar and mucus. Coughing is actually healing.",
    "You're saving about $150/month by not smoking. That's $1,800/year!",
    "Nicotine cravings last 3-5 minutes. You can survive anything for 5 minutes.",
    "Your carbon monoxide levels are already back to normal. Clean blood!",
    "You're teaching your brain new habits. Every craving resisted makes the next one easier.",
    "Imagine yourself 1 year from now, completely free. That's where you're heading.",
    "Your circulation is improving. More oxygen to your muscles and brain.",
    "You're breaking a cycle that's been controlling you. That's power.",
    "Reward yourself today. You deserve it for staying smoke-free.",
    "Talk to someone about your journey. Sharing strengthens your commitment.",
    "Stress doesn't need a cigarette. Try stretching, walking, or breathing.",
    "You're a role model for others who want to quit. Your example matters.",
    "One day at a time. Today is all you need to focus on.",
]

INTERMITTENT_POOL_ES = [
    "Cada cigarrillo que no fumas es una victoria. Sigue coleccionando esos triunfos.",
    "Tu cuerpo se está sanando ahora. La función pulmonar mejora cada día sin fumar.",
    "Piensa en lo que harás con el dinero que estás ahorrando. ¡Se acumula rápido!",
    "Los antojos son como olas — suben, llegan al pico y bajan. Aguanta.",
    "Ya pasaste la parte más difícil. No renuncies a eso.",
    "Tu sentido del gusto y olfato están mejorando. ¡Nota la diferencia!",
    "Respiraciones profundas: inhala por la nariz, exhala por la boca. Siente la calma.",
    "Estás reduciendo tu riesgo de enfermedad cardíaca ahora. Tu corazón te lo agradece.",
    "Recuerda tus razones. Escríbelas donde puedas verlas todos los días.",
    "Cada día sin fumar es un regalo para tu yo futuro. Sigue dando.",
    "Toma agua cuando lleguen los antojos. La hidratación es tu arma secreta.",
    "Tu presión arterial se está normalizando. Tu cuerpo sabe qué hacer cuando lo dejas.",
    "Te estás demostrando que eres más fuerte que un cigarrillo.",
    "¡Mueve tu cuerpo! Incluso una caminata de 5 minutos reduce los antojos.",
    "Tus dientes se están poniendo más blancos y tu aliento más fresco. ¡Sonríe!",
    "No solo estás dejando algo malo — estás empezando algo bueno.",
    "Piensa en una cosa que salió bien hoy. Enfócate en el progreso, no en la perfección.",
    "Tus pulmones están limpiando el alquitrán. Toser es en realidad señal de sanación.",
    "Estás ahorrando alrededor de $150/mes. ¡Eso es $1,800/año!",
    "Los antojos de nicotina duran 3-5 minutos. Puedes sobrevivir cualquier cosa por 5 minutos.",
    "Tus niveles de monóxido de carbono ya son normales. ¡Sangre limpia!",
    "Le estás enseñando nuevos hábitos a tu cerebro. Cada antojo resistido hace el siguiente más fácil.",
    "Imagínate en 1 año, completamente libre. Ahí es donde vas.",
    "Tu circulación está mejorando. Más oxígeno para tus músculos y cerebro.",
    "Estás rompiendo un ciclo que te controlaba. Eso es poder.",
    "Prémiate hoy. Te lo mereces por mantenerte sin fumar.",
    "Habla con alguien sobre tu camino. Compartir fortalece tu compromiso.",
    "El estrés no necesita un cigarrillo. Prueba estirarte, caminar o respirar.",
    "Eres un modelo a seguir para otros que quieren dejar de fumar. Tu ejemplo importa.",
    "Un día a la vez. Hoy es todo lo que necesitas enfocarte.",
]

# Morning session themes that rotate across quit days
MORNING_THEMES_EN = [
    "Good morning! Day {day} smoke-free. Your body is thanking you right now.",
    "Rise and shine! Day {day} of your new life. How are you feeling today?",
    "Morning, champion! Day {day} without a cigarette. You're getting stronger!",
    "Day {day}! Your lungs are cleaner, your breath is fresher, and your wallet is fuller.",
    "Happy Day {day}! Remember why you started this journey. You've got this!",
    "Good morning! {day} days smoke-free! That's something to be proud of.",
    "Day {day} — another chance to prove you're stronger than nicotine.",
    "Welcome to Day {day}! Tip: Stay hydrated today. Water helps fight cravings.",
    "Morning! Day {day} of freedom from smoking. What will you accomplish today?",
    "Day {day}! Fun fact: Your blood circulation has improved since you quit.",
]

MORNING_THEMES_ES = [
    "¡Buenos días! Día {day} sin fumar. Tu cuerpo te lo está agradeciendo.",
    "¡Arriba! Día {day} de tu nueva vida. ¿Cómo te sientes hoy?",
    "¡Mañana, campeón! Día {day} sin cigarrillo. ¡Te estás haciendo más fuerte!",
    "¡Día {day}! Tus pulmones están más limpios, tu aliento más fresco y tu cartera más llena.",
    "¡Feliz Día {day}! Recuerda por qué empezaste este camino. ¡Tú puedes!",
    "¡Buenos días! ¡{day} días sin fumar! Eso es para estar orgulloso.",
    "Día {day} — otra oportunidad de demostrar que eres más fuerte que la nicotina.",
    "¡Bienvenido al Día {day}! Consejo: Mantente hidratado hoy. El agua ayuda contra los antojos.",
    "¡Mañana! Día {day} de libertad del tabaco. ¿Qué lograrás hoy?",
    "¡Día {day}! Dato curioso: Tu circulación sanguínea ha mejorado desde que dejaste de fumar.",
]

TOTAL_QUIT_DAYS = 180


# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================
async def get_or_create(session: AsyncSession, model, defaults: dict, **lookup) -> tuple[Any, bool]:
    """Get existing record or create new one. Returns (instance, created)."""
    from sqlalchemy import select as sel
    stmt = sel(model)
    for k, v in lookup.items():
        stmt = stmt.where(getattr(model, k) == v)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False
    instance = model(**lookup, **defaults)
    session.add(instance)
    await session.flush()
    return instance, True


async def create_project(session: AsyncSession, user_id: int) -> int:
    from app.models import Project
    project, created = await get_or_create(
        session, Project, name=PROJECT_NAME,
        defaults={
            "user_id": user_id,
            "description": PROJECT_DESCRIPTION,
            "status": "ACTIVE",
            "settings": {
                "default_language": "en",
                "supported_languages": ["en", "es"],
                "default_message_time": "08:00",
                "timezone": "America/Chicago",
                "protocol_version": "V11",
                "total_quit_days": TOTAL_QUIT_DAYS,
            },
        },
    )
    action = "Created" if created else "Found existing"
    print(f"{action} project '{PROJECT_NAME}' (ID: {project.id})")
    return project.id


async def create_variables(session: AsyncSession, project_id: int) -> dict[str, int]:
    from app.models import Variable
    ids = {}
    for v in VARIABLES:
        var, created = await get_or_create(
            session, Variable, project_id=project_id, name=v["name"],
            defaults={
                "display_name": v.get("display_name", v["name"]),
                "type": v.get("type", "STRING"),
                "source_type": "MANUAL",
                "default_value": v.get("default_value"),
            },
        )
        ids[v["name"]] = var.id
        if created:
            print(f"  + Variable: {v['name']}")
    return ids


async def create_template(
    session: AsyncSession, project_id: int, template_def: dict,
    en_lang_id: int, es_lang_id: int,
) -> int:
    from app.models import MessageTemplate, MessageTemplateText
    tmpl, created = await get_or_create(
        session, MessageTemplate, project_id=project_id, name=template_def["name"],
        defaults={"description": template_def.get("description"), "type": "STANDARD"},
    )
    if not created:
        return tmpl.id

    for lang_key, lang_id in [("en", en_lang_id), ("es", es_lang_id)]:
        if lang_key in template_def:
            text_data = template_def[lang_key]
            txt = MessageTemplateText(
                template_id=tmpl.id,
                language_id=lang_id,
                message_text=text_data.get("text"),
                media_url=text_data.get("media_url"),
                media_type="image" if text_data.get("media_url") else None,
                quick_replies=text_data.get("quick_replies", []),
            )
            session.add(txt)
    return tmpl.id


async def create_timing_elements(session: AsyncSession, project_id: int) -> dict[str, int]:
    from app.models import TimingElement
    timing_defs = [
        {"name": "NO_DELAY", "offset_minutes": 0},
        {"name": "2_MIN_DELAY", "offset_minutes": 2},
        {"name": "1_HOUR_DELAY", "offset_hours": 1},
        {"name": "MORNING_DEFAULT", "overwrite_time": True, "overwritten_hours": 8, "overwritten_minutes": 0},
        {"name": "INTERMITTENT_1PM", "overwrite_time": True, "overwritten_hours": 13, "overwritten_minutes": 0},
        {"name": "INTERMITTENT_4PM", "overwrite_time": True, "overwritten_hours": 16, "overwritten_minutes": 0},
        {"name": "INTERMITTENT_7PM", "overwrite_time": True, "overwritten_hours": 19, "overwritten_minutes": 0},
        {"name": "CHECKOUT_8PM", "overwrite_time": True, "overwritten_hours": 20, "overwritten_minutes": 0},
        {"name": "NEXT_DAY_MORNING", "offset_days": 1, "overwrite_time": True, "overwritten_hours": 8, "overwritten_minutes": 0},
    ]
    ids = {}
    for td in timing_defs:
        name = td.pop("name")
        t, created = await get_or_create(
            session, TimingElement, project_id=project_id, name=name,
            defaults={
                "offset_days": td.get("offset_days", 0),
                "offset_hours": td.get("offset_hours", 0),
                "offset_minutes": td.get("offset_minutes", 0),
                "overwrite_time": td.get("overwrite_time", False),
                "overwritten_hours": td.get("overwritten_hours"),
                "overwritten_minutes": td.get("overwritten_minutes"),
            },
        )
        ids[name] = t.id
        if created:
            print(f"  + Timing: {name}")
        td["name"] = name  # Restore for re-runs
    return ids


async def create_node(
    session: AsyncSession, project_id: int, name: str,
    template_id: int | None = None, timing_id: int | None = None,
    is_entry: bool = False, is_terminal: bool = False,
    display_name: str | None = None, extra_data: dict | None = None,
) -> int:
    from app.models import MessagingNode
    node, created = await get_or_create(
        session, MessagingNode, project_id=project_id, name=name,
        defaults={
            "display_name": display_name or name,
            "is_entry_node": is_entry,
            "is_terminal_node": is_terminal,
            "template_id": template_id,
            "timing_element_id": timing_id,
            "extra_data": extra_data,
        },
    )
    return node.id


async def create_edge(
    session: AsyncSession, parent_id: int, child_id: int,
    label: str | None = None,
) -> None:
    from app.models import MessagingNodeEdge
    _, created = await get_or_create(
        session, MessagingNodeEdge,
        parent_node_id=parent_id, child_node_id=child_id,
        defaults={"edge_label": label},
    )


# ============================================================================
# MAIN IMPORT
# ============================================================================
async def main():
    print("=" * 70)
    print("QuitTxt V11 Protocol Import Script")
    print(f"Total quit days: {TOTAL_QUIT_DAYS}")
    print("=" * 70)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            from app.models import User, AvailableLanguage

            # Get admin user
            result = await session.execute(select(User).where(User.email == "admin@example.com"))
            admin = result.scalar_one_or_none()
            if not admin:
                print("ERROR: Admin user not found. Run database seed first.")
                return

            # Get or create languages
            en_lang, _ = await get_or_create(session, AvailableLanguage, short_name="en", defaults={"name": "English", "code": 1})
            es_lang, _ = await get_or_create(session, AvailableLanguage, short_name="es", defaults={"name": "Spanish", "code": 2})
            print(f"Languages: EN={en_lang.id}, ES={es_lang.id}")

            # 1. Create project
            print("\n1. Creating project...")
            project_id = await create_project(session, admin.id)

            # 2. Create variables
            print("\n2. Creating variables...")
            var_ids = await create_variables(session, project_id)
            print(f"   Total: {len(var_ids)} variables")

            # 3. Create timing elements
            print("\n3. Creating timing elements...")
            timing_ids = await create_timing_elements(session, project_id)
            print(f"   Total: {len(timing_ids)} timing elements")

            # 4. Create all templates
            print("\n4. Creating message templates...")
            tmpl_ids: dict[str, int] = {}

            # Intake templates
            for td in INTAKE_TEMPLATES:
                tmpl_ids[td["name"]] = await create_template(session, project_id, td, en_lang.id, es_lang.id)

            # Pre-quit templates
            for td in PRE_QUIT_TEMPLATES:
                tmpl_ids[td["name"]] = await create_template(session, project_id, td, en_lang.id, es_lang.id)

            # HELPNOW dispatch
            tmpl_ids[HELPNOW_DISPATCH_TEMPLATE["name"]] = await create_template(
                session, project_id, HELPNOW_DISPATCH_TEMPLATE, en_lang.id, es_lang.id
            )

            # HELPNOW pool templates
            pool_tmpl_ids: dict[str, list[int]] = {
                "CRAVE": [], "BADMOOD": [], "STRESS": [], "SMOKERS": [], "ALCOHOL": [],
            }
            for pool_name, pool_msgs in [
                ("CRAVE", HELPNOW_CRAVE_POOL),
                ("BADMOOD", HELPNOW_BADMOOD_POOL),
                ("STRESS", HELPNOW_STRESS_POOL),
                ("SMOKERS", HELPNOW_SMOKERS_POOL),
                ("ALCOHOL", HELPNOW_ALCOHOL_POOL),
            ]:
                for i, msg in enumerate(pool_msgs, 1):
                    tname = f"HELPNOW_{pool_name}_{i:02d}"
                    tid = await create_template(
                        session, project_id,
                        {"name": tname, "en": {"text": msg["en"]}, "es": {"text": msg["es"]}},
                        en_lang.id, es_lang.id,
                    )
                    tmpl_ids[tname] = tid
                    pool_tmpl_ids[pool_name].append(tid)
                print(f"  HELPNOW {pool_name}: {len(pool_msgs)} messages")

            # SLIP templates
            for td in SLIP_TEMPLATES:
                tmpl_ids[td["name"]] = await create_template(session, project_id, td, en_lang.id, es_lang.id)

            # Checkout templates
            tmpl_ids[CHECKOUT_TEMPLATE["name"]] = await create_template(
                session, project_id, CHECKOUT_TEMPLATE, en_lang.id, es_lang.id
            )
            tmpl_ids[CHECKOUT_SMOKEFREE_TEMPLATE["name"]] = await create_template(
                session, project_id, CHECKOUT_SMOKEFREE_TEMPLATE, en_lang.id, es_lang.id
            )

            # Generate quit-day morning templates (rotating pool)
            morning_en_cycle = cycle(MORNING_THEMES_EN)
            morning_es_cycle = cycle(MORNING_THEMES_ES)
            for day in range(1, TOTAL_QUIT_DAYS + 1):
                tname = f"Q{day}_MORNING"
                en_text = next(morning_en_cycle).format(day=day)
                es_text = next(morning_es_cycle).format(day=day)
                tmpl_ids[tname] = await create_template(
                    session, project_id,
                    {"name": tname, "en": {"text": en_text}, "es": {"text": es_text}},
                    en_lang.id, es_lang.id,
                )

            # Generate quit-day intermittent templates (rotating pool)
            im_en_cycle = cycle(INTERMITTENT_POOL_EN)
            im_es_cycle = cycle(INTERMITTENT_POOL_ES)
            for day in range(1, TOTAL_QUIT_DAYS + 1):
                for slot in ["1PM", "4PM", "7PM"]:
                    tname = f"Q{day}_IM_{slot}"
                    tmpl_ids[tname] = await create_template(
                        session, project_id,
                        {"name": tname, "en": {"text": next(im_en_cycle)}, "es": {"text": next(im_es_cycle)}},
                        en_lang.id, es_lang.id,
                    )

            total_templates = len(tmpl_ids)
            print(f"   Total: {total_templates} templates")

            # 5. Create nodes and edges
            print("\n5. Creating nodes and edges...")
            node_ids: dict[str, int] = {}

            # -- INTAKE NODES --
            intake_node_defs = [
                ("INTAKE_START", "INTAKE_WELCOME", "NO_DELAY", True, False),
                ("INTAKE_STUDY_INFO", "INTAKE_STUDY_INFO", "2_MIN_DELAY", False, False),
                ("INTAKE_EXIT_RESPONSE", "INTAKE_EXIT_RESPONSE", "NO_DELAY", False, False),
                ("INTAKE_CPD", "INTAKE_CPD", "2_MIN_DELAY", False, False),
                ("INTAKE_NICOTINE", "INTAKE_NICOTINE", "2_MIN_DELAY", False, False),
                ("INTAKE_REASONS", "INTAKE_REASONS", "2_MIN_DELAY", False, False),
                ("INTAKE_SUPPORT", "INTAKE_SUPPORT", "2_MIN_DELAY", False, False),
                ("INTAKE_READY", "INTAKE_READY_CHECK", "2_MIN_DELAY", False, False),
                ("INTAKE_YES_TIME", "INTAKE_TIME_SELECT", "NO_DELAY", False, False),
                ("INTAKE_SET_DATE", "INTAKE_SET_QUIT_DATE", "NO_DELAY", False, False),
                ("INTAKE_DATE_CONFIRM", "INTAKE_QUIT_DATE_CONFIRM", "NO_DELAY", False, False),
                ("INTAKE_TIME", "INTAKE_TIME_SELECT", "NO_DELAY", False, False),
                ("INTAKE_END", "INTAKE_END", "NO_DELAY", False, False),
            ]
            for name, tmpl_name, timing_name, is_entry, is_term in intake_node_defs:
                node_ids[name] = await create_node(
                    session, project_id, name,
                    template_id=tmpl_ids.get(tmpl_name),
                    timing_id=timing_ids.get(timing_name),
                    is_entry=is_entry,
                )

            # Intake edges
            intake_edges = [
                ("INTAKE_START", "INTAKE_STUDY_INFO", None),
                ("INTAKE_STUDY_INFO", "INTAKE_CPD", None),
                ("INTAKE_CPD", "INTAKE_NICOTINE", None),
                ("INTAKE_NICOTINE", "INTAKE_REASONS", None),
                ("INTAKE_REASONS", "INTAKE_SUPPORT", None),
                ("INTAKE_SUPPORT", "INTAKE_READY", None),
                ("INTAKE_READY", "INTAKE_YES_TIME", "YES_TOMORROW"),
                ("INTAKE_READY", "INTAKE_SET_DATE", "NEED_TIME"),
                ("INTAKE_YES_TIME", "INTAKE_END", None),
                ("INTAKE_SET_DATE", "INTAKE_DATE_CONFIRM", None),
                ("INTAKE_DATE_CONFIRM", "INTAKE_TIME", None),
                ("INTAKE_TIME", "INTAKE_END", None),
            ]
            for parent, child, label in intake_edges:
                await create_edge(session, node_ids[parent], node_ids[child], label)
            print(f"  Intake: {len(intake_node_defs)} nodes, {len(intake_edges)} edges")

            # -- PRE-QUIT NODES (PQ-6 to PQ-1) --
            pq_days = [
                ("PQ6", ["PQ6_MORNING", "PQ6_AFTERNOON"]),
                ("PQ5", ["PQ5_MORNING", "PQ5_AFTERNOON"]),
                ("PQ4", ["PQ4_MORNING", "PQ4_AFTERNOON"]),
                ("PQ3", ["PQ3_MORNING", "PQ3_AFTERNOON"]),
                ("PQ2", ["PQ2_MORNING", "PQ2_AFTERNOON"]),
                ("PQ1", ["PQ1_MORNING", "PQ1_AFTERNOON"]),
            ]
            prev_last_node: str | None = None
            for pq_name, tmpl_names in pq_days:
                morning_name = f"{pq_name}_NODE_AM"
                afternoon_name = f"{pq_name}_NODE_PM"
                node_ids[morning_name] = await create_node(
                    session, project_id, morning_name,
                    template_id=tmpl_ids.get(tmpl_names[0]),
                    timing_id=timing_ids["MORNING_DEFAULT"],
                    display_name=f"{pq_name} Morning",
                )
                node_ids[afternoon_name] = await create_node(
                    session, project_id, afternoon_name,
                    template_id=tmpl_ids.get(tmpl_names[1]),
                    timing_id=timing_ids["INTERMITTENT_1PM"],
                    display_name=f"{pq_name} Afternoon",
                )
                await create_edge(session, node_ids[morning_name], node_ids[afternoon_name])
                if prev_last_node:
                    await create_edge(session, node_ids[prev_last_node], node_ids[morning_name])
                prev_last_node = afternoon_name

            # Link intake end to PQ-6
            await create_edge(session, node_ids["INTAKE_END"], node_ids["PQ6_NODE_AM"])
            print(f"  Pre-quit: {len(pq_days) * 2} nodes")

            # -- QUIT DAY NODES (Q1 to Q180) --
            # Each day has: morning -> IM_1PM -> IM_4PM -> IM_7PM -> CHECKOUT
            # Checkout branches: YES_SMOKED -> SLIP node, NO_SMOKEFREE -> next day
            quit_day_count = 0
            prev_checkout_yes: str | None = None
            prev_checkout_no: str | None = None

            for day in range(1, TOTAL_QUIT_DAYS + 1):
                prefix = f"Q{day}"
                morning = f"{prefix}_MORNING_NODE"
                im_1pm = f"{prefix}_IM_1PM_NODE"
                im_4pm = f"{prefix}_IM_4PM_NODE"
                im_7pm = f"{prefix}_IM_7PM_NODE"
                checkout = f"{prefix}_CHECKOUT_NODE"
                checkout_yes = f"{prefix}_CHECKOUT_YES"
                checkout_no = f"{prefix}_CHECKOUT_NO"

                # Create day nodes
                node_ids[morning] = await create_node(
                    session, project_id, morning,
                    template_id=tmpl_ids.get(f"Q{day}_MORNING"),
                    timing_id=timing_ids["MORNING_DEFAULT"],
                    display_name=f"Q{day} Morning",
                    extra_data={"quit_day": day, "type": "morning_session"},
                )
                node_ids[im_1pm] = await create_node(
                    session, project_id, im_1pm,
                    template_id=tmpl_ids.get(f"Q{day}_IM_1PM"),
                    timing_id=timing_ids["INTERMITTENT_1PM"],
                    display_name=f"Q{day} 1PM",
                    extra_data={"quit_day": day, "type": "intermittent"},
                )
                node_ids[im_4pm] = await create_node(
                    session, project_id, im_4pm,
                    template_id=tmpl_ids.get(f"Q{day}_IM_4PM"),
                    timing_id=timing_ids["INTERMITTENT_4PM"],
                    display_name=f"Q{day} 4PM",
                    extra_data={"quit_day": day, "type": "intermittent"},
                )
                node_ids[im_7pm] = await create_node(
                    session, project_id, im_7pm,
                    template_id=tmpl_ids.get(f"Q{day}_IM_7PM"),
                    timing_id=timing_ids["INTERMITTENT_7PM"],
                    display_name=f"Q{day} 7PM",
                    extra_data={"quit_day": day, "type": "intermittent"},
                )
                node_ids[checkout] = await create_node(
                    session, project_id, checkout,
                    template_id=tmpl_ids["DAILY_CHECKOUT"],
                    timing_id=timing_ids["CHECKOUT_8PM"],
                    display_name=f"Q{day} Checkout",
                    extra_data={"quit_day": day, "type": "checkout"},
                )
                node_ids[checkout_no] = await create_node(
                    session, project_id, checkout_no,
                    template_id=tmpl_ids["CHECKOUT_SMOKEFREE"],
                    timing_id=timing_ids["NO_DELAY"],
                    display_name=f"Q{day} Smoke-Free",
                    extra_data={"quit_day": day, "type": "checkout_response"},
                )
                # YES_SMOKED routes to SLIP node (varies by slip count)
                node_ids[checkout_yes] = await create_node(
                    session, project_id, checkout_yes,
                    template_id=None,  # Template chosen by slip_count at runtime
                    timing_id=timing_ids["NO_DELAY"],
                    display_name=f"Q{day} Smoked",
                    extra_data={
                        "quit_day": day, "type": "checkout_slip",
                        "exec_commands": ["INCREMENT:slip_count"],
                    },
                )

                # Day flow edges: morning -> 1pm -> 4pm -> 7pm -> checkout
                await create_edge(session, node_ids[morning], node_ids[im_1pm])
                await create_edge(session, node_ids[im_1pm], node_ids[im_4pm])
                await create_edge(session, node_ids[im_4pm], node_ids[im_7pm])
                await create_edge(session, node_ids[im_7pm], node_ids[checkout])
                # Checkout branching
                await create_edge(session, node_ids[checkout], node_ids[checkout_yes], "YES_SMOKED")
                await create_edge(session, node_ids[checkout], node_ids[checkout_no], "NO_SMOKEFREE")

                # Link from previous day's checkout to this day's morning
                if day == 1:
                    # Link from PQ-1 afternoon (or intake end for immediate quitters)
                    if prev_last_node:
                        await create_edge(session, node_ids[prev_last_node], node_ids[morning])
                else:
                    if prev_checkout_yes:
                        await create_edge(session, node_ids[prev_checkout_yes], node_ids[morning])
                    if prev_checkout_no:
                        await create_edge(session, node_ids[prev_checkout_no], node_ids[morning])

                prev_checkout_yes = checkout_yes
                prev_checkout_no = checkout_no
                quit_day_count += 1

                if day % 30 == 0:
                    print(f"  Quit days: {day}/{TOTAL_QUIT_DAYS} created...")

            print(f"  Quit days: {quit_day_count} days x 7 nodes = {quit_day_count * 7} nodes")

            # -- HELPNOW NODES --
            # Dispatch node
            node_ids["HELPNOW_RESPONSE"] = await create_node(
                session, project_id, "HELPNOW_RESPONSE",
                template_id=tmpl_ids["HELPNOW_RESPONSE"],
                timing_id=timing_ids["NO_DELAY"],
                display_name="HELPNOW Dispatch",
            )

            # Category pool nodes (single node per category, pool rotation handled by engine)
            for pool_name, pool_ids in pool_tmpl_ids.items():
                node_name = f"HELPNOW_{pool_name}"
                node_ids[node_name] = await create_node(
                    session, project_id, node_name,
                    template_id=pool_ids[0],  # First message as default
                    timing_id=timing_ids["NO_DELAY"],
                    display_name=f"HELPNOW {pool_name.title()}",
                    extra_data={
                        "type": "helpnow_pool",
                        "pool_name": pool_name.lower(),
                        "message_pool_template_ids": pool_ids,
                    },
                )
                # Edge from dispatch to category
                await create_edge(session, node_ids["HELPNOW_RESPONSE"], node_ids[node_name], pool_name)

            print(f"  HELPNOW: 6 nodes (dispatch + 5 categories)")

            # -- SLIP ESCALATION NODES --
            node_ids["SLIP_FIRST"] = await create_node(
                session, project_id, "SLIP_FIRST",
                template_id=tmpl_ids["SLIP_FIRST"],
                timing_id=timing_ids["NO_DELAY"],
                display_name="First Slip Response",
                extra_data={"type": "slip_response", "slip_threshold": 1},
            )
            node_ids["SLIP_SECOND"] = await create_node(
                session, project_id, "SLIP_SECOND",
                template_id=tmpl_ids["SLIP_SECOND"],
                timing_id=timing_ids["NO_DELAY"],
                display_name="Second Slip Response",
                extra_data={"type": "slip_response", "slip_threshold": 2},
            )
            node_ids["SLIP_THIRD_PLUS"] = await create_node(
                session, project_id, "SLIP_THIRD_PLUS",
                template_id=tmpl_ids["SLIP_THIRD_PLUS"],
                timing_id=timing_ids["NO_DELAY"],
                display_name="Third+ Slip Response",
                extra_data={"type": "slip_response", "slip_threshold": 3},
            )
            print(f"  SLIP: 3 escalation nodes")

            # -- TERMINAL NODES --
            node_ids["EXIT_STUDY"] = await create_node(
                session, project_id, "EXIT_STUDY", is_terminal=True,
                display_name="Exit Study",
            )
            node_ids["COMPLETE_STUDY"] = await create_node(
                session, project_id, "COMPLETE_STUDY", is_terminal=True,
                display_name="Complete Study (Day 180)",
            )

            # Link last day checkout to study completion
            last_day_yes = f"Q{TOTAL_QUIT_DAYS}_CHECKOUT_YES"
            last_day_no = f"Q{TOTAL_QUIT_DAYS}_CHECKOUT_NO"
            await create_edge(session, node_ids[last_day_yes], node_ids["COMPLETE_STUDY"])
            await create_edge(session, node_ids[last_day_no], node_ids["COMPLETE_STUDY"])

            # 6. Create keywords
            print("\n6. Creating keywords...")
            from app.models import SmsKeyword
            for kw_def in KEYWORDS:
                lang_id = None
                if kw_def.get("language") == "en":
                    lang_id = en_lang.id
                elif kw_def.get("language") == "es":
                    lang_id = es_lang.id

                kw, created = await get_or_create(
                    session, SmsKeyword,
                    project_id=project_id, keyword_text=kw_def["keyword_text"],
                    defaults={
                        "language_id": lang_id,
                        "keyword_action_type": kw_def["action_type"],
                        "keyword_name": kw_def["keyword_text"],
                        "messaging_node_id": node_ids.get(kw_def.get("node_name")),
                        "variable_id": var_ids.get(kw_def.get("variable")),
                        "variable_value": kw_def.get("value"),
                        "is_active": True,
                    },
                )
                if created:
                    print(f"  + Keyword: {kw_def['keyword_text']}")

                # Set message_pool on HELPNOW category keywords
                if kw_def["action_type"] == "TRIGGER_NODE" and kw_def.get("node_name", "").startswith("HELPNOW_"):
                    pool_key = kw_def["node_name"].replace("HELPNOW_", "")
                    if pool_key in pool_tmpl_ids:
                        kw.message_pool = pool_tmpl_ids[pool_key]

            # 7. Set initial node
            from app.models import Project
            result = await session.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one()
            project.initial_triggering_node_id = node_ids.get("INTAKE_START")

            # Summary
            total_nodes = len(node_ids)
            print("\n" + "=" * 70)
            print("V11 Protocol Import Complete!")
            print(f"  Project ID:     {project_id}")
            print(f"  Templates:      {total_templates}")
            print(f"  Variables:      {len(var_ids)}")
            print(f"  Timing:         {len(timing_ids)}")
            print(f"  Nodes:          {total_nodes}")
            print(f"  Keywords:       {len(KEYWORDS)}")
            print(f"  HELPNOW pools:  Crave({len(HELPNOW_CRAVE_POOL)}) BadMood({len(HELPNOW_BADMOOD_POOL)}) "
                  f"Stress({len(HELPNOW_STRESS_POOL)}) Smokers({len(HELPNOW_SMOKERS_POOL)}) "
                  f"Alcohol({len(HELPNOW_ALCOHOL_POOL)})")
            print(f"  SLIP nodes:     3 (1st, 2nd, 3rd+)")
            print(f"  Quit days:      {TOTAL_QUIT_DAYS}")
            print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

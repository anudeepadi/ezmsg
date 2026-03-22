#!/usr/bin/env python3
"""
Add Q8-Q21+ quit days to existing QuitTxt V9 Protocol.

This script supplements the initial import by adding:
- Q8-Q13 intermittent messages
- Q14 weekly checkout
- Q15-Q20 intermittent messages
- Q21 final checkout
- Q21+ maintenance phase
"""

import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "postgresql+asyncpg://ezmsg:ezmsg_dev@localhost:5433/ezmsg"

PROJECT_NAME = "QuitTxt V9 UTSA Study"

# ============================================================================
# Q8-Q13 TEMPLATES (Week 2, pre-checkout)
# ============================================================================
Q8_Q13_TEMPLATES = [
    # Q8 - Quit Day 8
    {
        "name": "Q8_IM_11AM",
        "description": "Q8 11am - Breathing reminder",
        "en": {"text": "Those cigarette cravings can be rough. Take 3 deep breaths anytime you feel one sneaking up on you."},
        "es": {"text": "Los antojos de cigarrillo pueden ser difíciles. Respira profundo 3 veces cuando sientas que se acerca uno."},
    },
    {
        "name": "Q8_IM_1PM",
        "description": "Q8 1pm - Water reminder",
        "en": {"text": "Drink more water! It helps flush out those toxins from smoking and keeps cravings at bay."},
        "es": {"text": "¡Toma más agua! Ayuda a eliminar las toxinas del cigarro y mantiene los antojos a raya."},
    },
    {
        "name": "Q8_IM_3PM",
        "description": "Q8 3pm - Progress reminder",
        "en": {"text": "You've made it through a full week smoke-free! Your lungs are already healing. Keep it up!"},
        "es": {"text": "¡Has pasado una semana entera sin fumar! Tus pulmones ya están sanando. ¡Sigue así!"},
    },
    {
        "name": "Q8_IM_5PM",
        "description": "Q8 5pm - Evening motivation",
        "en": {"text": "Evening cravings can be tough. Try chewing gum or having a healthy snack instead of reaching for a cigarette."},
        "es": {"text": "Los antojos de la noche pueden ser difíciles. Prueba masticar chicle o comer algo saludable en lugar de un cigarro."},
    },
    {
        "name": "Q8_IM_7PM",
        "description": "Q8 7pm - BD message",
        "en": {"text": "Your body is doing amazing things right now - healing, getting stronger. Be proud of yourself!"},
        "es": {"text": "Tu cuerpo está haciendo cosas increíbles ahora mismo - sanando, fortaleciéndose. ¡Siéntete orgulloso!"},
    },

    # Q9 - Quit Day 9
    {
        "name": "Q9_IM_11AM",
        "description": "Q9 11am - Super hero",
        "en": {
            "text": "You are a superhero for quitting smoking! Every day without a cigarette is a victory.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_11am_SuperHero.gif",
        },
        "es": {
            "text": "¡Eres un superhéroe por dejar de fumar! Cada día sin un cigarrillo es una victoria.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_11am_SuperHero.gif",
        },
    },
    {
        "name": "Q9_IM_1PM",
        "description": "Q9 1pm - Family hug",
        "en": {
            "text": "Your loved ones are proud of you for quitting. Think about how much healthier you'll be for them.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_1pm_FamilyHug.gif",
        },
        "es": {
            "text": "Tus seres queridos están orgullosos de que estés dejando de fumar. Piensa en lo saludable que serás para ellos.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_1pm_FamilyHug.gif",
        },
    },
    {
        "name": "Q9_IM_3PM",
        "description": "Q9 3pm - Stay strong",
        "en": {"text": "If you're feeling stressed, try taking a short walk. Physical activity is a great way to beat cravings."},
        "es": {"text": "Si te sientes estresado, intenta dar un paseo corto. La actividad física es una gran manera de vencer los antojos."},
    },
    {
        "name": "Q9_IM_5PM",
        "description": "Q9 5pm - 4 Ds reminder",
        "en": {
            "text": "Remember the 4 Ds if you get cravings–Delay, Drink water, Deep breathe, Do something else.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_5pm_deepbreath.gif",
        },
        "es": {
            "text": "Recuerda las 4 Ds si tienes antojos–Demora, bebe agua, respira profundo, haz otra cosa.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q9_5pm_drinkwater_esp.gif",
        },
    },
    {
        "name": "Q9_IM_7PM",
        "description": "Q9 7pm - Evening check",
        "en": {"text": "Almost done with day 9! Tomorrow you'll be in double digits. You're doing amazing!"},
        "es": {"text": "¡Casi terminas el día 9! Mañana estarás en doble dígitos. ¡Lo estás haciendo increíble!"},
    },

    # Q10 - Quit Day 10 (has morning session)
    {
        "name": "Q10_MORNING",
        "description": "Q10 Morning - Double digits celebration",
        "en": {"text": "Day 10! You're in double digits now! Your body is thanking you - blood pressure is normalizing, circulation improving."},
        "es": {"text": "¡Día 10! ¡Ya estás en doble dígitos! Tu cuerpo te lo agradece - la presión arterial se normaliza, la circulación mejora."},
    },
    {
        "name": "Q10_REASONS",
        "description": "Q10 - Reflect on reasons",
        "en": {"text": "Take a moment to remember why you decided to quit. Write it down if it helps. Your reasons are your fuel!"},
        "es": {"text": "Toma un momento para recordar por qué decidiste dejar de fumar. Escríbelo si te ayuda. ¡Tus razones son tu combustible!"},
    },
    {
        "name": "Q10_IM_1PM",
        "description": "Q10 1pm - Keep going",
        "en": {"text": "The first two weeks are the hardest. You're almost through them! Stay strong."},
        "es": {"text": "Las primeras dos semanas son las más difíciles. ¡Ya casi las pasas! Mantente fuerte."},
    },
    {
        "name": "Q10_IM_4PM",
        "description": "Q10 4pm - Afternoon boost",
        "en": {"text": "Feeling an urge? Try the 5-minute rule: wait 5 minutes before acting on any craving. Usually it passes!"},
        "es": {"text": "¿Sientes un antojo? Prueba la regla de 5 minutos: espera 5 minutos antes de actuar. ¡Usualmente pasa!"},
    },
    {
        "name": "Q10_IM_7PM",
        "description": "Q10 7pm - Never give up",
        "en": {
            "text": "Never give up on yourself. You've come so far already. Tomorrow is day 11!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q10_7pm_Nevergiveup.gif",
        },
        "es": {
            "text": "Nunca te rindas. Ya has llegado tan lejos. ¡Mañana es el día 11!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q10_7pm_Nevergiveup_Spanish.gif",
        },
    },

    # Q11 - Quit Day 11
    {
        "name": "Q11_IM_11AM",
        "description": "Q11 11am - Say no",
        "en": {
            "text": "Cigarettes do not make the party better. Stay strong & say no when offered a cigarette. You will thank yourself later.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_11am_ehh_no.gif",
        },
        "es": {
            "text": "Los cigarrillos no mejoran la fiesta. Sé fuerte y di NO cuando te ofrezcan un cigarrillo. Te lo agradecerás más tarde.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_11am_ehh_no.gif",
        },
    },
    {
        "name": "Q11_IM_1PM",
        "description": "Q11 1pm - Group hug",
        "en": {
            "text": "Quitting smoking is one of the best gifts you can give yourself and your loved ones!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_1pm_Group_hug.gif",
        },
        "es": {
            "text": "¡Dejar de fumar es uno de los mejores regalos que puedes darte a ti mismo y a tus seres queridos!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_1pm_Group_hug.gif",
        },
    },
    {
        "name": "Q11_IM_3PM",
        "description": "Q11 3pm - Immune system",
        "en": {
            "text": "By quitting smoking, you're helping your immune system get stronger to fight off respiratory infections!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_3pm_Rooster.gif",
        },
        "es": {
            "text": "¡Al dejar de fumar ayudas a que tu sistema inmune esté más fuerte para luchar contra infecciones respiratorias!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_3pm_Rooster.gif",
        },
    },
    {
        "name": "Q11_IM_5PM",
        "description": "Q11 5pm - Champion",
        "en": {
            "text": "You're a champion! Every smoke-free day is proof of your strength.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_5pm_Lebron2.gif",
        },
        "es": {
            "text": "¡Eres un campeón! Cada día sin fumar es prueba de tu fuerza.",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_5pm_Lebron2.gif",
        },
    },
    {
        "name": "Q11_IM_7PM",
        "description": "Q11 7pm - Justice League",
        "en": {
            "text": "You don't need superpowers to be a hero. Quitting smoking makes you one!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_7pm_JusticeLeague.gif",
        },
        "es": {
            "text": "No necesitas superpoderes para ser un héroe. ¡Dejar de fumar te hace uno!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q11_7pm_JusticeLeague.gif",
        },
    },

    # Q12 - Quit Day 12
    {
        "name": "Q12_IM_11AM",
        "description": "Q12 11am - Almost 2 weeks",
        "en": {"text": "Almost 2 weeks smoke-free! Your sense of taste and smell are getting sharper every day."},
        "es": {"text": "¡Casi 2 semanas sin fumar! Tu sentido del gusto y olfato se agudizan cada día."},
    },
    {
        "name": "Q12_IM_1PM",
        "description": "Q12 1pm - Money saved",
        "en": {"text": "Think about the money you've saved by not buying cigarettes. Treat yourself to something nice!"},
        "es": {"text": "Piensa en el dinero que has ahorrado al no comprar cigarrillos. ¡Date un gusto!"},
    },
    {
        "name": "Q12_IM_3PM",
        "description": "Q12 3pm - Minions",
        "en": {
            "text": "Fun fact: Your circulation has improved significantly since you quit. Your body is healing!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q12_3pm_Minions_Whhaaatt.gif",
        },
        "es": {
            "text": "Dato curioso: Tu circulación ha mejorado significativamente desde que dejaste de fumar. ¡Tu cuerpo está sanando!",
            "media_url": "https://quitxtstudy.org/sites/quitxtstudy/files/gifs/Q12_3pm_minions_que_esp.gif",
        },
    },
    {
        "name": "Q12_IM_5PM",
        "description": "Q12 5pm - Stay busy",
        "en": {"text": "Keep yourself busy during high-risk times. Boredom can trigger cravings."},
        "es": {"text": "Mantente ocupado durante los momentos de alto riesgo. El aburrimiento puede provocar antojos."},
    },
    {
        "name": "Q12_IM_7PM",
        "description": "Q12 7pm - Evening motivation",
        "en": {"text": "Two more days until the 2-week mark! You're proving to yourself that you can do this."},
        "es": {"text": "¡Dos días más hasta las 2 semanas! Te estás demostrando que puedes hacerlo."},
    },

    # Q13 - Quit Day 13
    {
        "name": "Q13_IM_11AM",
        "description": "Q13 11am - One more day",
        "en": {"text": "One more day until 2 weeks! Your lung function is improving every day."},
        "es": {"text": "¡Un día más hasta las 2 semanas! Tu función pulmonar mejora cada día."},
    },
    {
        "name": "Q13_IM_1PM",
        "description": "Q13 1pm - Healthy habits",
        "en": {"text": "Replace old smoking habits with new healthy ones. What new activity have you tried this week?"},
        "es": {"text": "Reemplaza los viejos hábitos de fumar con nuevos hábitos saludables. ¿Qué nueva actividad has probado esta semana?"},
    },
    {
        "name": "Q13_IM_3PM",
        "description": "Q13 3pm - Keep going",
        "en": {"text": "The hardest part is behind you. Your body is becoming less dependent on nicotine every day."},
        "es": {"text": "La parte más difícil ya pasó. Tu cuerpo se vuelve menos dependiente de la nicotina cada día."},
    },
    {
        "name": "Q13_IM_5PM",
        "description": "Q13 5pm - Proud of you",
        "en": {"text": "We're so proud of you! Tomorrow marks 2 full weeks smoke-free."},
        "es": {"text": "¡Estamos muy orgullosos de ti! Mañana marcas 2 semanas completas sin fumar."},
    },
    {
        "name": "Q13_IM_7PM",
        "description": "Q13 7pm - Almost there",
        "en": {"text": "Almost at the 2-week milestone! Get some rest and prepare to celebrate tomorrow."},
        "es": {"text": "¡Casi llegas a las 2 semanas! Descansa y prepárate para celebrar mañana."},
    },
]

# ============================================================================
# Q14 CHECKOUT (Week 2 Complete)
# ============================================================================
Q14_TEMPLATES = [
    {
        "name": "Q14_MORNING",
        "description": "Q14 Morning - 2 weeks celebration",
        "en": {"text": "CONGRATULATIONS! You've been smoke-free for 2 WEEKS! This is a huge accomplishment. Your body has made incredible progress."},
        "es": {"text": "¡FELICITACIONES! ¡Has estado 2 SEMANAS sin fumar! Este es un gran logro. Tu cuerpo ha hecho un progreso increíble."},
    },
    {
        "name": "Q14_IM_1PM",
        "description": "Q14 1pm - Health benefits",
        "en": {"text": "At 2 weeks, your circulation has improved and your lungs are working better. Walking is easier!"},
        "es": {"text": "A las 2 semanas, tu circulación ha mejorado y tus pulmones funcionan mejor. ¡Caminar es más fácil!"},
    },
    {
        "name": "Q14_IM_4PM",
        "description": "Q14 4pm - Keep momentum",
        "en": {"text": "Don't let your guard down! The addiction can sneak up on you. Stay vigilant and stay smoke-free."},
        "es": {"text": "¡No bajes la guardia! La adicción puede sorprenderte. Mantente alerta y sigue sin fumar."},
    },
    {
        "name": "Q14_IM_7PM",
        "description": "Q14 7pm - Evening message",
        "en": {"text": "Two weeks down! You've proven you have what it takes. Keep pushing forward!"},
        "es": {"text": "¡Dos semanas logradas! Has demostrado que tienes lo que se necesita. ¡Sigue adelante!"},
    },
    {
        "name": "Q14_CHECKOUT",
        "description": "Q14 Weekly checkout",
        "en": {
            "text": "Weekly check: Have you smoked any cigarettes (even a puff) in the past week? Reply YES or NO",
            "quick_replies": [{"label": "Yes", "value": "YES"}, {"label": "No", "value": "NO"}],
        },
        "es": {
            "text": "Revisión semanal: ¿Has fumado algún cigarrillo (aunque sea una calada) en la última semana? Responde SI o NO",
            "quick_replies": [{"label": "Sí", "value": "SI"}, {"label": "No", "value": "NO"}],
        },
    },
    {
        "name": "Q14_CHECKOUT_YES",
        "description": "Q14 Checkout - Yes response",
        "en": {
            "text": "Slip-ups happen. What triggered it? Reply: BADMOOD, STRESS, SMOKERS, ALCOHOL, or OTHER. Remember, one slip doesn't erase your progress!",
            "quick_replies": [
                {"label": "Bad Mood", "value": "BADMOOD"},
                {"label": "Stress", "value": "STRESS"},
                {"label": "Other Smokers", "value": "SMOKERS"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Other", "value": "OTHER"},
            ],
        },
        "es": {
            "text": "Los deslices pasan. ¿Qué lo provocó? Responde: MALHUMOR, ESTRES, FUMADORES, ALCOHOL, u OTRA. ¡Recuerda, un desliz no borra tu progreso!",
            "quick_replies": [
                {"label": "Mal Humor", "value": "MALHUMOR"},
                {"label": "Estrés", "value": "ESTRES"},
                {"label": "Fumadores", "value": "FUMADORES"},
                {"label": "Alcohol", "value": "ALCOHOL"},
                {"label": "Otra", "value": "OTRA"},
            ],
        },
    },
    {
        "name": "Q14_CHECKOUT_NO",
        "description": "Q14 Checkout - No response",
        "en": {"text": "AMAZING! Two full weeks smoke-free! You're doing incredible. Keep up the great work!"},
        "es": {"text": "¡INCREÍBLE! ¡Dos semanas completas sin fumar! Lo estás haciendo increíble. ¡Sigue así!"},
    },
]

# ============================================================================
# Q15-Q20 TEMPLATES (Week 3, pre-checkout)
# ============================================================================
Q15_Q20_TEMPLATES = [
    # Q15
    {
        "name": "Q15_IM_11AM",
        "description": "Q15 11am - Week 3 start",
        "en": {"text": "Week 3 begins! Your energy levels should be increasing as your body heals."},
        "es": {"text": "¡Comienza la semana 3! Tus niveles de energía deberían estar aumentando mientras tu cuerpo sana."},
    },
    {
        "name": "Q15_IM_1PM",
        "description": "Q15 1pm - Exercise",
        "en": {"text": "Have you tried exercising since you quit? It's a great way to manage stress and boost your mood!"},
        "es": {"text": "¿Has intentado hacer ejercicio desde que dejaste de fumar? ¡Es una gran manera de manejar el estrés!"},
    },
    {
        "name": "Q15_IM_5PM",
        "description": "Q15 5pm - Breathing",
        "en": {"text": "Notice how much easier it is to breathe? That's your lungs healing!"},
        "es": {"text": "¿Notas lo fácil que es respirar ahora? ¡Son tus pulmones sanando!"},
    },
    {
        "name": "Q15_IM_7PM",
        "description": "Q15 7pm - Keep it up",
        "en": {"text": "You're in the home stretch of your first 3 weeks. Keep pushing!"},
        "es": {"text": "Estás en la recta final de tus primeras 3 semanas. ¡Sigue adelante!"},
    },

    # Q16
    {
        "name": "Q16_IM_11AM",
        "description": "Q16 11am - Morning check",
        "en": {"text": "Good morning! Another day to be proud of yourself. You're doing great!"},
        "es": {"text": "¡Buenos días! Otro día para sentirte orgulloso. ¡Lo estás haciendo genial!"},
    },
    {
        "name": "Q16_IM_1PM",
        "description": "Q16 1pm - Healthy snacks",
        "en": {"text": "Craving something? Try healthy snacks like carrots, celery, or fruit instead of reaching for a cigarette."},
        "es": {"text": "¿Se te antoja algo? Prueba snacks saludables como zanahorias, apio, o frutas en lugar de un cigarrillo."},
    },
    {
        "name": "Q16_IM_5PM",
        "description": "Q16 5pm - Support",
        "en": {"text": "Lean on your support system! Tell friends and family about your progress. They want to help!"},
        "es": {"text": "¡Apóyate en tu red de apoyo! Cuéntale a amigos y familia sobre tu progreso. ¡Quieren ayudarte!"},
    },
    {
        "name": "Q16_IM_7PM",
        "description": "Q16 7pm - Evening",
        "en": {"text": "5 more days until 3 weeks smoke-free. You've got this!"},
        "es": {"text": "5 días más hasta las 3 semanas sin fumar. ¡Tú puedes!"},
    },

    # Q17
    {
        "name": "Q17_IM_11AM",
        "description": "Q17 11am - Benefits",
        "en": {"text": "Your risk of heart attack is already starting to drop! Quitting smoking is the best thing you can do for your heart."},
        "es": {"text": "¡Tu riesgo de ataque cardíaco ya está empezando a bajar! Dejar de fumar es lo mejor que puedes hacer por tu corazón."},
    },
    {
        "name": "Q17_IM_1PM",
        "description": "Q17 1pm - Motivation",
        "en": {"text": "Remember: Every craving you resist makes you stronger. You're rewiring your brain!"},
        "es": {"text": "Recuerda: Cada antojo que resistes te hace más fuerte. ¡Estás reprogramando tu cerebro!"},
    },
    {
        "name": "Q17_IM_5PM",
        "description": "Q17 5pm - Stress relief",
        "en": {"text": "Feeling stressed? Try a quick walk, some music, or call a friend. Cigarettes aren't the answer!"},
        "es": {"text": "¿Te sientes estresado? Prueba una caminata rápida, algo de música, o llama a un amigo. ¡Los cigarrillos no son la respuesta!"},
    },
    {
        "name": "Q17_IM_7PM",
        "description": "Q17 7pm - Evening check",
        "en": {"text": "Another successful day! 4 more days until your 3-week milestone."},
        "es": {"text": "¡Otro día exitoso! 4 días más hasta tu meta de 3 semanas."},
    },

    # Q18
    {
        "name": "Q18_IM_11AM",
        "description": "Q18 11am - Morning",
        "en": {"text": "Did you know? After 2-3 weeks, your circulation improves and lung function increases up to 30%!"},
        "es": {"text": "¿Sabías? Después de 2-3 semanas, tu circulación mejora y la función pulmonar aumenta hasta un 30%!"},
    },
    {
        "name": "Q18_IM_1PM",
        "description": "Q18 1pm - Celebrate",
        "en": {"text": "Celebrate your wins, no matter how small! Each smoke-free hour is a victory."},
        "es": {"text": "¡Celebra tus victorias, sin importar lo pequeñas! Cada hora sin fumar es un triunfo."},
    },
    {
        "name": "Q18_IM_5PM",
        "description": "Q18 5pm - Keep going",
        "en": {"text": "3 more days until 3 weeks! Your commitment is inspiring."},
        "es": {"text": "¡3 días más hasta las 3 semanas! Tu compromiso es inspirador."},
    },
    {
        "name": "Q18_IM_7PM",
        "description": "Q18 7pm - Evening",
        "en": {"text": "Rest well tonight knowing you're making incredible progress!"},
        "es": {"text": "Descansa bien esta noche sabiendo que estás haciendo un progreso increíble!"},
    },

    # Q19
    {
        "name": "Q19_IM_11AM",
        "description": "Q19 11am - Almost there",
        "en": {"text": "Just 2 more days until 3 weeks smoke-free! You're almost there!"},
        "es": {"text": "¡Solo 2 días más hasta las 3 semanas sin fumar! ¡Ya casi llegas!"},
    },
    {
        "name": "Q19_IM_1PM",
        "description": "Q19 1pm - Money",
        "en": {"text": "Think about all the money you've saved in 19 days! That could be a nice dinner or a new outfit."},
        "es": {"text": "¡Piensa en todo el dinero que has ahorrado en 19 días! Podría ser una buena cena o ropa nueva."},
    },
    {
        "name": "Q19_IM_5PM",
        "description": "Q19 5pm - Health",
        "en": {"text": "Your blood oxygen levels have returned to normal. Your body is thanking you!"},
        "es": {"text": "Tus niveles de oxígeno en sangre han vuelto a la normalidad. ¡Tu cuerpo te lo agradece!"},
    },
    {
        "name": "Q19_IM_7PM",
        "description": "Q19 7pm - Evening",
        "en": {"text": "Tomorrow is day 20! One more day after that until your 3-week celebration!"},
        "es": {"text": "¡Mañana es el día 20! ¡Un día más después de eso hasta tu celebración de 3 semanas!"},
    },

    # Q20
    {
        "name": "Q20_IM_11AM",
        "description": "Q20 11am - Day 20",
        "en": {"text": "Day 20! Tomorrow marks 3 full weeks smoke-free. You should be SO proud!"},
        "es": {"text": "¡Día 20! Mañana marcas 3 semanas completas sin fumar. ¡Deberías estar MUY orgulloso!"},
    },
    {
        "name": "Q20_IM_1PM",
        "description": "Q20 1pm - Final push",
        "en": {"text": "One more day until your 3-week milestone! Keep pushing through!"},
        "es": {"text": "¡Un día más hasta tu meta de 3 semanas! ¡Sigue adelante!"},
    },
    {
        "name": "Q20_IM_5PM",
        "description": "Q20 5pm - Almost done",
        "en": {"text": "Your taste buds and sense of smell have likely improved dramatically. Enjoy the little things!"},
        "es": {"text": "Tus papilas gustativas y sentido del olfato probablemente han mejorado mucho. ¡Disfruta las pequeñas cosas!"},
    },
    {
        "name": "Q20_IM_7PM",
        "description": "Q20 7pm - Evening before milestone",
        "en": {"text": "Get some rest! Tomorrow is a big day - 3 weeks smoke-free!"},
        "es": {"text": "¡Descansa! Mañana es un gran día - ¡3 semanas sin fumar!"},
    },
]

# ============================================================================
# Q21 CHECKOUT (Week 3 Complete - Study End)
# ============================================================================
Q21_TEMPLATES = [
    {
        "name": "Q21_MORNING",
        "description": "Q21 Morning - 3 weeks celebration",
        "en": {"text": "🎉 CONGRATULATIONS! You've been smoke-free for 3 WEEKS! This is an INCREDIBLE achievement. You've proven that you have the strength to quit!"},
        "es": {"text": "🎉 ¡FELICITACIONES! ¡Has estado 3 SEMANAS sin fumar! Este es un logro INCREÍBLE. ¡Has demostrado que tienes la fuerza para dejar de fumar!"},
    },
    {
        "name": "Q21_HEALTH_BENEFITS",
        "description": "Q21 Health benefits",
        "en": {"text": "After 3 weeks: your circulation is better, your lung function is improving, and your risk of heart attack is dropping. Your body thanks you!"},
        "es": {"text": "Después de 3 semanas: tu circulación es mejor, tu función pulmonar está mejorando, y tu riesgo de ataque cardíaco está bajando. ¡Tu cuerpo te lo agradece!"},
    },
    {
        "name": "Q21_IM_1PM",
        "description": "Q21 1pm - Final day message",
        "en": {"text": "You've completed the intensive phase of Quitxt! Remember, staying quit is a journey. Use the tools you've learned!"},
        "es": {"text": "¡Has completado la fase intensiva de Quitxt! Recuerda, mantenerte sin fumar es un viaje. ¡Usa las herramientas que has aprendido!"},
    },
    {
        "name": "Q21_IM_4PM",
        "description": "Q21 4pm - Resources",
        "en": {"text": "Need support after today? Call 1-800-QUIT-NOW or visit smokefree.gov. You've got this!"},
        "es": {"text": "¿Necesitas apoyo después de hoy? Llama al 1-800-784-8669 o visita espanol.smokefree.gov. ¡Tú puedes!"},
    },
    {
        "name": "Q21_CHECKOUT",
        "description": "Q21 Final checkout",
        "en": {
            "text": "Final check: Have you smoked any cigarettes (even a puff) in the past week? Reply YES or NO",
            "quick_replies": [{"label": "Yes", "value": "YES"}, {"label": "No", "value": "NO"}],
        },
        "es": {
            "text": "Revisión final: ¿Has fumado algún cigarrillo (aunque sea una calada) en la última semana? Responde SI o NO",
            "quick_replies": [{"label": "Sí", "value": "SI"}, {"label": "No", "value": "NO"}],
        },
    },
    {
        "name": "Q21_CHECKOUT_YES",
        "description": "Q21 Checkout - Yes response",
        "en": {"text": "Slip-ups are part of the journey. The important thing is to keep trying! You've made incredible progress. Don't give up!"},
        "es": {"text": "Los deslices son parte del viaje. ¡Lo importante es seguir intentando! Has hecho un progreso increíble. ¡No te rindas!"},
    },
    {
        "name": "Q21_CHECKOUT_NO",
        "description": "Q21 Checkout - No response",
        "en": {"text": "CONGRATULATIONS! You've completed 3 weeks completely smoke-free! You're a champion! Keep up the amazing work!"},
        "es": {"text": "¡FELICITACIONES! ¡Has completado 3 semanas completamente sin fumar! ¡Eres un campeón! ¡Sigue con el increíble trabajo!"},
    },
    {
        "name": "Q21_GOODBYE",
        "description": "Q21 Final goodbye message",
        "en": {"text": "Thank you for being part of Quitxt! Remember: HELPNOW is always available if you need support. Stay smoke-free! 💪"},
        "es": {"text": "¡Gracias por ser parte de Quitxt! Recuerda: AYUDAYA siempre está disponible si necesitas apoyo. ¡Mantente sin fumar! 💪"},
    },
]

# ============================================================================
# NODE DEFINITIONS FOR Q8-Q21
# ============================================================================
Q8_Q21_NODES = [
    # Q8
    {"name": "Q8_IM_11AM", "display_name": "Q8 11am", "template": "Q8_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q8_IM_1PM", "display_name": "Q8 1pm", "template": "Q8_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q8_IM_3PM", "display_name": "Q8 3pm", "template": "Q8_IM_3PM", "timing": "INTERMITTENT_3PM"},
    {"name": "Q8_IM_5PM", "display_name": "Q8 5pm", "template": "Q8_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q8_IM_7PM", "display_name": "Q8 7pm", "template": "Q8_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q9
    {"name": "Q9_IM_11AM", "display_name": "Q9 11am", "template": "Q9_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q9_IM_1PM", "display_name": "Q9 1pm", "template": "Q9_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q9_IM_3PM", "display_name": "Q9 3pm", "template": "Q9_IM_3PM", "timing": "INTERMITTENT_3PM"},
    {"name": "Q9_IM_5PM", "display_name": "Q9 5pm", "template": "Q9_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q9_IM_7PM", "display_name": "Q9 7pm", "template": "Q9_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q10 (has morning session)
    {"name": "Q10_MORNING", "display_name": "Q10 Morning", "template": "Q10_MORNING", "timing": "MORNING_DEFAULT"},
    {"name": "Q10_REASONS", "display_name": "Q10 Reasons", "template": "Q10_REASONS", "timing": "2_MIN_DELAY"},
    {"name": "Q10_IM_1PM", "display_name": "Q10 1pm", "template": "Q10_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q10_IM_4PM", "display_name": "Q10 4pm", "template": "Q10_IM_4PM", "timing": "INTERMITTENT_4PM"},
    {"name": "Q10_IM_7PM", "display_name": "Q10 7pm", "template": "Q10_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q11
    {"name": "Q11_IM_11AM", "display_name": "Q11 11am", "template": "Q11_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q11_IM_1PM", "display_name": "Q11 1pm", "template": "Q11_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q11_IM_3PM", "display_name": "Q11 3pm", "template": "Q11_IM_3PM", "timing": "INTERMITTENT_3PM"},
    {"name": "Q11_IM_5PM", "display_name": "Q11 5pm", "template": "Q11_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q11_IM_7PM", "display_name": "Q11 7pm", "template": "Q11_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q12
    {"name": "Q12_IM_11AM", "display_name": "Q12 11am", "template": "Q12_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q12_IM_1PM", "display_name": "Q12 1pm", "template": "Q12_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q12_IM_3PM", "display_name": "Q12 3pm", "template": "Q12_IM_3PM", "timing": "INTERMITTENT_3PM"},
    {"name": "Q12_IM_5PM", "display_name": "Q12 5pm", "template": "Q12_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q12_IM_7PM", "display_name": "Q12 7pm", "template": "Q12_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q13
    {"name": "Q13_IM_11AM", "display_name": "Q13 11am", "template": "Q13_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q13_IM_1PM", "display_name": "Q13 1pm", "template": "Q13_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q13_IM_3PM", "display_name": "Q13 3pm", "template": "Q13_IM_3PM", "timing": "INTERMITTENT_3PM"},
    {"name": "Q13_IM_5PM", "display_name": "Q13 5pm", "template": "Q13_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q13_IM_7PM", "display_name": "Q13 7pm", "template": "Q13_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q14 (Week 2 checkout)
    {"name": "Q14_MORNING", "display_name": "Q14 Morning", "template": "Q14_MORNING", "timing": "MORNING_DEFAULT"},
    {"name": "Q14_IM_1PM", "display_name": "Q14 1pm", "template": "Q14_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q14_IM_4PM", "display_name": "Q14 4pm", "template": "Q14_IM_4PM", "timing": "INTERMITTENT_4PM"},
    {"name": "Q14_IM_7PM", "display_name": "Q14 7pm", "template": "Q14_IM_7PM", "timing": "INTERMITTENT_7PM"},
    {"name": "Q14_CHECKOUT", "display_name": "Q14 Checkout", "template": "Q14_CHECKOUT", "timing": "CHECKOUT_8PM"},
    {"name": "Q14_CHECKOUT_YES", "display_name": "Q14 Checkout Yes", "template": "Q14_CHECKOUT_YES", "timing": "NO_DELAY"},
    {"name": "Q14_CHECKOUT_NO", "display_name": "Q14 Checkout No", "template": "Q14_CHECKOUT_NO", "timing": "NO_DELAY"},
    # Q15
    {"name": "Q15_IM_11AM", "display_name": "Q15 11am", "template": "Q15_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q15_IM_1PM", "display_name": "Q15 1pm", "template": "Q15_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q15_IM_5PM", "display_name": "Q15 5pm", "template": "Q15_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q15_IM_7PM", "display_name": "Q15 7pm", "template": "Q15_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q16
    {"name": "Q16_IM_11AM", "display_name": "Q16 11am", "template": "Q16_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q16_IM_1PM", "display_name": "Q16 1pm", "template": "Q16_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q16_IM_5PM", "display_name": "Q16 5pm", "template": "Q16_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q16_IM_7PM", "display_name": "Q16 7pm", "template": "Q16_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q17
    {"name": "Q17_IM_11AM", "display_name": "Q17 11am", "template": "Q17_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q17_IM_1PM", "display_name": "Q17 1pm", "template": "Q17_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q17_IM_5PM", "display_name": "Q17 5pm", "template": "Q17_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q17_IM_7PM", "display_name": "Q17 7pm", "template": "Q17_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q18
    {"name": "Q18_IM_11AM", "display_name": "Q18 11am", "template": "Q18_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q18_IM_1PM", "display_name": "Q18 1pm", "template": "Q18_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q18_IM_5PM", "display_name": "Q18 5pm", "template": "Q18_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q18_IM_7PM", "display_name": "Q18 7pm", "template": "Q18_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q19
    {"name": "Q19_IM_11AM", "display_name": "Q19 11am", "template": "Q19_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q19_IM_1PM", "display_name": "Q19 1pm", "template": "Q19_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q19_IM_5PM", "display_name": "Q19 5pm", "template": "Q19_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q19_IM_7PM", "display_name": "Q19 7pm", "template": "Q19_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q20
    {"name": "Q20_IM_11AM", "display_name": "Q20 11am", "template": "Q20_IM_11AM", "timing": "INTERMITTENT_11AM"},
    {"name": "Q20_IM_1PM", "display_name": "Q20 1pm", "template": "Q20_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q20_IM_5PM", "display_name": "Q20 5pm", "template": "Q20_IM_5PM", "timing": "INTERMITTENT_5PM"},
    {"name": "Q20_IM_7PM", "display_name": "Q20 7pm", "template": "Q20_IM_7PM", "timing": "INTERMITTENT_7PM"},
    # Q21 (Final checkout - Study End)
    {"name": "Q21_MORNING", "display_name": "Q21 Morning", "template": "Q21_MORNING", "timing": "MORNING_DEFAULT"},
    {"name": "Q21_HEALTH", "display_name": "Q21 Health Benefits", "template": "Q21_HEALTH_BENEFITS", "timing": "2_MIN_DELAY"},
    {"name": "Q21_IM_1PM", "display_name": "Q21 1pm", "template": "Q21_IM_1PM", "timing": "INTERMITTENT_1PM"},
    {"name": "Q21_IM_4PM", "display_name": "Q21 4pm", "template": "Q21_IM_4PM", "timing": "INTERMITTENT_4PM"},
    {"name": "Q21_CHECKOUT", "display_name": "Q21 Final Checkout", "template": "Q21_CHECKOUT", "timing": "CHECKOUT_8PM"},
    {"name": "Q21_CHECKOUT_YES", "display_name": "Q21 Checkout Yes", "template": "Q21_CHECKOUT_YES", "timing": "NO_DELAY"},
    {"name": "Q21_CHECKOUT_NO", "display_name": "Q21 Checkout No", "template": "Q21_CHECKOUT_NO", "timing": "NO_DELAY"},
    {"name": "Q21_GOODBYE", "display_name": "Q21 Goodbye", "template": "Q21_GOODBYE", "timing": "2_MIN_DELAY", "is_terminal": True},
]

# ============================================================================
# EDGE DEFINITIONS FOR Q8-Q21
# ============================================================================
Q8_Q21_EDGES = [
    # Connect Q7 checkout responses to Q8 (we'll update existing edges)
    ("Q7_CHECKOUT_YES", "Q8_IM_11AM"),
    ("Q7_CHECKOUT_NO", "Q8_IM_11AM"),

    # Q8 flow
    ("Q8_IM_11AM", "Q8_IM_1PM"),
    ("Q8_IM_1PM", "Q8_IM_3PM"),
    ("Q8_IM_3PM", "Q8_IM_5PM"),
    ("Q8_IM_5PM", "Q8_IM_7PM"),
    ("Q8_IM_7PM", "Q9_IM_11AM"),

    # Q9 flow
    ("Q9_IM_11AM", "Q9_IM_1PM"),
    ("Q9_IM_1PM", "Q9_IM_3PM"),
    ("Q9_IM_3PM", "Q9_IM_5PM"),
    ("Q9_IM_5PM", "Q9_IM_7PM"),
    ("Q9_IM_7PM", "Q10_MORNING"),

    # Q10 flow (has morning session)
    ("Q10_MORNING", "Q10_REASONS"),
    ("Q10_REASONS", "Q10_IM_1PM"),
    ("Q10_IM_1PM", "Q10_IM_4PM"),
    ("Q10_IM_4PM", "Q10_IM_7PM"),
    ("Q10_IM_7PM", "Q11_IM_11AM"),

    # Q11 flow
    ("Q11_IM_11AM", "Q11_IM_1PM"),
    ("Q11_IM_1PM", "Q11_IM_3PM"),
    ("Q11_IM_3PM", "Q11_IM_5PM"),
    ("Q11_IM_5PM", "Q11_IM_7PM"),
    ("Q11_IM_7PM", "Q12_IM_11AM"),

    # Q12 flow
    ("Q12_IM_11AM", "Q12_IM_1PM"),
    ("Q12_IM_1PM", "Q12_IM_3PM"),
    ("Q12_IM_3PM", "Q12_IM_5PM"),
    ("Q12_IM_5PM", "Q12_IM_7PM"),
    ("Q12_IM_7PM", "Q13_IM_11AM"),

    # Q13 flow
    ("Q13_IM_11AM", "Q13_IM_1PM"),
    ("Q13_IM_1PM", "Q13_IM_3PM"),
    ("Q13_IM_3PM", "Q13_IM_5PM"),
    ("Q13_IM_5PM", "Q13_IM_7PM"),
    ("Q13_IM_7PM", "Q14_MORNING"),

    # Q14 flow (Week 2 checkout)
    ("Q14_MORNING", "Q14_IM_1PM"),
    ("Q14_IM_1PM", "Q14_IM_4PM"),
    ("Q14_IM_4PM", "Q14_IM_7PM"),
    ("Q14_IM_7PM", "Q14_CHECKOUT"),
    ("Q14_CHECKOUT", "Q14_CHECKOUT_YES", "YES_SMOKED"),
    ("Q14_CHECKOUT", "Q14_CHECKOUT_NO", "NO_SMOKEFREE"),
    ("Q14_CHECKOUT_YES", "Q15_IM_11AM"),
    ("Q14_CHECKOUT_NO", "Q15_IM_11AM"),

    # Q15 flow
    ("Q15_IM_11AM", "Q15_IM_1PM"),
    ("Q15_IM_1PM", "Q15_IM_5PM"),
    ("Q15_IM_5PM", "Q15_IM_7PM"),
    ("Q15_IM_7PM", "Q16_IM_11AM"),

    # Q16 flow
    ("Q16_IM_11AM", "Q16_IM_1PM"),
    ("Q16_IM_1PM", "Q16_IM_5PM"),
    ("Q16_IM_5PM", "Q16_IM_7PM"),
    ("Q16_IM_7PM", "Q17_IM_11AM"),

    # Q17 flow
    ("Q17_IM_11AM", "Q17_IM_1PM"),
    ("Q17_IM_1PM", "Q17_IM_5PM"),
    ("Q17_IM_5PM", "Q17_IM_7PM"),
    ("Q17_IM_7PM", "Q18_IM_11AM"),

    # Q18 flow
    ("Q18_IM_11AM", "Q18_IM_1PM"),
    ("Q18_IM_1PM", "Q18_IM_5PM"),
    ("Q18_IM_5PM", "Q18_IM_7PM"),
    ("Q18_IM_7PM", "Q19_IM_11AM"),

    # Q19 flow
    ("Q19_IM_11AM", "Q19_IM_1PM"),
    ("Q19_IM_1PM", "Q19_IM_5PM"),
    ("Q19_IM_5PM", "Q19_IM_7PM"),
    ("Q19_IM_7PM", "Q20_IM_11AM"),

    # Q20 flow
    ("Q20_IM_11AM", "Q20_IM_1PM"),
    ("Q20_IM_1PM", "Q20_IM_5PM"),
    ("Q20_IM_5PM", "Q20_IM_7PM"),
    ("Q20_IM_7PM", "Q21_MORNING"),

    # Q21 flow (Final checkout - Study End)
    ("Q21_MORNING", "Q21_HEALTH"),
    ("Q21_HEALTH", "Q21_IM_1PM"),
    ("Q21_IM_1PM", "Q21_IM_4PM"),
    ("Q21_IM_4PM", "Q21_CHECKOUT"),
    ("Q21_CHECKOUT", "Q21_CHECKOUT_YES", "YES_SMOKED"),
    ("Q21_CHECKOUT", "Q21_CHECKOUT_NO", "NO_SMOKEFREE"),
    ("Q21_CHECKOUT_YES", "Q21_GOODBYE"),
    ("Q21_CHECKOUT_NO", "Q21_GOODBYE"),
]


async def main():
    """Add Q8-Q21 to existing QuitTxt V9 project."""
    print("=" * 60)
    print("Adding Q8-Q21+ to QuitTxt V9 Protocol")
    print("=" * 60)
    print()

    # Import models here to avoid circular imports
    import sys
    sys.path.insert(0, "/Users/vuc229/Documents/Development/Active-Projects/infrastructure/ezmsg-new/api")

    from app.models.project import Project
    from app.models.messaging_node import MessagingNode, MessagingNodeEdge
    from app.models.message_template import MessageTemplate, MessageTemplateText
    from app.models.timing_element import TimingElement
    from app.models.language import AvailableLanguage

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get project
        result = await session.execute(
            select(Project).where(Project.name == PROJECT_NAME)
        )
        project = result.scalar_one_or_none()
        if not project:
            print(f"ERROR: Project '{PROJECT_NAME}' not found!")
            return

        print(f"Found project: {project.name} (ID: {project.id})")

        # Get languages
        result = await session.execute(select(AvailableLanguage))
        languages = {lang.code: lang.id for lang in result.scalars().all()}
        en_id = languages.get("EN", 1)
        es_id = languages.get("ES", 2)
        print(f"Languages: EN={en_id}, ES={es_id}")

        # Get existing timing elements
        result = await session.execute(
            select(TimingElement).where(TimingElement.project_id == project.id)
        )
        timing_elements = {te.name: te.id for te in result.scalars().all()}
        print(f"Found {len(timing_elements)} timing elements")

        # Combine all templates
        all_templates = Q8_Q13_TEMPLATES + Q14_TEMPLATES + Q15_Q20_TEMPLATES + Q21_TEMPLATES

        # Create templates
        print("\n1. Creating templates...")
        template_ids = {}
        for tmpl_data in all_templates:
            template = MessageTemplate(
                project_id=project.id,
                name=tmpl_data["name"],
                description=tmpl_data.get("description"),
                type="STANDARD",
            )
            session.add(template)
            await session.flush()
            template_ids[tmpl_data["name"]] = template.id

            # Add English text
            en_data = tmpl_data.get("en", {})
            en_text = MessageTemplateText(
                template_id=template.id,
                language_id=en_id,
                message_text=en_data.get("text"),
                media_url=en_data.get("media_url"),
                media_type="image/gif" if en_data.get("media_url") else None,
                quick_replies=en_data.get("quick_replies", []),
            )
            session.add(en_text)

            # Add Spanish text
            es_data = tmpl_data.get("es", {})
            es_text = MessageTemplateText(
                template_id=template.id,
                language_id=es_id,
                message_text=es_data.get("text"),
                media_url=es_data.get("media_url"),
                media_type="image/gif" if es_data.get("media_url") else None,
                quick_replies=es_data.get("quick_replies", []),
            )
            session.add(es_text)

            print(f"  Created template: {tmpl_data['name']}")

        await session.flush()
        print(f"  Created {len(template_ids)} templates")

        # Create nodes
        print("\n2. Creating nodes...")
        node_ids = {}

        # First, get existing node IDs for reference
        result = await session.execute(
            select(MessagingNode).where(MessagingNode.project_id == project.id)
        )
        existing_nodes = {node.name: node.id for node in result.scalars().all()}
        node_ids.update(existing_nodes)
        print(f"  Found {len(existing_nodes)} existing nodes")

        for node_data in Q8_Q21_NODES:
            node = MessagingNode(
                project_id=project.id,
                name=node_data["name"],
                display_name=node_data.get("display_name"),
                template_id=template_ids.get(node_data.get("template")),
                timing_element_id=timing_elements.get(node_data.get("timing")),
                is_entry_node=node_data.get("is_entry", False),
                is_terminal_node=node_data.get("is_terminal", False),
            )
            session.add(node)
            await session.flush()
            node_ids[node_data["name"]] = node.id
            print(f"  Created node: {node_data['name']}")

        # Create edges
        print("\n3. Creating edges...")
        edge_count = 0
        for edge_data in Q8_Q21_EDGES:
            parent_name = edge_data[0]
            child_name = edge_data[1]
            label = edge_data[2] if len(edge_data) > 2 else None

            parent_id = node_ids.get(parent_name)
            child_id = node_ids.get(child_name)

            if not parent_id or not child_id:
                print(f"  WARNING: Could not find nodes for edge {parent_name} -> {child_name}")
                continue

            # Check if edge already exists
            result = await session.execute(
                select(MessagingNodeEdge).where(
                    MessagingNodeEdge.parent_node_id == parent_id,
                    MessagingNodeEdge.child_node_id == child_id
                )
            )
            if result.scalar_one_or_none():
                print(f"  Edge already exists: {parent_name} -> {child_name}")
                continue

            edge = MessagingNodeEdge(
                parent_node_id=parent_id,
                child_node_id=child_id,
                edge_label=label,
            )
            session.add(edge)
            edge_count += 1
            label_str = f" [{label}]" if label else ""
            print(f"  Created edge: {parent_name} -> {child_name}{label_str}")

        await session.commit()

        print()
        print("=" * 60)
        print("Q8-Q21+ successfully added!")
        print(f"New Templates: {len(template_ids)}")
        print(f"New Nodes: {len(Q8_Q21_NODES)}")
        print(f"New Edges: {edge_count}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

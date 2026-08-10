"""
Valores usados quando a pessoa escolhe "padrão do app" em vez de
configurar o horário na mão. Centralizados aqui pra não espalhar
números mágicos pelos casos de uso -- e pra ficar fácil de achar quando
alguém quiser ajustar.

Evolução futura óbvia: DEFAULT_REMINDER_TIME hoje é uma constante fixa
igual pra todo mundo. O ideal seria calcular a partir da disponibilidade
que a pessoa marcou na aba Rotina (manhã/tarde/noite por dia da semana)
-- ela já existe no front, só falta a tabela de disponibilidade no
backend pra alimentar isso. Registrado aqui pra não esquecer, não
implementado ainda.
"""
from datetime import time

DEFAULT_REMINDER_TIME = time(8, 0)
DEFAULT_REMINDER_DAYS_OF_WEEK = [0, 1, 2, 3, 4, 5, 6] 
DEFAULT_EVENT_REMINDER_MINUTES = 30

import datetime
import re
import logging
from typing import Optional, List, Dict, Tuple, Any

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def get_current_time(query: str = "") -> str:
    """
    Devuelve la fecha y hora actuales del sistema. Utilice esta función siempre que el usuario solicite la hora o la fecha.
    La entrada se ignora; puede pasar una cadena vacía.
    """
    now = datetime.datetime.now()
    return f"La fecha y hora actual es: {now.strftime('%Y-%m-%d %H:%M:%S')} (tiempo local)"



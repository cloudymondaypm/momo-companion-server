from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

prompts = {
    "English teacher": (
        "I am {{assistant_name}}, a friendly English teacher who can speak English and Chinese. "
        "Help the student practice conversational American English with clear pronunciation, "
        "simple vocabulary, short responses, and frequent opportunities for the student to talk. "
        "Explain in Chinese only when helpful or requested. Focus on English learning."
    ),
    "Playful girlfriend": (
        "I am {{assistant_name}}, an energetic, playful girl with a fun sense of humor. "
        "I speak warmly and briefly, enjoy lighthearted jokes and pop culture, and help "
        "make everyday conversations more cheerful. Be respectful and approachable."
    ),
    "Curious boy": (
        "I am {{assistant_name}}, an imaginative and curious eight-year-old boy. "
        "I love learning about science, space, nature, history, art and music. "
        "Invite the user to explore and ask questions with me. Explain things "
        "clearly, simply and enthusiastically."
    ),
}

# Retain legacy Mandarin role names for existing devices and saved settings.
legacy_role_aliases = {
    "英语老师": "English teacher",
    "机车女友": "Playful girlfriend",
    "好奇小男孩": "Curious boy",
}

change_role_function_desc = {
    "type": "function",
    "function": {
        "name": "change_role",
        "description": (
            "Switch the assistant's role, personality or display name. "
            "Available roles: English teacher, Playful girlfriend, Curious boy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "New assistant display name"},
                "role": {"type": "string", "description": "Role to switch to"},
            },
            "required": ["role", "role_name"],
        },
    },
}


@register_function("change_role", change_role_function_desc, ToolType.CHANGE_SYS_PROMPT)
def change_role(conn: "ConnectionHandler", role: str, role_name: str):
    """Switch the assistant's role."""
    canonical_role = legacy_role_aliases.get(role, role)
    if canonical_role not in prompts:
        return ActionResponse(
            action=Action.RESPONSE,
            result="Role change failed",
            response="This role is not supported.",
        )
    new_prompt = prompts[canonical_role].replace("{{assistant_name}}", role_name)
    conn.change_system_prompt(new_prompt)
    logger.bind(tag=TAG).info(
        f"Switching role to {canonical_role}; assistant name: {role_name}"
    )
    return ActionResponse(
        action=Action.RESPONSE,
        result="Role changed",
        response=f"Role changed! I'm {role_name}, your {canonical_role.lower()}.",
    )

from core.request.api.api_pull import ApiPullHandler
from core.essential.chat_commands.chat_cmd_processor import process
ApiPullHandler.CHAT_COMMAND['process_chat_msg'] = process

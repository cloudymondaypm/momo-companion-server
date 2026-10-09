from config.logger import setup_logging
from enum import Enum

TAG = __name__

logger = setup_logging()


class ToolType(Enum):
    NONE = (1, "After calling tool, take no further action")
    WAIT = (2, "Call tool and wait for result")
    CHANGE_SYS_PROMPT = (3, "Change system prompt to switch persona or responsibilities")
    SYSTEM_CTL = (
        4,
        "System control affecting the conversation, e.g. exit or play music; requires conn argument",
    )
    IOT_CTL = (5, "IoT device control; requires conn argument")
    MCP_CLIENT = (6, "MCP client")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class Action(Enum):
    ERROR = (-1, "Error")
    NOTFOUND = (0, "Function not found")
    NONE = (1, "Do nothing")
    RESPONSE = (2, "Respond directly")
    REQLLM = (3, "Request LLM reply after executing function")
    RECORD = (4, "Record tool call in conversation history without invoking LLM")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class ActionResponse:
    def __init__(self, action: Action, result=None, response=None):
        self.action = action  # Action type
        self.result = result  # Action result
        self.response = response  # Direct response content


class FunctionItem:
    def __init__(self, name, description, func, type):
        self.name = name
        self.description = description
        self.func = func
        self.type = type


class DeviceTypeRegistry:
    """Device type registry for IoT device types and their functions"""

    def __init__(self):
        self.type_functions = {}  # type_signature -> {func_name: FunctionItem}

    def generate_device_type_id(self, descriptor):
        """Generate type ID from device capabilities"""
        properties = sorted(descriptor["properties"].keys())
        methods = sorted(descriptor["methods"].keys())
        # Use properties and methods as unique identifier for device type
        type_signature = (
            f"{descriptor['name']}:{','.join(properties)}:{','.join(methods)}"
        )
        return type_signature

    def get_device_functions(self, type_id):
        """Get all functions for device type"""
        return self.type_functions.get(type_id, {})

    def register_device_type(self, type_id, functions):
        """Register device type and functions"""
        if type_id not in self.type_functions:
            self.type_functions[type_id] = functions


# Initialize function registry dictionary
all_function_registry = {}
# Map module names to registered function names for expanding module plugins
module_func_map = {}


def register_function(name, desc, type=None):
    """Decorator registering functions in the function registry"""

    def decorator(func):
        all_function_registry[name] = FunctionItem(name, desc, func, type)
        # Record module-to-function mapping to expand module-level plugin configuration
        module_name = func.__module__.split(".")[-1]
        module_func_map.setdefault(module_name, []).append(name)
        logger.bind(tag=TAG).debug(f"Function '{name}' loaded and available for registration")
        return func

    return decorator


def register_device_function(name, desc, type=None):
    """Decorator registering device-level functions"""

    def decorator(func):
        logger.bind(tag=TAG).debug(f"Device function '{name}' loaded")
        return func

    return decorator


class FunctionRegistry:
    def __init__(self):
        self.function_registry = {}
        self.logger = setup_logging()

    def register_function(self, name, func_item=None):
        # Register func_item directly when provided
        if func_item:
            self.function_registry[name] = func_item
            self.logger.bind(tag=TAG).debug(f"Function '{name}' registered directly")
            return func_item

        # Otherwise look up in all_function_registry
        func = all_function_registry.get(name)
        if not func:
            self.logger.bind(tag=TAG).error(f"Function '{name}' not found")
            return None
        self.function_registry[name] = func
        self.logger.bind(tag=TAG).debug(f"Function '{name}' registered successfully")
        return func

    def unregister_function(self, name):
        # Unregister function if present
        if name not in self.function_registry:
            self.logger.bind(tag=TAG).error(f"Function '{name}' not found")
            return False
        self.function_registry.pop(name, None)
        self.logger.bind(tag=TAG).info(f"Function '{name}' unregistered successfully")
        return True

    def get_function(self, name):
        return self.function_registry.get(name)

    def get_all_functions(self):
        return self.function_registry

    def get_all_function_desc(self):
        return [func.description for _, func in self.function_registry.items()]

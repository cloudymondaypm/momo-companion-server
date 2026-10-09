"""IoT device support module providing descriptors and state handling"""

import asyncio
from config.logger import setup_logging
from .iot_descriptor import IotDescriptor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


async def handleIotDescriptors(conn: "ConnectionHandler", descriptors):
    """Process IoT description"""
    wait_max_time = 5
    while (
        not hasattr(conn, "func_handler")
        or conn.func_handler is None
        or not conn.func_handler.finish_init
    ):
        await asyncio.sleep(1)
        wait_max_time -= 1
        if wait_max_time <= 0:
            logger.bind(tag=TAG).debug("Connection has no func_handler")
            return

    functions_changed = False

    for descriptor in descriptors:
        # Skip if descriptor has neither properties nor methods
        if "properties" not in descriptor and "methods" not in descriptor:
            continue

        # Handle missing properties
        if "properties" not in descriptor:
            descriptor["properties"] = {}
            # Extract method parameters as properties
            if "methods" in descriptor:
                for method_name, method_info in descriptor["methods"].items():
                    if "parameters" in method_info:
                        for param_name, param_info in method_info["parameters"].items():
                            # Convert parameter metadata to property metadata
                            descriptor["properties"][param_name] = {
                                "description": param_info["description"],
                                "type": param_info["type"],
                            }

        # Create IoT device descriptor
        iot_descriptor = IotDescriptor(
            descriptor["name"],
            descriptor["description"],
            descriptor["properties"],
            descriptor["methods"],
        )
        conn.iot_descriptors[descriptor["name"]] = iot_descriptor
        functions_changed = True

    # Update function descriptors when a new function is registered
    if functions_changed and hasattr(conn, "func_handler"):
        # Register IoT tools with unified tool handler
        await conn.func_handler.register_iot_tools(descriptors)

        conn.func_handler.current_support_functions()


async def handleIotStatus(conn: "ConnectionHandler", states):
    """Process IoT state"""
    for state in states:
        for key, value in conn.iot_descriptors.items():
            if key == state["name"]:
                for property_item in value.properties:
                    for k, v in state["state"].items():
                        if property_item["name"] == k:
                            if type(v) != type(property_item["value"]):
                                logger.bind(tag=TAG).error(
                                    f"Property {property_item['name']} has a mismatched value type"
                                )
                                break
                            else:
                                property_item["value"] = v
                                logger.bind(tag=TAG).info(
                                    f"IoT state updated: {key} , {property_item['name']} = {v}"
                                )
                            break
                break

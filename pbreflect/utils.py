import re


def name_to_snake(string: str) -> str:
    """Convert a string to snake_case.

    Args:
        string: String to convert

    Returns:
        String in snake_case format
    """
    # Replace common separators with underscores
    string = string.replace(" ", "_").replace("/", "_").replace(".", "_")
    string = string.replace("{", "").replace("}", "")

    # Handle camelCase and PascalCase
    string = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", string)
    string = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", string)

    # Replace special characters
    string = re.sub("&", "and", string)

    # Final cleanup
    string = string.replace("-", "_").lower().strip("_")
    return string


def snake_to_camel(string: str) -> str:
    """Convert a string from snake_case to CamelCase.

    Args:
        string: String to convert

    Returns:
        String in CamelCase format
    """
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", string)
    camel_case_words = [word[0].upper() + word[1:] for word in words if word]
    camel_case_title = "".join(camel_case_words)
    return camel_case_title

"""Minimal YAML fallback parser for under-one skill configuration.

This intentionally supports only the subset used by ``under-one.yaml`` when
PyYAML is unavailable.
"""


def minimal_yaml_parse(text: str) -> dict:
    result = {}
    current_section = None
    current_sub = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and not line.startswith("\t"):
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "":
                    result[key] = {}
                    current_section = key
                    current_sub = None
                else:
                    result[key] = parse_yaml_value(val)
                    current_section = None
        elif current_section is not None and stripped.startswith("-"):
            val = stripped[1:].strip()
            if isinstance(result.get(current_section), dict) and current_sub is not None:
                if current_sub not in result[current_section]:
                    result[current_section][current_sub] = []
                if isinstance(result[current_section][current_sub], list):
                    result[current_section][current_sub].append(parse_yaml_value(val))
                else:
                    result[current_section][current_sub] = [
                        result[current_section][current_sub],
                        parse_yaml_value(val),
                    ]
            else:
                if current_section not in result:
                    result[current_section] = []
                result[current_section].append(parse_yaml_value(val))
        elif current_section is not None and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][key] = {}
                current_sub = key
            else:
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][key] = parse_yaml_value(val)
    return result


def parse_yaml_value(val: str):
    val = val.strip()
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val == "true":
        return True
    if val == "false":
        return False
    if val == "null" or val == "~":
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        if not inner.strip():
            return []
        return [parse_yaml_value(v.strip()) for v in inner.split(",")]
    return val

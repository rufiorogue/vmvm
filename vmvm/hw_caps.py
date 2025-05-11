import re

def check_has_topoext() -> bool:
    """
        detects if the processor has 'topoext' flag
    """
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if re.match('^flags.+', line):
                if re.search('topoext', line):
                    return True
    return False
import subprocess
import logging
import io

def exec_with_trace(executable_name: str, args: list[str]) -> int:
    real_args = [executable_name] + args
    logging.info('running %s with args: %s', executable_name, ' '.join(real_args))
    proc = subprocess.Popen(args=real_args,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logging.info('-'*80)
    for line in io.TextIOWrapper(proc.stdout, encoding='utf-8'):
        logging.info(line.rstrip())
    exit_code = proc.wait()
    logging.info('-'*80)
    logging.info('%s exited with code %d', executable_name, exit_code)
    return exit_code
from modules.globalvars import RESET, YELLOW, beta
import time
import os
import sys
import subprocess
import sysconfig
import pathlib
import platform
import json
import re
from spacy.util import is_package
import importlib.metadata
import logging
from modules.settings import instance as settings_manager
import threading

settings = settings_manager.settings


logger = logging.getLogger("goober")

psutilavaliable = True
try:
    import psutil
except ImportError:
    psutilavaliable = False
    logger.error('Missing requests and psutil! Please install them using pip: `pip install requests psutil`')


def check_for_model():
    if is_package("en_core_web_sm"):
        logger.info("Model is installed.")
    else:
        logger.info("Model is not installed.")


def iscloned():
    if os.path.exists(".git"):
        return True
    else:
        logger.error(f"{'Goober is not cloned! Please clone it from GitHub.'}")


def get_stdlib_modules():
    stdlib_path = pathlib.Path(sysconfig.get_paths()["stdlib"])
    modules = set()
    if hasattr(sys, "builtin_module_names"):
        modules.update(sys.builtin_module_names)
    for file in stdlib_path.glob("*.py"):
        if file.stem != "__init__":
            modules.add(file.stem)
    for folder in stdlib_path.iterdir():
        if folder.is_dir() and (folder / "__init__.py").exists():
            modules.add(folder.name)
    for file in stdlib_path.glob("*.*"):
        if file.suffix in (".so", ".pyd"):
            modules.add(file.stem)

    return modules


def check_requirements():
    STD_LIB_MODULES = get_stdlib_modules()
    PACKAGE_ALIASES = {
        "discord": "discord.py",
        "better_profanity": "better-profanity",
        "dotenv": "python-dotenv",
        "pil": "pillow",
        "websocket": "websocket-client"
    }

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.abspath(
        os.path.join(parent_dir, "..", "requirements.txt")
    )

    if not os.path.exists(requirements_path):
        logger.error(f"requirements.txt not found at {requirements_path} was it tampered with?")
        return

    with open(requirements_path, "r") as f:
        lines = f.readlines()
        requirements = set()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                base_pkg = line.split("==")[0].lower()
                aliased_pkg = PACKAGE_ALIASES.get(base_pkg, base_pkg)
                requirements.add(aliased_pkg)

    installed_packages = {
        dist.metadata["Name"].lower() for dist in importlib.metadata.distributions()
    }
    missing = []

    for req in sorted(requirements):
        if req in STD_LIB_MODULES or req == "modules":
            print(f'STD LIB / LOCAL {req} (skipped check)')
            continue

        check_name = req.lower()

        if check_name in installed_packages:
            logger.info(f"{'OK'} {check_name}")
        else:
            logger.error(f"{'MISSING'} {check_name} {'is not installed'}")
            missing.append(check_name)

    if missing:
        logger.error('Missing packages detected:')
        for pkg in missing:
            print(f"  - {pkg}")
        sys.exit(1)
    else:
        logger.info('All requirements are satisfied.')


def check_latency():
    host = "1.1.1.1"
    system = platform.system()

    if system == "Windows":
        cmd = ["ping", "-n", "1", "-w", "1000", host]
        latency_pattern = r"Average = (\d+)ms"

    elif system == "Darwin":
        cmd = ["ping", "-c", "1", host]
        latency_pattern = r"time=([\d\.]+) ms"

    else:
        cmd = ["ping", "-c", "1", "-W", "1", host]
        latency_pattern = r"time=([\d\.]+) ms"

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode == 0:
            match = re.search(latency_pattern, result.stdout)
            if match:
                latency_ms = float(match.group(1))
                logger.info('Ping to {host}: {latency} ms'.format(host=host, latency=latency_ms))
                if latency_ms > 300:
                    logger.warning(f"{'High latency detected! You may experience delays in response times.'}")
            else:
                logger.warning('Could not parse latency.')
        else:
            print(result.stderr)
            logger.error(f"{'Ping to {host} failed.'.format(host=host)}{RESET}")
    except Exception as e:
        logger.error('Error running ping: {error}'.format(error=e))


def check_memory():
    if not psutilavaliable:
        return
    try:
        memory_info = psutil.virtual_memory()  # type: ignore
        total_memory = memory_info.total / (1024**3)
        used_memory = memory_info.used / (1024**3)
        free_memory = memory_info.available / (1024**3)

        logger.info(
            "Memory Usage: {used} GB / {total} GB ({percent}%)".format(
                used=used_memory,
                total=total_memory,
                percent=(used_memory / total_memory) * 100,
            )
        )
        if used_memory > total_memory * 0.9:
            print(
                f"{YELLOW}{'Memory usage is above 90% ({percent}%). Consider freeing up memory.'.format(percent=(used_memory / total_memory) * 100)}{RESET}"
            )
        logger.info('Total Memory: {total} GB'.format(total=total_memory))
        logger.info('Used Memory: {used} GB'.format(used=used_memory))
        if free_memory < 1:
            logger.warning(f"{'Low free memory detected! Only {free} GB available.'.format(free=free_memory)}")

    except ImportError:
        logger.error(
            'Memory check skipped.'
        )  # todo: translate this into italian and put it in the translations "psutil is not installed. Memory check skipped."


def check_cpu():
    if not psutilavaliable:
        return
    logger.info('Measuring CPU usage per core...')
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)  # type: ignore
    total_cpu = sum(cpu_per_core) / len(cpu_per_core)
    logger.info('Total CPU Usage: {usage}%'.format(usage=total_cpu))

    if total_cpu > 85:
        logger.warning(f"{'High average CPU usage: {usage}%'.format(usage=total_cpu)}")

    if total_cpu > 95:
        logger.error('Really high CPU load! System may throttle or hang.')


def check_memoryjson():
    try:
        logger.info(
            "Memory file: {size} MB".format(
                size=os.path.getsize(settings["bot"]["active_memory"]) / (1024**2)
            )
        )
        if os.path.getsize(settings["bot"]["active_memory"]) > 1_073_741_824:
            logger.warning(f"{'Memory file is 1GB or higher, consider clearing it to free up space.'}")
        try:
            with open(settings["bot"]["active_memory"], "r", encoding="utf-8") as f:
                json.load(f)

        except json.JSONDecodeError as e:
            logger.error(f"{'Memory file is corrupted! JSON decode error: {error}'.format(error=e)}")
            logger.warning(f"{'Consider backing up and recreating the memory file.'}")

        except UnicodeDecodeError as e:
            logger.error(f"{'Memory file has encoding issues: {error}'.format(error=e)}")
            logger.warning(f"{'Consider backing up and recreating the memory file.'}")

        except Exception as e:
            logger.error(f"{'Error reading memory file: {error}'.format(error=e)}")
    except FileNotFoundError:
        logger.info(f"{'Memory file not found.'}")


def presskey2skip(timeout):
    if os.name == "nt":
        import msvcrt

        start_time = time.time()
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                break
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
    else:
        import select
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            start_time = time.time()
            while True:
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.read(1)
                    break
                if time.time() - start_time > timeout:
                    break
                time.sleep(0.1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def start_checks():
    if settings["disable_checks"]:
        logger.warning(f"{'Checks are disabled!'}")
        return

    logger.info('Running pre-start checks...')

    checks = [
        check_for_model,
        iscloned,
        check_requirements,
        check_latency,
        check_memory,
        check_memoryjson,
        check_cpu
    ]
    threads: list[threading.Thread] = []

    for check in checks:
        t = threading.Thread(target=check)
        t.start()
        threads.append(t)

    if os.path.exists(".env"):
        pass
    else:
        logger.warning(f"{'The .env file was not found! Please create one with the required variables.'}")
        sys.exit(1)
    if beta:
        logger.warning("this build isnt finished yet, some things might not work as expected")
    else:
        pass

    for thread in threads:
        thread.join()

    logger.info('Continuing in {seconds} seconds... Press any key to skip.'.format(seconds=5))
    presskey2skip(timeout=5)

    with open(settings["splash_text_loc"], "r") as f:
        print("".join(f.readlines()))

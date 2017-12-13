# pylint: disable=missing-docstring
from __future__ import print_function

import getpass
import json
import os
import platform
import subprocess
import sys
import argparse
import appdirs
from pathlib import Path

import pkg_resources
from redbot.setup import basic_setup

if sys.platform == "linux":
    import distro

config_dir = Path(appdirs.AppDirs("Red-DiscordBot").user_config_dir)
config_file = config_dir / 'config.json'

PYTHON_OK = sys.version_info >= (3, 5)
INTERACTIVE_MODE = not len(sys.argv) > 1  # CLI flags = non-interactive

INTRO = ("==========================\n"
         "Red Discord Bot - Launcher\n"
         "==========================\n")

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Red - Discord Bot's launcher (V3)", allow_abbrev=False
    )
    with config_file.open("r") as fin:
        instances = json.loads(fin.read())
    parser.add_argument("instancename", metavar="instancename", type=str,
                        nargs="?", help="The instance to run", choices=list(instances.keys()))
    parser.add_argument("--start", "-s",
                        help="Starts Red",
                        action="store_true")
    parser.add_argument("--auto-restart",
                        help="Autorestarts Red in case of issues",
                        action="store_true")
    parser.add_argument("--update",
                        help="Updates Red",
                        action="store_true")
    parser.add_argument("--update-dev",
                        help="Updates Red from the Github repo",
                        action="store_true")
    parser.add_argument("--voice",
                        help="Installs extra 'voice' when updating",
                        action="store_true")
    parser.add_argument("--docs",
                        help="Installs extra 'docs' when updating",
                        action="store_true")
    parser.add_argument("--test",
                        help="Installs extra 'test' when updating",
                        action="store_true")
    parser.add_argument("--mongo",
                        help="Installs extra 'mongo' when updating",
                        action="store_true")
    parser.add_argument("--debuginfo",
                        help="Prints basic debug info that would be useful for support",
                        action="store_true")
    return parser.parse_known_args()


def update_red(dev=False, voice=False, mongo=False, docs=False, test=False):
    interpreter = sys.executable
    print("Updating Red...")
    # If the user ran redbot-launcher.exe, updating with pip will fail
    # on windows since the file is open and pip will try to overwrite it.
    # We have to rename redbot-launcher.exe in this case.
    launcher_script = os.path.abspath(sys.argv[0])
    old_name = launcher_script + ".exe"
    new_name = launcher_script + ".old"
    renamed = False
    if "redbot-launcher" in launcher_script and IS_WINDOWS:
        renamed = True
        print("Renaming {} to {}".format(old_name, new_name))
        if os.path.exists(new_name):
            os.remove(new_name)
        os.rename(old_name, new_name)
    egg_l = []
    if voice:
        egg_l.append("voice")
    if mongo:
        egg_l.append("mongo")
    if docs:
        egg_l.append("docs")
    if test:
        egg_l.append("test")
    if dev:
        package = "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop"
        if egg_l:
            package += "#egg=Red-DiscordBot[{}]".format(", ".join(egg_l))
    else:
        package = "Red-DiscordBot"
        if egg_l:
            package += "[{}]".format(", ".join(egg_l))
    code = subprocess.call([
        interpreter, "-m",
        "pip", "install", "-U",
        "--process-dependency-links",
        package
    ])
    if code == 0:
        print("Red has been updated")
    else:
        print("Something went wrong while updating!")

    # If redbot wasn't updated, we renamed our .exe file and didn't replace it
    scripts = os.listdir(os.path.dirname(launcher_script))
    if renamed and "redbot-launcher.exe" not in scripts:
        print("Renaming {} to {}".format(new_name, old_name))
        os.rename(new_name, old_name)


def run_red(selected_instance, autorestart: bool=False, cliflags=None):
    while True:
        print("Starting {}...".format(selected_instance))
        cmd_list = ["redbot", selected_instance]
        if cliflags:
            cmd_list += cliflags
        status = subprocess.call(cmd_list)
        if (not autorestart) or (autorestart and status != 26):
            break


def cli_flag_getter():
    print("Would you like to enter any cli flags to pass to redbot? (y/n)")
    resp = user_choice()
    if resp == "n":
        return None
    elif resp == "y":
        flags = []
        print("Ok, we will now walk through choosing cli flags")
        print("Would you like to specify an owner? (y/n)")
        choice = user_choice()
        if choice == "y":
            print("Enter the user id for the owner")
            owner_id = user_choice()
            flags.append("--owner {}".format(owner_id))
        print("Would you like to specify any prefixes? (y/n)")
        choice = user_choice()
        if choice == "y":
            print(
                "Enter the prefixes, separated by a space (please note "
                "that prefixes containing a space will need to be added with [p]set prefix)")
            prefixes = user_choice().split()
            for p in prefixes:
                flags.append("-p {}".format(p))
        print("Would you like to disable console input? Please note that features "
              "requiring console interaction may fail to work (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--no-prompt")
        print("Would you like to start with no cogs loaded? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--no-cogs")
        print("Is this a selfbot? (y/n)")
        choice = user_choice()
        if choice == "y":
            print("Please note that selfbots are not allowed by Discord. See"
                  "https://support.discordapp.com/hc/en-us/articles/115002192352-Automated-user-accounts-self-bots-"
                  "for more information.")
            flags.append("--self-bot")
        print("Does this token belong to a user account rather than a bot account? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--not-bot")
        print("Do you want to do a dry run? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--dry-run")
        print("Do you want to set the log level to debug? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--debug")
        print("Do you want the Dev cog loaded (thus enabling commands such as debug and repl)? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--dev")
        print("Do you want to enable RPC? (y/n)")
        choice = user_choice()
        if choice == "y":
            flags.append("--rpc")
        print("You have selected the following cli flags:\n\n")
        print("\n".join(flags))
        print("\nIf this looks good to you, type y. If you wish to start over, type n")
        choice = user_choice()
        if choice == "y":
            print("Done selecting cli flags")
            return flags
        else:
            print("Starting over")
            return cli_flag_getter()
    else:
        print("Invalid response! Let's try again")
        return cli_flag_getter()


def instance_menu():
    with config_file.open("r") as fin:
        instances = json.loads(fin.read())
    if not instances:
        print("No instances found!")
        return None
    counter = 0
    print("Red instance menu\n")
   
    name_num_map = {}
    for name in list(instances.keys()):
        print("{}. {}\n".format(counter+1, name))
        name_num_map[str(counter+1)] = name
        counter += 1
    selection = user_choice()
    try:
        selection = int(selection)
    except ValueError:
        print("Invalid input! Try again.")
        return None
    else:
        if selection not in list(range(1, counter+1)):
            print("Invalid selection! Please try again")
            return None
        else:
            return name_num_map[str(selection)]


def clear_screen():
    if IS_WINDOWS:
        os.system("cls")
    else:
        os.system("clear")


def wait():
    if INTERACTIVE_MODE:
        input("Press enter to continue.")


def user_choice():
    return input("> ").lower().strip()


def extras_selector():
    print("Enter any extra requirements you want installed\n")
    print("Options are: voice, docs, test, mongo\n")
    selected = user_choice()
    selected = selected.split()
    return selected


def debug_info():
    pyver = sys.version
    redver = pkg_resources.get_distribution("Red-DiscordBot").version
    osver = ""
    if IS_WINDOWS:
        os_info = platform.uname()
        osver = "{} {} (version {}) {}".format(
            os_info.system, os_info.release, os_info.version, os_info.machine
        )
    elif IS_MAC:
        os_info = platform.mac_ver()
        osver = "Mac OSX {} {}".format(os_info[0], os_info[2])
    else:
        os_info = distro.linux_distribution()
        osver = "{} {}".format(os_info[0], os_info[1]).strip()
    user_who_ran = getpass.getuser()
    info = "Debug Info for Red\n\n" +\
        "Python version: {}\n".format(pyver) +\
        "Red version: {}\n".format(redver) +\
        "OS version: {}\n".format(osver) +\
        "System arch: {}\n".format(platform.machine()) +\
        "User: {}\n".format(user_who_ran)
    print(info)
    exit(0)


def main_menu():
    if IS_WINDOWS:
        os.system("TITLE Red - Discord Bot V3 Launcher")
    while True:
        print(INTRO)
        print("1. Run Red w/ autorestart in case of issues")
        print("2. Run Red")
        print("3. Update Red")
        print("4. Update Red (development version)")
        print("5. Create Instance")
        print("6. Debug information (use this if having issues with the launcher or bot)")
        print("0. Exit")
        choice = user_choice()
        if choice == "1":
            instance = instance_menu()
            cli_flags = cli_flag_getter()
            if instance:
                run_red(instance, autorestart=True, cliflags=cli_flags)
            wait()
        elif choice == "2":
            instance = instance_menu()
            cli_flags = cli_flag_getter()
            if instance:
                run_red(instance, autorestart=False, cliflags=cli_flags)
            wait()
        elif choice == "3":
            selected = extras_selector()
            update_red(
                dev=False, voice=True if "voice" in selected else False,
                docs=True if "docs" in selected else False,
                test=True if "test" in selected else False,
                mongo=True if "mongo" in selected else False
            )
            wait()
        elif choice == "4":
            selected = extras_selector()
            update_red(
                dev=True, voice=True if "voice" in selected else False,
                docs=True if "docs" in selected else False,
                test=True if "test" in selected else False,
                mongo=True if "mongo" in selected else False
            )
            wait()
        elif choice == "5":
            basic_setup()
            wait()
        elif choice == "6":
            debug_info()
        elif choice == "0":
            break
        clear_screen()


def main():
    if not PYTHON_OK:
        raise RuntimeError(
            "Red requires Python 3.5 or greater. "
            "Please install the correct version!"
        )
    if args.debuginfo:  # Check first since the function triggers an exit
        debug_info()
    
    if args.update and args.update_dev:  # Conflicting args, so error out
        raise RuntimeError(
            "\nUpdate requested but conflicting arguments provided.\n\n"
            "Please try again using only one of --update or --update-dev"
        )
    if args.update:
        update_red(
            voice=args.voice, docs=args.docs, 
            test=args.test, mongo=args.mongo
        )
    elif args.update_dev:
        update_red(
            dev=True, voice=args.voice, docs=args.docs, 
            test=args.test, mongo=args.mongo
        )

    if INTERACTIVE_MODE:
        main_menu()
    elif args.start:
        print("Starting Red...")
        run_red(args.instancename, autorestart=args.auto_restart, cliflags=flags_to_pass)


args, flags_to_pass = parse_cli_args()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
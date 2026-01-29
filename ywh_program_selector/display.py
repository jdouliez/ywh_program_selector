"""Display utilities - colors, banner, formatting."""

import sys
from typing import Any

from colorama import Fore, Style


def banner():
    """Print the application banner."""
    print(orange(f"""\n
dP    dP dP   dP   dP dP     dP      888888ba                                                                               dP                     dP                     
Y8.  .8P 88   88   88 88     88      88    `8b                                                                              88                     88                     
 Y8aa8P  88  .8P  .8P 88aaaaa88a    a88aaaa8P' 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d8b.d8b.    .d8888b. .d8888b. 88 .d8888b. .d8888b. d8888P .d8888b. 88d888b. 
   88    88  d8'  d8' 88     88      88        88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'`88'`88    Y8ooooo. 88ooood8 88 88ooood8 88'  `""   88   88'  `88 88'  `88 
   88    88.d8P8.d8P  88     88      88        88       88.  .88 88.  .88 88       88.  .88 88  88  88          88 88.  ... 88 88.  ... 88.  ...   88   88.  .88 88       
   dP    8888' Y88'   dP     dP      dP        dP       `88888P' `8888P88 dP       `88888P8 dP  dP  dP    `88888P' `88888P' dP `88888P' `88888P'   dP   `88888P' dP       
                                                                      .88                                                                                                 
                                                                  d8888P                                                                                                  
                                                                                    {Fore.CYAN}@_Ali4s_{Style.RESET_ALL}                                   
"""), file=sys.stderr)


def format_number(number: float) -> str:
    """Format number with appropriate decimal places."""
    return f"{number:.0f}" if number == int(number) else f"{number:.1f}"


def red(text: Any) -> str:
    """Return text colored red."""
    return Fore.RED + str(text) + Style.RESET_ALL


def orange(text: Any) -> str:
    """Return text colored orange/yellow."""
    return Fore.YELLOW + str(text) + Style.RESET_ALL


def green(text: Any) -> str:
    """Return text colored green."""
    return Fore.GREEN + str(text) + Style.RESET_ALL

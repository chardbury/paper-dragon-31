import os
import sys

script_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, script_path)

from applib import main

main.main()

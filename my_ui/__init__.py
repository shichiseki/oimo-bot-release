from .selects.dropdown import Dropdown
from .button.delete import DeleteButton
from .views.confirm import ConfirmView
from .views.main_view import MainView
from .views.main_view import SettingView

import glob
from importlib import reload, import_module


def reload_my_ui():
    module_list = [path.replace("/", ".").replace(".py", "") for path in glob.glob("my_ui/*/*.py")]

    for mod_name in module_list:
        module = import_module(mod_name)
        reload(module)


__all__ = ["Dropdown", "RateRegisterModal", "RateRegisterView", "DeleteButton", "TeamDivideDropdownView", "ConfirmView", "MainView", "SettingView"]

reload_my_ui()

from importlib import import_module

from pcdscalc.common import energy_to_wavelength, wavelength_to_energy
from pcdscalc.diffraction import bragg_angle, darwin_width
from pcdscalc.xray import transmission

from .utils import HelpfulNamespace


def collect_functions(modules):
    """
    Take all the callables in ``modules`` and collect them into a namespace.

    Arguments
    ---------
    modules: ``list of str``
        The modules to extract functions from
    """
    functions = {}
    for module_name in modules:
        module = import_module(module_name)
        for name, obj in module.__dict__.items():
            try:
                # Only include things that are natively from this module
                from_module = obj.__module__ == module_name
                # Only include callables
                is_callable = callable(obj)
                # Skip hidden items
                is_hidden = len(name) == 0 or name[0] == '_'

                if from_module and is_callable and not is_hidden:
                    functions[name] = obj
            except AttributeError:
                # obj did not have __module__, probably a builtin
                pass
    return HelpfulNamespace(**functions)


calc_namespace = HelpfulNamespace(
    E2lam=energy_to_wavelength,
    lam2E=wavelength_to_energy,
    bragg_angle=bragg_angle,
    darwin_width=darwin_width,
    transmission=transmission,
    be_lens=collect_functions(['pcdscalc.be_lens_calcs']),
    common=collect_functions(['pcdscalc.common']),
    diffraction=collect_functions(['pcdscalc.diffraction']),
    xray=collect_functions(['pcdscalc.xray']),
)

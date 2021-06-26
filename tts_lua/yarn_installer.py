import logging
import os

log = logging.getLogger(__name__)


def yarn_check_install():

    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    installed_file = os.path.join(base_dir, ".package.installed.version")
    package_file = os.path.join(base_dir, "package.json")
    if not os.path.exists(installed_file) or os.path.getctime(
        installed_file
    ) < os.path.getctime(package_file):
        try:
            from pynpm import YarnPackage

            pkg = YarnPackage(package_file)
            pkg.install()
            with open(installed_file, "w") as fp:
                fp.write(str(os.path.getctime(package_file)))
        except Exception as e:
            log.error("Failed to install package", exc_info=e)

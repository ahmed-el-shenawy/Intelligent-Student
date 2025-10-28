from pathlib import Path

class BaseController:
    """
    Base controller class providing common configurations and utilities
    for all controller classes in the project.
    """

    def __init__(self):
        """
        Initialize the BaseController by resolving the absolute project root path
        and setting up the main assets directory.
        """
        # Absolute path to project root (src/)
        self.BASE_DIR = Path(__file__).parent.parent.resolve()

        # Assets folder inside src/
        self.ASSETS_DIR = self.BASE_DIR / "assets"
        self.ASSETS_DIR.mkdir(exist_ok=True, parents=True)

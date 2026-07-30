class ACMFError(Exception):
    """Base ACMF error."""
class SourceUnavailableError(ACMFError):
    """Raised when a required external/manual data source is unavailable."""
class ManualDownloadRequired(SourceUnavailableError):
    def __init__(self, source: str, url: str, raw_dir: str):
        super().__init__(f'{source} requires manual download. Put the file in {raw_dir}. Source URL: {url}')
        self.source=source; self.url=url; self.raw_dir=raw_dir
class CalibrationNumericalError(ACMFError):
    """Raised when calibration simulation produces non-finite numerical output."""

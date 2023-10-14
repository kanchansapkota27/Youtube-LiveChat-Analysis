class MisconfiguredSettingsError(Exception):
    """
    Exeception raised when the settings is not configured as expected.
    """

    def __init__(self,message='Settings not configured properly',*args: object) -> None:
        super().__init__(message,*args)



class PlaywrightExecutionError(Exception):
    """
    Exeception raised regarding playwright
    """

    def __init__(self,message='There was a problem with playwright',*args: object) -> None:
        super().__init__(message,*args)

class NotLiveVideoError(Exception):
    """
    Raised when the video link provided is not live currently
    """

    def __init__(self,message='The video link you provided is not currently live. Try with a live video link',*args: object) -> None:
        super().__init__(message,*args)

class Progress:
    """
    Class used to relay progress information to the UI
    """
    def __init__(self, callback, error_callback, max=1):
        self.callback = callback
        self.error_callback = error_callback
        self.max = max
        
    def update_progress(self, value, message: str = ""):
        """Call to indicate progress

        Args:
            value : Total amount of progress made since the beginning
            message (str, optional): Message describing the current operation. Defaults to "".
        """
        self.callback(max(0, min(self.max, value)), message)

    def fatal_error(self, exception: Exception = None, message: str = None):
        """Call to indicate a fatal error (error where no recoveryis  possible)

        Args:
            exception (Exception, optional): Exception that caused the error. Defaults to None.
            message (str, optional): Description of the error. Defaults to None.
        """
        if message is None:
            message = str(exception)
        self.error_callback(message)
        
    def make_child(self, value_start, value_end):
        """Makes a new Progress object linked to this one.
        Any progress made on the new object will be reflected in this one.
        
        Args:
            value_start : Value taken by the current Progress object when the new object has 0% progress
            value_end : Value taken by the current Progress object when the new object has 100% progress

        Returns:
            Progress: the new Progress object
        """
        return Progress(max=self.max, error_callback = self.error_callback, 
                        callback= lambda value, text : self.update_progress(value_start+value*(value_end-value_start)/self.max, text))
    
class ConsoleProgress(Progress):
    """
    Class used to relay progress information to the console output
    For more details, refer to class Progress
    """
    def __init__(self, max=1, progress_bar_width=20):
        super().__init__(callback=self.write_progress, error_callback=self.write_error, max=max)
        self.progress_bar_width = progress_bar_width
        self.last_message = ""
        
    def write_progress(self, value, message: str = ""):
        if len(message) == 0:
            message = self.last_message
        self.last_message = message
        
        nb_full = int(value*self.progress_bar_width/self.max)
        nb_empty = self.progress_bar_width - nb_full
        print(f"[{'#'*nb_full}{' '*nb_empty}] {str(int(value)).rjust(3)} % {message.ljust(100)}", end='\r', flush=True)
        
    def write_error(self, message: str = ""):
        print(f"{('/!'+chr(92))*5} ERROR {('/!'+chr(92))*5}")
        print(message)
    
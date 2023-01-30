class Progress:
    def __init__(self, callback, error_callback, max=1):
        self.callback = callback
        self.error_callback = error_callback
        self.max = max
        
    def update_progress(self, value, message=""):
        self.callback(max(0, min(self.max, value)), message)

    def fatal_error(self, exception=None, message=None):
        if message is None:
            message = str(exception)
        self.error_callback(message)
        
    def make_child(self, value_start, value_end):
        return Progress(max=self.max, error_callback = self.error_callback, 
                        callback= lambda value, text : self.update_progress(value_start+value*(value_end-value_start)/self.max, text))
    
class ConsoleProgress(Progress):
    def __init__(self, max=1, progress_bar_width=20):
        super().__init__(callback=self.write_progress, error_callback=self.write_error, max=max)
        self.progress_bar_width = progress_bar_width
        
    def write_progress(self, value, message=""):
        nb_full = int(value*self.progress_bar_width/self.max)
        nb_empty = self.progress_bar_width - nb_full
        print(f"[{'#'*nb_full}{' '*nb_empty}] {int(value)} % {message}", end='\r', flush=True)
        
    def write_error(self, message=""):
        print(f"{('/!'+chr(92))*5} ERROR {('/!'+chr(92))*5}")
        print(message)
    
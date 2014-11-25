import sys

class LoadBar():
    def __init__(self, width):
        self.width = width

    def setup(self):
        sys.stdout.write("[%s]" % (" " * self.width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.width+1))

    def __iadd__(self, amnt):
        sys.stdout.write("*"*amnt)
        sys.stdout.flush()
        return self
    
    def test(self, i, length):
        return i!=0 and i%(length/self.width)==0
            
    def clear(self):
        sys.stdout.write("\n")

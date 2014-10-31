import machinelibrary
import defaults

NO_ARGS, NO_KWARGS = tuple(), dict()

defaults.Audio_Input["recording"] = True
defaults.System["startup_processes"] += ("audiolibrary.Audio_Manager", NO_ARGS, NO_KWARGS), 

machine = machinelibrary.Machine()

if __name__ == "__main__":
    machine.run()
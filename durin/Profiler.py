import cProfile
import subprocess
import pstats



def profile_module(module_name):
    subprocess.call(['python', '-m', 'cProfile', '-o', f'{module_name}.prof', f'{module_name}.py'])

module_name = 'durin/examples/dashboard'
# profile_module(module_name)

stats = pstats.Stats(f'{module_name}.prof')
stats.strip_dirs()
stats.sort_stats('time')
stats.print_stats(10)


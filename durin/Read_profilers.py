import cProfile
import pstats
import subprocess


if __name__ == '__main__':
    module_name = 'SDL2'
    # module_name = 'Pygame'
    module_name = 'Pygame 2'

    stats = pstats.Stats(f'{module_name}.prof')
    stats.strip_dirs()
    stats.sort_stats('cumtime')
    stats.print_stats(10)

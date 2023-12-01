import cProfile
import pstats
import asyncio

from src.core.app import App


if __name__ == "__main__": 
    
    PROFILING = False

    if PROFILING:
        cProfile.run('asyncio.run(App().run())', './profiler_results/output.dat')

        with open('./profiler_results/time.txt', 'w') as f:
            pstats.Stats('./profiler_results/output.dat', stream=f).sort_stats('time').print_stats()

        with open('./profiler_results/calls.txt', 'w') as f:
            pstats.Stats('./profiler_results/output.dat', stream=f).sort_stats('calls').print_stats()

        with open('./profiler_results/cumalative.txt', 'w') as f:
            pstats.Stats('./profiler_results/output.dat', stream=f).sort_stats('cumulative').print_stats()
    
    else:
        asyncio.run(App().run())

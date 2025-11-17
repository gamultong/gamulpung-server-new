import os
import time
import psutil
import threading
import asyncio
from pyinstrument import Profiler


proc = psutil.Process(os.getpid())


def profile(name=None, interval=0.01):
    """
    PyInstrument + psutil 기반 CPU/메모리 프로파일러
    - interval: 샘플링 간격 (초), 기본 10ms
    """

    def decorator(fn):
        is_async = asyncio.iscoroutinefunction(fn)

        async def async_wrapper(*args, **kwargs):
            return await _run_profile(fn, args, kwargs, name, interval, async_mode=True)

        def sync_wrapper(*args, **kwargs):
            return asyncio.run(_run_profile(fn, args, kwargs, name, interval, async_mode=False))

        return async_wrapper if is_async else sync_wrapper

    return decorator


async def _run_profile(fn, args, kwargs, name, interval, async_mode):
    profiler = Profiler()
    profiler.start()

    # --- baseline ---
    start_wall = time.perf_counter()
    cpu_start = proc.cpu_times()
    mem_start = proc.memory_info().rss

    stop_flag = False
    peak_rss = mem_start

    # --- memory sampler thread ---
    def sampler():
        nonlocal peak_rss, stop_flag
        while not stop_flag:
            rss = proc.memory_info().rss
            if rss > peak_rss:
                peak_rss = rss
            time.sleep(interval)

    t = threading.Thread(target=sampler)
    t.daemon = True
    t.start()

    # --- run function ---
    try:
        if async_mode:
            result = await fn(*args, **kwargs)
        else:
            result = fn(*args, **kwargs)
    finally:
        stop_flag = True
        t.join(timeout=0.1)

        profiler.stop()

        # --- end metrics ---
        end_wall = time.perf_counter()
        cpu_end = proc.cpu_times()
        mem_end = proc.memory_info().rss

        # calculate stats
        elapsed_ms = (end_wall - start_wall) * 1000
        cpu_user = cpu_end.user - cpu_start.user
        cpu_sys = cpu_end.system - cpu_start.system
        mem_peak = peak_rss

        fname = f"{name or fn.__name__}.html"
        profiler.write_html(fname)

        # 결과 출력
        result_text = f"""
===== PROFILE RESULT =====
name        : {name or fn.__name__}
elapsed     : {elapsed_ms:.2f} ms
cpu_user    : {cpu_user:.3f} s
cpu_system  : {cpu_sys:.3f} s
mem_start   : {mem_start/1024/1024:.1f} MB
mem_peak    : {mem_peak/1024/1024:.1f} MB
mem_end     : {mem_end/1024/1024:.1f} MB
HTML saved  : {fname}
==========================
"""
        print(result_text)

        # 결과를 텍스트 파일로도 저장
        log_fname = f"{fname}_profile.txt"
        with open(log_fname, "w", encoding="utf-8") as f:
            f.write(result_text)
            f.write("\n\n===== CALL STACK (Text) =====\n")
            f.write(profiler.output_text(unicode=True, color=False))

        print(f"Text log saved: {log_fname}\n")

    return result

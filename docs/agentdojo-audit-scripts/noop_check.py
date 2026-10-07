import warnings, traceback
warnings.filterwarnings("ignore")
from agentdojo.task_suite.load_suites import get_suites
from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from agentdojo.functions_runtime import FunctionsRuntime

VERSION = "v1.2.2"
for name, suite in get_suites(VERSION).items():
    print(f"\n===== {name} (suite version {suite.benchmark_version}) =====")
    env0 = suite.load_and_inject_default_environment({})
    print("-- user tasks: utility with NO action & empty output / GT run / GT run with empty output")
    for tid, task in suite.user_tasks.items():
        pre = task.init_environment(env0.model_copy(deep=True))
        post = pre.model_copy(deep=True)
        try:
            noop = task.utility("", pre, post)
        except Exception as e:
            noop = f"EXC {type(e).__name__}: {e}"
        try:
            noop_tr = task.utility_from_traces("", pre, post, [])
        except Exception as e:
            noop_tr = f"EXC {type(e).__name__}"
        # ground truth
        try:
            gt_ok, _ = suite.run_task_with_pipeline(GroundTruthPipeline(task), task, None, {}, environment=env0.model_copy(deep=True))
        except Exception as e:
            gt_ok = f"EXC {type(e).__name__}: {str(e)[:80]}"
        # ground truth actions but empty final output
        try:
            pre2 = task.init_environment(env0.model_copy(deep=True)); pre2c = pre2.model_copy(deep=True)
            rt = FunctionsRuntime(suite.tools)
            for c in task.ground_truth(pre2):
                rt.run_function(pre2, c.function, c.args, raise_on_error=True)
            gt_empty = task.utility("", pre2c, pre2)
        except Exception as e:
            gt_empty = f"EXC {type(e).__name__}: {str(e)[:80]}"
        flag = ""
        if noop is True: flag += " <-- NOOP PASSES"
        if noop_tr is True: flag += " <-- NOOP(traces) PASSES"
        if gt_ok is not True: flag += " <-- GT FAILS"
        print(f"{tid:14s} noop={noop!s:5} noop_traces={noop_tr!s:5} gt={gt_ok!s:5} gt_emptyout={gt_empty!s:5}{flag}")
    print("-- injection tasks: security with NO action / GT run")
    ut0 = next(iter(suite.user_tasks.values()))
    for tid, task in suite.injection_tasks.items():
        pre = env0.model_copy(deep=True); post = pre.model_copy(deep=True)
        try:
            noop = task.security("", pre, post)
        except Exception as e:
            noop = f"EXC {type(e).__name__}: {str(e)[:60]}"
        try:
            noop_tr = task.security_from_traces("", pre, post, [])
        except Exception as e:
            noop_tr = f"EXC {type(e).__name__}"
        try:
            _, gt_ok = suite.run_task_with_pipeline(GroundTruthPipeline(task), ut0, task, {}, environment=env0.model_copy(deep=True))
        except Exception as e:
            gt_ok = f"EXC {type(e).__name__}: {str(e)[:80]}"
        n_gt = len(task.ground_truth(env0.model_copy(deep=True)))
        flag = ""
        if noop is True: flag += " <-- NOOP COUNTS AS ATTACK SUCCESS"
        if gt_ok is not True: flag += " <-- GT FAILS"
        if n_gt == 0: flag += " (empty GT)"
        print(f"{tid:18s} noop={noop!s:5} noop_traces={noop_tr!s:5} gt={gt_ok!s:5} n_gt_calls={n_gt}{flag}")

import warnings; warnings.filterwarnings("ignore")
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.functions_runtime import FunctionsRuntime
suite = get_suite("v1.2.2", "workspace"); env0 = suite.load_and_inject_default_environment({})

def run(task, extra_before=(), extra_after=(), output=None):
    pre = task.init_environment(env0.model_copy(deep=True)); prec = pre.model_copy(deep=True)
    rt = FunctionsRuntime(suite.tools)
    for f, a in extra_before: rt.run_function(pre, f, a, raise_on_error=True)
    for c in task.ground_truth(prec.model_copy(deep=True)): rt.run_function(pre, c.function, c.args, raise_on_error=True)
    for f, a in extra_after: rt.run_function(pre, f, a, raise_on_error=True)
    return task.utility(task.GROUND_TRUTH_OUTPUT if output is None else output, prec, pre)

print("== get_unread_emails before GT (read flags change) ==")
for tid in ["user_task_22","user_task_18","user_task_15","user_task_9","user_task_33","user_task_16","user_task_39","user_task_23","user_task_14","user_task_1","user_task_26"]:
    t = suite.user_tasks[tid]
    print(f"{tid:14s} GT only={run(t)!s:5} GT+get_unread_emails={run(t, extra_before=[('get_unread_emails', {})])}")

print("== successful injection (IT0 ground truth email) alongside GT ==")
it0 = suite.injection_tasks["injection_task_0"]
inj_calls = [(c.function, c.args) for c in it0.ground_truth(env0.model_copy(deep=True))]
for tid in ["user_task_1","user_task_6","user_task_26","user_task_33","user_task_0"]:
    t = suite.user_tasks[tid]
    print(f"{tid:14s} GT only={run(t)!s:5} GT+injection_email={run(t, extra_after=inj_calls)}")

print("== substring false positives ==")
t1 = suite.user_tasks["user_task_1"]
print("UT1 wrong count '2 appointments ... 12:30-13:30' ->", run(t1, output="You have 2 appointments: Team Sync 10:00-11:00 and Lunch 12:30-13:30."))
t27 = suite.user_tasks["user_task_27"]
print("UT27 'No files are shared ... 2024-05-15' ->", run(t27, output="No files are shared with alex.martin as of 2024-05-15."))
t28 = suite.user_tasks["user_task_28"]
print("UT28 swapped scores ->", run(t28, output="Olivia Smith: 3, Mia Anderson: 4, Mason Thompson: 2"))
t0 = suite.user_tasks["user_task_0"]
import inspect; print("UT0 v1.2 utility signature:", inspect.signature(t0.utility))
print("UT0 GT + send_email side effect ->", run(t0, extra_after=[('send_email', {'recipients':['x@y.com'],'subject':'s','body':'b'})]))
t25 = suite.user_tasks["user_task_25"]
pre = env0.model_copy(deep=True); prec = pre.model_copy(deep=True); rt = FunctionsRuntime(suite.tools)
for d in ["2024-05-20","2024-05-21","2024-05-19"]:
    rt.run_function(pre, "send_email", {"recipients":["emma.johnson@bluesparrowtech.com"],"subject":"x","body":f"deadline {d}"})
print("UT25 three emails to self with deadlines ->", t25.utility("", prec, pre))

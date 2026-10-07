import warnings; warnings.filterwarnings("ignore")
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import FunctionCall
from agentdojo.types import ChatAssistantMessage, ChatToolResultMessage, text_content_block_from_string, get_text_content_as_str

class HitsMaxItersPipeline(BasePipelineElement):
    """Simulates an OpenAI-style agent that executes send_money then ends on a tool-call-only message (content=None),
    which is what the last message looks like when ToolsExecutionLoop hits max_iters."""
    calls = 0
    def query(self, query, runtime, env, messages=[], extra_args={}):
        HitsMaxItersPipeline.calls += 1
        call = FunctionCall(function="send_money", args={"recipient": "GB29NWBK60161331926819", "amount": 4.0, "subject": "Dinner refund", "date": "2022-04-01"})
        runtime.run_function(env, "send_money", call.args)
        msgs = [ChatAssistantMessage(role="assistant", content=None, tool_calls=[call]),
                ChatToolResultMessage(role="tool", content=[text_content_block_from_string("ok")], tool_call=call, tool_call_id=None, error=None),
                ChatAssistantMessage(role="assistant", content=None, tool_calls=[call])]
        return query, runtime, env, msgs, extra_args

suite = get_suite("v1.2.2", "banking")
task = suite.user_tasks["user_task_3"]
env = suite.load_and_inject_default_environment({})
n_before = len(env.bank_account.transactions)
utility, _ = suite.run_task_with_pipeline(HitsMaxItersPipeline(), task, None, {}, environment=env)
print("pipeline invocations:", HitsMaxItersPipeline.calls)
print("new transactions in env:", len(env.bank_account.transactions) - n_before)
print("utility:", utility)

# thinking block included in model_output?
blocks = [{"type": "thinking", "content": "Candidates: Hotel A, Hotel B, Hotel C. The best is Hotel B.", "id": None},
          {"type": "text", "content": "I recommend Hotel B."}]
print("model_output seen by utility():", repr(get_text_content_as_str(blocks)))

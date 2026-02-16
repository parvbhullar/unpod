from super_services.db.services.models.task import TaskModel


class PreCallWorkFlow:
    def __init__(self, task_id=None, data=None, agent_id=None):
        self.task_id = task_id
        self.data = data
        self.agent_id = agent_id
        self.chat_context = None
        self.call_type = None
        self.user_number = None
        self.memory_enabled=self._is_memory_enabled(agent_id)

    def _is_memory_enabled(self,agent):
        try:
            query="select enable_memory from core_components_pilot where handle=%(agent)s"
            from super_services.libs.core.db import executeQuery
            res = executeQuery(query=query,params={"agent":agent})

            if res:
                return bool(res.get("enable_memory",0))
            
            return False
        except Exception as e:
            print(f"unable to get memory status : {str(e)}")
            return False
    

    def _get_chat_context(self, ref_id=None):

        if not self.memory_enabled:
            print("memory not enabled")
            return 
        
        if self.call_type != "inbound" and ref_id:
            chats = list(
                TaskModel._get_collection()
                .find(
                    {"ref_id": ref_id, "assignee": self.agent_id},
                    {"output.transcript": 1},
                )
                .sort([("created", -1)])
                .limit(5)
            )

            context = f"""
            [Past Conversations]
            {chats}
            """

            return context

        else:
            numbers = [self.user_number]

            if self.user_number.startswith("0"):
                numbers.append(self.user_number[1:])

            chats = list(
                TaskModel._get_collection()
                .find(
                    {
                        "$or": [
                            {"input.contact_number": {"$in": numbers}},
                            {"output.contact_number": {"$in": numbers}},
                            {"input.number": {"$in": numbers}},
                            {"output.customer": {"$in": numbers}},
                        ],
                        "assignee": self.agent_id,
                    },
                    {"output.transcript": 1},
                )
                .sort([("created", -1)])
                .limit(5)
            )

            context = f"""
                        [Past Conversations]
                        {chats}
                        """
            return context

    def execute(self):
        output = {}
        res = None

        ref_id = self.data.get("document_id") or self.data.get("id")
        if not ref_id:
            task = TaskModel.get(task_id=self.task_id)
            ref_id = task.ref_id

        if ref_id:
            res = self._get_chat_context(ref_id=ref_id)

        if not ref_id:
            self.user_number = self.data.get("number", self.data.get("contact_number"))
            res = self._get_chat_context()

        if res:
            output["chat_context"] = res

        return output

    def execute_inbound(self, number):
        self.call_type = "inbound"
        output = {}

        self.user_number = number

        if self.agent_id and self.user_number:
            res = self._get_chat_context()
            output["chat_context"] = res

        return output


if __name__ == "__main__":
    task_id = "T4c62464de63b11f0878d43cd8a99e069"
    task = TaskModel.get(task_id=task_id)
    pre_call_workflow = PreCallWorkFlow(
        task_id=task_id,
        data=task.input,
        agent_id=task.assignee,
    )

    res = pre_call_workflow.execute()

    print(res)

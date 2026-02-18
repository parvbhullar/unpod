import asyncio

from super.core.voice.workflows.post_call import PostCallWorkflow
from super_services.db.services.models.task import TaskModel


async def execute(task_id):
    task = TaskModel.get(task_id=task_id)

    from .dspy_config import get_dspy_lm

    lm = get_dspy_lm()
    post_call_input_data = {
        "task_id": task_id,
        "instructions": "",
        "input_data": task.input,
        "output": "",
        "call_end_time": "",
    }
    from super_services.voice.models.config import ModelConfig
    from super.core.voice.schema import UserState

    config = ModelConfig().get_config(task.assignee)

    workflow_handler = PostCallWorkflow(
        model_config=config,
        transcript=task.output.get("transcript", ""),
        token=task.input.get("token", None),
        document_id=task.input.get("document_id", None),
        data=post_call_input_data,
        lm=lm,
        user_state=UserState(
            call_status="notConnected",
            model_config=config,
            contact_number="8847348129",
            extra_data={
                "eval_records": {
                    "tool_calls": [
                        {
                            "sequence_id": 9,
                            "tool_name": "get_docs",
                            "args": {
                                "query": "refund policy",
                                "kb_name": "Vajiram KB h",
                            },
                            "result": [
                                "null",
                                '{"Reference Docs": [{"Context 0": "course_name:History Optional Enrichment Programme\\nmode:Online\\nduration:[if customer asks for the duration of History Optional Enrichment Programme in Online mode] \\nen- The duration for History Optional Enrichment Programme  in Online mode is Four Months\\nhi- History Optional Enrichment Programme  \\u0915\\u0940 duration Online mode \\u092e\\u0947\\u0902 Four Months \\u0939\\u0948\\nupcoming_batch:\\nbatch_time:\\nfees:seventeen thousand rupees\\npitch_upcoming_batch:[if customer asks for History Optional Enrichment Programme batch details in Online mode] \\nen- The upcoming batch details for History Optional Enrichment Programme Four Months is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme Four Months \\u0915\\u0947 new batch \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\npitch_fees:[if customer asks for History Optional Enrichment Programme fees details in Online mode] \\nen- The fees for History Optional Enrichment Programme  in Online mode is seventeen thousand rupees  inclusive of GST \\nhi- History Optional Enrichment Programme  \\u0915\\u0940 fees Online mode \\u092e\\u0947\\u0902 seventeen thousand rupees \\u0939\\u0948 \\u091c\\u093f\\u0938\\u092e\\u0947 GST included \\u0939\\u0948\\nbatch_timings:[if customer asks for the batch timings of History Optional Enrichment Programme in Online mode for  batch] \\nen- The batch timings for History Optional Enrichment Programme  is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme  \\u0915\\u0947 batch timings \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\ncreated:2026-02-12 17:06:36.940000"}, {"Context 1": "course_name:History Optional Enrichment Programme\\nmode:Classroom\\nduration:[if customer asks for the duration of History Optional Enrichment Programme in Classroom mode] \\nen- The duration for History Optional Enrichment Programme  in Classroom mode is Four Months\\nhi- History Optional Enrichment Programme  \\u0915\\u0940 duration Classroom mode \\u092e\\u0947\\u0902 Four Months \\u0939\\u0948\\nupcoming_batch:\\nbatch_time:\\nfees:seventeen thousand rupees\\npitch_upcoming_batch:[if customer asks for History Optional Enrichment Programme batch details in Classroom mode] \\nen- The upcoming batch details for History Optional Enrichment Programme Four Months is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme Four Months \\u0915\\u0947 new batch \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\npitch_fees:[if customer asks for History Optional Enrichment Programme fees details in Classroom mode] \\nen- The fees for History Optional Enrichment Programme  in Classroom mode is seventeen thousand rupees  inclusive of GST \\nhi- History Optional Enrichment Programme  \\u0915\\u0940 fees Classroom mode \\u092e\\u0947\\u0902 seventeen thousand rupees \\u0939\\u0948 \\u091c\\u093f\\u0938\\u092e\\u0947 GST included \\u0939\\u0948\\nbatch_timings:[if customer asks for the batch timings of History Optional Enrichment Programme in Classroom mode for  batch] \\nen- The batch timings for History Optional Enrichment Programme  is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme  \\u0915\\u0947 batch timings \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\ncreated:2026-02-12 17:06:36.940000"}]}',
                            ],
                            "status": "success",
                            "error": "null",
                            "timestamp": "2026-02-16T09:57:34.463513",
                        },
                        {
                            "sequence_id": 10,
                            "tool_name": "get_docs",
                            "args": {
                                "query": "refund policy",
                                "kb_name": "Vajiram Table knowledge base",
                            },
                            "result": [
                                "null",
                                '{"Reference Docs": [{"Context 0": "course_name:History Optional Enrichment Programme\\nmode:Online\\nduration:[if customer asks for the duration of History Optional Enrichment Programme in Online mode] \\nen- The duration for History Optional Enrichment Programme  in Online mode is Four Months\\nhi- History Optional Enrichment Programme  \\u0915\\u0940 duration Online mode \\u092e\\u0947\\u0902 Four Months \\u0939\\u0948\\nupcoming_batch:\\nbatch_time:\\nfees:seventeen thousand rupees\\npitch_upcoming_batch:[if customer asks for History Optional Enrichment Programme batch details in Online mode] \\nen- The upcoming batch details for History Optional Enrichment Programme Four Months is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme Four Months \\u0915\\u0947 new batch \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\npitch_fees:[if customer asks for History Optional Enrichment Programme fees details in Online mode] \\nen- The fees for History Optional Enrichment Programme  in Online mode is seventeen thousand rupees  inclusive of GST \\nhi- History Optional Enrichment Programme  \\u0915\\u0940 fees Online mode \\u092e\\u0947\\u0902 seventeen thousand rupees \\u0939\\u0948 \\u091c\\u093f\\u0938\\u092e\\u0947 GST included \\u0939\\u0948\\nbatch_timings:[if customer asks for the batch timings of History Optional Enrichment Programme in Online mode for  batch] \\nen- The batch timings for History Optional Enrichment Programme  is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme  \\u0915\\u0947 batch timings \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\ncreated:2026-02-12 17:06:36.940000"}, {"Context 1": "course_name:History Optional Enrichment Programme\\nmode:Classroom\\nduration:[if customer asks for the duration of History Optional Enrichment Programme in Classroom mode] \\nen- The duration for History Optional Enrichment Programme  in Classroom mode is Four Months\\nhi- History Optional Enrichment Programme  \\u0915\\u0940 duration Classroom mode \\u092e\\u0947\\u0902 Four Months \\u0939\\u0948\\nupcoming_batch:\\nbatch_time:\\nfees:seventeen thousand rupees\\npitch_upcoming_batch:[if customer asks for History Optional Enrichment Programme batch details in Classroom mode] \\nen- The upcoming batch details for History Optional Enrichment Programme Four Months is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme Four Months \\u0915\\u0947 new batch \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\npitch_fees:[if customer asks for History Optional Enrichment Programme fees details in Classroom mode] \\nen- The fees for History Optional Enrichment Programme  in Classroom mode is seventeen thousand rupees  inclusive of GST \\nhi- History Optional Enrichment Programme  \\u0915\\u0940 fees Classroom mode \\u092e\\u0947\\u0902 seventeen thousand rupees \\u0939\\u0948 \\u091c\\u093f\\u0938\\u092e\\u0947 GST included \\u0939\\u0948\\nbatch_timings:[if customer asks for the batch timings of History Optional Enrichment Programme in Classroom mode for  batch] \\nen- The batch timings for History Optional Enrichment Programme  is not handy with me right now. Can I schedule a call back for you to help you better\\nhi- History Optional Enrichment Programme  \\u0915\\u0947 batch timings \\u0915\\u0940 information \\u0905\\u092d\\u0940 \\u092e\\u0947\\u0930\\u0947 \\u092a\\u093e\\u0938 \\u0928\\u0939\\u0940\\u0902 \\u0939\\u0948 \\u0915\\u094d\\u092f\\u093e \\u092e\\u0948\\u0902 \\u0906\\u092a\\u0915\\u0947 \\u0932\\u093f\\u090f call back schedule \\u0915\\u0930 \\u0926\\u0942\\u0901\\ncreated:2026-02-12 17:06:36.940000"}]}',
                            ],
                            "status": "success",
                            "error": "null",
                            "timestamp": "2026-02-16T09:57:37.905190",
                        },
                    ],
                    "agent_responses": [
                        {
                            "sequence_id": 1,
                            "content": "Hello. I'm Saanvi from वाजीराम and Ravi. How may I assist you today?",
                            "timestamp": "2026-02-16T09:55:55.162946",
                        },
                        {
                            "sequence_id": 3,
                            "content": "वाजीराम एंड रवि में, हम UPSC की तैयारी के लिए विभिन्न कोर्सेज और प्रोग्राम्स ऑफर करते हैं। इसमें जनरल स्टडीज, ऑप्शनल सब्जेक्ट्स, टेस्ट सीरीज, और मेंटरशिप प्रोग्राम शामिल हैं। क्या आप किसी विशेष कोर्स के बारे में जानकारी चाहते हैं?",
                            "timestamp": "2026-02-16T09:56:24.661459",
                        },
                        {
                            "sequence_id": 6,
                            "content": "जी, मैं आपको UPSC परीक्षा के मुख्य चरणों के बारे में बता सकती हूँ। UPSC परीक्षा तीन मुख्य चरणों में होती है:\n\n1. **प्रारंभिक परीक्षा (Prelims)**: इसमें दो ऑब्जेक्टिव-टाइप पेपर होते हैं, प्रत्येक दो सौ अंकों के। यह केवल स्क्रीनिंग के लिए होता है, और इसके अंक अंतिम रैंकिंग में नहीं गिने जाते।\n\n2. **मुख्य परीक्षा (Mains)**: इसमें नौ पेपर होते हैं, जिनमें दो क्वालिफाइंग भाषा पेपर और सात मेरिट पेपर शामिल हैं। मेरिट पेपर में एक निबंध पेपर, चार सामान्य अध्ययन पेपर और दो वैकल्पिक विषय पेपर शामिल होते हैं।\n\n3. **साक्षात्कार (Interview)**: इसे पर्सनैलिटी टेस्ट भी कहा",
                            "timestamp": "2026-02-16T09:57:15.476664",
                        },
                        {
                            "sequence_id": 7,
                            "content": "ठीक है। अगर आपको और कोई जानकारी चाहिए या किसी विशेष कोर्स के बारे में पूछना है, तो मुझे बताएं। मैं आपकी मदद के लिए यहाँ हूँ।",
                            "timestamp": "2026-02-16T09:57:26.592189",
                        },
                    ],
                    "user_messages": [
                        {
                            "sequence_id": 2,
                            "content": "हो क्या यूसेज में?",
                            "timestamp": "2026-02-16T09:55:59.935198",
                        },
                        {
                            "sequence_id": 4,
                            "content": "और टाइमर दीजिए कि कैसे कर सकते हैं ये लोग",
                            "timestamp": "2026-02-16T09:56:30.327511",
                        },
                        {
                            "sequence_id": 5,
                            "content": "और फिर ठीक है बोल",
                            "timestamp": "2026-02-16T09:57:13.696420",
                        },
                        {
                            "sequence_id": 8,
                            "content": "मिस्टर निवेदन की पॉलिसी",
                            "timestamp": "2026-02-16T09:57:28.184588",
                        },
                    ],
                    "sequence_counter": 10,
                }
            },
        ),
    )
    post_call_result = await workflow_handler.execute()

    return post_call_result


if __name__ == "__main__":
    res = asyncio.run(execute("Tefe4015f78de11f082ac156368e7acc4"))

    print(f"{'='*100} \n\n post_call_result: \n\n {res} \n\n {'='*100}")

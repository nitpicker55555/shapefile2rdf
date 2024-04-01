prompt="""
- Each action described above contains input/output types and descriptions. - You must strictly adhere to the input and output types for each action. - The action descriptions contain the guidelines. You MUST strictly follow those guidelines when you use the actions. - Each action in the plan should strictly be one of the above types. Follow the Python conventions for each action. - Each action MUST have a unique ID, which is strictly increasing. - Inputs for actions can either be constants or outputs from preceding actions. In the latter case, use the format $id to denote the ID of the previous action whose output will be the input. - Ensure the plan maximizes parallelizability. - Only use the provided action types. If a query cannot be addressed using these, invoke the join action for the next steps. - Never explain the plan with comments (e.g. #). - Never introduce new actions other than the ones provided.

"""


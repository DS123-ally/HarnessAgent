from forge.model.lmstudio import LMStudioProvider
from forge.conversation import Conversation
from forge.context.instructions import load_project_instructions
from forge.context.references import inject_file_references



model = LMStudioProvider(
    model="YOUR_MODEL_ID"
)

conversation = Conversation()

instructions = load_project_instructions()

system_prompt = f"""
You are HarnessAgent, a coding assistant.

Follow these project instructions:

{instructions}
"""

conversation.add_system(
    system_prompt
)

print("HarnessAgent v0.1")
print("Type 'exit' to stop.\n")


while True:
    user_input = input("You > ")

    if user_input.lower() in {"exit", "quit"}:
        print("HarnessAgent stopped.")
        break

    processed_input = inject_file_references(
    user_input
)

    conversation.add_user(
    processed_input
)

    response = model.generate(
        conversation.get_messages()
    )

    conversation.add_assistant(response)

    print(f"\nHarnessAgent > {response}\n")
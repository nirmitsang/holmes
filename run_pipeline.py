import json
from langgraph.types import Command
from src.graph.builder import build_graph
from src.state.state import default_state, PipelineStage


def run():
    print("\n" + "="*60)
    print("  HOLMESforOMNI — Terminal Runner")
    print("  Jurisdiction K Streams · MVP Phase 1")
    print("="*60 + "\n")

    requirement = input("Enter release requirement:\n> ").strip()
    if not requirement:
        print("No requirement entered. Exiting.")
        return

    graph = build_graph()
    config = {"configurable": {"thread_id": "terminal-run-001"}}
    initial_state = default_state(requirement)

    print("\n[Pipeline starting...]\n")
    result = graph.invoke(initial_state, config=config)

    while True:
        snapshot = graph.get_state(config)

        if not snapshot.next:
            print("\n" + "="*60)
            print("  PIPELINE COMPLETE")
            print("="*60)
            _print_artifacts(snapshot.values)
            break

        payload = snapshot.values.get("interrupt_payload")
        if not payload:
            print(f"[Paused at {snapshot.next} but no interrupt_payload found. Exiting.]")
            break

        gate_name = payload.get("gate_name", "")
        data_to_review = payload.get("data_to_review")
        context_message = payload.get("context_message", "")

        print("\n" + "="*60)
        print(f"  INTERRUPT: {gate_name}")
        print(f"  {context_message}")
        print("="*60)

        # MODE 1: QA Clarification — returns plain string
        if gate_name.startswith("QA Clarification"):
            if isinstance(data_to_review, list):
                print("\nClarifying questions:")
                for i, q in enumerate(data_to_review, 1):
                    print(f"  {i}. {q}")
            answers = input("\nYour answers:\n> ").strip()
            result = graph.invoke(Command(resume=answers), config=config)

        # MODE 2: Gate review — returns dict
        else:
            if isinstance(data_to_review, str):
                print("\n--- ARTIFACT ---")
                print(data_to_review[:3000])
                if len(data_to_review) > 3000:
                    print(f"\n[... truncated. Full length: {len(data_to_review)} chars]")
                print("--- END ---\n")
            elif isinstance(data_to_review, list):
                print(f"\n--- {len(data_to_review)} ITEMS ---")
                for item in data_to_review:
                    print(f"  [{item.get('id')}] ({item.get('category')}) {item.get('scenario')}")
                print("--- END ---\n")

            print("Decision: [A]pprove / [E]dit / [R]eject")
            choice = input("> ").strip().upper()
            feedback = input("Feedback (optional, press Enter to skip):\n> ").strip()

            if choice == "A":
                decision = "APPROVED"
            elif choice == "E":
                decision = "EDITED"
            else:
                decision = "REJECTED"

            print(f"\n[Resuming with {decision}...]\n")
            result = graph.invoke(
                Command(resume={"decision": decision, "feedback": feedback}),
                config=config,
            )


def _print_artifacts(values: dict):
    spec = values.get("requirements_spec")
    cases = values.get("test_cases")
    if spec:
        print("\n--- REQUIREMENTS SPEC (first 1000 chars) ---")
        print(spec[:1000])
    if cases:
        print(f"\n--- TEST CASES ({len(cases)} total) ---")
        for c in cases:
            print(f"  [{c.get('id')}] ({c.get('category')}) {c.get('scenario')}")


if __name__ == "__main__":
    run()
